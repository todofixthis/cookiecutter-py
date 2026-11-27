---
status: Accepted
date: 2026-11-27
scope: [.github/workflows/ci.yml, AGENTS.md, renovate.json, template/.github/workflows/build.yml.jinja, template/AGENTS.md, template/renovate.json, test/]
summary: A renovate job that gate needs runs renovate-config-validator --strict via npx at a pinned version, from the directory holding each renovate.json (this repo's, a baked project's, and in generated projects their own), after checking the file exists; the pin's minor and patch bumps are monthly and automerged, majors reviewed; not a JSON-schema check, a lockfile-pinned install, or checking the Dependency Dashboard after merge.
revisit-when: Renovate publishes its validator outside the npm package; the pin's monthly bumps repeatedly fail CI or sit unmerged; the renovate job becomes the slowest job gate waits on.
---

# 026: Validate Renovate config in CI with Renovate's own validator

## Context

This repo ships two Renovate configs: its own `renovate.json`, and `template/renovate.json`,
which every generated project receives. Nothing checks either before merge. A fault, such as
an unknown option, a regex that doesn't compile or an option needing migration, surfaces
only after merge, on the Dependency Dashboard, if anyone looks. A fault in the template's
config reaches every project at the next release. [#76][] changed both configs and couldn't
validate them: its session had no `npx`. Generated projects can edit their own
`renovate.json`, and nothing checks those edits either.

Renovate's validator ships only inside the `renovate` npm package, whose `engines` field
limits the Node versions it runs on (`^24.11.0 || ^26.13.0` at 44.x). This is a Python
template, so Node is not otherwise on its CI path. The validator checks the config files in
its working directory, and finding none, exits 0 having checked nothing. Given a file
argument, it validates that file as global self-hosted config unless also given
`--no-global`.

## Options

### Option 1: Do nothing

Check the Dependency Dashboard after merge.

**Pros:** No CI time, and no Node on a Python project's CI path.
**Cons:** A faulty config merges, and a template fault ships to every project.
**Risks:** Renovate stops bumping a pin and nobody notices, because nothing fails.

### Option 2: Run `renovate-config-validator --strict` in CI via `npx` (Accepted)

Run it with `npx --package renovate@<version>`, where the version is a `RENOVATE_VERSION` env
pin with a `# renovate:` comment that a regex manager tracks. A `renovate` job, which `gate`
needs, runs it in this repo's `ci.yml` against the root config and a baked project's, and in
the template's `build.yml` against the project's own.

**Pros:** It runs the same checks Renovate itself does: it compiles every regex, and
`--strict` also fails a config that only needs migration.
**Cons:** Every push of every project installs Node and downloads the `renovate` package,
about 360 MB, since no step caches it and the job has no path filter. The pin fixes only the
top-level package: npm resolves its 400-odd dependencies afresh within their ranges,
with no lock and no release-age cooldown, and runs their install scripts.
**Risks:** The pin trails the hosted Renovate app, so a config valid for the app could fail
an older validator, or the reverse. Without `re2`'s install script, Renovate falls back to
JavaScript regexes and accepts patterns the hosted app rejects.

### Option 3: Install the validator from a lockfile

Commit a `package.json` and lockfile declaring `renovate`, and install with a frozen lock.

**Pros:** Every transitive dependency is pinned, and Renovate's lock-file maintenance
refreshes them (ADR 013).
**Cons:** Adds a JavaScript package manifest, lockfile and install step to this repo and to
every generated Python project, for one CI tool.
**Risks:** A weekly lock refresh of 400-odd packages in every project, each a PR that can
fail.

### Option 4: Check the config against Renovate's JSON schema

Use a Python tool such as `check-jsonschema`.

**Pros:** No Node.
**Cons:** The schema checks shape, not meaning. It types `matchStrings` as an array of
strings, so a regex that doesn't compile passes, and it can't tell when a config needs
migration.
**Risks:** A green check that misses the faults most likely to stop a pin being bumped.

## Decision

Option 2. Only Renovate's own validator catches the faults that silently stop updates, and
`--strict` turns a deprecation into a failure while it is still cheap to fix. Option 3's
transitive pinning doesn't justify a JavaScript toolchain in every Python project: the
validator reads config and never ships in what a project builds. The job runs it with no
file argument, from the directory holding each config, so it checks the file a project
receives. Each step first checks `renovate.json` exists, since the validator passes on a
directory without one. Install scripts stay on, for `re2`.

Renovate releases several times a day. So every config that tracks the pin bumps its minor
and patch releases monthly, at least three days old (`security:minimumReleaseAgeNpm`), and
automerges them once `gate` passes: a bump that breaks the job fails CI, not a project. A
major can change `engines` or the config schema, so it waits for review. `setup-node` pins
the major only (`"24"`), so Node's patch releases cause no churn.

## Consequences

- When a Renovate release needs a migration, `--strict` turns its bump PR red here and in
  every generated project at once. Projects take the fix from a template release, since
  `renovate.json` is template-owned.
- A generated project's Renovate bumps the template-owned `RENOVATE_VERSION` and
  `node-version` pins in `build.yml` alongside the template's own bumps, which adds lines to
  the template-update conflicts that
  [the pin-conflict backlog item][backlog] describes.
- Agent sessions need a Node version Renovate's `engines` field accepts to run the validator
  locally. Cloud sessions have one, and todofixthis/config-paddock's baseline image installs
  one.
- This repo's `renovate.json` tracks both its own pin in `ci.yml` and the template's copy, so
  one PR bumps both, and a test fails if they differ. Another test fails if either config's
  regex manager stops extracting its workflow's pin.

[#76]: https://github.com/todofixthis/cookiecutter-py/pull/76
[backlog]: ../backlog/stop-renovate-pin-conflicts-in-template-updates.md
