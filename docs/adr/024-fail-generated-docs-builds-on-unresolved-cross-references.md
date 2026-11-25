---
status: Accepted
date: 2026-11-25
scope: [template/docs/]
summary: Generated projects with their own docs site set nitpicky = True in the template's docs/conf.py, so the strict build fails on a Python cross-reference Sphinx can't resolve; a project documents its own TypeVars and aliases so references to them resolve, never ignoring them, and its own content in the template-owned conf.py is limited to intersphinx_mapping entries for dependencies that publish Sphinx docs and nitpick_ignore entries for third-party targets no mapped inventory resolves; not a project-owned settings file conf.py imports.
revisit-when: A docs build goes red on a nitpicky warning caused by a dependency's code or published inventory rather than the project's own docs; template updates repeatedly conflict in docs/conf.py over a project's nitpick_ignore or intersphinx_mapping lines; nitpick_ignore entries in generated projects grow beyond a handful each.
---

# 024: Fail Generated Docs Builds on Unresolved Cross-References

## Context

[ADR 020][] fails a generated project's docs build on any Sphinx warning.
An unresolved Python cross-reference raises none unless Sphinx's `nitpicky`
is on: a `:class:` role or an autodoc annotation naming something Sphinx
can't find renders as plain text, and the build stays green. paddock turned
`nitpicky` off to take the template's `docs/conf.py` (its ADR 025, whose
`revisit-when` names the template gaining it), and a backlog item deferred
turning it on for the cost it carried.

That cost, counted with `sphinx-build -E -n` on each project's `develop`:
class-registry 112 warnings, filters 46, filters-pydantic 2; a fresh bake and
paddock none. Most were the projects' own TypeVars and aliases, which autodoc
names in signatures but nothing documents, and unqualified names in
docstrings. Fixing those leaves targets no project can document:

- `SupportsAllComparisons`, a `_typeshed` protocol that exists only as stubs
  (class-registry);
- `_regex.Pattern`, whose library publishes no Sphinx docs (filters);
- `filters.base.FilterCompatible`, in filters-pydantic's signatures, which
  phx-filters' published docs don't yet hold under that path.

`docs/conf.py` is template-owned, so wherever such an exception lives decides
how a template update treats it.

## Options

All but Option 1 need a docs entry for every new TypeVar or alias a
signature names, which the docs pre-commit hook (ADR 020) enforces; that
cost doesn't rank them.

### Option 1: Do nothing

**Cons:** A broken reference ships silently, in docs whose build is strict
in every other way.

### Option 2: nitpicky on, projects' own exceptions in the template's conf.py (Accepted)

The template sets `nitpicky = True` and an empty `nitpick_ignore` beside it,
with the rule in a comment. A project documents its own TypeVars and
aliases, maps a dependency that publishes Sphinx docs in
`intersphinx_mapping`, and lists in `nitpick_ignore` only a third-party
target no mapped inventory resolves, removing it once one does.

**Cons:** The project's lines conflict whenever a template update changes
the lines around them. An entry in `nitpick_ignore` hides that reference for
good, so one added for a project's own object would undo the check where it
matters. Each intersphinx mapping fetches a dependency's live inventory,
outside `uv.lock`, so a dependency renaming an object can turn any PR red.

### Option 3: Option 2, with the exceptions in a project-owned file the template's conf.py imports

**Cons:** A new project-owned file and an import convention in `conf.py` for a
list most projects keep empty and the rest hold to a handful of entries.

### Option 4: nitpicky on, projects ignore their own TypeVars

**Cons:** An entry that hides rather than documents: a reader following a
signature's `T_out` finds nothing.

## Decision

Option 2. Documenting a project's own TypeVars fixes the docs rather than
the warning, and leaves only third-party gaps, which are few and change
rarely. A slot in the template with its rule beside it puts that rule where
the edit is made, the only place an agent in a generated project meets it,
and costs less than Option 3's file for a list that stays short.

## Consequences

- Each docs-site project fixes its warnings before the template update that
  brings `nitpicky`, and that update PR adds its exceptions: lines added
  before it would collide with the template's own hunk. Pushing them onto
  Renovate's branch stops Renovate rebasing that PR.
- intersphinx matches a `py:class` reference only to a `py:class`,
  `py:exception` or `py:type` entry at the same path, never `py:data`, which
  `autodata` writes. A dependency documents an alias with a hand-written
  `py:type` for a dependent's mapping to resolve it: phx-filters does so for
  `filters.base.FilterCompatible`, after which filters-pydantic maps
  phx-filters' docs instead of ignoring it.
- Deletes the nitpicky backlog item. paddock's ADR 025 condition is met once
  this ships in a release, and paddock discharges it when it takes the
  update.

[ADR 020]: 020-fail-generated-docs-builds-on-sphinx-warnings-in-ci-and-before-commit.md
