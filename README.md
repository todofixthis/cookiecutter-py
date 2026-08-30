# cookiecutter-py

[![CI](https://github.com/todofixthis/cookiecutter-py/actions/workflows/ci.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-py/actions/workflows/ci.yml)
[![Generate and Validate](https://github.com/todofixthis/cookiecutter-py/actions/workflows/generate-and-validate.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-py/actions/workflows/generate-and-validate.yml)

A [cookiecutter](https://cookiecutter.readthedocs.io/) template for new Python projects, wired up with `uv`, `hatchling`, Sphinx/ReadTheDocs docs, and the shared `phx` agent tooling from the start.

## Usage

```bash
uv tool install cookiecutter  # once
cookiecutter gh:todofixthis/cookiecutter-py
```

You'll be prompted for a project name, a short description, and an author name/email (defaults to Phoenix Zerin's); the Python version floor and the current year are filled in automatically from the interpreter running cookiecutter.

## What you get

- `uv` + `hatchling` packaging, `pytest` + `mypy --strict` + `ruff`/`black` (via `autohooks`, not the `pre-commit` framework)
- Sphinx docs on ReadTheDocs, GitHub Actions CI (test matrix, type-check, docs build), Renovate for dependency/Action updates
- `AGENTS.md`/`CLAUDE.md`, an ADR workflow under `docs/adr/`, and the `phx@todofixthis` skill marketplace enabled out of the box
- A guided `release` skill covering version bumps, GPG-signed release artefacts, and PyPI publishing

## Developing this template

See `AGENTS.md` for the dev workflow (`uv sync --group=dev`, `uv run pytest` bakes the template and checks the output, `uv run mypy scripts test`, `uv run ruff check`).
