<!-- SPDX-FileCopyrightText: 2026 sv-shell contributors -->
<!-- SPDX-License-Identifier: LGPL-3.0-or-later -->

# Releasing ab-sv-shell

This repository publishes to PyPI via GitHub Actions in `.github/workflows/publish.yml`.

## Release process

1. Bump `version` in `pyproject.toml`.
2. Commit and push the change to `main`.
3. Create and publish a GitHub Release (or run the workflow manually).
4. Confirm the `Publish to PyPI` workflow succeeds.
