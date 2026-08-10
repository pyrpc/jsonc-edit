from typing import Union, List, Dict, Any

JsonValue = Union[str, int, float, bool, None, Dict[str, 'JsonValue'], List['JsonValue']]
JsonPath = List[Union[str, int]]
ModificationOptions = Dict[str, Any]
