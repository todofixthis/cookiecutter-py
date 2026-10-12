---
status: Accepted
date: 2026-10-12
scope: [cookiecutter.json, test/]
summary: The templated AGENTS.md is identical across libraries and holds no project-specific sections; each project's Architecture, Tests, Package and Troubleshooting content lives in `.agents/rules/project.md`, which copier writes only on first copy (`_skip_if_exists`), and shared test conventions live in the templated `.agents/rules/testing.md`.
revisit-when: A harness the maintainer uses reads AGENTS.md but not `.agents/rules/`; copier stops honouring `_skip_if_exists` on update.
---

# 010: Split AGENTS.md into Templated and Project Parts

## Context

[ADR 008][] delivers every template release to each library through
`copier update`. Every library's AGENTS.md mixes sections the template ships
(ADR process, commands, code comments, worktrees) with sections only that
project has: filters' Architecture, Package and Troubleshooting, paddock's
Configuration, each repository's own test layout. copier updates a file with a three-way merge,
so a local section in a templated file survives only until the template edits
the lines around it, and `copier copy`, which adopts a library, overwrites it
outright.

The shared test conventions (one docstring per test function, file naming)
appear in some libraries' AGENTS.md and in filters-pydantic's path-scoped
`.agents/rules/testing.md`, so they drift like everything else.

## Options

### Option 1: Do nothing

Keep one AGENTS.md per library, templated and locally edited at once.

**Pros:** One file to read.
**Cons:** Adoption overwrites each library's local sections, which must be
restored by hand, and every later Renovate PR that touches AGENTS.md risks a
conflict with them.
**Risks:** A Renovate PR merged with a bad conflict resolution silently drops a
local rule.

### Option 2: Templated AGENTS.md plus `.agents/rules/project.md` (Accepted)

AGENTS.md is fully templated and identical across libraries. A project's own
sections live in `.agents/rules/project.md`, listed in copier's
`_skip_if_exists`, so copier writes a stub on first copy and never touches it
again. Shared test conventions move from AGENTS.md into a templated,
path-scoped `.agents/rules/testing.md`. `.claude/rules` symlinks to
`.agents/rules`, and AGENTS.md's Getting Started points at `.agents/rules/`.

**Cons:** Project rules are one hop away from AGENTS.md. Claude Code loads them
through the `.claude/rules` symlink, but another harness reaches them only by
following AGENTS.md's pointer. A template fix to the stub never reaches an
existing project.
**Risks:** A library edits AGENTS.md directly anyway, and the next Renovate PR
overwrites or conflicts with the edit.

### Option 3: List AGENTS.md in `_skip_if_exists` and sync it by hand

**Pros:** Each library keeps one AGENTS.md, untouched by updates.
**Cons:** Template fixes to AGENTS.md, the file the audit found most drifted,
never propagate.
**Risks:** Reproduces the drift ADR 008 exists to end, for the file agents read
first.

## Decision

Option 2. It's the only option where the shared instructions propagate and the
local ones survive: Option 3 gives up the former, Option 1 the latter.
`_skip_if_exists` makes the boundary mechanical rather than a matter of merge
luck, and a pointer in AGENTS.md keeps project rules reachable from harnesses
that don't load `.agents/rules/`.

## Consequences

- Adopting a library moves every local AGENTS.md section into
  `.agents/rules/project.md` before `copier copy` runs, and checks section by
  section that nothing was lost.
- A change to a project's own conventions goes in `project.md`; a change meant
  for every library goes in the template's AGENTS.md or `testing.md`.
- The template's `project.md` is a stub, so improving it later reaches only new
  projects.
- A bake test proves `project.md` survives `copier update`, and that the test
  fails without `_skip_if_exists`.

[ADR 008]: 008-propagate-template-changes-with-copier-and-renovate.md
