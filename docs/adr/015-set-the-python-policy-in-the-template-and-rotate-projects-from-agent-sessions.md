---
status: Accepted
date: 2026-10-31
scope: [copier.yml, renovate.json, .agents/skills/rotate-python-versions/, template/.agents/skills/rotate-python-versions/, template/.github/workflows/build.yml.jinja, template/renovate.json]
summary: The template's computed python_policy sets the Python range every project should support, while each project's recorded python_version stays where an agent session running its rotate-python-versions skill puts it, never moved by Renovate, whose Python updates are disabled; a python-policy CI job fails while a project lags the policy, and gate tolerates that one failure so the nudge never blocks a merge.
revisit-when: A project needs to lag the policy on purpose for longer than a release cycle; Renovate gains a way to run an agent session on its update PRs; the python-policy job's red stops reaching the maintainer as a notification.
---

# 015: Set the Python Policy in the Template and Rotate Projects from Agent Sessions

## Context

[ADR 008][] keeps ADR 001's three-release policy but makes `python_version` a recorded
answer, so `copier update` never moves a project's Python floor. Its default was static,
bumped by this repository's [`rotate-python-versions`][repo skill] skill, and reached new
projects only. An existing project had no way to learn that the template had moved on: its
maintainer had to notice a Python release and rotate each library by hand.

The maintainer wants every rotation to start from an agent session in the project, never
from a Renovate PR. Dropping a version means removing compat code (version checks, fallback
imports, backports), which no update tool does. Renovate would open such PRs today: its
github-actions manager reads `actions/setup-python`'s `python-version` as a dependency named
`python` ([known actions][]), and the generated workflow's `type-check`, `lint` and `docs`
jobs pin the newest version as a literal.

A nudge has to reach the maintainer. A warning annotation notifies nobody, and the email
GitHub sends for a scheduled run's failure goes to whoever last edited the cron line.

## Options

### Option 1: Do nothing

**Pros:** No new moving parts.
**Cons:** A project lags until someone notices; Renovate's `python-version` PRs move CI
without `requires-python` or compat code.
**Risks:** Libraries drift to different ranges, with nothing that records which are behind.

### Option 2: The template sets a policy, and agent sessions apply it (Accepted)

`copier.yml` gains `python_policy`, a `when: false` question, so every template release
re-renders it in every project and no answer records it. `python_version` stays recorded
and defaults to it. A `python-policy` CI job compares the two rendered values and fails
while the project is behind. `gate` needs it like every other job, but tolerates its
failure alone. A Renovate rule disables updates to the `python` dependency, in generated
projects and in this repository.

**Cons:** The job stays red on every PR from the update that raises the policy until the
rotation lands, so a red check stops meaning "something broke" for that one job.
**Risks:** An unrelated failure in the job (a broken runner) is tolerated too, since `gate`
can't tell a lagging project from a crashed step.

### Option 3: Let Renovate rotate via a computed `python_version`

Make `python_version` computed, so each template release moves every project's range in
its update PR.

**Pros:** No lag and no separate step.
**Cons:** Compat code stays behind, and a project can't hold its range while a dependency
lacks wheels for a new version.

### Option 4: A recorded lag answer

Record how many releases a project lags the policy, defaulting to zero, and derive its range
from the policy minus the lag.

**Cons:** A default of zero rotates every project on update, as Option 3 does; a high
default leaves new projects behind. No default suits both.

### Option 5: A nudge that blocks merges

As Option 2, but `gate` fails while the project lags.

**Cons:** The template-update PR raising the policy can't merge without the rotation, and
nor can any other PR, including a security fix, until a session rotates the project.

## Decision

Option 2. It is the only option that leaves the rotation, and so the compat-code removal,
to an agent session, while still telling each project when it is due. Option 3 moves the
range without the code, Option 4 has no workable default, and Option 5 makes Python
rotation a blocker for unrelated work.

The nudge is a failing check, not an annotation, because a red check is what reaches the
maintainer: it shows on the template-update PR they review anyway and on every PR after,
and it notifies whoever pushed the run. `gate` tolerates the failure in its own step rather
than leaving the job out of `needs`, so [ADR 009][]'s rule that every job feeds `gate`
holds, and an edit that tidies `needs` changes nothing.

Renovate's Python updates are disabled by dependency name rather than by file, so a new
workflow, or another manager that reports `python`, is covered without a further rule.

## Consequences

- A template release that raises `python_policy` reaches every project as its usual update
  PR. That PR keeps `python_version` and turns `python-policy` red; the project's
  `rotate-python-versions` skill then re-answers with `copier update --data`, runs
  `uv lock` and removes compat code.
- This repository's rotation changes `python_policy`'s default, not `python_version`'s,
  which defaults to it.
- `gate` reads every job's result from `toJSON(needs)` with `jq`, failing on any
  non-success except a `python-policy` failure; a `skipped` or `cancelled` `python-policy`
  still fails it. A test runs the step against simulated results.
- ADR 008's rule that drift shows as a Renovate PR, never as a CI job, still holds for
  template files. The `python-policy` job reports a project lagging the template's policy,
  and blocks nothing.
- A project that must lag on purpose, say for a dependency without wheels, stays red until
  it can rotate.

[ADR 008]: 008-propagate-template-changes-with-copier-and-renovate.md
[ADR 009]: 009-gate-adr-ci-and-the-phx-pin.md
[known actions]: https://github.com/renovatebot/renovate/blob/main/lib/modules/manager/github-actions/known-actions/github-releases.ts
[repo skill]: ../../.agents/skills/rotate-python-versions/SKILL.md
