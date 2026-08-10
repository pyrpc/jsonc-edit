import pytest
from jsonc_edit import edit

def test_path_semantics_dot_notation():
    """Ensure dots in paths are treated as literal property names, not nested objects."""
    source = '{\n  "foo.bar": 1,\n  "foo": { "bar": 2 }\n}'
    
    # Modifying the literal "foo.bar" property
    result = edit(source, ["foo.bar"], 3)
    assert '"foo.bar": 3' in result
    assert '"bar": 2' in result
    
    # Modifying the nested property
    result2 = edit(source, ["foo", "bar"], 4)
    assert '"foo.bar": 1' in result2
    assert '"bar": 4' in result2

def test_path_semantics_array_index():
    """Ensure array indexes work correctly."""
    source = '{\n  "items": ["a", "b", "c"]\n}'
    
    result = edit(source, ["items", 1], "z")
    assert '["a", "z", "c"]' in result

def test_path_semantics_special_characters():
    """Ensure special characters like @ and / are treated literally."""
    source = '{\n  "dependencies": {\n    "@pyrpc/types": "1.0.0"\n  }\n}'
    
    result = edit(source, ["dependencies", "@pyrpc/types"], "2.0.0")
    assert '"@pyrpc/types": "2.0.0"' in result

def test_path_semantics_spaces():
    """Ensure spaces in keys are supported."""
    source = '{\n  "my key": "value"\n}'
    
    result = edit(source, ["my key"], "new_value")
    assert '"my key": "new_value"' in result

def test_path_semantics_complex_nested():
    """Ensure complex nested paths with wildcards and special characters work."""
    source = '''{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}'''
    
    result = edit(source, ["compilerOptions", "paths", "@/*"], ["./dist/*"])
    assert '"@/*": [' in result
    assert '"./dist/*"' in result
