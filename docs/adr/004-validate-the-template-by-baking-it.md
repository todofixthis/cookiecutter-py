---
status: Accepted
date: 2026-08-29
scope: [test/, .github/workflows/generate-and-validate.yml]
summary: Validate the template by actually baking a project with cookiecutter and running its own lint/type-check/test/docs-build, not just static checks on the template files.
---

# 004: Validate the Template by Baking It

## Context

Before this modernization, this repo had no test suite and no CI at all — a
change to `cookiecutter.json`, a hook, or the templated project's own files
could silently break what `cookiecutter gh:todofixthis/cookiecutter-py`
produces, and nothing would catch it before a user hit the failure directly.

## Options

### Option 1: Static checks only

Lint/format the raw template files (including the Jinja templates) without
ever rendering them.

**Pros:** Simple; no need to actually run `cookiecutter` in CI.
**Cons:** A static linter can't validate Jinja expressions like `{{
cookiecutter.__python_minor | int - 2 }}` or catch a computed value that
renders to something syntactically invalid (e.g. malformed TOML) — the
failure mode this repo actually had (the `mypyc`/tox-env-name bugs fixed in
ADR 002) is exactly the kind of thing rendering, not linting, would catch.
**Risks:** False confidence — CI passes while the generated output is still
broken.

### Option 2: Bake and validate the real output (Accepted)

Add a `test/` suite (`test_bake.py`) that runs `cookiecutter` with the
template's own default answers and asserts the output is well-formed (no
leftover Jinja markers, valid `pyproject.toml`, expected package layout).
Separately, add a CI workflow (`generate-and-validate.yml`) that bakes a
project and runs *that project's own* `ruff check`/`mypy src test`/`pytest`/
docs build — the same commands a human maintainer of a generated project
would run.

**Pros:** Catches exactly the class of bug this repo already had; the CI
workflow doubles as a live demonstration that a freshly generated project
actually builds, on every push.
**Cons:** Slower CI (an extra `uv sync` and Sphinx build per matrix entry);
duplicates some assertions between the lightweight `test/` suite and the
heavier CI workflow.
**Risks:** The generated project's own dependency versions can drift and
break this CI independently of any change to the template itself — same
risk Renovate (ADR 003) exists to manage.

## Decision

Option 2, at both levels: `test/test_bake.py` for a fast, always-run check of
the raw output's shape, and `generate-and-validate.yml` for the slower,
end-to-end check that the generated project's own tooling actually works.
Neither replaces the other — `test/` runs on every `uv run pytest` a
contributor does locally without ever installing the generated project's own
dependencies; the workflow is the one that would have caught the `mypyc` bug.

## Consequences

- CI now depends on network access to install the generated project's
  dependencies mid-run — same dependency CI already had for this repo's own
  `uv sync`.
- Future changes to the templated project's `pyproject.toml`/CI/docs need to
  keep working under `generate-and-validate.yml`'s matrix, not just render
  without Jinja errors.
