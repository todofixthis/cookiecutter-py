# cookiecutter-py

[![CI](https://github.com/todofixthis/cookiecutter-py/actions/workflows/ci.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-py/actions/workflows/ci.yml)
[![Generate and Validate](https://github.com/todofixthis/cookiecutter-py/actions/workflows/generate-and-validate.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-py/actions/workflows/generate-and-validate.yml)

A [copier](https://copier.readthedocs.io/) template for new Python projects, wired up with `uv`, `hatchling`, Sphinx/ReadTheDocs docs, and the shared `phx` agent tooling from the start.

## Usage

```bash
uvx "copier>=9,<10" copy gh:todofixthis/cookiecutter-py my-python-project
```

copier prompts for each answer; all but the short description and copyright year have a default. `python_version` (default `3.14`) is the newest Python release the project supports, along with the two before it. copier records the answers in `.copier-answers.yml`, so a later template release can reach the project as a Renovate PR.

## What you get

- `uv` + `hatchling` packaging, `pytest` + `mypy --strict` + `ruff`/`black` (via `autohooks`, not the `pre-commit` framework)
- Sphinx docs on ReadTheDocs, GitHub Actions CI (test matrix, type-check, docs build), Renovate for dependency/Action updates
- `AGENTS.md`/`CLAUDE.md`, an ADR workflow under `docs/adr/`, and the `phx@todofixthis` skill marketplace enabled out of the box
- A guided `release` skill covering version bumps, GPG-signed release artefacts, and PyPI publishing

## Developing this template

See `AGENTS.md` for the dev workflow (`uv sync --group=dev`, `uv run pytest` bakes the template and checks the output, `uv run mypy test`, `uv run ruff check test`).
