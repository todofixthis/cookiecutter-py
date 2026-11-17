# Protecting release tags with a ruleset stops a published tag moving

> Recorded 2026-11-17, from the review of ADR 017. Not a GitHub issue.

## What

Add a tag ruleset on `refs/tags/*` with `deletion` and `non_fast_forward`, as
phx-claude-siat's `docs/release-automation.md` describes, so a published tag
can't be moved or deleted. This repository's only ruleset targets its
branches. Rulesets may be managed by todofixthis/terraform-github-repository
(ADR 009), so the change may belong there rather than in GitHub's settings.

`.github/workflows/release.yml` creates tags with `GITHUB_TOKEN`. Those two
rules don't block creation, but check that before relying on it. A rule that
does block the token reopens ADR 017.

Make the same change require the Release workflow's `check` job on
`refs/heads/main`, so a release PR with a bad version can't merge. Only
release PRs target `main`, so that costs other PRs nothing, but the module's
ruleset requires only `gate`.

## Why it is still worth doing

Generated projects record the tag they took in `.copier-answers.yml`. The
workflow stops a bad tag from being created, but nothing stops a tag being
moved afterwards, and the 1.3.0 incident shows tags do get moved. The cost is
that a wrong tag can no longer be corrected in place: the fix becomes a new
release.

## Acceptance

- Deleting or force-moving a bare-semver tag is refused.
- The next release's workflow run still tags and publishes.
- A PR into `main` can't merge while its Release `check` job fails.
