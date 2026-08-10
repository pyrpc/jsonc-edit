import pytest
from jsonc_edit import edit

pytestmark = pytest.mark.integration

def test_idempotency_no_op():
    """Ensure that editing a value that is already present results in exactly the same string."""
    source = '''{
  // My config
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}'''

    # First edit: adds the new value (which should format somewhat cleanly)
    first_pass = edit(source, ["compilerOptions", "paths", "@pyrpc/types"], ["./__pyrpc.d.ts"])
    
    # Second edit: applies the identical operation to the result of the first pass
    second_pass = edit(first_pass, ["compilerOptions", "paths", "@pyrpc/types"], ["./__pyrpc.d.ts"])
    
    # Assert idempotency: the second pass must not modify the string at all
    assert second_pass == first_pass

def test_idempotency_existing_value():
    """Ensure that editing an already correct complex value in the original source is a true no-op."""
    source = '''{
  "compilerOptions": {
    "paths": {
      "@pyrpc/types": [
        "./__pyrpc.d.ts"
      ]
    }
  }
}'''

    result = edit(source, ["compilerOptions", "paths", "@pyrpc/types"], ["./__pyrpc.d.ts"])
    assert result == source
