# jsonc-edit

A Python interface to Microsoft's `jsonc-parser`, designed for source-preserving JSONC edits.

## What it is

`jsonc-edit` is a lightweight Python package that provides surgical source-editing capabilities for JSONC (JSON with Comments) files. Instead of providing standard JSON parsing and dumping, it wraps Microsoft's world-class AST-aware `jsonc-parser` library under the hood, giving you exact, developer-grade source manipulation in Python.

## Why it exists

When modifying configuration files (like `tsconfig.json` or `.vscode/settings.json`), the standard programmatic approach is highly destructive:
```text
parse source string → modify Python dict in memory → dump back to string
```
This naive approach immediately strips all `// line comments`, `/* block comments */`, trailing commas, and completely mangles the developer's original indentation and formatting choices.

`jsonc-edit` uses a fundamentally different approach:
```text
semantic JSONC edit → generate precise text offset edits → apply edits to raw string
```
By analyzing the AST and applying surgical character replacements, `jsonc-edit` perfectly preserves all human-authored elements in the file, including neighboring comments and specific array formatting.

## Scope

`jsonc-edit` is intended to be a reusable, generalized JSONC source-editing library. It is strictly scoped to this purpose.

It is **not**:
* A `tsconfig.json` manager.
* A framework-specific plugin or library.
* A full JSONC configuration framework that validates schemas or paths.

## Installation

```bash
pip install jsonc-edit
```

### Runtime Prerequisites

Because `jsonc-edit` leverages the official Microsoft parser to ensure exact semantic correctness, it runs a tiny invisible Node.js daemon under the hood to process the edits. 

**You must have `node` and `npm` installed and available on your system path.** 
During its first execution, `jsonc-edit` will automatically install the necessary pinned parser package into an isolated user-level cache (`~/.jsonc-edit/versions/`). It does not pollute your project's `node_modules`.

**Windows users:** `jsonc-edit` fully supports Windows. The runtime installer automatically routes `npm` through `cmd.exe` to work around Windows-specific batch file execution constraints.

## Basic Example

```python
from jsonc_edit import modify, apply_edits

source = """{
  // My custom aliases
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}"""

# Generate the specific string manipulations needed
edits = modify(
    source,
    ["compilerOptions", "paths", "@example"],
    ["./types.d.ts"],
)

# Apply them to the raw source code
result = apply_edits(source, edits)

print(result)
```

The output will safely insert the new alias while completely respecting the existing `// My custom aliases` comment and the surrounding whitespace preferences.

## Important Semantics

Because `jsonc-edit` uses Microsoft's parser engine, you inherit its intelligent formatting behavior natively:

* **Comments**: `//` and `/* */` comments anywhere in the file are perfectly preserved.
* **Trailing Commas**: Existing trailing commas on unaffected properties remain untouched.
* **Formatting**: You can optionally pass `options={"formattingOptions": {"insertSpaces": True, "tabSize": 4}}` to `modify()` to ensure any newly scaffolded objects match your project's preferred spacing.
* **Existing Values**: Modifying a deeply nested property that does not exist yet (e.g., `["compilerOptions", "paths", "new"]` on an empty `{}` file) will correctly and cleanly scaffold out the missing `compilerOptions` and `paths` objects for you.
* **Idempotency**: Attempting to set an array or object that is already functionally identical may still result in edits if the underlying parser chooses to reformat the specific block to match uniform JSON spacing. 
* **Errors**: Invalid operations or syntax crashes will natively bubble up into Python as a `JsoncParseError`. Missing Node/NPM environments will raise a `RuntimeBootstrapError`.

## Architecture

`jsonc-edit` uses a persistent, line-buffered Node.js daemon managed directly by Python. This means:
1. It does not spawn a new Node process for every edit. It boots once.
2. It communicates blisteringly fast via newline-delimited JSON over `stdin`/`stdout`.
3. It cleanly shuts down alongside the Python interpreter via `atexit` hooks.

You do not need to manage this daemon yourself. It operates entirely transparently behind the `modify` and `apply_edits` functions. If you need explicit deterministic lifecycle management, a context manager is available:

```python
from jsonc_edit import edit_session, modify

with edit_session():
    edits = modify("{}", ["a"], 1)
```

## API Reference

### `edit(text: str, path: List[str | int], value: Any, options=None) -> str`
Generates edits for modifying the value at `path` to `value` and immediately applies them to `text`. Path segments are interpreted literally (no escaping needed).

### `edit_file(filepath: str | Path, path: List[str | int], value: Any, options=None) -> None`
Safely reads `filepath`, applies the edit via `edit()`, and atomically writes back the modification *only* if the content actually changed.

### `edit_many(text: str, operations: List[Tuple[path, value]], options=None) -> str`
Applies multiple operations sequentially without causing internal offset corruption.

### `get_value(text: str, path: List[str | int]) -> Any | MISSING`
Semantically parses and returns the value at the target path. Returns the `MISSING` sentinel if the path does not exist, explicitly distinguishing from an actual `"property": null` assignment.

### `modify(text: str, path: List[str | int], value: Any, options=None) -> List[Edit]`
Analyzes the AST and generates a precise list of raw offset character edits (without applying them).

### `apply_edits(text: str, edits: List[Edit]) -> str`
Applies raw offset character edits to the source string.

### `edit_session()`
A context manager that guarantees the background Node.js daemon shuts down perfectly when exiting the `with` block. Mostly useful for strict deterministic lifecycle scripts.
