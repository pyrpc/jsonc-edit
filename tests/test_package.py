import jsonc_edit

def test_imports():
    assert jsonc_edit is not None

def test_version_exists_and_is_string():
    assert hasattr(jsonc_edit, "__version__")
    assert isinstance(jsonc_edit.__version__, str)
