# The autohooks worktree hook copy can go once autohooks finds its hook in linked worktrees

> Recorded 2026-11-28, from a session investigating autohooks crashing in todofixthis/paddock's worktrees. Not a GitHub issue. The upstream report, for greenbone/autohooks, was drafted but not yet filed.

## What

`AGENTS.md` and `template/AGENTS.md`, under "Git Worktrees", have a second Bash block that copies the main checkout's pre-commit hook into the worktree's own git dir, `.git/worktrees/<name>/hooks`. That block, and the paragraph introducing it, work around a bug in autohooks 26: `get_git_hook_directory_path()` builds the hooks dir from `git rev-parse --git-dir`, which in a linked worktree is the worktree's own git dir, not the common git dir that git runs hooks from. `autohooks activate` and the pre-commit run then crash with `FileNotFoundError`.

A fix building the path from `git rev-parse --git-common-dir` is on the `claude/sleepy-euler-ti8s7u` branch of todofixthis/autohooks, a fork of greenbone/autohooks, ready to open upstream.

Once a greenbone/autohooks release has the fix:

- Raise the `autohooks` lower bound to that release in `pyproject.toml` and `template/pyproject.toml.jinja`. Renovate won't, because the release still satisfies `>=26,<27`.
- Delete the second block and the paragraph before it from both `AGENTS.md` files. Keep the first block, which installs the hook in the main checkout, and the paragraph after it.

## Acceptance

- Both `autohooks` lower bounds name a release with the fix.
- Neither `AGENTS.md` mentions `.git/worktrees/<name>/hooks`.
- In a baked project, a commit in a linked worktree runs the pre-commit hook after only the first block has run.
