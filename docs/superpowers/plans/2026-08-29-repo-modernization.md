# Repo Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Worktree:** none — working directly on `claude/todofixthis-repo-modernization-nhorm5` in `/home/user/cookiecutter-py` (harness-assigned branch; the whole container is already an isolated remote session, so no nested worktree was created).

**Goal:** Bring `todofixthis/cookiecutter-py`'s own dev/agent tooling, and the tooling it generates for new projects, up to the standard already in place in `todofixthis/class-registry` and `todofixthis/phx-claude-siat`, and add a GitHub Actions workflow that bakes a real project with cookiecutter and validates it end-to-end.

**Architecture:** This repo is a cookiecutter template, not a package — its "own" tooling (root-level `pyproject.toml`, ADR system, CI) validates the *template*, while a second, separate set of changes updates the *templated project* under `{{ cookiecutter.github_project_name }}/`, which is what a `cookiecutter gh:todofixthis/cookiecutter-py` run actually produces. Both model repos (class-registry, phx-claude-siat) converged on the same conventions independently: `AGENTS.md` canonical with `CLAUDE.md` symlinked to it, `uv` + `hatchling` (not Poetry), `autohooks` (not the `pre-commit` framework) wired to a custom ADR-index generator, Renovate (not Dependabot) with pinned Action digests, and a `.claude/settings.json` enabling the shared `phx@todofixthis` plugin marketplace. This plan ports those conventions into both halves of this repo.

**Completed pre-work** (commit `01b5482`, before this plan was written): added root `AGENTS.md`, a `CLAUDE.md` symlink to it, and `.claude/settings.json` enabling the `phx@todofixthis` marketplace, so every task below (and any skill it uses, e.g. `writing-adrs`) already has correct guidance in place.

**Tech Stack:** Python, `uv`, `hatchling`, `cookiecutter`, `pytest`, `mypy`, `ruff`, `black`, `autohooks`, GitHub Actions, Sphinx, ReadTheDocs.

**Spec:** No separate spec doc — the spec is the user's request ("bring this repo up to date with class-registry and phx-claude-siat's conventions; add a PR workflow that bakes and validates a generated project") plus the inventory gathered from all three repos in this session (recorded in the task's chat history, not a file).

## Global Constraints

- NZ English throughout, comments precede the code they document (per the `AGENTS.md` just committed).
- Match sibling conventions exactly where they're directly portable (file layout, `.gitignore` patterns, workflow structure); adapt where this repo's shape genuinely differs (no package to publish at the template-repo root, no `develop` branch, no release automation for the template repo itself since it's never published).
- Every new GitHub Actions step pins `actions/checkout`, `astral-sh/setup-uv`, and `actions/setup-python` to the exact commit SHAs currently used in `class-registry/.github/workflows/build.yml` (`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` # v7.0.1, `astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d` # v10.0.1, `actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97` # v7.0.0) — real, verified pins, not invented ones. Renovate (added in Task 1) takes over re-pinning them from here.
- The generated project keeps supporting "the three most recent Python minor releases," computed the same way it already is today (`hooks/pre_prompt.py` + `__python_major`/`__python_minor` in `cookiecutter.json`) — this plan does not change that mechanism, only the build tooling around it.
- No GitHub App / branch-ruleset release automation (phx-claude-siat's `release.yml`) is in scope anywhere in this plan: it needs secrets and admin-configured branch rulesets only a human can set up, and neither this repo nor the projects it generates currently publish anything through it. The generated project keeps a manual, skill-guided release process instead (matching class-registry's `release` skill), which needs no platform configuration.

---

## File Map

**This repo's own dev tooling (validates the template itself):**
- `pyproject.toml` (new) — `uv`, `package = false`, dev/ci dependency groups, `autohooks` config
- `scripts/__init__.py`, `scripts/adr/__init__.py`, `scripts/adr/generate_index.py` (new) — ADR index generator, ported verbatim from class-registry
- `.autohooks/adr_index.py` (new) — pre-commit plugin wiring the generator in, ported verbatim from class-registry
- `renovate.json` (new)
- `.gitignore` (edit) — add worktree/venv/cache patterns
- `test/test_bake.py` (new) — bakes the template, asserts the output is well-formed
- `.github/workflows/ci.yml` (new) — lint/type-check/test/adr-index for this repo's own tooling
- `.github/workflows/generate-and-validate.yml` (new) — the requested workflow: bakes a real project and runs its own lint/type-check/test/docs-build
- `docs/adr/001-*.md` … `004-*.md`, `docs/adr/INDEX.md` (new) — decisions recorded once everything above exists
- `.github/dependabot.yml` (delete) — superseded by `renovate.json`
- `README.md` (new) — usage instructions for the template itself

**The templated project (`{{ cookiecutter.github_project_name }}/`, what `cookiecutter` generates):**
- `pyproject.toml` (edit) — Poetry → `uv` + `hatchling`, fixes the `mypyc`-as-typecheck bug, adds `tox-uv`
- `.github/workflows/build.yml` (edit) — Poetry → `uv`, pinned Action SHAs, `mypyc` → `mypy`
- `.readthedocs.yaml` (edit) — Poetry → `uv`
- `.github/dependabot.yml` → `renovate.json` (replace)
- `README.rst` (edit) — commands updated to `uv`
- `AGENTS.md` (new), `CLAUDE.md` (new symlink), `.claude/settings.json` (new), `.claude/skills` (new symlink to `.agents/skills`)
- `.agents/skills/release/SKILL.md` (new) — ported from class-registry, templated
- `.agents/skills/rotate-python-versions/SKILL.md` (new) — ported verbatim from class-registry
- `.gitignore` (edit) — add worktree/cache patterns

---

## Task 1: Root dev-tooling scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `scripts/__init__.py`, `scripts/adr/__init__.py`, `scripts/adr/generate_index.py`
- Create: `.autohooks/adr_index.py`
- Create: `renovate.json`
- Modify: `.gitignore`

**Interfaces:**
- Produces: `scripts.adr.generate_index.generate(adr_dir, repo_root) -> int` and `main(argv, adr_dir, repo_root) -> int`, used by Task 5's CI job and by the `.autohooks/adr_index.py` plugin created in this same task.

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "cookiecutter-py"
version = "0.0.0"
description = "Cookiecutter template for todofixthis Python projects"
requires-python = ">=3.12"

[dependency-groups]
dev = [
    "autohooks>=26,<27",
    "autohooks-plugin-black>=23,<24",
    "autohooks-plugin-mypy>=23,<24",
    "autohooks-plugin-pytest>=23,<24",
    "autohooks-plugin-ruff>=25,<26",
    "cookiecutter>=2,<3",
    "mypy>=2,<3",
    "pytest>=9,<10",
    "pyyaml>=6.0.3,<7.0.0",
    "types-pyyaml>=6.0.12.20260518,<7.0.0.0",
]
ci = [
    "cookiecutter>=2,<3",
    "mypy>=2,<3",
    "pytest>=9,<10",
    "pyyaml>=6.0.3,<7.0.0",
    "types-pyyaml>=6.0.12.20260518,<7.0.0.0",
]

[tool.uv]
# This repo is a cookiecutter template, not a Python package — nothing here
# gets built or published, so uv shouldn't try to.
package = false

[tool.autohooks]
mode = "pythonpath"
pre-commit = [
    "adr_index",
    "autohooks.plugins.black",
    "autohooks.plugins.mypy",
    "autohooks.plugins.pytest",
    "autohooks.plugins.ruff",
]

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["test"]
```

- [ ] **Step 2: Port the ADR index generator verbatim**

Copy `/home/user/todofixthis/class-registry/scripts/adr/generate_index.py` to `scripts/adr/generate_index.py` unchanged — it resolves `REPO_ROOT` from its own file location (`Path(__file__).resolve().parents[2]`), which is the same relative depth in this repo, so no path adjustment is needed. Create empty `scripts/__init__.py` and `scripts/adr/__init__.py` alongside it (makes `scripts` and `scripts.adr` importable packages, as `python -m scripts.adr.generate_index` requires).

This ports class-registry's PyYAML-based fork rather than `phx-claude-siat`'s stdlib-only canonical version (the one `writing-adrs` names as the reference implementation) — see Intentional Decisions.

- [ ] **Step 3: Port the autohooks plugin verbatim**

Copy `/home/user/todofixthis/class-registry/.autohooks/adr_index.py` to `.autohooks/adr_index.py` unchanged — it imports `scripts.adr.generate_index`, which now exists at the same path in this repo.

- [ ] **Step 4: Write `renovate.json`**

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "helpers:pinGitHubActionDigests"
  ]
}
```

- [ ] **Step 5: Update `.gitignore`**

Replace the current one-line `.gitignore` (just `venv`) with:

```gitignore
# Agent worktrees
.claude/worktrees/

# Byte-compiled / optimized / DLL files
__pycache__
*.pyc

# Linting cache
.ruff_cache

# Pytest cache
.pytest_cache

# Virtual environments
venv
.venv
```

- [ ] **Step 6: Sync dependencies**

```bash
uv sync --group=dev
```

Expected: completes without error; `uv.lock` is created/updated. Do **not** run `uv run autohooks activate` yet — `[tool.pytest.ini_options] testpaths = ["test"]` above points at a directory that doesn't exist until Task 2, and `autohooks.plugins.pytest` runs on every commit once the hook is active. Activating now would make Task 2's own creation commit (and this task's) fail pre-commit. Activation happens in Task 2, once `test/` exists.

- [ ] **Step 7: Commit**

Run `git status` to catch `uv.lock` and any other untracked files from the sync, then use the `creative-commits` skill. No pre-commit hook is installed yet, so this is a plain commit.

## Task 2: Bake-and-validate test suite

**Files:**
- Create: `test/test_bake.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (only the `cookiecutter` dependency added in Task 1).
- Produces: nothing consumed by later tasks — this is this repo's only test suite, run by `uv run pytest` and by Task 5's `ci.yml`.

- [ ] **Step 1: Write the test file**

```python
"""Bakes the template with default answers and checks the output is well-formed."""

import re
import tomllib
from pathlib import Path
from typing import Iterator

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

# Anything of this shape surviving in a baked file means cookiecutter's Jinja
# pass missed it — the whole point of baking is that none of this remains.
RE_UNRENDERED_JINJA = re.compile(r"\{\{.*cookiecutter[^}]*\}\}")


@pytest.fixture
def baked_project(tmp_path: Path) -> Iterator[Path]:
    """Bakes the template with its default answers into a temp directory."""
    output_dir = cookiecutter(
        str(TEMPLATE_ROOT),
        no_input=True,
        output_dir=str(tmp_path),
    )
    yield Path(output_dir)


def test_bakes_without_error(baked_project: Path) -> None:
    """The template renders into a directory that actually exists."""
    assert baked_project.is_dir()


def test_leaves_no_unrendered_jinja(baked_project: Path) -> None:
    """No `{{ cookiecutter.* }}` markers survive rendering in any generated file."""
    offenders = [
        str(path.relative_to(baked_project))
        for path in baked_project.rglob("*")
        if path.is_file() and RE_UNRENDERED_JINJA.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_generates_valid_pyproject_toml(baked_project: Path) -> None:
    """The generated project's pyproject.toml parses and names the PyPI package."""
    with (baked_project / "pyproject.toml").open("rb") as f_in:
        data = tomllib.load(f_in)
    assert data["project"]["name"] == "phx-my-python-project"


def test_generates_expected_package_layout(baked_project: Path) -> None:
    """The generated package directory and its py.typed marker both exist."""
    package_dir = baked_project / "src" / "my_python_project"
    assert package_dir.is_dir()
    assert (package_dir / "py.typed").is_file()
    assert (package_dir / "__init__.py").is_file()


def test_generates_licence(baked_project: Path) -> None:
    """The generated project ships an MIT licence file."""
    licence_text = (baked_project / "LICENCE.txt").read_text(encoding="utf-8")
    assert "MIT" in licence_text
```

- [ ] **Step 2: Run it**

```bash
uv run pytest test/test_bake.py -v
```

Expected: all 5 tests PASS. If `test_generates_valid_pyproject_toml` fails on the package name, re-check `cookiecutter.json`'s default `project_name` ("My Python Project") still derives to `phx-my-python-project` via `pypi_project_name`.

- [ ] **Step 3: Activate the autohooks pre-commit hook**

`test/` now exists and its tests pass, so it's now safe to turn on the hook Task 1 deliberately deferred:

```bash
uv run autohooks activate --mode=pythonpath
```

Expected: completes without error. From here on, use `uv run git commit` (per `AGENTS.md`) instead of a plain `git commit` — the active hook runs `ruff`/`black`/`mypy`/`pytest` (and `adr_index`, a no-op until `docs/adr/` exists in Task 7) on every commit from now on.

- [ ] **Step 4: Commit**

Run `git status` first, then use the `creative-commits` skill (`uv run git commit`, since the hook is now active).

## Task 3: Root CI workflows

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/workflows/generate-and-validate.yml`
- Delete: `.github/dependabot.yml`

**Interfaces:**
- Consumes: `uv run pytest` / `uv run mypy scripts test` / `uv run ruff check` (Task 1), `uv run python -m scripts.adr.generate_index` (Task 1) — the `adr-index` job in `ci.yml` will show a diff until Task 7 populates `docs/adr/`; that's expected mid-plan and resolves before the branch is pushed.

- [ ] **Step 1: Write `.github/workflows/ci.yml`**

```yaml
# https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
name: CI

on:
  push: ~

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version-file: "pyproject.toml"
      - name: Install dependencies
        run: uv sync --group ci
      - name: Run tests
        run: uv run pytest

  type-check:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version-file: "pyproject.toml"
      - name: Install dependencies
        run: uv sync --group ci
      - name: Type checking
        run: uv run mypy scripts test

  adr-index:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version-file: "pyproject.toml"
      - name: Install dependencies
        run: uv sync --group ci
      - name: Regenerate the ADR index
        run: uv run python -m scripts.adr.generate_index
      - name: Check the index is up to date
        run: git diff --exit-code docs/adr/INDEX.md
```

- [ ] **Step 2: Write `.github/workflows/generate-and-validate.yml`**

```yaml
# Bakes a real project from this template with cookiecutter and validates the
# result the same way a maintainer of a generated project would: lint,
# type-check, test, and build its docs.
name: Generate and Validate

on:
  push: ~

permissions:
  contents: read

jobs:
  generate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version:
          # Note: Use quotes to avoid float cast - especially important if the
          # version number ends with 0!
          - "3.12"
          - "3.13"
          - "3.14"

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: ${{ matrix.python-version }}
      - name: Bake a project with default answers
        # --python pins which interpreter uvx runs cookiecutter under, since
        # hooks/pre_prompt.py derives the generated project's Python floor
        # from that interpreter — without this, uvx could resolve its own
        # managed Python and bake identical output on all 3 matrix legs.
        run: uvx --python "${{ matrix.python-version }}" "cookiecutter>=2,<3" . --no-input --output-dir /tmp/baked
      - name: Install the generated project's dependencies
        run: uv sync --group ci
        working-directory: /tmp/baked/my-python-project
      - name: Lint the generated project
        run: uv run ruff check
        working-directory: /tmp/baked/my-python-project
      - name: Type-check the generated project
        run: uv run mypy src test
        working-directory: /tmp/baked/my-python-project
      - name: Test the generated project
        run: uv run pytest
        working-directory: /tmp/baked/my-python-project
      - name: Build the generated project's docs
        run: |
          mkdir -p _static
          uv run make html
        working-directory: /tmp/baked/my-python-project/docs
```

- [ ] **Step 3: Delete the old dependabot config**

```bash
git rm .github/dependabot.yml
```

- [ ] **Step 4: Commit**

Run `git status` first, then use the `creative-commits` skill.

## Task 4: Migrate the generated project's build tooling to `uv` + `hatchling`

**Files:**
- Modify: `{{ cookiecutter.github_project_name }}/pyproject.toml`
- Modify: `{{ cookiecutter.github_project_name }}/.github/workflows/build.yml`
- Modify: `{{ cookiecutter.github_project_name }}/.readthedocs.yaml`
- Modify: `{{ cookiecutter.github_project_name }}/README.rst`
- Delete: `{{ cookiecutter.github_project_name }}/.github/dependabot.yml`
- Create: `{{ cookiecutter.github_project_name }}/renovate.json`

**Interfaces:**
- Produces: a generated project buildable with `uv sync` / `uv run pytest` / `uv run mypy src test` / `uv run ruff check` / `uv run tox -p` — exactly what Task 3's `generate-and-validate.yml` and Task 2's `test_bake.py` exercise.

- [ ] **Step 1: Rewrite `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "{{ cookiecutter.pypi_project_name }}"
version = "{{ cookiecutter.version }}"
description = "{{ cookiecutter.project_short_description }}"
authors = [{ name = "{{ cookiecutter.author_name }}", email = "{{ cookiecutter.author_email }}" }]
requires-python = ">={{ cookiecutter.__python_major }}.{{ cookiecutter.__python_minor | int - 2 }}"
readme = "README.rst"
license = "MIT"

# :see: https://pypi.org/classifiers/
keywords = [
]
classifiers = [
]

[project.urls]
Repository = "https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}"
Documentation = "https://{{ cookiecutter.pypi_project_name }}.readthedocs.io/"
Changelog = "https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/releases"
Issues = "https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/issues"

[dependency-groups]
# I'm only one person, so to keep from getting overwhelmed, I'm only committing
# to supporting the 3 most recent versions of Python (see docs/adr/001).
dev = [
    "autohooks>=26,<27",
    "autohooks-plugin-black>=23,<24",
    "autohooks-plugin-mypy>=23,<24",
    "autohooks-plugin-pytest>=23,<24",
    "autohooks-plugin-ruff>=25,<26",
    "mypy>=2,<3",
    "pytest>=9,<10",
    "sphinx>=8,<9",
    "sphinx_rtd_theme>=3,<4",
    "tox>=4,<5",
    "tox-uv>=1,<2",
]

# Used by GitHub Actions and ReadTheDocs.
ci = [
    "mypy>=2,<3",
    "pytest>=9,<10",
    "sphinx>=8,<9",
    "sphinx_rtd_theme>=3,<4",
    "tox-uv>=1,<2",
]

[tool.autohooks]
mode = "pythonpath"
pre-commit = [
    "autohooks.plugins.black",
    "autohooks.plugins.mypy",
    "autohooks.plugins.pytest",
    "autohooks.plugins.ruff",
]

[tool.hatch.build.targets.sdist]
include = [
    "src/{{ cookiecutter.package_name }}",
    "LICENCE.txt",
    "docs",
    "test",
]
exclude = ["docs/_build"]

[tool.hatch.build.targets.wheel]
include = ["src/{{ cookiecutter.package_name }}"]
exclude = ["docs/_build"]

[tool.hatch.build.targets.wheel.sources]
"src/{{ cookiecutter.package_name }}" = "{{ cookiecutter.package_name }}"

[tool.mypy]
strict = true

[tool.pytest.ini_options]
testpaths = ["test"]

[tool.tox]
env_list = [
    "py{{ cookiecutter.__python_major }}{{ cookiecutter.__python_minor }}",
    "py{{ cookiecutter.__python_major }}{{ cookiecutter.__python_minor | int - 1 }}",
    "py{{ cookiecutter.__python_major }}{{ cookiecutter.__python_minor | int - 2 }}",
]

[tool.tox.env_run_base]
commands = [
    ["pytest"],
    ["mypy", "src", "test"],
]
runner = "uv-venv-lock-runner"
```

This fixes two real bugs along the way: the old `env_list` used dotted version names (`py3.12`, not valid tox env syntax — class-registry's own tox uses `py312`), and CI/tox/README all ran `mypyc src test` where plain `mypy src test` was clearly intended (mypyc is the mypy-to-C *compiler*, not a type checker — the `mypy = {extras = ["mypyc"], ...}` dependency spec was left over from an abandoned experiment per the repo's own commit history, `9f2b5d7`).

- [ ] **Step 2: Rewrite `.github/workflows/build.yml`**

```yaml
# https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python
name: CI

on:
  push: ~

permissions:
  contents: read

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version:
          # Note: Use quotes to avoid float cast - especially important if the
          # version number ends with 0!
          - "{{ cookiecutter.python_version }}"
          - "{{ cookiecutter.__python_major }}.{{ cookiecutter.__python_minor | int - 1 }}"
          - "{{ cookiecutter.__python_major }}.{{ cookiecutter.__python_minor | int - 2 }}"

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python {% raw %}${{ matrix.python-version }}{% endraw %}
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: {% raw %}${{ matrix.python-version }}{% endraw %}
      - name: Install dependencies
        run: uv sync --group ci
      - name: Run tests
        run: uv run pytest

  type-check:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: "{{ cookiecutter.python_version }}"
      - name: Install dependencies
        run: uv sync --group ci
      - name: Type checking
        run: uv run mypy src test

  docs:
    runs-on: ubuntu-latest

    steps:
      - name: Clone repo
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - name: Install uv
        uses: astral-sh/setup-uv@20cfd1bf945f4377ade1205e4dbc17946fc9a30d # v10.0.1
      - name: Set up Python
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: "{{ cookiecutter.python_version }}"
      - name: Install dependencies
        run: uv sync --group ci
      - name: Check docs build
        run: |
          cd docs
          mkdir -p _static
          uv run make html
```

- [ ] **Step 3: Rewrite `.readthedocs.yaml`**

```yaml
# https://docs.readthedocs.io/en/stable/config-file/v2.html
version: 2

build:
  os: ubuntu-24.04
  tools:
    python: "latest"

  jobs:
    post_create_environment:
      # Install uv
      # https://docs.astral.sh/uv/getting-started/installation/
      - pip install uv
    post_install:
      # Install dependencies with the 'ci' dependency group.
      # VIRTUAL_ENV needs to be set manually for now.
      # See https://github.com/readthedocs/readthedocs.org/pull/11152/
      - VIRTUAL_ENV=$READTHEDOCS_VIRTUALENV_PATH uv sync --group ci

sphinx:
  configuration: docs/conf.py
```

- [ ] **Step 4: Replace dependabot with Renovate**

```bash
git rm '{{ cookiecutter.github_project_name }}/.github/dependabot.yml'
```

Create `{{ cookiecutter.github_project_name }}/renovate.json`:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "helpers:pinGitHubActionDigests"
  ]
}
```

- [ ] **Step 5: Update `README.rst`'s Maintainers/Releases sections**

Replace the `Maintainers` through `Releases` sections (everything from `Maintainers\n-----------` to the end of the file) with:

```rst
Maintainers
-----------
To install the distribution for local development, some additional setup is required:

#. `Install uv <https://docs.astral.sh/uv/getting-started/installation/>`_ (only needs to be
   done once).

#. Run the following command to install additional dependencies::

      uv sync --group=dev

#. Activate pre-commit hook::

      uv run autohooks activate --mode=pythonpath

Running Unit Tests and Type Checker
-----------------------------------
Run the tests for all supported versions of Python using
`tox <https://tox.readthedocs.io/>`_::

   uv run tox -p

.. note::

   The first time this runs, it will take awhile, as mypy needs to build up its cache.
   Subsequent runs should be much faster.

If you just want to run unit tests in the current virtualenv (using
`pytest <https://docs.pytest.org>`_)::

   uv run pytest

If you just want to run type checking in the current virtualenv (using
`mypy <https://mypy.readthedocs.io>`_)::

   uv run mypy src test

Documentation
-------------
To build the documentation locally:

#. Switch to the ``docs`` directory::

    cd docs

#. Build the documentation::

    uv run make html

Releases
--------
Steps to build releases are based on
`Packaging Python Projects Tutorial <https://packaging.python.org/en/latest/tutorials/packaging-projects/>`_.

.. important::

   Make sure to build releases off of the ``main`` branch!

One-time Setup
~~~~~~~~~~~~~~
#. Install the ``keyring`` tool and add it to your ``PATH``::

      uv tool install keyring
      uv tool update-shell

   Restart your shell after running ``update-shell``.
#. `Create a PyPI API token <https://pypi.org/manage/account/#api-tokens>`_ and store it
   in the OS keychain::

      keyring set https://upload.pypi.org/legacy/ __token__

   Paste the ``pypi-...`` token when prompted.

1. Build the Project
~~~~~~~~~~~~~~~~~~~~~
#. Delete artefacts from previous builds, if applicable::

    rm dist/*

#. Run the build::

    uv build

#. The build artefacts will be located in the ``dist`` directory at the top level of the
   project.

2. Upload to PyPI
~~~~~~~~~~~~~~~~~
#. Bump the version (also updates ``uv.lock``)::

      uv version <version>

#. Upload build artefacts to PyPI::

    uv publish --username __token__

3. Create GitHub Release
~~~~~~~~~~~~~~~~~~~~~~~~
#. Create a tag and push to GitHub::

      git tag -a <version> -m "Release <version>"
      git push origin <version>

#. Go to the `Releases page for the repo`_.
#. Click ``Draft a new release``.
#. Select the tag that you created above.
#. Specify the title of the release (e.g., ``{{ cookiecutter.project_name }} v1.2.3``).
#. Write a description for the release.  Make sure to include:
   - Credit for code contributed by community members.
   - Significant functionality that was added/changed/removed.
   - Any backwards-incompatible changes and/or migration instructions.
   - SHA256 hashes of the build artefacts.
#. GPG-sign the description for the release (ASCII-armoured).
#. Attach the build artefacts to the release.
#. Click ``Publish release``.

.. _Releases page for the repo: https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/releases
```

The `Requirements` section above `Maintainers` (Python version list) is unchanged — it already reads from the same `cookiecutter.__python_major`/`__python_minor` variables and needs no edit.

- [ ] **Step 6: Commit**

Run `git status` first, then use the `creative-commits` skill.

## Task 5: Add baseline agent infra to the generated project

**Files:**
- Create: `{{ cookiecutter.github_project_name }}/AGENTS.md`
- Create: `{{ cookiecutter.github_project_name }}/CLAUDE.md` (symlink to `AGENTS.md`)
- Create: `{{ cookiecutter.github_project_name }}/.claude/settings.json`
- Create: `{{ cookiecutter.github_project_name }}/.claude/skills` (symlink to `../.agents/skills`)
- Create: `{{ cookiecutter.github_project_name }}/.agents/skills/release/SKILL.md`
- Create: `{{ cookiecutter.github_project_name }}/.agents/skills/rotate-python-versions/SKILL.md`
- Modify: `{{ cookiecutter.github_project_name }}/.gitignore`

**Interfaces:**
- Consumes: the `uv`/`hatchling` pyproject and `renovate.json` from Task 4 (the ported `release` skill's commands assume both).

- [ ] **Step 1: Write `AGENTS.md`**

```markdown
## Getting Started

Before writing code, check:

- `docs/adr/INDEX.md` — prior decisions (don't re-litigate)
- `docs/plans/` — current implementation plan, if one exists

## Architecture Decision Records

When making significant decisions — choosing between libraries, patterns, tools, or conventions — you **must** write an ADR before implementing the decision. Use the `writing-adrs` skill for the format and conventions. ADRs live in `docs/adr/`. Before writing, run `ls docs/adr/` to find the highest existing number and increment it.

## Commands

```bash
uv run autohooks activate --mode=pythonpath   # install pre-commit hook (once per clone)
uv run git commit                             # always use instead of git commit (runs autohooks)
uv sync --group=dev                           # sync deps after pulling
uv run pytest                                 # run tests (current Python)
uv run tox -p                                 # run tests (all supported versions)
uv run mypy src test                          # type check
uv run ruff check                             # lint
uv run make -C docs clean && uv run make -C docs html  # build docs
```

**In a worktree:** the shell can silently reset to the main checkout, so always prefix state-mutating commands (`uv add`/`sync`/`run`) with `cd <worktree> &&` to ensure they hit the worktree.

## Architecture

_Describe the package's public API and class/module layout here as it grows — list high-level modules, not individual files._

## Docstrings

Google/Napoleon format (`Args:`, `Returns:`, `Note:`) — not Sphinx `:param:` style. Max 80 chars per line. Escape backslashes (e.g. `'\\n'` not `'\n'`). Blank line before lists inside `Args:` sections to avoid Sphinx indentation warnings. ReadTheDocs treats all Sphinx warnings as errors — resolve them before pushing.

## Tests

Every test function has a one-line docstring stating the behaviour it verifies.

## Code Comments

Place comments on the line preceding the code they document, not as trailing comments.

## Language and Style

- NZ English; incorporate Te Reo Māori where natural (e.g. "mahi", "kaupapa")
- Use "Initialises" not "Initializes"

### Writing for coding agents

- Do not document information that already exists in the coding agent's training data or could be easily discovered by reading the code.
- Do not list individual files; list high-level directories so the agent knows where to look.
- Aim for concise style that optimises token count without sacrificing clarity.

## Branches

- `main` — releases only; merge from `develop` via PR
- `develop` — main development branch
- Feature branches off `develop` for all new work

## Git Worktrees

Use the `using-git-worktrees` skill; it creates worktrees via the native `EnterWorktree` tool under `.claude/worktrees/` (gitignored). Don't hand-roll `git worktree add` when the native tool is available. Keep `.claude/` a real directory (only `.claude/skills` is a symlink into `.agents/skills`) — the native tool refuses to run if `.claude` itself is a symlink.

After creating a worktree, install its pre-commit hook (see the autohooks activate command in Commands). A fresh worktree has no per-worktree hooks directory, so create it first:

```bash
mkdir -p "$(git rev-parse --git-dir)/hooks"
```
```

Note the `Branches` section here restores the `develop`/`main` gitflow model (unlike this repo's own root `AGENTS.md`) — a generated project is expected to reach an actual PyPI release, where class-registry's model applies directly; this repo's own root does not, per the Global Constraints above.

- [ ] **Step 2: Create the `CLAUDE.md` symlink and `.claude/settings.json`**

```bash
cd '{{ cookiecutter.github_project_name }}'
ln -s AGENTS.md CLAUDE.md
mkdir -p .claude
```

Write `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "phx@todofixthis": true
  },
  "extraKnownMarketplaces": {
    "todofixthis": {
      "source": {
        "source": "github",
        "repo": "todofixthis/phx-claude-siat"
      }
    }
  }
}
```

- [ ] **Step 3: Create the `.claude/skills` symlink**

```bash
cd '{{ cookiecutter.github_project_name }}'
mkdir -p .agents/skills
ln -s ../.agents/skills .claude/skills
```

- [ ] **Step 4: Port `rotate-python-versions/SKILL.md` verbatim**

Copy `/home/user/todofixthis/class-registry/.agents/skills/rotate-python-versions/SKILL.md` to `{{ cookiecutter.github_project_name }}/.agents/skills/rotate-python-versions/SKILL.md` unchanged — its content (locations to update: `pyproject.toml`, `.github/workflows/`, `docs/`/`README.rst`, `CLAUDE.md`) is already generic and needs no cookiecutter substitution.

- [ ] **Step 5: Write a templated `release/SKILL.md`**

Adapted from `/home/user/todofixthis/class-registry/.agents/skills/release/SKILL.md`, with the project name, PyPI/import names, and GitHub repo templated, and the GPG fingerprint looked up dynamically instead of hardcoded (a new project has no prior release to have published a fixed fingerprint for, and a looked-up value can't go stale):

```markdown
---
name: release
description: Use when preparing or publishing a new release of {{ cookiecutter.project_name }} — covers release notes, version bump, build, PyPI upload, and GitHub release creation
---
# Release

## Phase 1 — Research & draft (before touching any files)

### 1. Gather changes since last release
```bash
gh release list --limit 1 --json tagName --jq '.[0].tagName'   # find last release tag
git log <last-tag>..HEAD --oneline                              # all commits since
```

### 2. Look up PR and issue context
For every merge commit, extract the PR number and fetch its description:
```bash
git log <last-tag>..HEAD --oneline --merges
gh pr view <number> --json title,body,labels
```

For every `#<number>` reference in commit messages, fetch the issue:
```bash
gh issue view <number> --json title,body,labels
```

### 3. Draft release notes
Using the commit list, PR descriptions, and issue context, draft the release notes following the _Writing Release Notes_ guide below. When a bullet relates to a GitHub issue, prefix it with `[#number]`. Run the `nz-english` skill on the draft, then present it to the developer for review and incorporate feedback before proceeding.

### 4. Recommend version number
Based on the changes, recommend a semver bump:
- **major** — breaking changes
- **minor** — new features or behaviour changes, fully backwards-compatible
- **patch** — bug fixes only

### 5. Gate: breaking changes require a migration guide
A **breaking change** is anything that makes previously-working code fail — at runtime, or under a type checker. Undocumented behaviour someone relied on still counts; "only a couple of users" measures blast radius, not compatibility. If this release has none, skip to the stop below.

**First, settle the version.** Step 4 defines minor and patch as *fully backwards-compatible*, so a breaking change in anything but a major contradicts it. When that happens, stop and put it to the developer: bump to major, or keep the smaller bump and record why in an ADR. Neither pick it for them nor draft around it — the answer decides which guide the rest of this step is about, and a release drafted for one version and linked to another ships broken.

**Then the guide.** One guide per major line, `docs/upgrading_to_v<major>.rst` — never a per-minor page. `<major>` is the major being released, or, for a break shipped in a minor or patch, the major line it lands on.

It must:
- **cover *this* release's breaking change.** A guide left over from an earlier release satisfies nothing — its existence is what makes this the easy check to fake. A break shipped in a `.3.0` gets its own section in `upgrading_to_v<major>.rst`, headed by the version that introduced it.
- exist, be listed in the `docs/index.rst` toctree, and be linked from the upgrade-alert listing in **both** `docs/index.rst` and `README.rst` — the two carry the same listing and drift apart easily. The link syntax differs by file: `docs/index.rst` uses a Sphinx `:doc:` role targeting `upgrading_to_v<major>`; `README.rst` uses a relative link to the source, `` `Upgrading to {{ cookiecutter.project_name }} v<major> <docs/upgrading_to_v<major>.rst>`_ `` — the `:doc:` role renders as raw text on GitHub, where the README is read.
- follow _Writing a Migration Guide_ below.

**If any of that is missing, the release stops here** — write it first.

Release notes do not satisfy this gate. They are read once, by people who already know a release happened; the guide is what someone finds months later when their code breaks and they don't yet know why.

```bash
ls docs/upgrading_to_v<major>.rst                        # exists
rg 'upgrading_to_v<major>' docs/index.rst README.rst     # index: toctree + alert; README: alert
uv run make -C docs clean && uv run make -C docs html    # builds, and it isn't orphaned
```
Then read the guide and confirm it covers this release's break. No command checks that for you.

**Stop here. Get explicit confirmation of the release notes and version number before continuing.**

---

## Phase 2 — Publish (after confirmation)

### 6. Bump version on `develop`
```bash
uv version <version>
```
This updates `pyproject.toml` and re-locks `uv.lock` in one step. Commit both files and push to `develop`.

### 7. Open release PR
```bash
gh pr create --base main --title "Release v<version>" --body-file release-<version>.md
```
**Stop here. Wait for the user to confirm the PR is merged before continuing.**

### 8. Switch to `main`
```bash
git checkout main && git pull
```

### 9. Build
```bash
uv sync --group=dev
rm -f dist/*
uv build
```
Sync first — pulling `main` may have brought in dependency changes. Artefacts land in `dist/`.

### 10. Tag and push
```bash
git tag -a <version> -m "Release <version>"
git push origin <version>
```
`<version>` must match `pyproject.toml`.

### 11. Create GitHub release

**a. Append checksums to the release notes file:**
```bash
sha256sum dist/{{ cookiecutter.pypi_project_name.replace('-', '_') }}-* >> release-<version>.md
```

**b. GPG-sign the document and each build artefact:**
```bash
GPG_KEY=$(git config user.email)
gpg --local-user "$GPG_KEY" --clearsign release-<version>.md   # → release-<version>.md.asc
for f in dist/{{ cookiecutter.pypi_project_name.replace('-', '_') }}-*; do gpg --local-user "$GPG_KEY" --detach-sign "$f"; done
# Creates dist/{{ cookiecutter.pypi_project_name.replace('-', '_') }}-*.sig alongside each artefact
```

**c. Build the release body** — concatenate the notes and the signed copy:
```
<contents of release-<version>.md>

---

````
<contents of release-<version>.md.asc>
````
```
Write this to `release-<version>-body.md`.

**d. Create the release and upload all artefacts:**
```bash
gh release create <version> dist/* \
  --title "{{ cookiecutter.project_name }} v<version>" \
  --notes-file release-<version>-body.md
```
`dist/*` picks up the `.whl`, `.tar.gz`, and `.sig` files.

### 12. Upload to PyPI
```bash
uv publish --username __token__
```

### 13. Clean up
```bash
rm release-<version>.md release-<version>.md.asc release-<version>-body.md
git checkout develop && git pull
```

### 14. Close related GitHub issues
For every issue referenced in the release notes, close it with a comment:
```bash
gh issue close <number> --comment "Implemented in [v<version>](https://github.com/{{ cookiecutter.github_username }}/{{ cookiecutter.github_project_name }}/releases/tag/<version>)."
```

### 15. Rebase `develop` onto `main`
```bash
git rebase origin/main
git push
```
Because `develop` now contains all of `main`'s commits, the histories no longer diverge and a regular (non-force) push succeeds.

---

## Writing Release Notes

### Structure
```markdown
# {{ cookiecutter.project_name }} v<version>
<one-sentence summary of the release character>

> [!WARNING]
> **Breaking changes**
> - {what changed}
>   - {migration instructions}
>   - {error you'll see if you don't migrate}
>
> Full migration guide: [Upgrading to {{ cookiecutter.project_name }} v{major}](https://{{ cookiecutter.pypi_project_name }}.readthedocs.io/en/latest/upgrading_to_v{major}.html)

## New features
## Enhancements
## Bug fixes

> [!NOTE]
> **Verifying release artefacts**
> 1. Import the signing key: `curl https://github.com/{{ cookiecutter.github_username }}.gpg | gpg --import`
> 2. Download the `.whl` or `.tar.gz` and its matching `.sig` file from the release assets
> 3. Verify: `gpg --verify {{ cookiecutter.pypi_project_name.replace('-', '_') }}-<version>-py3-none-any.whl.sig {{ cookiecutter.pypi_project_name.replace('-', '_') }}-<version>-py3-none-any.whl`
>
> Key fingerprint: run `gpg --fingerprint {{ cookiecutter.author_email }}` to look it up

# SHA256 Checksums
```

Only include the `[!WARNING]` block if there are breaking changes — but when it is present, the migration guide link is **required**, not optional. Omit any section that has no entries.

### Grouping related items
- **2–4 related bullets:** nest as a hierarchical sublist under the parent bullet
- **5+ related bullets:** promote to a `###` subheading within the section

### Content filter

**Always include**
- New capabilities developers can use
- Architectural decisions
- Behaviour changes
- Breaking changes

**Usually omit**
- Technical details of how something works internally
- Configuration consolidation (unless it changes developer-facing behaviour)
- Code organisation changes
- Dependency updates (include only if resolving a critical or high-severity vulnerability)
- Improvements to coding agent instructions

**Always omit**
- Formatting, linting, minor refactoring
- Test coverage updates

---

## Writing a Migration Guide

`docs/upgrading_to_v<major>.rst`. It stays unreachable until wired into three slots: the `docs/index.rst` toctree, and the upgrade-alert listing in **both** `docs/index.rst` and `README.rst`. The two listings (one bullet per major upgrade) drift apart easily — add the bullet to each, or the README goes stale. Their link syntax differs: `docs/index.rst` uses a Sphinx `:doc:` role targeting `upgrading_to_v<major>`; `README.rst` uses a relative link to the source, `` `Upgrading to {{ cookiecutter.project_name }} v<major> <docs/upgrading_to_v<major>.rst>`_ `` — `:doc:` renders as raw text on GitHub, where the README is read.

One page covers a whole major line: the move onto it, and any break shipped later within it. Say so in the opening paragraph. Breaks after the major boundary get their own `Changes in v<version>` section; the major boundary itself is the page's main content.

Write for someone who upgraded, hit an error, and does not yet know a release caused it. They arrive by searching the error text — not by reading release notes.

Each breaking change needs four things:

1. **What changed**, in terms of what the developer wrote, not what the internals do.
2. **The error they'll actually see** — copy it verbatim from the tool. Never paraphrase a compiler; they match on this text.
3. **The fix**, as code.
4. **Whether runtime behaviour changed.** If it didn't, say so plainly and early — it converts a panic into a chore.

Then add what the fix leads them into next:

- **Second-order traps.** A fix that lands people in a subtler failure needs that failure documented beside it, with its error text.
- **Facts stranded in ADRs.** ADRs are not in the toctree and readers never see them. If an ADR holds the only explanation of something a migrating developer needs, the guide is where it goes.

Verify every code sample and every error message by running it.

Before wiring the guide in, run two passes over the draft:

### Audience-surrogate review

Dispatch one subagent on the main model (a reasoning task, not a cheap one), given only the draft and cast as the reader above. It must resolve its problem from the guide alone and flag every place it stays stuck: an error string it can't match verbatim against what a tool emits, a fix it can't apply without knowledge the guide assumes, unexplained jargon, a missing second-order trap or stranded-ADR fact. Address the feedback before continuing.

### Conciseness pass

Tighten the reviewed draft: cut repetition, merge overlapping fixes, drop hedging and prose that restates a code sample. Never trim two things for length: **verbatim error text and code fixes** — readers match on them — and any **migration step**. Then, since this project uses NZ English, run `phx:nz-english` over the result.
```

- [ ] **Step 6: Update `.gitignore`**

Append to the generated project's existing `.gitignore` (adds worktree/cache patterns to the existing Python-artefact patterns):

```gitignore

# Agent worktrees
.claude/worktrees/

# Linting cache
.ruff_cache
```

- [ ] **Step 7: Commit**

Run `git status` first, then use the `creative-commits` skill.

## Task 6: Root README for the template repo itself

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write it**

```markdown
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
```

- [ ] **Step 2: Commit**

Run `git status` first, then use the `creative-commits` skill.

## Task 7: Write the ADRs and regenerate the index

By this point every path these ADRs cite already exists (created in Tasks 1–4), so `scripts/adr/generate_index.py`'s scope validation will pass.

**Files:**
- Create: `docs/adr/001-support-three-most-recent-python-releases.md`
- Create: `docs/adr/002-generate-projects-with-uv-and-hatchling.md`
- Create: `docs/adr/003-manage-updates-with-renovate.md`
- Create: `docs/adr/004-validate-the-template-by-baking-it.md`
- Create: `docs/adr/INDEX.md` (generated, not hand-written)

- [ ] **Step 1: Write ADR 001**

```markdown
---
status: Accepted
date: 2026-08-29
scope: [cookiecutter.json, hooks/pre_prompt.py, "{{ cookiecutter.github_project_name }}/pyproject.toml"]
summary: Generated projects support the three most recent Python minor releases, computed dynamically from whichever interpreter runs cookiecutter.
---

# 001: Support the Three Most Recent Python Minor Releases

## Context

Every project this template generates ships `requires-python = ">=X.Y-2"` and a
three-entry tox/CI matrix, derived from `cookiecutter.__python_major`/
`__python_minor` — themselves computed by `hooks/pre_prompt.py` from the
interpreter running `cookiecutter`, not hardcoded in `cookiecutter.json`. This
was already true before this modernization; it's recorded here because
`todofixthis/class-registry` (very likely once generated by an earlier version
of this exact template) states the same policy as its own ADR 001, and the
`rotate-python-versions` skill ported into generated projects (Task 5 of this
modernization) assumes a written policy to update when a version rotates.

## Decision

Keep computing the floor dynamically rather than hardcoding a version in
`cookiecutter.json`: a template baked today should always support the three
most recent releases as of *today*, not whatever was current when this
repo was last edited.

## Consequences

- A generated project's actual floor depends on which Python baked it. Two
  people running `cookiecutter gh:todofixthis/cookiecutter-py` a year apart
  get different (both currently-correct) floors.
- The `generate-and-validate.yml` workflow (this modernization's Task 3) bakes
  under 3.12/3.13/3.14 explicitly, so CI exercises the same matrix width
  regardless of which Python happens to run the workflow itself.
```

- [ ] **Step 2: Write ADR 002**

```markdown
---
status: Accepted
date: 2026-08-29
scope: ["{{ cookiecutter.github_project_name }}/pyproject.toml", "{{ cookiecutter.github_project_name }}/.github/workflows/build.yml", "{{ cookiecutter.github_project_name }}/.readthedocs.yaml"]
summary: Generate projects using uv + hatchling instead of Poetry, matching what class-registry and phx-claude-siat have both since moved to.
---

# 002: Generate Projects Using uv + hatchling Instead of Poetry

## Context

The template previously generated a Poetry-based project (`poetry-core`
build backend, `poetry install`/`poetry run` throughout CI, README, and the
`autohooks` `mode = "poetry"` setting). Both sibling repos this template is
being brought in line with — `class-registry` and `phx-claude-siat` — have
since moved their own Python tooling to `uv` + `hatchling`, and `class-registry`
in particular is a close match for what this template still generates
(same `src`-layout, Sphinx/ReadTheDocs docs, `autohooks` pre-commit setup),
making it the direct reference for the migration.

Alongside this, CI, tox, and the README were all invoking `poetry run mypyc
src test` for "type checking" — `mypyc` is the mypy-to-C *compiler*, not a
type checker; this traces to an abandoned experiment (`9f2b5d7`, "[Experimental]
Added mypyc") that was never cleaned up. `class-registry`'s own CI runs plain
`mypy src test`.

## Options

### Option 1: Keep Poetry, only fix the mypyc bug

Smallest possible change: swap `mypyc` for `mypy` everywhere it's invoked as a
type-check step, leave the build backend and dependency management as Poetry.

**Pros:** Minimal diff.
**Cons:** Leaves the template diverging further from both sibling repos'
actual current tooling every time either one moves forward again; keeps
`autohooks` in its Poetry-specific mode while everything else this
modernization ports (the ADR system, the `release`/`rotate-python-versions`
skills) assumes the `uv`-based commands those skills already use verbatim.
**Risks:** A future modernization pass has to redo this migration anyway,
on top of whatever's changed by then.

### Option 2: Migrate to uv + hatchling (Accepted)

Match `class-registry`'s current `pyproject.toml` structure: `hatchling`
build backend, PEP 621 `[project]` metadata, `[dependency-groups]` `dev`/`ci`
(not Poetry's `[tool.poetry.group.*.dependencies]`), `autohooks` `mode =
"pythonpath"`, and `tox` with the `uv-venv-lock-runner`. Fix the `mypyc` bug
as part of the same change, since both touch the same CI/tox/README
invocations.

**Pros:** Generated projects match the two reference repos exactly, so the
`release` and `rotate-python-versions` skills ported into them (Task 5) work
unmodified; `uv sync`/`uv run` is uniformly faster than Poetry's resolver.
**Cons:** Larger diff across `pyproject.toml`, `build.yml`, `.readthedocs.yaml`,
and `README.rst` at once.
**Risks:** Anyone with an existing project generated by the old (Poetry-based)
template doesn't get this migration retroactively — it only applies to
projects generated from this point forward.

## Decision

Option 2. The mypyc bug needed fixing regardless, and fixing it inside a
Poetry setup that's already diverged from both reference repos would leave
the template in an intermediate state neither skill nor sibling repo matches.

## Consequences

- `{{ cookiecutter.github_project_name }}/pyproject.toml`'s `[tool.tox]`
  `env_list` now uses undotted env names (`py312`, not `py3.12`) — the
  dotted form the old template used isn't valid tox environment-name syntax,
  and `class-registry`'s own tox config confirms the undotted form is what
  actually works.
- `renovate.json` replaces `dependabot.yml` in the generated project too (ADR
  003), since Renovate's `helpers:pinGitHubActionDigests` is what keeps the
  now-SHA-pinned Action references in `build.yml` current.
```

- [ ] **Step 3: Write ADR 003**

```markdown
---
status: Accepted
date: 2026-08-29
scope: [renovate.json, "{{ cookiecutter.github_project_name }}/renovate.json"]
summary: Manage dependency and GitHub Action updates via Renovate, not Dependabot, matching both sibling repos.
---

# 003: Manage Updates with Renovate, Not Dependabot

## Context

This repo's own `.github/dependabot.yml` targeted a glob directory (since the
templated project directory name isn't a literal path), and the generated
project's own `dependabot.yml` pointed at a concrete path. Both `class-registry`
and `phx-claude-siat` instead use a single `renovate.json` extending
`config:recommended` plus `helpers:pinGitHubActionDigests`, which — unlike
Dependabot's `github-actions` ecosystem — pins Actions to commit SHAs (with a
version-tag comment) rather than floating tags, closing the gap this
modernization's CI changes (SHA-pinned `actions/checkout`, `astral-sh/setup-uv`,
`actions/setup-python`) rely on staying current.

## Decision

Replace `dependabot.yml` with `renovate.json` (`{"extends": ["config:recommended",
"helpers:pinGitHubActionDigests"]}`) in both this repo's own root and the
generated project.

## Consequences

- Renovate needs the GitHub App installed on the repo (and, once generated
  projects exist, on each of those too) — a one-time, per-repo setup step
  outside this template's own files, same as it presumably already is for
  the two sibling repos.
- The SHA pins added by this modernization's CI workflows (see Global
  Constraints) are a snapshot Renovate will keep moving forward from here.
```

- [ ] **Step 4: Write ADR 004**

```markdown
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
```

- [ ] **Step 5: Generate the index**

```bash
uv run python -m scripts.adr.generate_index
```

Expected: `docs/adr/INDEX.md` is created listing all four ADRs with their scope/summary columns populated, and prints `Generated docs/adr/INDEX.md (4 entries)` with no `Error:` lines. If a scope entry errors as "nothing matches", re-check that the corresponding Task actually created that path before this task ran.

- [ ] **Step 6: Commit**

Run `git status` first, then use the `creative-commits` skill.

## Task 8: Final validation pass

- [ ] **Step 1: Run every check this repo's own CI will run**

```bash
uv run ruff check
uv run mypy scripts test
uv run pytest -v
uv run python -m scripts.adr.generate_index && git diff --exit-code docs/adr/INDEX.md
```

Expected: all pass with no diff.

- [ ] **Step 2: Manually smoke-test the generate-and-validate workflow's steps locally**

```bash
uvx "cookiecutter>=2,<3" . --no-input --output-dir /tmp/baked-manual-check
cd /tmp/baked-manual-check/my-python-project
uv sync --group ci
uv run ruff check
uv run mypy src test
uv run pytest
mkdir -p docs/_static && uv run --directory docs make html
```

Expected: every command succeeds. This is the same sequence `generate-and-validate.yml` runs in CI, minus the matrix — if anything here fails, a task above needs revisiting before pushing.

- [ ] **Step 3: Delete this plan file**

```bash
git rm docs/superpowers/plans/2026-08-29-repo-modernization.md
```

Nothing that ships should reference an ephemeral planning doc — the code and the ADRs written in Task 7 are the lasting record.

- [ ] **Step 4: Commit**

Use the `creative-commits` skill for this final commit, then push the branch and open the PR.

---

## Intentional Decisions

*(Populated during review — reviewers must not re-raise these)*

- **ADRs are written last (Task 7), after the decisions they document are already implemented**, rather than before implementation as `AGENTS.md`'s general rule prescribes. This is a one-off, coordinated modernization touching many interdependent files at once (an ADR's `scope` must validate against paths that don't all exist until several other tasks complete); the general "ADR before implementation" rule applies to normal day-to-day work going forward.
- **No GitHub App-based release automation** (`phx-claude-siat`'s `release.yml`) is ported anywhere — it needs admin-configured secrets and branch rulesets, and neither this repo nor its generated output currently publish anything through it. See Global Constraints.
- **The generated project's `AGENTS.md` restores the `develop`/`main` gitflow branch model**, while this repo's own root `AGENTS.md` stays trunk-based `main`-only — deliberate, since a generated project is expected to eventually cut PyPI releases (where the two-branch model matters) and this template repo itself never will.
- **`scripts/adr/generate_index.py` is ported from `class-registry`'s PyYAML-based fork, not `phx-claude-siat`'s stdlib-only canonical version** that `writing-adrs` names as the reference implementation. The two are behaviourally identical (same frontmatter rules, same `--for` mode); the canonical version stays stdlib-only because `phx-claude-siat` has no Python project root to hang a PyYAML dependency off (ADR 007 there). That constraint doesn't apply here any more than it applies to `class-registry` — this repo now has a real `pyproject.toml` and dev dependency group — and `class-registry`'s own ADR 004 already made and recorded this exact call for the same reason. Porting class-registry's version (and taking on `pyyaml`/`types-pyyaml` as dev dependencies) follows that precedent rather than re-deriving it.
- **The root `.github/workflows/ci.yml` `test` job runs on a single Python version, with no matrix** — unlike `class-registry`'s `build` job, which matrixes 3.12/3.13/3.14. This repo's own tooling (the ADR generator, the bake-and-validate tests) isn't a published library with a version-support commitment of its own; it only needs to run under whatever Python develops it. The three-version matrix that matters — the *generated* project's support window — is exercised by `generate-and-validate.yml` instead (Task 3 Step 2).
- **The GPG key fingerprint in the ported `release` skill and README is looked up dynamically** (`gpg --fingerprint <email>`) rather than hardcoded to the literal value found in `class-registry`'s own skill — that value is real key material observed in a sibling repo, not confirmed as intentionally identical across every future generated project, so a dynamic lookup is both safer and won't go stale.

## Self-Review Checklist

- [ ] Does the plan header include a `**Worktree:**` field naming the existing worktree and branch? — N/A, explicitly noted as no nested worktree, with rationale.
- [ ] Does every commit step remind the agent to run `git status` first? — yes, every commit step.
- [ ] Does the plan include an Intentional Decisions section? — yes.
- [ ] Does the final task delete the plan file? — yes, Task 8 Step 3.
- [ ] Spec coverage: agent infra (AGENTS.md/CLAUDE.md/.claude — done pre-work + Task 5), tooling (uv/hatchling/autohooks/ADRs — Tasks 1, 4), conventions (Renovate, NZ English, ADRs — Tasks 1, 3, 4, 7), the requested generate-and-validate PR workflow (Task 3) — all covered.
- [ ] Placeholder scan: no "TBD"/"implement later" in any step; the one `_Describe the package's public API..._` line in Task 5's `AGENTS.md` is intentional boilerplate for a project with no code yet, not a plan placeholder.
- [ ] Type/name consistency: `scripts.adr.generate_index.generate(adr_dir, repo_root)` and `main(argv, adr_dir, repo_root)` are used identically in Task 1 (creation) and Task 3/7 (CI/manual invocation).
