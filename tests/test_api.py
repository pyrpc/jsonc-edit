import pytest
import os
from pathlib import Path
from jsonc_edit import modify, apply_edits, edit, edit_file, Edit, JsoncParseError
import jsonc_edit._api as api

pytestmark = pytest.mark.integration

@pytest.fixture(autouse=True)
def cleanup_daemon():
    # Make sure daemon starts fresh if needed, though reuse is expected.
    # We will just verify it stays alive across tests naturally.
    yield
    # No explicit kill, we want to verify it stays alive.

def test_basic_modification():
    text = '{\n  "compilerOptions": {}\n}'
    edits = modify(text, ["compilerOptions", "paths", "@pyrpc/types"], ["./__pyrpc.d.ts"])
    
    # Should get some edits
    assert len(edits) > 0
    assert isinstance(edits[0], Edit)
    
    new_text = apply_edits(text, edits)
    assert '"paths":' in new_text
    assert '"@pyrpc/types":' in new_text
    assert '"./__pyrpc.d.ts"' in new_text

def test_edit_convenience():
    source = '{\n  "hello": "world"\n}'
    
    result = edit(source, ["hello"], "universe")
    assert '"universe"' in result
    
    # Test no changes (e.g. value is the same)
    result_same = edit(source, ["hello"], "world")
    assert result_same == source

def test_edit_file_convenience(tmp_path):
    source_file = tmp_path / "config.json"
    source_file.write_text('{\n  "hello": "world"\n}', encoding="utf-8")
    
    # Get original mtime to verify it doesn't change when there's no edit
    mtime_before = source_file.stat().st_mtime
    
    # Test actual edit
    edit_file(source_file, ["hello"], "universe")
    assert '"universe"' in source_file.read_text(encoding="utf-8")
    
    mtime_after = source_file.stat().st_mtime
    
    # Test no change edit
    edit_file(source_file, ["hello"], "universe")
    # File shouldn't be touched
    assert source_file.stat().st_mtime == mtime_after

def test_existing_object():
    text = '{\n  "compilerOptions": {\n    "paths": {}\n  }\n}'
    edits = modify(text, ["compilerOptions", "paths", "@pyrpc/types"], ["./__pyrpc.d.ts"])
    new_text = apply_edits(text, edits)
    assert '"@pyrpc/types"' in new_text

def test_existing_property():
    text = '{\n  "compilerOptions": {\n    "paths": {\n      "@pyrpc/types": []\n    }\n  }\n}'
    edits = modify(text, ["compilerOptions", "paths", "@pyrpc/types"], ["./__pyrpc.d.ts"])
    new_text = apply_edits(text, edits)
    assert '"./__pyrpc.d.ts"' in new_text
    assert "[]" not in new_text

def test_nested_paths():
    text = '{}'
    edits = modify(text, ["a", "b", "c"], 42)
    new_text = apply_edits(text, edits)
    assert '"a"' in new_text
    assert '"b"' in new_text
    assert '"c": 42' in new_text

def test_arrays():
    text = '{\n  "items": [1, 2]\n}'
    # Insert at end of array (index 2)
    edits = modify(text, ["items", 2], 3)
    new_text = apply_edits(text, edits)
    assert '3' in new_text

def test_multiple_operations():
    text = '{}'
    edits1 = modify(text, ["first"], 1)
    text = apply_edits(text, edits1)
    
    edits2 = modify(text, ["second"], 2)
    text = apply_edits(text, edits2)
    
    assert '"first": 1' in text
    assert '"second": 2' in text

def test_idempotent_application():
    text = '{\n  "key": "value"\n}'
    edits = modify(text, ["key"], "value")
    new_text = apply_edits(text, edits)
    assert new_text == text

def test_jsonc_parse_error():
    with pytest.raises(JsoncParseError):
        # Pass None as text to force a JS TypeError in the parser
        apply_edits(None, [Edit(offset=0, length=1, content="")])

from jsonc_edit import get_value, MISSING

def test_get_value():
    text = '{\n  "a": 1,\n  "b": {"c": [1, 2, 3]},\n  "d": null\n}'
    
    assert get_value(text, ["a"]) == 1
    assert get_value(text, ["b", "c"]) == [1, 2, 3]
    assert get_value(text, ["b", "c", 1]) == 2
    assert get_value(text, ["d"]) is None
    
    # Missing nodes should return MISSING sentinel, not None (which is a valid JSON value)
    assert get_value(text, ["x"]) is MISSING
    assert get_value(text, ["b", "x"]) is MISSING
    assert get_value(text, ["b", "c", 5]) is MISSING

from jsonc_edit import edit_many

def test_edit_many():
    source = '{\n  "a": 1\n}'
    
    result = edit_many(source, [
        (["b"], 2),
        (["c"], 3)
    ])
    
    assert '"b": 2' in result
    assert '"c": 3' in result
