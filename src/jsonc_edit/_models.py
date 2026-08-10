from dataclasses import dataclass

@dataclass
class Edit:
    """Represents a text replacement operation."""
    offset: int
    length: int
    content: str
