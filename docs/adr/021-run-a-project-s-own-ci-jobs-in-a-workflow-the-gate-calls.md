---
status: Accepted
date: 2026-11-23
scope: [AGENTS.md, copier.yml, scripts/template_owned.py, template/.github/workflows/]
summary: A generated project's own CI jobs go in .github/workflows/project.yml, a reusable workflow (on workflow_call) that copier writes once as a stub and the project then owns (_skip_if_exists), which the template-owned build.yml calls as its `project` job, passing its secrets through, and `gate` needs; not a separate workflow outside `gate`, a project-owned build.yml, or a second required check.
revisit-when: A project's own job needs more permissions than build.yml grants its caller; copier stops honouring `_skip_if_exists` on update; GitHub lets a ruleset require every check in a workflow, or `needs` reach across workflow files; todofixthis/terraform-github-repository gains a per-repository list of required checks.
---

# 021: Run a Project's Own CI Jobs in a Workflow the Gate Calls

## Context

[ADR 018][] makes `gate`, in the template-owned `build.yml`, the only
required check in a generated project: todofixthis/terraform-github-repository
requires `gate` alone, and `gate` fails unless every job in its `needs`
succeeded. The template-owned rule told a project to put an extra CI job in
a workflow file of its own, so template updates wouldn't conflict with it.
But `needs` can't reach a job in another workflow file, so such a job runs
and never blocks a merge, and nothing said so.

todofixthis/paddock, adopting the template next, has such a job: it builds
and smoke-tests each bundled Dockerfile, and its own `gate` requires it
today. Moved where the rule said, it would stop blocking merges.

## Options

### Option 1: Do nothing

Project jobs live in their own workflow files, outside `gate`.

**Cons:** A project job can never block a merge, so a project like paddock
loses a check it has today by adopting the template.

### Option 2: A project-owned reusable workflow that `build.yml` calls (Accepted)

The template ships `.github/workflows/project.yml`, triggered only by
`workflow_call`, with a placeholder job. copier writes it on first copy and
never again (`_skip_if_exists`, as [ADR 010][] does for `project.md`).
`build.yml` calls it as a `project` job with `secrets: inherit`, and `gate`
needs that job.

**Cons:** Every project runs a placeholder job until it adds its own. The
call job grants `build.yml`'s permissions (`contents: read`); a called
workflow asking for more fails `build.yml`'s run before any job starts.
`gate` sees only the called workflow's overall result, which a skipped
inner job doesn't fail, so ADR 018's guard against a silently skipped job
doesn't reach inside it. A template fix to the stub, like one to
`project.md`, reaches new projects only.

### Option 3: A project-owned `build.yml`

Take `build.yml` out of the template-owned set, so a project adds jobs to
it directly.

**Cons:** Template changes to CI, such as pin bumps and new checks, stop
reaching the project.

### Option 4: A second required check

Require the project's own workflow beside `gate`.

**Cons:** Needs the per-repository list of required checks in the shared
Terraform module that ADR 018 rejected for generated projects.

## Decision

Option 2. It is the only option that keeps both `build.yml`'s template
updates and `gate` as the single required check, at the cost of one short
placeholder job. Making the workflow reusable rather than a job list
merged into `build.yml` means a project can also call it from a workflow
of its own, such as a weekly schedule.

## Consequences

- The template-owned rule sends a project's extra CI job to
  `project.yml`, and its test counts `project.yml` among the
  first-copy-only files, with `project.md`.
- ADR 018's rule that every job in `build.yml` goes in `gate`'s `needs`
  covers the `project` call job. A job inside `project.yml` that may have
  nothing to do skips its steps, not itself, since a skipped inner job
  passes `gate` unseen; the stub's comments say so, and that the file and
  at least one job must stay.
- The stub repeats `build.yml`'s `UV_NO_DEFAULT_GROUPS`, since a caller's
  workflow-level `env` doesn't reach a called workflow.
- A project job that needs a trigger `build.yml` lacks, such as a weekly
  schedule, runs from a workflow of the project's own that calls
  `project.yml`. One that needs more permissions than `contents: read` is a
  template candidate.
- Existing projects get the stub on their next template update, since
  `_skip_if_exists` skips only a file that already exists.

[ADR 010]: 010-split-agents-md-into-templated-and-project-parts.md
[ADR 018]: 018-require-gate-everywhere-and-the-release-check-on-main.md
