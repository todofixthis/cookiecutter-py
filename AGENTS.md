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
uv run pytest                                 # bake the template and validate the output
uv run mypy hooks scripts test                # type check
uv run ruff check hooks scripts test          # lint
```

`hooks`/`scripts`/`test` are named explicitly — a bare `ruff check` walks the whole repo and trips over `{{ cookiecutter.github_project_name }}/pyproject.toml`'s unrendered Jinja (it isn't a real project; `[tool.ruff] extend-exclude` alone doesn't stop ruff's directory walk from touching it).

**In a worktree:** the shell can silently reset to the main checkout, so always prefix state-mutating commands (`uv add`/`sync`/`run`) with `cd <worktree> &&` to ensure they hit the worktree.

## Architecture

This repo is a [cookiecutter](https://cookiecutter.readthedocs.io/) template, not a Python package in its own right:

- `cookiecutter.json` / `hooks/pre_prompt.py` — the prompts a user answers, plus a pre-prompt hook that fills in `python_version` (from the host interpreter) and `this_year` before prompting starts.
- `{{ cookiecutter.github_project_name }}/` — the templated project content. Everything a generated project ships (its own `pyproject.toml`, CI, docs, agent infra) lives here, separate from this repo's own dev tooling below.
- `scripts/` — this repo's own dev tooling (the ADR index generator).
- `test/` — bakes the template with default answers and asserts the output is well-formed (no leftover Jinja markers, valid `pyproject.toml`, etc.). This is this repo's only test suite; there's no source package of its own to unit-test.

The `.github/workflows/generate-and-validate.yml` workflow goes further than `test/`: it bakes a real project and runs *that project's own* lint/type-check/test/docs-build commands, so a template change that breaks what it generates fails CI even if `test/`'s lighter checks pass.

## Docstrings

Google/Napoleon format (`Args:`, `Returns:`, `Note:`) — not Sphinx `:param:` style.

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

This repo has no release/versioning process of its own (it isn't published to PyPI), so it stays trunk-based: work off `main` directly, PR review before merging. There's no `develop` branch.

## Git Worktrees

Use the `using-git-worktrees` skill; it creates worktrees via the native `EnterWorktree` tool under `.claude/worktrees/` (gitignored). Don't hand-roll `git worktree add` when the native tool is available. Keep `.claude/` a real directory — the native tool refuses to run if `.claude` itself is a symlink.

After creating a worktree, install its pre-commit hook (see the autohooks activate command in Commands). A fresh worktree has no per-worktree hooks directory, so create it first:

```bash
mkdir -p "$(git rev-parse --git-dir)/hooks"
```
