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

When making significant decisions — choosing between libraries, patterns, tools, or conventions — you **must** write an ADR before implementing the decision. Use the `phx:writing-adrs` skill (from the phx plugin, which `.claude/settings.json` enables) for the format, conventions and tooling: its `adr.py` allocates the number, generates `docs/adr/INDEX.md` and validates the corpus. Where the skill isn't available (outside Claude Code, or the plugin isn't loaded), read the [skill](https://github.com/todofixthis/phx-claude-siat/blob/9.2.0/skills/writing-adrs/SKILL.md) and run the same tool as `phx-adr` (see Commands). Don't hand-edit the index, or add a repo-local ADR script, pre-commit hook or vendored copy of the tool (ADR 019). ADRs live in `docs/adr/`.

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

The phx plugin's ADR tool, for use where the skill isn't available. Renovate bumps these pins and the `adrs` CI job's together, matching each on its trailing `# X.Y.Z` comment (ADR 018) — keep that comment on the same line, despite the Code Comments rule below; moved or dropped, that pin silently stops being bumped.

```bash
# Scaffold the next ADR
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@86f320fb6af2894dafd30cbd1e0dc1cbdb5c4575#subdirectory=skills/writing-adrs' phx-adr new "Title" --summary "…" --scope path/ # 9.2.0
# List the decisions binding a path, before changing it
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@86f320fb6af2894dafd30cbd1e0dc1cbdb5c4575#subdirectory=skills/writing-adrs' phx-adr for path/to/file # 9.2.0
# Mark an ADR superseded
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@86f320fb6af2894dafd30cbd1e0dc1cbdb5c4575#subdirectory=skills/writing-adrs' phx-adr supersede OLD --by NEW # 9.2.0
# Regenerate docs/adr/INDEX.md
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@86f320fb6af2894dafd30cbd1e0dc1cbdb5c4575#subdirectory=skills/writing-adrs' phx-adr index # 9.2.0
# Validate, as CI does
uvx --from 'git+https://github.com/todofixthis/phx-claude-siat@86f320fb6af2894dafd30cbd1e0dc1cbdb5c4575#subdirectory=skills/writing-adrs' phx-adr check # 9.2.0
```

If CI reports a stale index the session's own tool can't reproduce, the installed plugin (which tracks phx-claude-siat's `main`) and the pinned release differ. Compare the two versions: if the installed one is newer, merge Renovate's pending bump, or bump by hand: each pin to the release's commit, and its comment and the skill link above to the release's version. The commit is the `refs/tags/<version>^{}` line of `git ls-remote --tags https://github.com/todofixthis/phx-claude-siat`, not the tag object above it. Otherwise update the plugin.

## Architecture

This repo is a [copier](https://copier.readthedocs.io/) template, not a Python package in its own right (ADR 015):

- `copier.yml` — the questions a user answers, and the template's settings. Every question needs a default except those with no possible one, since Renovate updates projects with `copier update --defaults`. Use no copier unsafe features (`_tasks`, `_migrations`, `_jinja_extensions`): Renovate runs without `--trust`. A value that must stay fixed after the first copy is a recorded question, never a computed variable; computed values re-render on every update (so `copyright_year` and `copyright_holder` are recorded, where cookiecutter's `this_year` was computed).
- `template/` — the templated project content. Only the contents of files ending `.jinja` are rendered; every other file's contents copy verbatim, symlinks included. Path names are always rendered, suffix or not. Jinja delimiters are `[[ ]]`, `[% %]` and `[# #]`, so a templated `run:` block uses `[ ]` or `test`, never bash's `[[ ]]`. Inside a `.jinja` file, wrap a TOML array of tables (`[[tool.mypy.overrides]]`) or a literal `[#` in `[% raw %]…[% endraw %]`. The generated AGENTS.md is identical across projects; a project's own sections go in `.agents/rules/project.md`, and its own CI jobs in `.github/workflows/project.yml`, both of which copier writes only on first copy (ADRs 010 and 021), so a change to either reaches new projects only. `project.md` may add to, narrow or override a templated rule, and wins where the two conflict; the generated AGENTS.md's pointer to `.agents/rules/` must say so. `.agents/rules/template-owned.md.jinja` lists every template-owned file and is generated by `scripts/template_owned.py` (ADR 012), so never edit it by hand. A new file the project is meant to replace (a seed, like `test/test_placeholder.py`) goes in that script's `SEED_FILES`, spelt as it renders: no `.jinja`, but with any `[[ … ]]` or `[% if … %]` path marker kept. A file only some projects get has a conditional name, such as `docs/[% if docs_site %]conf.py[% endif %].jinja`, which copier skips when it renders empty; add it to the path list in `test_without_docs_site_bakes_no_sphinx_site`. A project answering `docs_site` no gets no Sphinx/ReadTheDocs site (it keeps `docs/adr/`), so every instruction to build, edit or link that site is conditional on it (ADR 016): a Jinja `[% if docs_site %]` block, giving the file a `.jinja` suffix if it lacks one. Only AGENTS.md, identical in every project (ADR 010), names the condition in prose instead, as "where `.readthedocs.yaml` exists". `test_without_docs_site_names_no_docs_site` catches the common forms of such an instruction left in a no bake; when it fails, fix the instruction, never that test's exempt set.
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

Merging `develop` into `main` is the release: `.github/workflows/release.yml` then tags the merge commit from the top `CHANGELOG.md` entry and publishes a GitHub Release with its notes (ADR 017), and Renovate offers that tag to every generated project, quoting the entry. Every push to `main` is a release, so nothing else merges into `main`: retarget any other PR into `main` to `develop`, ignoring its red Release check, and if one has already merged, stop and ask. Never tag by hand, even when asked: a hand tag on the wrong commit reaches every project unchecked. Say that merging the release PR does the tagging, and offer to prepare it.

1. On a branch off `develop`, prepend a `CHANGELOG.md` entry: a `## X.Y.Z - YYYY-MM-DD` heading (bare semver, no `v` prefix, today's date), a one-line theme, a blank line, then one bullet per change a generated project receives since the newest tag: a change under `template/` or to `copier.yml`'s questions or settings, the only files that shape a project. After `git fetch origin --tags`, list them with `git diff --stat "$(git tag --sort=-v:refname | head -n 1)"..origin/develop -- template copier.yml`; tags sit on `main`, so `git describe` from `develop` finds none. A large PR may take several bullets, and routine dependency bumps share one. Leave out everything else, this repo's own harness: the reader is a generated project's reviewer. If nothing in that diff changes what a project receives, there is nothing to release: say so and stop. For a major release, end the entry with the manual steps a project needs. Bump major for a release projects can't take with a plain `copier update`, minor for a new question or behaviour, otherwise patch. Confirm the version with the maintainer, then set `pyproject.toml`'s `version` to the same `X.Y.Z` and run `uv lock`: a test fails `gate` until the two match. Open a PR into `develop` for the entry and the bump, and leave its merge to the maintainer.
2. Once the entry is on `develop`, open the `develop` → `main` PR and leave the merge to the maintainer. Its Release check runs the version checks early; if it fails, fix the cause (usually the entry) on `develop` rather than merging. A release ships everything on `develop`: if the maintainer wants only part of it (a fix ahead of unreleased features, say), stop and ask, since nothing here supports a hotfix branch. If `develop` gains a change a project receives before the merge, update the entry first, date included, and the `pyproject.toml` version if the bump level changes.
3. After the merge, check the Release workflow run on `main`. The release is done once the tag and the GitHub Release both exist. A re-run uses the failed commit's `CHANGELOG.md`, workflow and script, so it fixes only a cause outside this repo (permissions, a GitHub outage): re-run for those. If the run failed before tagging for a cause inside this repo, fix it on `develop` and repeat from step 2; the same entry then tags the new merge commit. If the tag exists and the run failed after it for a cause inside this repo, stop and ask: a new merge commit can't take a version already tagged.

## Git Worktrees

Use the `using-git-worktrees` skill; it creates worktrees via the native `EnterWorktree` tool under `.claude/worktrees/` (gitignored). Don't hand-roll `git worktree add` when the native tool is available. Keep `.claude/` a real directory — the native tool refuses to run if `.claude` itself is a symlink.

After creating a worktree, install its pre-commit hook (see the autohooks activate command in Commands). A fresh worktree has no per-worktree hooks directory, so create it first:

```bash
mkdir -p "$(git rev-parse --git-dir)/hooks"
```
