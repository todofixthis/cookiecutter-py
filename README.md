# cookiecutter-py

[![CI](https://github.com/todofixthis/cookiecutter-py/actions/workflows/ci.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-py/actions/workflows/ci.yml)

A [copier](https://copier.readthedocs.io/) template for new Python projects, wired up with `uv`, `hatchling`, Sphinx/ReadTheDocs docs, and the shared `phx` agent tooling from the start.

## Usage

```bash
uvx "copier>=9,<10" copy https://github.com/todofixthis/cookiecutter-py.git my-python-project
```

copier prompts for each answer; all but the short description and copyright year have a default. `python_version` (default `3.14`) is the newest Python release the project supports, along with the two before it. copier records the answers in `.copier-answers.yml`, so a later template release can reach the project as a Renovate PR. Use the full URL, not the `gh:` shorthand: copier records the source verbatim, and Renovate can't resolve `gh:`.

## After creating the GitHub repo

- **Renovate.** If Renovate is installed for selected repositories only, add the repo at <https://github.com/settings/installations> → Renovate → Configure → Repository access. Until then the repo gets no dependency updates, nor the PRs that bring template releases, and nothing says so.
- **Watching.** Unless the repo already shows as watched, click Watch → All Activity on it. A watch belongs to a person, not the repo, so the todofixthis Terraform module leaves it out by design ([its ADR 005](https://github.com/todofixthis/terraform-github-repository/blob/develop/docs/adr/005-keep-personal-preferences-out-of-the-module.md)).

## What you get

- `uv` + `hatchling` packaging, `pytest` + `mypy --strict` + `ruff`/`black` (via `autohooks`, not the `pre-commit` framework)
- Sphinx docs on ReadTheDocs, GitHub Actions CI (test matrix, type-check, docs build, ADR validation, and a `gate` job aggregating the rest as the one required check), Renovate for dependency/Action updates
- `AGENTS.md`/`CLAUDE.md`, an ADR workflow under `docs/adr/`, and the `phx@todofixthis` skill marketplace enabled out of the box
- A guided `release` skill covering version bumps, GPG-signed release artefacts, and PyPI publishing

## Developing this template

See `AGENTS.md` for the dev workflow, including how to bake your working tree into a project (`uv sync --group=dev`, `uv run pytest` bakes the template and checks the output, `uv run mypy test`, `uv run ruff check test`).
