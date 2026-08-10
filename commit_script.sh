#!/bin/bash
set -e

# Create and checkout branch
git checkout -b feat/jsonc-edit-core-implementation

# 1. Project structure
git add pyproject.toml
git commit -m "chore(project): initialize project structure and pyproject.toml"

# 2. Errors
git add src/jsonc_edit/_errors.py
git commit -m "feat(errors): implement exception hierarchy for robust error handling"

# 3. Typing
git add src/jsonc_edit/_typing.py src/jsonc_edit/_models.py
git commit -m "feat(typing): add strong typing models for public API"

# 4. Runtime
git add src/jsonc_edit/_runtime.py
git commit -m "feat(runtime): implement deterministic node/npm bootstrapping and file locks"

# 5. Test Runtime
git add tests/test_runtime.py
git commit -m "test(runtime): add tests for dependency caching and bootstrapping"

# 6. Daemon
git add src/jsonc_edit/_daemon.js src/jsonc_edit/_daemon.py
git commit -m "feat(daemon): implement persistent Node.js daemon and protocol with thread-safety"

# 7. Test Daemon
git add tests/test_daemon.py
git commit -m "test(daemon): add daemon health and protocol tests"

# 8. API
git add src/jsonc_edit/_api.py src/jsonc_edit/__init__.py
git commit -m "feat(api): implement modify, apply_edits, and edit_session public API"

# 9. Test API
git add tests/test_api.py
git commit -m "test(api): add unit tests for public API"

# 10. Test Lifecycle
git add tests/test_lifecycle.py
git commit -m "test(lifecycle): add thread and multiprocess concurrency tests"

# 11. Test Preservation
git add tests/test_preservation.py tests/test_package.py
git commit -m "test(preservation): add comprehensive source-preservation test suite"

# 12. README
git add README.md
git commit -m "docs: write comprehensive README explaining architecture and usage"

# 13. CI Tests
git add .github/workflows/ci.yml
git commit -m "chore(ci): add github action for python tests across multiple versions"

# 14. CI Publish
git add .github/workflows/publish.yml
git commit -m "chore(ci): add pypi trusted publishing action"

# 15. Gitignore
git add .gitignore
git commit -m "chore(git): add comprehensive .gitignore for python and nextjs"

# 16. Contributing
git add CONTRIBUTING.md
git commit -m "docs: add CONTRIBUTING.md guidelines"

# 17. Fumadocs
git add docs/
git commit -m "docs(site): migrate fumadocs documentation to jsonc-edit"

# Add any stragglers
git add .
if ! git diff --staged --quiet; then
  git commit -m "chore: add remaining project files"
fi

# Push and create PR
git push -u origin feat/jsonc-edit-core-implementation
gh pr create --title "feat: jsonc-edit core library implementation and documentation" --body "This PR introduces the foundational implementation of the jsonc-edit library, tests, CI/CD, and Fumadocs documentation."
