# The autohooks worktree hook copy can go once autohooks finds its hook in linked worktrees

> Recorded 2026-11-28, from a session investigating autohooks crashing in todofixthis/paddock's worktrees. Not a GitHub issue. A report for greenbone/autohooks was drafted but not filed; link it here once it is.

## What

`AGENTS.md` and `template/AGENTS.md`, under "Git Worktrees", have a second Bash block that copies the main checkout's pre-commit hook into the worktree's own git dir, `.git/worktrees/<name>/hooks`. That block, and the paragraph introducing it, work around a bug in every autohooks release up to at least 26.9.0: `get_git_hook_directory_path()` in `autohooks/utils.py` builds the hooks dir from `git rev-parse --git-dir`, which in a linked worktree is the worktree's own git dir, not the common git dir that git runs hooks from. `autohooks activate` and the pre-commit run then crash with `FileNotFoundError`.

A fix building the path from `git rev-parse --git-common-dir` is on the `claude/sleepy-euler-ti8s7u` branch of todofixthis/autohooks, a fork of greenbone/autohooks. Upstream may fix it differently, so judge a release by its behaviour: it has the fix if `autohooks activate` run in a linked worktree, after the main checkout is activated, reports the hook as already installed instead of crashing.

Once a release has the fix:

- Raise every `autohooks` lower bound to that release: the `dev` and `ci` groups in `pyproject.toml`, and `template/pyproject.toml.jinja`. Then run `uv lock`. Renovate won't raise a bound that a 26.x release still satisfies. If the fix ships in a new major, Renovate's major-bump PR moves the bounds itself, so only the next step is left.
- Delete the second block and the paragraph before it from both `AGENTS.md` files. Keep the first block, which installs the hook in the main checkout, and the paragraph after it.

## Acceptance

- Every `autohooks` lower bound names a release with the fix.
- Neither `AGENTS.md` mentions `.git/worktrees/<name>/hooks`.
- In a baked project made a git repo (`git init`, an initial commit, `uv sync`), with a worktree added by `git worktree add` and only the first block run, `uv run git commit` in the worktree succeeds and prints autohooks' plugin output.
