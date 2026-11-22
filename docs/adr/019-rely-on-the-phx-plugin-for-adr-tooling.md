---
status: Accepted
date: 2026-11-22
scope: [.autohooks/, .claude/settings.json, .github/workflows/, AGENTS.md, docs/adr/, pyproject.toml, scripts/, template/.autohooks/, template/.claude/settings.json, template/.github/workflows/, template/AGENTS.md, template/docs/adr/, template/pyproject.toml.jinja]
summary: This repository and every generated project index, validate and look up ADRs only with the phx plugin's writing-adrs tool, through its hooks in Claude Code sessions and its `phx-adr` entry point in CI and AGENTS.md (pinned as ADR 018 decides), never a repo-local generator, a vendored copy of the tool, or any pre-commit hook running ADR tooling; ADR frontmatter follows the skill's conventions (`scope`, not `tags`), and `docs/adr/INDEX.md` is the tool's output, never hand-edited.
revisit-when: A phx plugin release imposes an ADR convention the maintainer rejects; ADRs in this repository or a generated project are routinely authored outside a Claude Code session with the plugin, so CI is the first check most of them meet; plugin releases routinely outrun the pin and leave CI red; sessions can install the plugin at the pinned release; the phx plugin drops its ADR tooling.
---

# 019: Rely on the phx Plugin for ADR Tooling

## Context

[`phx:writing-adrs`][] ships `adr.py`, which scaffolds, indexes and validates
ADRs and answers which decisions bind a path. The phx plugin's hooks run it in
Claude Code sessions: they inject the decisions binding a file the first time a
session touches it, regenerate `docs/adr/INDEX.md` after an edit to an ADR, and
report faults, never blocking. They stay silent unless the index's first line
names `phx:writing-adrs`. The same tool installs as `phx-adr`, which CI's
`adrs` job and AGENTS.md's commands run at a pinned release ([ADR 018][]).
[`.claude/settings.json`][] and the template's copy register phx-claude-siat's
marketplace, whose manifest points the plugin at `main`, so sessions run its
newest release, not the pin.

This repository and its template already work this way, and the template's
AGENTS.md forbids a repo-local ADR script, pre-commit hook or vendored copy of
the tool. No ADR records why. The template's `adrs` job comment credits
ADR 009, but neither 009 nor 018, which superseded it, decides it: they decide
the CI job, its pin and `gate`.

So the generated projects record it themselves. todofixthis/class-registry's
ADR 007 decides it, and its ADR 008 waits on a template ADR to replace 007.
todofixthis/filters-iso's ADR 004 and todofixthis/filters-django's ADR 002
each restate it inside their deferral to the template, waiting likewise.
todofixthis/filters-pydantic's ADR 007, adopting the template next, holds it
too. class-registry's 007 records what a repo-local tool cost: a generator
ported from the skill, with a blocking pre-commit hook and its own CI job,
wrote the index under a different first line, so the two could not run side
by side, and a session that let the plugin write the index was reverted to get
CI green.

## Options

Every option keeps CI's `adrs` job, so a faulty corpus is blocked at merge
whichever is chosen, and every check pinned to a release disagrees with the
plugin's hooks whenever a release outruns the pin. Neither ranks them; they
differ in what runs before a commit.

### Option 1: Rely on the plugin's tool, with nothing local (Accepted)

The hooks in sessions; `phx-adr` at the pin in CI and AGENTS.md; nothing
ADR-specific in a repository beyond the corpus and those pins.

**Cons:** No local check blocks a faulty commit; a fault from a commit made
outside a session with the plugin surfaces only in CI. Outside Claude Code
nothing allocates a number or regenerates the index unless the author runs
`phx-adr` by hand.

### Option 2: A repo-local tool

A generator of the repository's own, or `adr.py` vendored in, run by a
pre-commit hook and CI.

**Pros:** Blocks a faulty commit for every committer, plugin or not.
**Cons:** A copy of the conventions to keep in step with the skill by hand,
in this repository and every generated project. Any divergence, the index's
first line being only the first, sets the copy and the plugin's hooks
fighting over the index.

### Option 3: A pre-commit hook running the plugin's tool

An autohooks plugin running `phx-adr check` at the pin, or the installed
plugin's own `adr.py`, before each commit.

**Pros:** Blocks a faulty commit locally without copying the tool.
**Cons:** At the pin, the hook rejects an index a newer session's tool just
wrote whenever a release changes the index or its checks, blocking ADR
commits until Renovate's bump lands, where Option 1 shows the same gap as one
red CI check. Running the installed plugin instead, it checks only where the
plugin's hooks already report. Its first run needs the network to fetch the
tool.

## Decision

Option 1, recording what the template already does. One implementation of the
conventions, maintained with the skill that states them, reaches every
project. Option 2 pays for its local block with a copy that diverges as the
skill moves. Option 3's pinned form turns the pin lag from a red CI check
into blocked commits, and its unpinned form adds nothing the hooks don't
report in the sessions that author nearly every ADR here and in the
generated projects.

The skill owns the conventions, `scope` rather than `tags` among them, and
`docs/adr/INDEX.md` is its tool's output: editing the index's first line
switches the hooks off.

## Consequences

- The template's `adrs` job comment cites this ADR, not ADR 009, and the pin
  comments in it, `renovate.json` and AGENTS.md cite ADR 018.
- Once a release carries this ADR, class-registry's 008 trigger fires and 007
  can be superseded by deferring here; filters-iso's 004 and filters-django's
  002 can drop their restatements. filters-pydantic's 007 can give way when it
  adopts the template.
- An agent in a harness other than Claude Code gets no session hooks; it
  meets the conventions only through AGENTS.md, the skill and CI.
- The gap between a plugin release and the pin stays short only while
  phx-claude-siat's `main` carries only releases, which ADR 018 already
  watches.

[ADR 018]: 018-require-gate-everywhere-and-the-release-check-on-main.md
[`.claude/settings.json`]: ../../.claude/settings.json
[`phx:writing-adrs`]: https://github.com/todofixthis/phx-claude-siat/blob/9.1.0/skills/writing-adrs/SKILL.md
