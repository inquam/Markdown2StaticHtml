class HTMLNode:
    def __init__(self, tag: str|None = None, value: str|None = None, children: list["HTMLNode"]|None = None, props: dict[str, str]|None = None):
        self.tag = tag
        self.value = value
        self.children = children
        self.props = props
        self.children = [] if children is None else children
        self.props = [] if props is None else props

    def __eq__(self, other) -> bool:
        return self.tag == other.tag and self.value == other.value and self.children == other.children

    def to_html(self) -> str:
        raise NotImplementedError()

    def props_to_html(self) -> str:
        str = ""
        if self.props:
            for prop_name, prop_value in self.props.items():
                str += f" {prop_name}=\"{prop_value}\""

        return str

    def __repr__(self) -> str:
        return f"HTMLNode({self.tag}, {self.value}, {self.children}, {self.props})"

class ParentNode(HTMLNode):
    def __init__(self, tag: str|None, children: list["HTMLNode"]|None, props: dict[str, str]|None = None):
        super().__init__(tag, None, children, props)

    def to_html(self) -> str:
        if self.tag is None:
            raise ValueError("Parent has not tag")

        children_html = ""

        for child in self.children:
            #if child.value is None:
            #    raise ValueError("Child has no value")
            children_html += child.to_html()

        return f"<{self.tag}{self.props_to_html()}>{children_html}</{self.tag}>"

class LeafNode(HTMLNode):
    def __init__(self, tag: str|None, value: str|None, props: dict[str, str]|None = None):
        super().__init__(tag, value, None, props)

    def to_html(self):
        if self.value is None:
            raise ValueError("Leaf has no value")
        elif self.tag is None:
            return self.value
        else:
            return f"<{self.tag}{self.props_to_html()}>{self.value}</{self.tag}>"
