---
status: Accepted
date: 2026-08-29
scope: [renovate.json, "{{ cookiecutter.github_project_name }}/renovate.json"]
summary: Manage dependency and GitHub Action updates via Renovate, not Dependabot, matching both sibling repos.
---

# 003: Manage Updates with Renovate, Not Dependabot

## Context

This repo's own `.github/dependabot.yml` targeted a glob directory (since the
templated project directory name isn't a literal path), and the generated
project's own `dependabot.yml` pointed at a concrete path. Both `class-registry`
and `phx-claude-siat` instead use a single `renovate.json` extending
`config:recommended` plus `helpers:pinGitHubActionDigests`, which — unlike
Dependabot's `github-actions` ecosystem — pins Actions to commit SHAs (with a
version-tag comment) rather than floating tags, closing the gap this
modernization's CI changes (SHA-pinned `actions/checkout`, `astral-sh/setup-uv`,
`actions/setup-python`) rely on staying current.

## Decision

Replace `dependabot.yml` with `renovate.json` (`{"extends": ["config:recommended",
"helpers:pinGitHubActionDigests"]}`) in both this repo's own root and the
generated project.

## Consequences

- Renovate needs the GitHub App installed on the repo (and, once generated
  projects exist, on each of those too) — a one-time, per-repo setup step
  outside this template's own files, same as it presumably already is for
  the two sibling repos.
- The SHA pins added by this modernization's CI workflows are a snapshot
  Renovate will keep moving forward from here.
