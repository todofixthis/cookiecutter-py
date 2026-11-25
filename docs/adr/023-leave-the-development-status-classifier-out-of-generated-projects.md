---
status: Accepted
date: 2026-11-25
scope: [template/.agents/skills/release/, template/pyproject.toml.jinja, test/test_bake.py]
summary: Generated projects carry no Development Status classifier, leaving the version's PEP 440 pre-release segment to state it; not one the release skill updates, and not one a Hatchling metadata hook derives from the version at build time.
revisit-when: pip, uv, PyPI or another tool the maintainer relies on starts acting on the Development Status classifier.
---

# 023: Leave the Development Status Classifier Out of Generated Projects

## Context

A reviewer of phx-filters' alpha releases found [`4.0.0a2` on PyPI][phx-filters 4.0.0a2]
declaring `Development Status :: 5 - Production/Stable` in the release page's classifier
list. The template seeds `classifiers` empty and has never added that classifier; projects
carry it by hand from before they took the template, and nothing updates it when the
version changes.

Checked on 2026-11-25, nothing that acts on a release reads the classifier to tell a
pre-release from a final one:

- pip 24.0 and uv 0.13.10 both resolve an unpinned `phx-filters` to `3.7.0`, and to
  `4.0.0a2` only with `--pre`, `--prerelease=allow` or a pre-release specifier.
- PyPI labels a release "Pre-release" from its version: Warehouse's
  [`project-status.html`] and [`project-release-history.html`] branch on
  `release.is_prerelease`, not on a classifier.
- PyPI's search index ([`warehouse/search/tasks.py`]) takes each project's newest stable
  release ahead of any pre-release, so the classifier's search facet shows a pre-release's
  value only for a project with no stable release yet.

Some of the classifier's values (`1 - Planning`, `2 - Pre-Alpha`, `6 - Mature`,
`7 - Inactive`) are judgements no version carries. PyPI's archived project status covers the inactive case.

## Options

### Option 1: Do nothing

The template stays silent, and each project keeps whatever classifier it added.

**Pros:** No change; a project can state a judgement the version can't, such as
`6 - Mature`.
**Cons:** A hand-kept classifier contradicts the version on every pre-release cycle, as on
`4.0.0a2`.
**Risks:** None beyond the contradiction itself.

### Option 2: Leave the classifier out (Accepted)

A comment above `classifiers` in the template says to omit `Development Status`, and a
bake test stops the template itself from rendering one.

**Pros:** No value to maintain, so none to go stale.
**Cons:** Projects drop out of PyPI searches filtered by Development Status, such as
`5 - Production/Stable`.
**Risks:** A project re-adds the classifier by hand; the comment is the only defence in a
generated project, since the bake test runs only here.

### Option 3: The release skill sets the classifier

The release skill's version-bump step also rewrites the classifier from the version.

**Pros:** Small change to one skill; keeps the search facet.
**Cons:** Correct only when a release goes through the skill.
**Risks:** A bump made by hand leaves the classifier stale again.

### Option 4: Derive it at build time with a Hatchling metadata hook

A `hatch_build.py` in every project computes the classifier from the version.

**Pros:** Always consistent with the version in the built metadata; keeps the search facet.
**Cons:** [PEP 808][] now lets `classifiers` be static and dynamic at once, but Hatchling
1.33.0 still refuses it, so `classifiers` would become dynamic wholesale: every project's
own classifiers move into a `[tool.…]` table the hook reads, a breaking change. Every
project gains build-time code.
**Risks:** A hook bug breaks every project's build.

## Decision

Option 2. Options 3 and 4 compute the classifier from the version, so whatever mapping they
use, it says nothing the version doesn't. Only a hand-kept value says more, and hand-kept
is what went stale. Two things are lost, both accepted as the cost of never publishing a
contradiction: the search facet, and a project's way to state a judgement such as
`6 - Mature`.

## Consequences

- Each existing project that carries the classifier removes it in its own repository; the
  release notes for the template release carrying this decision say so.
- How a generated project tells its own `pyproject.toml` fields from the template's is
  open: see [`docs/backlog/mark-project-owned-fields-in-pyproject.md`][backlog item].

[backlog item]: ../backlog/mark-project-owned-fields-in-pyproject.md
[PEP 808]: https://peps.python.org/pep-0808/
[phx-filters 4.0.0a2]: https://pypi.org/project/phx-filters/4.0.0a2/
[`project-release-history.html`]: https://github.com/pypi/warehouse/blob/main/warehouse/templates/includes/packaging/project-release-history.html
[`project-status.html`]: https://github.com/pypi/warehouse/blob/main/warehouse/templates/includes/packaging/project-status.html
[`warehouse/search/tasks.py`]: https://github.com/pypi/warehouse/blob/main/warehouse/search/tasks.py
