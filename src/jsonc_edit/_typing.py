from typing import Union, List, Dict, Any

try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

JsonValue = Union[str, int, float, bool, None, Dict[str, 'JsonValue'], List['JsonValue']]
JsonPath = List[Union[str, int]]

class FormattingOptions(TypedDict, total=False):
    insertSpaces: bool
    tabSize: int
    eol: str

ModificationOptions = Dict[str, Union[FormattingOptions, Any]]
