import os
import re
from htmlnode import LeafNode, ParentNode, HTMLNode
from textnode import TextNode, TextType

def text_node_to_html_node(text_node: TextNode) -> LeafNode:
    match text_node.text_type:
        case TextType.TEXT:
            return LeafNode(None, text_node.text)
        case TextType.BOLD:
            return LeafNode("b", text_node.text)
        case TextType.ITALIC:
            return LeafNode("i", text_node.text)
        case TextType.CODE:
            return LeafNode("code", text_node.text)
        case TextType.LINK:
            return LeafNode("a", text_node.text, {"href": text_node.url})
        case TextType.IMAGE:
            return LeafNode("img", "", {"src": text_node.url, "alt": text_node.text})
        case _:
            raise ValueError("Incorrect text type")


def split_nodes_delimiter(old_nodes: list["TextNode"], delimiter: str, text_type: TextType) -> list["TextNode"]:
    result = []
    for node in old_nodes:
        # Skip nodes that already have the target text_type
        if node.text_type == text_type:
            result.append(node)
            continue

        # Split node text by delimiter
        pieces = node.text.split(delimiter)
        # If no delimiter found, keep node as is
        if len(pieces) == 1:
            result.append(node)
            continue

        # Process pieces alternating between original and delimited content
        for i, piece in enumerate(pieces):
            if piece != "":  # Skip empty pieces
                if i % 2 == 0:
                    # Even pieces keep original text_type
                    result.append(TextNode(piece, node.text_type))
                else:
                    # Odd pieces get new text_type
                    result.append(TextNode(piece, text_type))

    return result


def extract_markdown_images(text: TextNode | str) -> list[tuple[str, str]]:
    # Regular expression pattern for Markdown images
    # ![alt text](url)
    pattern = r'!\[(.*?)\]\((.*?)\)'

    # Find all matches in the text
    # Returns list of tuples with (alt_text, url)
    matches = re.findall(pattern, text.text if isinstance(text, TextNode) else text)

    return matches

def extract_markdown_links(text: TextNode | str) -> list[tuple[str, str]]:
    # Regular expression pattern for Markdown links
    # [link text](url)
    pattern = r'\[(.*?)\]\((.*?)\)'

    # Find all matches in the text
    # Returns list of tuples with (link_text, url)
    matches = re.findall(pattern, text.text if isinstance(text, TextNode) else text)

    return matches


def split_nodes_link(old_nodes):
    """Split nodes by markdown links, creating new link nodes"""
    result = []

    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            result.append(old_node)
            continue

        # Get all link positions and information
        links = extract_markdown_links(old_node.text)
        if not links:
            result.append(old_node)
            continue

        # Track current position in text
        curr_idx = 0
        text = old_node.text

        # Process each link match
        for link_text, url in links:
            # Find full link pattern in remaining text
            full_pattern = f"[{link_text}]({url})"
            pattern_idx = text.find(full_pattern, curr_idx)

            # Add text before the link if any
            if pattern_idx > curr_idx:
                result.append(TextNode(text[curr_idx:pattern_idx], TextType.TEXT))

            # Add the link node
            result.append(TextNode(link_text, TextType.LINK, url))

            # Update current position
            curr_idx = pattern_idx + len(full_pattern)

        # Add remaining text after last link if any
        if curr_idx < len(text):
            result.append(TextNode(text[curr_idx:], TextType.TEXT))

    return result


def split_nodes_image(old_nodes):
    """Split nodes by markdown images, creating new image nodes"""
    result = []

    for old_node in old_nodes:
        if old_node.text_type != TextType.TEXT:
            result.append(old_node)
            continue

        # Get all image positions and information
        images = extract_markdown_images(old_node.text)
        if not images:
            result.append(old_node)
            continue

        # Track current position in text
        curr_idx = 0
        text = old_node.text

        # Process each image match
        for alt_text, url in images:
            # Find full image pattern in remaining text
            full_pattern = f"![{alt_text}]({url})"
            pattern_idx = text.find(full_pattern, curr_idx)

            # Add text before the image if any
            if pattern_idx > curr_idx:
                result.append(TextNode(text[curr_idx:pattern_idx], TextType.TEXT))

            # Add the image node
            result.append(TextNode(alt_text, TextType.IMAGE, url))

            # Update current position
            curr_idx = pattern_idx + len(full_pattern)

        # Add remaining text after last image if any
        if curr_idx < len(text):
            result.append(TextNode(text[curr_idx:], TextType.TEXT))

    return result


def text_to_textnodes(text: str) -> list[TextNode]:
    """Convert Markdown text to a list of TextNodes"""
    # Start with a single text node
    nodes = [TextNode(text, TextType.TEXT)]

    # Split on each markdown delimiter in sequence
    nodes = split_nodes_delimiter(nodes, "**", TextType.BOLD)
    nodes = split_nodes_delimiter(nodes, "*", TextType.ITALIC)
    nodes = split_nodes_delimiter(nodes, "`", TextType.CODE)
    nodes = split_nodes_image(nodes)
    nodes = split_nodes_link(nodes)

    return nodes


def markdown_to_blocks(markdown: str) -> list[str]:
    """Split Markdown text into blocks based on blank lines"""
    # Strip leading/trailing whitespace and split on double newlines
    blocks = markdown.strip().split("\n\n")

    # Filter out empty blocks and strip each block
    blocks = [block.strip() for block in blocks if block.strip()]

    return blocks


def block_to_block_type(block: str) -> str:
    """
    Determine the type of a Markdown block.

    Args:
        block (str): A block of Markdown text with leading/trailing whitespace stripped

    Returns:
        str: The type of block - one of 'paragraph', 'heading', 'code', 'quote',
             'unordered_list', or 'ordered_list'
    """

    # Split block into lines for multi-line analysis
    lines = block.split('\n')

    # Check for code block (must start and end with ```)
    if block.startswith('```') and block.endswith('```'):
        return 'code'

    # Check for heading (starts with 1-6 # characters followed by space)
    if block.startswith(('#', '##', '###', '####', '#####', '######')):
        marker_end = block.find(' ')
        if 0 < marker_end <= 6:  # Valid heading marker length
            return 'heading'

    # Check for quote block (every line starts with >)
    if all(line.startswith('>') for line in lines):
        return 'quote'

    # Check for unordered list (every line starts with * or - followed by space)
    if all(line.startswith(('* ', '- ')) for line in lines):
        return 'unordered_list'

    # Check for ordered list
    # Must start with 1 and increment by 1, followed by . and space
    if all(line.startswith(f"{i + 1}. ") for i, line in enumerate(lines)):
        return 'ordered_list'

    # Default case: paragraph
    return 'paragraph'


def text_to_children(text: str) -> list[HTMLNode]:
    """Convert text with inline markdown to a list of HTMLNode objects"""
    nodes = text_to_textnodes(text)
    children = []
    for node in nodes:
        children.append(text_node_to_html_node(node))
    return children


def code_block_to_html_node(block: str) -> HTMLNode:
    """Convert a code block to an HTMLNode"""
    # Remove the ``` delimiters and any language specification
    lines = block.split('\n')[1:-1]  # Remove first and last lines (```)
    code_content = '\n'.join(lines)
    return ParentNode("pre", [LeafNode("code", code_content)])


def quote_block_to_html_node(block: str) -> HTMLNode:
    """Convert a quote block to an HTMLNode"""
    # Remove '> ' from the start of each line and join
    lines = block.split('\n')
    quote_content = '\n'.join(line[2:] for line in lines)
    return ParentNode("blockquote", text_to_children(quote_content))


def paragraph_block_to_html_node(block: str) -> HTMLNode:
    """Convert a paragraph block to an HTMLNode"""
    return ParentNode("p", text_to_children(block))


def heading_block_to_html_node(block: str) -> HTMLNode:
    """Convert a heading block to an HTMLNode"""
    # Count the number of # symbols for heading level
    level = 0
    for char in block:
        if char == '#':
            level += 1
        else:
            break

    content = block[level + 1:]  # Skip the # symbols and the space
    return ParentNode(f"h{level}", text_to_children(content))


def list_item_to_html_node(item: str) -> HTMLNode:
    """Convert a single list item to an HTMLNode"""
    # Remove the list marker and leading space
    if item.startswith('* ') or item.startswith('- '):
        content = item[2:]
    else:  # Ordered list item
        content = item[item.index('. ') + 2:]
    return ParentNode("li", text_to_children(content))


def unordered_list_to_html_node(block: str) -> HTMLNode:
    """Convert an unordered list block to an HTMLNode"""
    items = block.split('\n')
    item_nodes = [list_item_to_html_node(item) for item in items]
    return ParentNode("ul", item_nodes)


def ordered_list_to_html_node(block: str) -> HTMLNode:
    """Convert an ordered list block to an HTMLNode"""
    items = block.split('\n')
    item_nodes = [list_item_to_html_node(item) for item in items]
    return ParentNode("ol", item_nodes)


def markdown_to_html_node(markdown: str) -> HTMLNode:
    """Convert a Markdown document to an HTMLNode"""
    # Split markdown into blocks
    blocks = markdown_to_blocks(markdown)

    # Process each block
    children = []
    for block in blocks:
        block_type = block_to_block_type(block)

        # Create appropriate HTMLNode based on block type
        match block_type:
            case "paragraph":
                children.append(paragraph_block_to_html_node(block))
            case "heading":
                children.append(heading_block_to_html_node(block))
            case "code":
                children.append(code_block_to_html_node(block))
            case "quote":
                children.append(quote_block_to_html_node(block))
            case "unordered_list":
                children.append(unordered_list_to_html_node(block))
            case "ordered_list":
                children.append(ordered_list_to_html_node(block))
            case _:
                raise ValueError(f"Unknown block type: {block_type}")

    # Return all blocks wrapped in a div
    return ParentNode("div", children)


def extract_title(markdown: str) -> str:
    """
    Extract the h1 header from a markdown string.
    Args:
        markdown: The Markdown text to process
    Returns:
        The text content of the first h1 header found
    Raises:
        ValueError: If no h1 header is found
    """
    # Split into lines and look for h1
    lines = markdown.split('\n')
    for line in lines:
        # Check for line starting with single #
        if line.strip().startswith('# '):
            # Remove # and strip whitespace
            return line.strip().removeprefix('# ').strip()

    raise ValueError("No h1 header found in markdown")


def generate_page(from_path: str, template_path: str, dest_path: str):
    """
    Generate an HTML page from markdown content and a template.

    Args:
        from_path: Path to the markdown file
        template_path: Path to the template HTML file
        dest_path: Destination path for the generated HTML file
    """
    print(f"Generating page from {from_path} to {dest_path} using {template_path}")

    # Read markdown content
    with open(from_path, 'r') as f:
        markdown_content = f.read()

    # Read template content
    with open(template_path, 'r') as f:
        template_content = f.read()

    # Convert markdown to HTML
    html_node = markdown_to_html_node(markdown_content)
    html_content = html_node.to_html()

    # Extract title
    title = extract_title(markdown_content)

    # Replace placeholders in template
    final_html = template_content.replace("{{ Title }}", title)
    final_html = final_html.replace("{{ Content }}", html_content)

    # Create destination directory if it doesn't exist
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)

    # Write the final HTML to destination
    with open(dest_path, 'w') as f:
        f.write(final_html)

def generate_pages_recursive(dir_path_content: str, template_path: str, dest_dir_path: str):
    """
    Recursively generate HTML pages from markdown files in a directory.

    Args:
        dir_path_content: Source directory containing markdown files
        template_path: Path to the template HTML file
        dest_dir_path: Destination directory for generated HTML files
    """
    # Ensure the content directory exists
    if not os.path.exists(dir_path_content):
        print(f"Content directory not found: {dir_path_content}")
        return

    # Create destination directory if it doesn't exist
    if not os.path.exists(dest_dir_path):
        os.makedirs(dest_dir_path)

    # Process all entries in the directory
    for item in os.listdir(dir_path_content):
        src_path = os.path.join(dir_path_content, item)

        # If it's a directory, recurse into it
        if os.path.isdir(src_path):
            # Create corresponding directory in destination
            new_dest_dir = os.path.join(dest_dir_path, item)
            new_content_dir = os.path.join(dir_path_content, item)
            generate_pages_recursive(new_content_dir, template_path, new_dest_dir)

        # If it's a markdown file, generate the HTML page
        elif item.endswith('.md'):
            # Replace .md extension with .html for destination path
            dest_file = item[:-3] + '.html'
            dest_path = os.path.join(dest_dir_path, dest_file)

            # Generate the page
            generate_page(src_path, template_path, dest_path)