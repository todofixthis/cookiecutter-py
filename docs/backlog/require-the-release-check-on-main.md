# Requiring the release check on main stops a bad version merging

> Recorded 2026-11-17, from the review of ADR 017. Not a GitHub issue.

## What

Require the Release workflow's `release-check` job
(`.github/workflows/release.yml`) on `refs/heads/main`, alongside `gate`, not
in place of it. Do it in a ruleset that targets `main` alone: the ruleset
requiring `gate` also covers `develop`, where `release-check` never runs, so
adding it there blocks every PR into `develop`. That ruleset may be managed by
todofixthis/terraform-github-repository (ADR 009), so the change may belong
there as per-branch checks rather than in GitHub's settings.

A second required check contradicts ADR 009, whose summary makes `gate` the
only one, so record it in a new ADR that supersedes 009's claim for `main`
(the partial-supersession workflow in `phx:writing-adrs`). Then update
everything that calls `release-check` advisory or `gate` the only required
check:
- ADR 017's summary, Option 2 Risks and Decision
- `.github/workflows/ci.yml`'s comment above `gate`
- `README.md`

## Why it is still worth doing

`release-check` is advisory, so a release PR whose top CHANGELOG.md entry is
already tagged, or older than the newest tag, can still merge. The bad merge
commit then stays in `main`'s history, and fixing it takes another release
through `develop`. Only release PRs target `main`, so requiring the check
costs other PRs nothing.

## Acceptance

- A PR into `main` can't merge while its `release-check` job fails.
- `gate` is still required on `main` and `develop`.
- PRs into `develop` still merge without `release-check`.
