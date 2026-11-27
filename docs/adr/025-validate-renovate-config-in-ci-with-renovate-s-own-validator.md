---
status: Accepted
date: 2026-11-27
scope: [.github/workflows/ci.yml, renovate.json, template/.github/workflows/build.yml.jinja, template/renovate.json]
summary: Run renovate-config-validator --strict at a Renovate-tracked pin, via npx, in this repo's CI (root and baked configs) and in generated projects' CI; not a JSON-schema check, nor checking the Dependency Dashboard after merge.
revisit-when: Renovate publishes its validator outside the npm package, or the pinned validator and the hosted Renovate app disagree on a config.
---

# 025: Validate Renovate config in CI with Renovate's own validator

## Context

This repo ships two Renovate configs: its own `renovate.json`, and `template/renovate.json`,
which every generated project receives. Nothing checks either before merge. A fault, such as
an unknown option, a regex that doesn't compile or a manager pattern that matches nothing,
surfaces only after merge, on the Dependency Dashboard, if anyone looks. A fault in the
template's config reaches every project at the next release. [#76][] changed both configs and
couldn't validate them: its session had no `npx`. Generated projects can edit their own
`renovate.json`, and nothing checks those edits either.

Renovate's validator ships only inside the `renovate` npm package, which needs Node
`^24.11.0 || ^26.13.0`. This is a Python template, so Node is not otherwise on its CI path.

## Options

### Option 1: Do nothing

**Pros:** No CI time, and no Node on a Python project's CI path.
**Cons:** A faulty config merges, and a template fault ships to every project.
**Risks:** Renovate stops bumping a pin and nobody notices, because nothing fails.

### Option 2: Run `renovate-config-validator --strict` in CI (Accepted)

Run it with `npx --package renovate@<version>`, where the version is a `RENOVATE_VERSION` env
pin with a `# renovate:` comment that a regex manager tracks. Run it in this repo's `ci.yml`
against the root config and a baked project's config, and in the template's `build.yml`
against the project's own config.

**Pros:** It runs the same checks Renovate itself does. It compiles every regex and
`managerFilePatterns` entry, and `--strict` also fails a config that only needs migration.
**Cons:** Each run installs Node and the `renovate` package.
**Risks:** The pin trails the hosted Renovate app, which runs the newest release, so a config
valid for the app could fail an older validator, or the reverse.

### Option 3: Check the config against Renovate's JSON schema

Use a Python tool such as `check-jsonschema`.

**Pros:** No Node.
**Cons:** The schema checks shape, not meaning. It types `matchStrings` as an array of
strings, so a regex that doesn't compile passes, and it can't tell when a config needs
migration.
**Risks:** A green check that misses the faults most likely to stop a pin being bumped.

## Decision

Option 2. Only Renovate's own validator catches the faults that silently stop updates, and
`--strict` turns a deprecation into a failure while it is still cheap to fix. The validator
checks the config files in its working directory: given a file argument, it validates that
file as global config, not repo config. So the job runs it with no arguments, once from the
repo root and once from the baked project.

Renovate releases several times a day, so every config that tracks the pin also schedules it
monthly and automerges it once `gate` passes. The validator is a CI tool, so a bump that
breaks the job fails CI rather than a project. The pin trails the app by at most a month,
which keeps the drift risk small.

## Consequences

- Generated projects gain a `renovate` job in `build.yml`, and `gate` needs it.
- Agent sessions need Node 24 or later to run the validator locally. Cloud sessions have it,
  and todofixthis/config-paddock's baseline image installs it.
- The template's `renovate.json` tracks `build.yml`'s pin, and this repo's `renovate.json`
  tracks both its own pin in `ci.yml` and the template's copy. Bumping them in one PR keeps
  the local command and CI on one version.

[#76]: https://github.com/todofixthis/cookiecutter-py/pull/76
