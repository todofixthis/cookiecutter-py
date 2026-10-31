---
name: rotate-python-versions
description: Use when adding or dropping Python version support, or when the python-policy CI check fails — updating requires-python, tox environments, the CI test matrix, and docs to reflect a new set of supported versions, and removing compat code for dropped versions.
---

# Rotate Python Versions

Update all version references consistently when adding or dropping Python support.

The template `todofixthis/cookiecutter-py` sets the target: CI's `python-policy` job fails while `python_version` in `.copier-answers.yml` is behind the template's policy, which its `run:` step in `.github/workflows/build.yml` names. Renovate never moves Python (ADR 015 in todofixthis/cookiecutter-py), because a rotation also removes compat code, which only a session can do. Rotate to the policy unless the user names another version.

## Locations to update

- **`pyproject.toml`** — `requires-python` constraint, `Programming Language :: Python :: 3.x` classifiers and `[tool.tox]` `env_list`
- **`uv.lock`** — regenerate with `uv lock` after changing `requires-python`, and commit it with the other edits; a stale lock no longer matches `pyproject.toml`, so CI's `uv sync` silently re-resolves it and tests dependencies nobody committed (`uv lock --check` confirms it is current)
- **`.github/workflows/`** — CI matrix `python-version` list (each entry must match a tox environment)
- **`docs/` and `README.rst`** — requirements/compatibility version list (not ADRs under `docs/adr/`, which record the versions at the time of each decision)
- **`.agents/rules/project.md`** — any version range this project's own rules mention

## Key detail

Change only the lower bound of `requires-python` and keep the rest of the specifier (e.g. the `, <4` cap). Use `>=X.Y`, not `~=X.Y` without a patch version — the tilde specifier without a patch (e.g. `~=3.12`) is ambiguous and triggers a uv warning.

Add a version only once it has a final release. Before making any edits, run `uv python list X.Y --only-downloads`: if every match carries an `a`, `b` or `rc` suffix (e.g. `cpython-3.15.0rc2`), the version isn't final, so ask the user how to proceed before touching anything. ReadTheDocs builds on the newest supported version too, so it must also list X.Y under `build.tools.python` in its [config-file reference](https://docs.readthedocs.io/en/stable/config-file/v2.html#build-tools-python); if it doesn't, ask the user before touching anything, since docs builds would fail while CI stays green.

Branch protection requires only the `gate` job, whose name doesn't change with the matrix, so a rotation needs no ruleset change.

Dependencies can lack wheels for a new version even after its final release. If `uv run tox run-parallel` fails while installing dependencies (a source build error) rather than in the tests themselves, stop and ask the user; don't install system packages to make the build pass.

## Apply the new range through copier

The `python_version` answer in `.copier-answers.yml` is the newest supported version; the template derives `requires-python`, the tox environments, the CI matrix and the version lists in `README.rst` and `docs/` from it. Once the checks in Key detail have passed, commit any local changes (`copier update` needs a clean working tree), then run `uvx "copier>=9,<10" update --defaults --vcs-ref=:current: --data python_version=X.Y` (`:current:` keeps the project on its current template version). Follow it with `uv lock`, and check each location above by hand for anything the template doesn't generate.

## Remove compat code

When dropping a version, remove code that exists only to support it: version checks (`sys.version_info` comparisons), fallback imports (`try: import tomllib` / `except ImportError`), backports in `pyproject.toml` dependencies whose markers only match dropped versions (`; python_version < "3.12"`), and `typing_extensions` imports of names `typing` now provides at the new floor. Search with:
```bash
rg -n "sys\.version_info|python_version *[<>]|typing_extensions|except (ImportError|ModuleNotFoundError)" src test pyproject.toml
```
It exits 1 when nothing matches, which is not a failure. Adopt syntax the new floor allows only where ruff's `UP` rules flag it (`uv run ruff check --select UP --fix`); leave other modernisation for its own change.

## After editing

Search for stray references. `--hidden` is needed to reach `.github/workflows/`, so the `!` globs keep out the directories it would otherwise add:
```bash
rg -n "3\.\d{2}|py3\d{2}" . --hidden --glob "*.toml" --glob "*.yml" --glob "*.rst" --glob "*.md" --glob "!uv.lock" --glob "!docs/adr/**" --glob "!.git/**" --glob "!.venv/**" --glob "!.tox/**"
```

Expect noise from dependency pins (e.g. `pytest-mock>=3.15.1`) and from skill files that mention versions in prose. When dropping a version, every remaining hit for it should be one of those.

Then run `uv run tox run-parallel` and confirm it exits 0.
