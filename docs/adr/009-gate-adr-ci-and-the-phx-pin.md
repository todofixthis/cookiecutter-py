---
status: Accepted
date: 2026-10-12
scope:
  - .github/workflows/
  - AGENTS.md
  - renovate.json
  - template/.github/workflows/build.yml.jinja
  - template/AGENTS.md
  - template/renovate.json
summary: CI runs an `adrs` job pinned to a phx-claude-siat release commit with a trailing `# X.Y.Z`, bumped with AGENTS.md by a Renovate `github-tags` regex manager, not hand-kept or tracking `main`; a single `gate` job aggregating every other job is the only required check.
revisit-when: The phx plugin drops its `phx-adr` entry point; todofixthis/terraform-github-repository stops requiring a check named `gate`.
---

# 009: Gate, ADR CI and the phx Pin

## Context

[`todofixthis/terraform-github-repository`][terraform module]'s rulesets (from
its v1.0.0) require one status check, `gate`, on `develop` and `main`. No
library has a job by that name, so applying the module would block every PR.

The phx plugin's hooks check ADRs inside Claude Code sessions but never block,
so a CI job running `phx-adr check` is the only check a commit made elsewhere
meets. The template has no such job, and its own ADR corpus fails
`phx-adr check` unnoticed. The libraries that do have one keep its pin current
four ways:

| Mechanism | Repos |
|---|---|
| Hand-kept | filters, class-registry |
| Renovate `git-tags`, keyed on a `# phx-claude-siat X.Y.Z` comment | filters-django |
| Renovate `git-refs` on the tip of `main` | filters-iso |
| Renovate `github-tags`, trailing `# X.Y.Z`, also bumping AGENTS.md | filters-pydantic, paddock |

The pin also appears in AGENTS.md, whose `phx-adr` commands are what an agent
outside Claude Code runs; a pin bumped in CI but not there reports a different
index than CI does.

The phx plugin itself installs from phx-claude-siat's `main` branch (its
marketplace entry sets `ref: main`), so sessions run the newest release while
CI runs the pinned one.

## Options

### Option 1: Do nothing

No `adrs` job in the template; each library keeps its own mechanism.

**Pros:** No change.
**Cons:** A faulty ADR from outside Claude Code lands unchecked. Four
mechanisms for one need, plus a fifth state, no mechanism at all, in the
template itself.
**Risks:** The pin drifts per repository, so the same corpus passes in one and
fails in another.

### Option 2: Pin a release's commit, with a `github-tags` regex manager (Accepted)

The `adrs` job runs `phx-adr check` from phx-claude-siat at a release's
40-character commit SHA, with the version as a trailing `# X.Y.Z` on the same
line. In a generated project, a Renovate regex manager with the `github-tags`
datasource matches every pin in `.github/workflows/build.yml` and AGENTS.md,
and AGENTS.md's skill link in tag form (`blob/X.Y.Z/`), and bumps them all in
one PR. This is filters-pydantic's form.

**Cons:** The trailing comment breaks the rule that comments go on the line
before the code. A pin that loses its comment, or has it moved, silently stops
being bumped.
**Risks:** Between a plugin release and the Renovate PR merging, sessions and
CI run different releases, and an index a session regenerates can fail CI as
stale.

### Option 3: Pin a commit and bump it by hand

**Pros:** No Renovate config.
**Cons:** Nothing says a release exists; filters and class-registry pins move
only when someone notices.
**Risks:** CI validates against an ever older tool than sessions run.

### Option 4: Track the tip of `main` with `git-refs`

**Pros:** CI matches what sessions install, since the plugin also follows
`main`.
**Cons:** No version to read in the pin, and a PR for every commit to `main`,
not every release.
**Risks:** Only as safe as `main` being releases-only, which is a convention
in phx-claude-siat rather than something this repository can check.

## Decision

Option 2. It's the only form that keeps CI on a named release, reviewed when
it moves, and moves AGENTS.md's commands with it. Renovate's `git-tags`
datasource would serve as well: its current source dereferences annotated tags
to commit SHAs, as `github-tags` does. `github-tags` wins only because two
libraries already use it, so adopting it moves the fewest repositories.

The trailing `# X.Y.Z` is a sanctioned exception to the comment-placement rule,
because Renovate's regex needs the version on the pin's own line.

The `gate` job is the second half of the decision. It `needs` every other job,
runs with `if: always()`, and fails if any of them reports `failure`,
`cancelled` or `skipped`. Without `if: always()`, a failed dependency skips the
gate, and GitHub counts a skipped required check as passing. `skipped` is
included because no job in the generated workflow is skipped by design, so a
skip means a dependency failed. The rejected alternative, listing every job as a required
check in the module, needs a per-repository list in shared Terraform, and
matrix job names such as `test (3.12)` change with every Python rotation.

A generated project's CI job names are `test`, `type-check`, `lint`, `docs`,
`adrs` and `gate`. The template repository's own CI is one workflow, `ci.yml`,
with jobs `test`, `type-check`, `generate`, `adrs` and `gate`, and its Renovate
manager also covers `template/AGENTS.md` and
`template/.github/workflows/*.jinja`.

## Consequences

- Every job added to a workflow must be added to `gate`'s `needs`, or it stops
  blocking merges.
- A job that is skipped on purpose (a path filter, say) still goes in
  `gate`'s `needs`. The fail step then tests each job's
  `needs.<job>.result` individually, tolerating `skipped` for that job alone,
  rather than `contains(needs.*.result, 'skipped')`.
- AGENTS.md documents the trailing-comment exception beside the pinned
  commands, so an agent tidying comments doesn't move it.
- Renovate's phx-adr PR is where a new release's stricter checks surface; fix
  what it reports in that PR.
- Sessions can run a newer `phx-adr` than CI until that PR merges, which is
  tolerable while phx-claude-siat's `main` takes only releases.

[terraform module]: https://github.com/todofixthis/terraform-github-repository
