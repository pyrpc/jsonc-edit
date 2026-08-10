import pytest
from jsonc_edit import modify, apply_edits

pytestmark = pytest.mark.integration

def verify_source(original: str, path: list, value, expected_fragments: list, unexpected_fragments: list = None, options: dict = None):
    """Helper to apply edits and verify the resulting source."""
    if options is None:
        options = {"formattingOptions": {"insertSpaces": True, "tabSize": 2}}
    edits = modify(original, path, value, options=options)
    result = apply_edits(original, edits)
    for fragment in expected_fragments:
        assert fragment in result, f"Expected fragment missing:\n{fragment}\nIn:\n{result}"
    if unexpected_fragments:
        for fragment in unexpected_fragments:
            assert fragment not in result, f"Unexpected fragment found:\n{fragment}\nIn:\n{result}"
    return result

def test_line_comments():
    original = '''{
  // compiler settings
  "compilerOptions": {}
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=["// compiler settings", '"@pyrpc/types": [']
    )

def test_block_comments():
    original = '''{
  /* important configuration */
  "compilerOptions": {}
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=["/* important configuration */", '"@pyrpc/types": [']
    )

def test_trailing_commas():
    original = '''{
  "compilerOptions": {
    "strict": true,
  },
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=['"strict": true,', '"@pyrpc/types": [']
    )

def test_existing_aliases():
    original = '''{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "~/*": ["./src/*"],
    },
  },
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=[
            '"@/*": ["./src/*"]',
            '"~/*": [\n        "./src/*"\n      ]',
            '"@pyrpc/types": [\n        "./__pyrpc.d.ts"\n      ]'
        ]
    )

def test_formatting_2_spaces():
    original = '''{
  "compilerOptions": {}
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "a"], 
        ["b"],
        options={"formattingOptions": {"insertSpaces": True, "tabSize": 2}},
        expected_fragments=['    "paths": {\n      "a": [\n        "b"\n      ]\n    }']
    )

def test_formatting_4_spaces():
    original = '''{
    "compilerOptions": {}
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "a"], 
        ["b"],
        options={"formattingOptions": {"insertSpaces": True, "tabSize": 4}},
        expected_fragments=['        "paths": {\n            "a": [\n                "b"\n            ]\n        }']
    )

def test_formatting_tabs():
    original = '''{
\t"compilerOptions": {}
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "a"], 
        ["b"],
        options={"formattingOptions": {"insertSpaces": False, "tabSize": 4}},
        expected_fragments=['\t\t"paths": {\n\t\t\t"a": [\n\t\t\t\t"b"\n\t\t\t]\n\t\t}']
    )

def test_unrelated_configuration():
    original = '''{
  "compilerOptions": {
    "target": "es2022",
    "lib": ["dom", "dom.iterable", "esnext"],
    "module": "esnext",
    "moduleResolution": "node",
    "strict": true,
    "jsx": "preserve",
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    },
    "baseUrl": "."
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"],
  "exclude": ["node_modules"]
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=[
            '"target": "es2022"',
            '"lib": ["dom", "dom.iterable", "esnext"]',
            '"moduleResolution": "node"',
            '"strict": true',
            '"jsx": "preserve"',
            '"name": "next"',
            '"@/*": [\n        "./src/*"\n      ]',
            '"baseUrl": "."',
            '"include": ["next-env.d.ts", "**/*.ts", "**/*.tsx"]',
            '"exclude": ["node_modules"]',
            '"@pyrpc/types": [\n        "./__pyrpc.d.ts"\n      ]'
        ]
    )

def test_existing_pyrpc_types():
    original = '''{
  "compilerOptions": {
    "paths": {
      "@pyrpc/types": ["./__pyrpc.d.ts"]
    }
  }
}'''
    # Microsoft semantics overwrite it if it's an array reference
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=['"@pyrpc/types": [\n        "./__pyrpc.d.ts"\n      ]']
    )

def test_conflicting_alias():
    original = '''{
  "compilerOptions": {
    "paths": {
      "@pyrpc/types": ["./somewhere-else.d.ts"]
    }
  }
}'''
    # generic JSONC library must NOT decide this is a pyRPC conflict
    # it just overwrites it
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=['"@pyrpc/types": [\n        "./__pyrpc.d.ts"\n      ]'],
        unexpected_fragments=['"./somewhere-else.d.ts"']
    )

def test_empty_configuration():
    original = '''{}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=['"compilerOptions":', '"paths":', '"@pyrpc/types":']
    )

def test_no_compiler_options():
    original = '''{
  "include": ["src/**/*"]
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=['"include": [\n    "src/**/*"\n  ]', '"compilerOptions":', '"paths":', '"@pyrpc/types": [\n        "./__pyrpc.d.ts"\n      ]']
    )

def test_realistic_tsconfig():
    original = '''// A realistic tsconfig with comments and trailing commas
{
  "compilerOptions": {
    /* Base Options: */
    "esModuleInterop": true,
    "skipLibCheck": true,
    "target": "es2022",
    "allowJs": true,
    "resolveJsonModule": true,
    "moduleDetection": "force",
    "isolatedModules": true,
    // Strictness
    "strict": true,
    "noUncheckedIndexedAccess": true,
    
    // Path aliases
    "paths": {
      "@/*": ["./src/*"],
    },
  },
  "include": ["src"],
}'''
    verify_source(
        original, 
        ["compilerOptions", "paths", "@pyrpc/types"], 
        ["./__pyrpc.d.ts"],
        expected_fragments=[
            '// A realistic tsconfig with comments and trailing commas',
            '/* Base Options: */',
            '"esModuleInterop": true',
            '// Strictness',
            '"noUncheckedIndexedAccess": true,',
            '// Path aliases',
            '"@/*": [\n        "./src/*"\n      ],',
            '"@pyrpc/types": [\n        "./__pyrpc.d.ts"\n      ]',
            '"include": ["src"],'
        ]
    )
