---
status: Accepted
date: 2026-11-17
scope: [.github/workflows/, AGENTS.md, renovate.json, template/.github/workflows/build.yml.jinja, template/AGENTS.md, template/renovate.json]
summary: CI runs an `adrs` job pinned to a phx-claude-siat release commit with a trailing `# X.Y.Z`, bumped with AGENTS.md (whose skill link stays in tag form) and the template's copies by one Renovate `github-tags` regex manager, not hand-kept or tracking `main`; a `gate` job aggregating every CI job is the required check on `develop` and `main`, and the only one in generated projects; this repository's `main` also requires the Release workflow's `release-check`, through a ruleset targeting `main` alone, never folded into `gate` or required on `develop`.
revisit-when: The phx plugin drops its `phx-adr` entry point; todofixthis/terraform-github-repository stops requiring a check named `gate`; a branch of this repository other than `main` needs a required check besides `gate`; phx-claude-siat's `main` starts taking commits that aren't releases.
---

# 018: Require Gate Everywhere and the Release Check on main

## Context

[ADR 009][] decided two things. CI runs an `adrs` job pinned to a
phx-claude-siat release, which a Renovate regex manager bumps together with
AGENTS.md. A single `gate` job, aggregating every other job, is the only
required check, which [todofixthis/terraform-github-repository][terraform
module] requires on `develop` and `main`.

[ADR 017][] added a Release workflow whose `release-check` job runs on PRs into
`main`. It checks the top CHANGELOG.md entry against the repository's tags, so
a release PR with a version that is already tagged, or not newer than every
tag, shows red before it merges. ADR 017 left the job advisory and outside
`gate`. `gate` runs on every push, and between releases `develop`'s top entry
legitimately tags an older commit, so folding the check in would turn
`develop` red.

An advisory check can be merged past. A bad release merge then stays in
`main`'s history, and fixing it takes another release through `develop`. On
2026-11-17 the maintainer split this repository's ruleset, adding one that
targets `main` alone and requires `release-check` alongside `gate`. That
contradicts ADR 009's claim that `gate` is the only required check, so this
ADR restates ADR 009 with that claim narrowed.

## Options

### Option 1: Do nothing

Keep `release-check` advisory and drop the `main`-only ruleset.

**Pros:** One required check everywhere, as ADR 009 states.
**Cons:** A release PR with a bad version can still merge.
**Risks:** The failure ADR 017 exists to catch reaches `main` whenever someone
merges past a red check.

### Option 2: Require `release-check` on `main` alone, beside `gate` (Accepted)

A ruleset targeting `main` requires `gate` and `release-check`. `develop`
requires `gate` only. Everything else in ADR 009 stands.

**Pros:** Only release PRs target `main`, so no other PR meets the extra
check.
**Cons:** Two required checks on `main`, set in two rulesets.
**Risks:** A ruleset change that merges the two back together drops the check
from `main`, or adds it to `develop`, where it never runs and so blocks every
PR.

### Option 3: Fold the release check into `gate`

**Pros:** `gate` stays the only required check.
**Cons:** `gate` would fail on `develop` between releases, when the top entry
legitimately tags an older commit. Skipping the check off `main` would need
branch logic in `ci.yml`, which runs on push, not on the PR's base.

### Option 4: Require `release-check` on `develop` and `main`

**Pros:** One shared ruleset.
**Cons:** `release-check` runs only on PRs into `main`, so on `develop` it never
reports, and every PR into `develop` waits on it forever.

## Decision

Option 2. It makes the release check blocking where it means something and
nowhere else. Option 3 breaks `develop` between releases, and Option 4 blocks
it outright.

ADR 009's decision otherwise carries over unchanged.

**The `adrs` job and its pin.** The phx plugin's hooks check ADRs in Claude
Code sessions but never block, so CI's `adrs` job running `phx-adr check` is
the only check a commit made elsewhere meets. It pins a phx-claude-siat
release's 40-character commit with the version as a trailing `# X.Y.Z` on the
same line, a sanctioned exception to the comment-placement rule because
Renovate's regex reads the version there. One `github-tags` regex manager
bumps, in one PR, every pin in CI, in AGENTS.md and in the template's
AGENTS.md and workflows, plus AGENTS.md's skill link, which must stay in tag
form (`blob/X.Y.Z/`) for the manager to match it. A hand-kept pin was
rejected because nothing says a release exists, so CI drifts behind sessions.
Tracking the tip of phx-claude-siat's `main` with `git-refs` was rejected
because the pin then names no version and moves on every commit, not every
release. Renovate's `git-tags` datasource would serve as well as
`github-tags`; `github-tags` won only because two libraries already used it.

**The `gate` job.** `gate` `needs` every job in `ci.yml` (or a generated
project's `build.yml`), runs with `if: always()`, and fails if any of them
reports `failure`, `cancelled` or `skipped`. Without `if: always()`, a failed
dependency skips `gate`, and GitHub counts a skipped required check as
passing. Generated projects require `gate` alone: they have no Release
workflow. Listing every job as a required check in the shared module stays
rejected: it needs a per-repository list in shared Terraform, and matrix job
names such as `test (3.12)` change with every Python rotation.

`release-check` is a required check that runs only on PRs into `main`. It is
skipped on pushes, which no ruleset reads, so `gate`'s rule against skips
doesn't apply to it.

## Consequences

- Every job added to `ci.yml` or `build.yml` must be added to `gate`'s
  `needs`, or it stops blocking merges. A job skipped on purpose still goes
  in, with its `needs.<job>.result` tested individually.
- The Release workflow's PR job keeps the name `release-check`. Renamed, it
  leaves the ruleset requiring a check that never reports, so no release PR
  can merge.
- Any job added to the Release workflow's PR path is advisory unless it is
  added to the `main` ruleset too.
- The `main`-only ruleset was created by hand in GitHub's settings, outside
  todofixthis/terraform-github-repository, so a repository rebuilt from the
  module lacks it. Moving it into the module must keep it targeting `main`
  alone.
- AGENTS.md documents the trailing-comment exception beside the pinned
  commands, so an agent tidying comments doesn't move it.
- Renovate's phx-adr PR is where a new release's stricter checks surface; fix
  what it reports in that PR.
- Sessions can run a newer `phx-adr` than CI until that PR merges, which is
  tolerable while phx-claude-siat's `main` takes only releases.
- Citations of ADR 009 elsewhere, including generated projects'
  AGENTS.md and `renovate.json`, still resolve through its supersession to
  this ADR.

[ADR 009]: 009-gate-adr-ci-and-the-phx-pin.md
[ADR 017]: 017-tag-releases-from-the-changelog-in-ci.md
[terraform module]: https://github.com/todofixthis/terraform-github-repository
