---
status: Accepted
date: 2026-10-16
scope: [AGENTS.md, docs/backlog/]
summary: Record deferred work as one plain Markdown file per item under docs/backlog/, naming the paths it binds in its prose, following phx-claude-siat's convention but not its backlog.py routing, and never as a GitHub issue, though the tracker stays enabled for Renovate's dependency dashboard.
revisit-when: A second person needs to see what is deferred without cloning; bug reports from people other than the maintainer start arriving in the tracker; phx-claude-siat changes its backlog convention or ships its backlog lookup in the phx plugin.
---

# 011: Track Deferred Work in docs/backlog

## Context

Review of [todofixthis/cookiecutter-py#11][] deferred a piece of work: a skill that audits
the maintainer's repositories for drift. AGENTS.md sends an agent to `docs/adr/INDEX.md` and
`docs/superpowers/plans/`, and nowhere that holds deferred work. The one open issue,
[#10][], shows the cost: it records a cookiecutter bake failure that #11 makes impossible,
and no agent working on #11 was sent to read it.

The maintainer's [phx-claude-siat][] met the same problem and settled it in three ADRs:
- deferred work lives in `docs/backlog/`, one file per item, and never in the issue tracker
  ([ADR 020][phx 020]);
- items carry no frontmatter ([ADR 032][phx 032]);
- `scripts/backlog.py` reports from the pre-commit hook the items whose links name a staged
  path ([ADR 030][phx 030], which superseded 020).

The tracker here is enabled, and Renovate's Dependency Dashboard is an issue in it ([#14][]).

## Options

### Option 1: Do nothing

Deferred work becomes GitHub issues, or a note in whatever file is open.

**Pros:** No new convention.
**Cons:** An issue is a note no agent reads, because nothing sends one to the tracker.
**Risks:** Each issue filed reads as work captured, though it's never found again.

### Option 2: Adopt phx-claude-siat's convention without its routing (Accepted)

`docs/backlog/<slug>.md`, one plain Markdown file per item, in the shape
[`docs/backlog/README.md`][] fixes. AGENTS.md says to read the directory before starting on
an area, and to write an item rather than an issue. Finding items rests on `rg`, so each item
names the paths it binds in its prose.

**Cons:** Nothing routes a reader to an item, and nothing flags a stale one.
**Risks:** An item that doesn't name its paths can't be found, and nothing reports the miss.

### Option 3: Adopt the convention with phx-claude-siat's routing

Option 2, plus `backlog.py` reporting the items bound to a staged path at commit time. The
pinned `phx-adr` package installs the `adr` module `backlog.py` imports, but not
`backlog.py` itself, so this repository would vendor or fetch that one file and run it under
the pinned package.

**Pros:** An item reaches a session about to commit a change to the paths it names.
**Cons:** `backlog.py` uses `adr`'s internals (`read_document`, `resolve_root` and others),
so a Renovate bump of the pin can break it. It needs an autohooks plugin to run, and it
reports only after the change is written.
**Risks:** The vendored file drifts from the pinned package, and a breakage there passes
silently in any session that can't run autohooks.

## Decision

Option 2. It matches the maintainer's existing convention, so an agent working across both
repositories meets one shape. Option 3's routing helps only at commit time, and here it costs
a vendored script coupled to another package's private API.

The tracker stays enabled, because turning it off would also remove the Dependency
Dashboard. So this rule is enforced only by AGENTS.md, and nothing stops an issue being
filed by hand.

## Consequences

- AGENTS.md gains a "Deferred work" section, and its Getting Started list points at
  `docs/backlog/`.
- `docs/backlog/README.md` keeps the directory in the tree once every item is deleted, which
  matters because `docs/backlog/` is in this ADR's `scope`.
- The branch that finishes an item deletes it. No check catches an item left behind.
- #11 makes #10's failure impossible, so #10 is closed by hand once #11 merges. #11 targets
  `develop`, which isn't the default branch, so a closing keyword in its body won't fire.
- Generated projects don't get the convention: `template/` is unchanged. Adding it there
  would be a template decision of its own.

[#10]: https://github.com/todofixthis/cookiecutter-py/issues/10
[#14]: https://github.com/todofixthis/cookiecutter-py/issues/14
[`docs/backlog/README.md`]: ../backlog/README.md
[phx 020]: https://github.com/todofixthis/phx-claude-siat/blob/8.1.0/docs/adr/020-track-deferred-work-in-the-repository.md
[phx 030]: https://github.com/todofixthis/phx-claude-siat/blob/8.1.0/docs/adr/030-route-backlog-items-from-the-paths-they-bind.md
[phx 032]: https://github.com/todofixthis/phx-claude-siat/blob/8.1.0/docs/adr/032-keep-backlog-items-as-plain-markdown-not-frontmatter.md
[phx-claude-siat]: https://github.com/todofixthis/phx-claude-siat
[todofixthis/cookiecutter-py#11]: https://github.com/todofixthis/cookiecutter-py/pull/11
