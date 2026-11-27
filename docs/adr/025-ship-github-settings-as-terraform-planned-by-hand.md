---
status: Accepted
date: 2026-11-27
scope: [.github/workflows/, copier.yml, renovate.json, template/.github/workflows/, template/.gitignore, template/AGENTS.md, template/infra/, template/renovate.json]
summary: Generated projects carry infra/github/, a template-owned main.tf calling the todofixthis Terraform module and a project-owned terraform.tfvars written on first copy only, with state on the maintainer's machine and plans run by hand before an infra PR merges; not the module repo's plan-comment CI gate, and not remote state with CI-run plans.
revisit-when: A change to main.tf or terraform.tfvars, a Renovate module or provider bump included, merges in a generated project without a plan having been run; a project's state is lost, or a second maintainer or machine needs to plan; the todofixthis account becomes a GitHub organisation; a private project needs the module; copier stops honouring `_skip_if_exists` on update.
---

# 025: Ship GitHub Settings as Terraform, Planned by Hand

## Context

[todofixthis/terraform-github-repository][module] holds the todofixthis
standard for a repo's GitHub settings: merge methods, features, security
settings, and the rulesets requiring `gate` ([ADR 018][]). Its ADR 001 has
every todofixthis repo provisioned through it, and since its v1.1.0 it can
adopt a repo that already exists. todofixthis/filters-iso adopted it by
hand as a pilot (its ADR 005), with a root module under `infra/github/`,
state on the maintainer's machine, and plans run by hand. The pilot's plan
found Dependabot alerts and secret-scanning push protection off, which
nobody had noticed. All six projects generated from this template are to
adopt the module, so the other five would each need the same hand copy.

The module's own repo gates infra PRs on a plan comment the maintainer posts
from their machine, matched by CI (the module's ADR 003). That needs a
`pull_request` run reading the PR's comments. A generated project's CI runs
on `push` alone, and its `gate` can't `need` a job in another workflow file
([ADR 021][]). Moving state off the maintainer's machine so CI could plan
needs a credential able to read each repo's admin settings, and todofixthis
is a personal account, which has no organisation secrets.

Five of the six projects' live descriptions differ from their
`project_short_description` answer, and filters has eleven topics, which
the module would remove unless told otherwise.

## Options

Options 2 to 4 share a cost that doesn't rank them: an existing project
adopts through hand-written `import` blocks on its template-update PR, as
the module's README describes, and its first plan is reviewed by hand.

### Option 1: Do nothing

Projects copy filters-iso's root module by hand, or stay unmanaged.

**Cons:** Five hand copies to keep in step with each module release, none
of them reaching a new project.
**Risks:** Settings drift in the projects nobody adopts, as they had in
filters-iso.

### Option 2: Ship the root module, planned by hand (Accepted)

The template ships `infra/github/main.tf`, template-owned, holding the
provider and the module call pinned to a release tag, with the repo's name
and owner taken from the copier answers. The values a project owns
(description, homepage, topics) come from `infra/github/terraform.tfvars`,
which copier writes on first copy only, seeded from the answers, as
`project.md` and `project.yml` are ([ADR 010][], ADR 021). State stays on
the maintainer's machine, gitignored. The maintainer plans before an infra
PR merges and applies after, from an up-to-date `develop`, and the
generated AGENTS.md tells agents never to apply.

**Cons:** Nothing in CI checks that a plan ran before an infra PR merged.
Renovate's weekly lock-file maintenance, which automerges, refreshes the
provider lock with no plan; that changes nothing on GitHub, but can move the
provider to a new minor release, which the next plan then shows.
**Risks:** One machine holds every project's state. Losing a state file
makes that project's next apply fail, since the repo already exists, until
the `import` blocks are written again.

### Option 3: Ship the module repo's plan-comment gate too

The template also ships the module's plan script, its pre-push hook, its
path patterns and an `infra-plan` job, so an infra PR stays red until the
maintainer posts a plan from their machine.

**Pros:** An infra PR can't merge unplanned.
**Cons:** Generated CI needs a `pull_request` trigger beside `push`, or a
workflow `gate` can't reach. The local plan per project that Option 2 asks
for becomes a step CI enforces, so each Renovate PR stays red until it's
posted.

### Option 4: Remote state, planned in CI

A remote backend, such as HCP Terraform's free tier, holds each project's
state, and CI plans every infra PR.

**Pros:** No local runs, and no state on one machine.
**Cons:** Each repo needs its own copy of a credential that can read every
repo's admin settings, there being no organisation secrets to share. The
backend is one more account to keep.
**Risks:** A leaked copy of that credential exposes every repo's settings,
and it reaches every project's CI.

## Decision

Option 2. It's what the filters-iso pilot ran, and the gap it leaves is one
the maintainer closes by habit: with one maintainer, the person merging an
infra PR is the person who applies it, and every apply shows its plan before
it acts. Option 3 would redesign every project's CI to guard that habit, and
Option 4 would spread an admin-capable credential across every repo to
replace it. Both answer problems a second maintainer or an organisation
account would bring, which the revisit conditions name.

Splitting the template-owned `main.tf` from a project-owned
`terraform.tfvars` keeps the five live descriptions and filters' topics
through template updates, which would otherwise reset them to the answers.
The template ships no `.terraform.lock.hcl`: `terraform init` writes it on a
project's first plan, and the project commits it.

## Consequences

- An existing project adopts on the template-update PR that first brings
  `infra/github/`, which shouldn't merge without it, or the project carries
  infra with no state behind it. On that PR, set `terraform.tfvars` to the
  repo's live description, topics and homepage (the seeded docs URL may not
  exist yet), and put the `import` blocks the module's README gives in a
  file of the project's own, such as `infra/github/imports.tf`, since
  `main.tf` is template-owned. Plan before merging, apply from `develop`
  after, and remove `imports.tf` in a follow-up. filters-iso's update
  conflicts on its hand-written `main.tf`, which gives way to the
  template's as its ADR 005 expects; its description moves into the seeded
  `terraform.tfvars`, which needs its live value.
- Renovate bumps the module tag both here and in each project, like the
  template's other pins; a bump arriving both ways can conflict, as the
  backlog's pin-conflict item records. Neither automerges, and each needs a
  plan before merging, as does a Renovate provider update that changes only
  the lock. Renovate's weekly lock-file maintenance needs none, as Option 2
  sets out, and the generated AGENTS.md says so. The template's
  `renovate.json` disables provider majors, which the module's ADR 001
  requires of every dependent, since the module owns that constraint.
- This repository's CI bakes a project and validates its `infra/github/`
  with Terraform, fetching the module the template pins.
- A private project can't adopt: a personal account on GitHub Free can't
  read or create rulesets on a private repo. `main.tf` passes no
  `visibility`, so adopting one anyway would also plan it public.
- The module's design of a byte-identical plan script in each template no
  longer holds; the module repo records that in an ADR of its own.

[ADR 010]: 010-split-agents-md-into-templated-and-project-parts.md
[ADR 018]: 018-require-gate-everywhere-and-the-release-check-on-main.md
[ADR 021]: 021-run-a-project-s-own-ci-jobs-in-a-workflow-the-gate-calls.md
[module]: https://github.com/todofixthis/terraform-github-repository
