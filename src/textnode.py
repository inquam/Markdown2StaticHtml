from enum import Enum 

class TextType(Enum):
    NORMAL  = "normal"
    TEXT    = "text"
    BOLD    = "bold"
    ITALIC  = "italic"
    CODE    = "code"
    LINK    = "link"
    IMAGE   = "image"

class TextNode:
    def __init__(self, text, text_type = TextType.TEXT, url = None):
        self.text: str                  = text
        self.text_type: TextType|None   = text_type
        self.url: str|None              = url

    def __eq__(self, other) -> bool:
        return (self.text == other.text and self.text_type == other.text_type and self.url == other.url)

    def __repr__(self) -> str:
        return f"TextNode({self.text}, {self.text_type.value}, {self.url})"