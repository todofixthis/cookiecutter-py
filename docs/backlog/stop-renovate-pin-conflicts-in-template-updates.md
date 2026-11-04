# Stop a project's Renovate and the template's from conflicting on the same pins

> Recorded 2026-10-31, from the template-owned rule discussion on todofixthis/class-registry#142. Never a GitHub issue.

## What

A generated project's Renovate and this repository's both bump the same lines in
template-owned files: dependency bounds in `template/pyproject.toml.jinja`, action SHAs in
`template/.github/workflows/build.yml.jinja`, and the phx-adr pins there and in
`template/AGENTS.md`. When the two land on different versions, the template-update PR
that `copier update` opens (ADR 008) conflicts on those lines. When they land on the same
version, it merges cleanly. class-registry met it on adoption, before any update PR: its
`develop` had setup-uv v10.3.3 while template 1.1.0 pinned v10.3.2, and its adoption
rebase conflicted on that workflow. It kept v10.3.3 by hand.

## The trade-off that shapes the fix

Stopping a project's Renovate from bumping template-owned pins removes the conflict, but
delays each bump, security fixes included, until a template release reaches the project.
Letting both keep bumping keeps projects current, at the cost of the conflicts.

## Acceptance

- An update PR from a template release whose pins differ from a project's own merges
  without conflict markers on those lines, keeping the newer of the two versions.
- The approach is recorded in an ADR, and in the `description` field of the Renovate rules
  it adds to `renovate.json` and `template/renovate.json`.
