from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TextFragment:
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    size: Optional[int] = None
    font: Optional[str] = None
    bbox: Optional[tuple] = None

@dataclass
class Paragraph:
    fragments: List[TextFragment] = field(default_factory=list)

@dataclass
class Cell:
    paragraphs: List[Paragraph] = field(default_factory=list)

@dataclass
class Table:
    rows: List[List[Cell]] = field(default_factory=list)

@dataclass
class Page:
    number: int = 0
    paragraphs: List[Paragraph] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    width: Optional[float] = None
    height: Optional[float] = None

@dataclass
class InternalDocument:
    pages: List[Page] = field(default_factory=list)

class Parser:
    def parse(self, file_path: str) -> InternalDocument:
        raise NotImplementedError("Метод parse() должен быть реализован в наследнике")

