# Generated docs should fail on unresolved Python cross-references

> Recorded 2026-11-24, a template candidate from todofixthis/paddock#69, where paddock
> turned `nitpicky` off to take the template's `docs/conf.py` (paddock's ADR 025, whose
> `revisit-when` names this template gaining `nitpicky`). The maintainer deferred it here
> on learning what it costs the projects already generated. Never a GitHub issue.

## What

Set `nitpicky = True` in `template/docs/[% if docs_site %]conf.py[% endif %].jinja`, so
the strict docs build (`-W`, ADR 020) also fails on a Python cross-reference Sphinx can't
resolve. Without it, an unresolved `:class:` or autodoc type renders as plain text and the
build stays green. That needs an ADR, as a change to how strictly every generated docs
site builds.

## The cost that deferred it

A fresh bake and paddock build clean with it on, intersphinx resolving the standard
library. The docs-site projects already generated don't. Counted on 2026-11-24 with
`sphinx-build -W -E -n --keep-going docs <out>` on each project's `develop`:

- class-registry: 112 warnings, mostly the `ValueType` and `KeyType` TypeVars and class
  names written unqualified in docstrings;
- filters: 41, mostly TypeVars (`T_out`, `T_allowed1` …) and `FilterCompatible`;
- filters-pydantic: 2, `FilterCompatible` and `T_model`.

`conf.py` is template-owned, so the release reaches all of them, and each update PR fails
its `docs` job until its warnings are fixed: `nitpick_ignore` entries for TypeVars, and
qualified references elsewhere. Fix them in each project first, or in its update PR.

## Acceptance

- The template's `conf.py` sets `nitpicky = True`, with a comment saying why.
- CI's bake builds the generated docs with it, still under `-W`.
- Every generated docs-site project builds with it before, or in, the update PR that
  brings it.
- Paddock's ADR 025 trigger is answered: paddock takes the template's line.
