---
name: rotate-python-versions
description: Use when changing which Python versions todofixthis/cookiecutter-py's template generates projects for, or the Python floor of cookiecutter-py's own test harness — in the template repository itself, not inside a generated project.
---

# Rotate Python Versions

todofixthis/cookiecutter-py has two Python settings:
- **The generated range** is the three newest Python releases a generated project supports,
  set by the `python_version` answer.
- **The harness floor** is the oldest Python cookiecutter-py's own tests run on.

The harness floor must not exceed the oldest version in the generated range. CI's `generate`
job syncs the harness under each version in that range, so a higher floor fails its oldest
leg. Rotate one setting at a time, and check that constraint before either.

## The generated range

`python_version` is the newest supported release, and the template derives everything else
from it (`requires-python`, tox, the CI matrix, the docs). Change three places together:

- **`copier.yml`:** `python_version`'s `default`.
- **`README.md`:** the default it quotes.
- **`.github/workflows/ci.yml`:** the `generate` job's `python-version` matrix, which lists
  the new default and the two releases before it, each quoted so YAML keeps `3.20` a string.

Add a version only once it has a final release: `uv python list X.Y --only-downloads` must
show a build without an `a`, `b` or `rc` suffix. uv lists only the builds it knows of, so a
missing final build can mean an outdated uv. Either way, stop and tell the maintainer rather
than adding the version.

Rotating the range up leaves the harness floor valid. Moving it down, so that its oldest
version falls below the floor, needs the harness floor lowered first.

Then check the result as CI does, using the bake commands in AGENTS.md's Commands section,
once under the new newest version and once under the new oldest, each with `UV_PYTHON` set
to that version for every `uv` command. Run `uv run pytest` too. If a dependency won't
install under a version, stop and tell the maintainer rather than pinning around it.

A released default reaches new projects only. `copier update --defaults`, which Renovate
runs, keeps each project's recorded answer, so an existing project moves only by
re-answering with `copier update --data python_version=X.Y`, which the generated projects'
own `rotate-python-versions` skill does. Don't edit a generated project from here.

## The harness floor

The root `pyproject.toml`'s `requires-python` and `[tool.black] target-version`, and
`uv.lock`, describe the harness, not the generated range. CI's `test` and `type-check` jobs
install the newest Python `requires-python` allows, so the floor is the only version they
pin. Change the floor only when the maintainer asks, and only to a version no higher than the
generated range's oldest. Change all three together:

- `requires-python` to `>=X.Y`;
- `target-version` to every version from the new floor up to the newest Python the
  pre-commit hook runs black under. Black warns on every run about a target newer than its
  interpreter, so leave that upper end alone when rotating the generated range;
- then run `uv lock` and `uv run pytest`.
