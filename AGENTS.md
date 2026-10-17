## Getting Started

Before writing code, check:

- `docs/adr/INDEX.md` — prior decisions (don't re-litigate)
- `docs/superpowers/plans/` — current implementation plan, if one exists
- `docs/backlog/` — deferred work; `rg <area> docs/backlog/` before starting on an area

## Deferred work

**Deferred work is never a GitHub issue here (ADR 011).** The tracker stays enabled for Renovate's Dependency Dashboard, so nothing stops you filing one, but no future session will read it. Asked to "file an issue for that", write the backlog file instead and say so. Do it their way only if they ask again after hearing that.

Work you defer goes in `docs/backlog/<slug>.md`, one file per item, in the shape `docs/backlog/README.md` fixes. Name the paths the item binds in its prose: `rg` is the only way to find it. Two cases go elsewhere:
- a condition that would reopen a decision goes in that ADR's `revisit-when`;
- a constraint a future editor must meet goes in a comment where they'll meet it.

Delete an item on the branch that finishes its work. Nothing checks for stale items.

## Architecture Decision Records

When making significant decisions — choosing between libraries, patterns, tools, or conventions — you **must** write an ADR before implementing the decision. Use the `phx:writing-adrs` skill (from the phx plugin, which `.claude/settings.json` enables) for the format, conventions and tooling: its `adr.py` allocates the number, generates `docs/adr/INDEX.md` and validates the corpus. Where the skill isn't available (outside Claude Code, or the plugin isn't loaded), read the [skill](https://github.com/todofixthis/phx-claude-siat/blob/8.1.0/skills/writing-adrs/SKILL.md) and run the same tool as `phx-adr` (see Commands). Don't hand-edit the index or add a repo-local ADR script. ADRs live in `docs/adr/`.

## Commands

```bash
# Install the pre-commit hook (once per clone)
uv run autohooks activate --mode=pythonpath
# Always use instead of git commit (runs autohooks)
uv run git commit
# Sync deps after pulling
uv sync --group=dev
# Bake the template and validate the output
uv run pytest
# Type check
uv run mypy test scripts .autohooks
# Lint
uv run ruff check test scripts .autohooks
# Regenerate the template-owned rule (the pre-commit hook does this for you)
uv run python scripts/template_owned.py
```

The directories are named explicitly: `template/`'s Python files belong to the generated project, and are checked there by CI's bake.

To bake your working tree into a real project, as CI does, then validate it from inside that project:

```bash
rm -rf /tmp/baked && uv run copier copy --defaults --vcs-ref=HEAD --data copyright_year=2026 --data project_short_description=x . /tmp/baked
cd /tmp/baked && uv sync --group ci && uv run ruff check && uv run mypy src test && uv run pytest
```

`uv run copier` uses the version `uv.lock` pins, as CI does.

Keep `--vcs-ref=HEAD`: without it copier bakes the newest release tag, not your change. With it, copier also folds in uncommitted edits.

**In a worktree:** the shell can silently reset to the main checkout, so always prefix state-mutating commands (`uv add`/`sync`/`run`) with `cd <worktree> &&` to ensure they hit the worktree.

The phx plugin's ADR tool, for use where the skill isn't available. Renovate bumps these pins and the `adrs` CI job's together, matching each on its trailing `# X.Y.Z` comment (ADR 009) — keep that comment on the same line, despite the Code Comments rule below; moved or dropped, that pin silently stops being bumped.

```bash
# Scaffold the next ADR
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@0725567cec6bab6a227c2a3d569e64c226c33a4e#subdirectory=skills/writing-adrs' phx-adr new "Title" --summary "…" --scope path/ # 8.1.0
# List the decisions binding a path, before changing it
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@0725567cec6bab6a227c2a3d569e64c226c33a4e#subdirectory=skills/writing-adrs' phx-adr for path/to/file # 8.1.0
# Mark an ADR superseded
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@0725567cec6bab6a227c2a3d569e64c226c33a4e#subdirectory=skills/writing-adrs' phx-adr supersede OLD --by NEW # 8.1.0
# Regenerate docs/adr/INDEX.md
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@0725567cec6bab6a227c2a3d569e64c226c33a4e#subdirectory=skills/writing-adrs' phx-adr index # 8.1.0
# Validate, as CI does
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@0725567cec6bab6a227c2a3d569e64c226c33a4e#subdirectory=skills/writing-adrs' phx-adr check # 8.1.0
```

If CI reports a stale index the session's own tool can't reproduce, the installed plugin (which tracks phx-claude-siat's `main`) and the pinned release differ. Compare the two versions: if the installed one is newer, merge Renovate's pending bump, or bump by hand: each pin to the release's commit, and its comment and the skill link above to the release's version. The commit is the `refs/tags/<version>^{}` line of `git ls-remote --tags https://github.com/todofixthis/phx-claude-siat`, not the tag object above it. Otherwise update the plugin.

## Architecture

This repo is a [copier](https://copier.readthedocs.io/) template, not a Python package in its own right (ADR 008):

- `copier.yml` — the questions a user answers, and the template's settings. Every question needs a default except those with no possible one, since Renovate updates projects with `copier update --defaults`. Use no copier unsafe features (`_tasks`, `_migrations`, `_jinja_extensions`): Renovate runs without `--trust`. A value that must stay fixed after the first copy is a recorded question, never a computed variable; computed values re-render on every update (so `copyright_year` and `copyright_holder` are recorded, where cookiecutter's `this_year` was computed).
- `template/` — the templated project content. Only the contents of files ending `.jinja` are rendered; every other file's contents copy verbatim, symlinks included. Path names are always rendered, suffix or not. Jinja delimiters are `[[ ]]`, `[% %]` and `[# #]`, so a templated `run:` block uses `[ ]` or `test`, never bash's `[[ ]]`. Inside a `.jinja` file, wrap a TOML array of tables (`[[tool.mypy.overrides]]`) or a literal `[#` in `[% raw %]…[% endraw %]`. The generated AGENTS.md is identical across projects; a project's own sections go in `.agents/rules/project.md`, which copier writes only on first copy (ADR 010). `project.md` may add to, narrow or override a templated rule, and wins where the two conflict; the generated AGENTS.md's pointer to `.agents/rules/` must say so. `.agents/rules/template-owned.md.jinja` lists every template-owned file and is generated by `scripts/template_owned.py` (ADR 012), so never edit it by hand. A new file the project is meant to replace (a seed, like `test/test_placeholder.py`) goes in that script's `SEED_FILES`, spelt as it renders: no `.jinja`, but with any `[[ … ]]` path marker kept.
- `test/` — bakes the template with copier and asserts the output is well-formed (no leftover Jinja markers, valid `pyproject.toml`, etc.). This is this repo's only test suite; there's no source package of its own to unit-test. copier bakes this checkout by cloning it and committing the working tree, so a new template file bakes without `git add`, but only `.gitignore` keeps local junk under `template/` (a venv, say) out of the bake.

The skills and agent files under `template/` (its `.claude/`, `.agents/`, AGENTS.md and CLAUDE.md) serve generated projects and don't apply when working on this repo. This repo's own skills live in `.agents/skills/`, which `.claude/skills` links to; its `rotate-python-versions` skill covers both the generated Python range and the harness Python.

CI goes further than `test/`: it bakes a real project and runs *that project's own* lint/type-check/test/docs-build commands, so a template change that breaks what it generates fails CI even if `test/`'s lighter checks pass.

A template change reaches existing projects only once it's released: Renovate's copier manager then opens a PR in every project whose `.copier-answers.yml` records this template. See Releases.

## Docstrings

Google/Napoleon format (`Args:`, `Returns:`, `Note:`) — not Sphinx `:param:` style.

## Tests

Every test function has a one-line docstring stating the behaviour it verifies.

## Code Comments

Place comments on the line preceding the code they document, not as trailing comments.

**Exception: version pins.** A pin's `# X.Y.Z` (`uses: …@<SHA> # v7.0.1`, or the `phx-adr` pins above) trails the line it pins, because Renovate reads the version from that line. Keep these trailing.

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

## Releases

1. Merge `develop` into `main` via PR.
2. The maintainer tags the merge commit on `main` as `X.Y.Z` (bare semver, no `v` prefix). Agents don't tag; ask the maintainer.

Renovate does the rest: it opens a PR updating each generated project to the new tag.

## Git Worktrees

Use the `using-git-worktrees` skill; it creates worktrees via the native `EnterWorktree` tool under `.claude/worktrees/` (gitignored). Don't hand-roll `git worktree add` when the native tool is available. Keep `.claude/` a real directory — the native tool refuses to run if `.claude` itself is a symlink.

After creating a worktree, install its pre-commit hook (see the autohooks activate command in Commands). A fresh worktree has no per-worktree hooks directory, so create it first:

```bash
mkdir -p "$(git rev-parse --git-dir)/hooks"
```
