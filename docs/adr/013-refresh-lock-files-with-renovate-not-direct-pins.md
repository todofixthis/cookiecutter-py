---
status: Accepted
date: 2026-10-22
scope: [pyproject.toml, renovate.json, template/pyproject.toml.jinja, template/renovate.json]
summary: Renovate's lock-file maintenance refreshes uv.lock weekly and automerges on green, in this repo and every generated project, with uv resolving only releases at least 3 days old; pin a transitive dependency only as a stopgap, with a comment naming when to remove it.
revisit-when: Lock-refresh PRs repeatedly fail CI or sit unmerged; a regression from a refresh can't be traced to the package that caused it; Renovate gains targeted updates for transitive dependencies in uv.lock.
---

# 013: Refresh Lock Files with Renovate, Not Direct Pins

## Context

[003-manage-updates-with-renovate.md][] set both `renovate.json` files to
`config:recommended` plus `helpers:pinGitHubActionDigests`. That opens PRs for
direct dependencies only; `config:recommended` leaves lock-file maintenance off.

[#16][] needed filelock 3.29, whose `SoftFileLock` (the lock filelock falls
back to where a filesystem refuses `fcntl` locking) breaks a stale lock after
any creation failure and evicts a malformed lock file, where 3.28 did neither.
filelock reaches generated projects only transitively, and every package that
pulls it in accepts older versions: tox 4.67.1 needs `>=3.25`, virtualenv
21.14.12 `>=3.24.2,<5`, python-discovery 1.6.4 `>=3.16.1`. A fresh lock
resolves the newest filelock, but `uv lock` keeps an existing locked version
while it still satisfies those ranges: with 3.25.0 locked, removing a pin and
re-locking left it at 3.25.0. So a project whose lock predates a fix keeps the
bug until some direct bump happens to re-resolve that package.

## Options

### Option 1: Do nothing

**Pros:** No extra PRs.
**Cons:** A transitive fix reaches a project only by accident.
**Risks:** Projects adopting the template bring old locks, which keep known bugs indefinitely.

### Option 2: Lock-file maintenance (Accepted)

`lockFileMaintenance` enabled, with `automerge`, in both `renovate.json` files.
Renovate's pep621 manager runs `uv lock --upgrade` before 4am UTC on Mondays,
and merges the PR itself once every check on it has passed.

**Pros:** Covers every transitive dependency, not just the ones someone noticed.
**Cons:** A refresh moves many versions at once, transitive majors included (filelock 3 to 4, say), with no PR of their own to announce them.
**Risks:** A refresh that fails CI for a reason unrelated to any fix, such as a new mypy release, blocks every later refresh until someone fixes it.

### Option 3: Constrain each fix

Raise the floor of each transitive package needing a fix, with
`[tool.uv] constraint-dependencies` (or a direct dependency, as #16 first did
with `filelock>=3.29,<5`).

**Pros:** The fix arrives in the PR that adds the constraint, with no wait. A constraint adds no dependency, and Renovate opens no PRs for it.
**Cons:** Each constraint stays long after every dependent's floor has passed the fix, unless someone remembers to remove it.
**Risks:** Only bugs someone has already hit get fixed.

## Decision

Option 2, keeping Option 3 as a stopgap only. Option 2 fixes the cause, a lock
that never moves, where Option 3 treats one symptom at a time and leaves
constraints behind. Where a fix can't wait for the next refresh, add a
constraint with a comment beside it naming the fixed version and saying to
remove it once the lock holds that version. A fix that recent is usually
younger than the cooldown below, so exempt the package with
`exclude-newer-package` too, and remove both together.

Automerge, since nobody meaningfully reviews a whole-lock diff and CI is the
real check; reviewing a PR a week in every library by hand would not last.

Renovate's `minimumReleaseAge` can't delay what a refresh picks up: the
package manager does the resolving, so Renovate has no release dates to
check, as its `security:minimumReleaseAgePypi` preset warns. The delay lives
in uv instead: `exclude-newer = "3 days"` makes every resolve, refreshes and
`uv add` alike, skip releases younger than that, so a broken or malicious
release is usually yanked before it lands. Both `renovate.json` files also
extend that preset, which holds back Renovate's direct-update PRs for the same
3 days; without it, a PR raising a range to a day-old release would fail to
lock under uv's cooldown.

## Consequences

- Each repository gets a weekly lock-refresh PR, which merges itself once its checks pass; a red one waits for its maintainer. Renovate merges it on a later run rather than through GitHub's auto-merge, which these repositories leave off.
- This repo's own `uv.lock` is refreshed and delayed the same way, for the harness's own transitive dependencies (copier's, say). It doesn't move the projects the harness bakes, which ship no lock and resolve afresh.
- Every lock-maintenance PR carries the preset's note that Renovate can't check release age during a refresh. That's expected: uv applies the delay itself.
- Adding a release under 3 days old means exempting that package with `exclude-newer-package`, which the generated AGENTS.md describes.
- 003 still decides Renovate over Dependabot; its quoted config gains these settings.

[#16]: https://github.com/todofixthis/cookiecutter-py/pull/16
[003-manage-updates-with-renovate.md]: 003-manage-updates-with-renovate.md
