---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/docs/", "{{ cookiecutter.github_project_name }}/.readthedocs.yaml"]
summary: Enable sphinx.ext.autosectionlabel with autosectionlabel_prefix_document = True in generated projects' docs, not its default unprefixed labels.
revisit-when: A generated project's docs grow large enough to have collided under the default (unprefixed) setting, and prefixing has proven not to be worth its extra verbosity in practice.
---

# 006: Enable autosectionlabel with Document-Prefixed Labels

## Context

A generated project's docs start with two pages — [`index.rst`][] and
[`api.rst`][] — with no section cross-references between them at all.
[`autosectionlabel`][] registers a label for every section automatically,
from the section's own title, so a page can grow and later link into
another without a maintainer ever hand-placing a `.. _label:` anchor.

Whether that label is the bare title or the title prefixed with the
document's name only matters once two sections somewhere in the project
share a title — not true of the two-page starting doc set, but true of
[`class-registry`][] and [`filters`][], the two sibling projects this
template already tracks conventions from ([`002`][], [`003`][]). Building
each sibling's docs with the bare (default) form, after temporarily
reverting the fix each had already applied, reproduces real `duplicate
label` collisions — two in class-registry, eleven in filters — entirely
from ordinary page growth, not from anything unusual either project did.
Both siblings' `.readthedocs.yaml` sets `fail_on_warning: true`, so either
warning breaks the published build.

A generated project starts from the same two-page docs this template ships
and is expected to grow them the same way its siblings did — this decision
is for the docs a generated project will have, not the two pages it starts
with.

## Options

### Option 1: Do nothing

**Pros:** No risk of introducing a warning that doesn't exist today.
**Cons:** Every section a generated project's docs later want to
cross-reference needs its own hand-placed anchor from day one, the
overhead `autosectionlabel` exists to remove — and, per Context, the
default (unprefixed) form of enabling it fails the exact way it already
has for both sibling projects once a project's docs grow past a page or
two.

### Option 2: Enable with default (unprefixed) labels

**Pros:** A label is just the section title, so a project maintainer who
already knows the heading can guess the `:ref:` target without checking.
**Cons:** Verified by reproducing both siblings' original collisions (see
Context) — the bare form breaks the build the moment two sections
anywhere in the project share a title, which is what happened to both
projects this template already imitates.
**Risks:** A generated project inherits this risk silently: nothing in the
two-page starting docs would warn a maintainer that the setting they
enabled works fine today and stops working the moment their docs grow.

### Option 3: Enable with `autosectionlabel_prefix_document = True` (Accepted)

**Pros:** Verified by re-applying both siblings' fix — it resolves every
collision Option 2 reproduces, since every generated label becomes
`<docname>:<Title>`, which cannot collide with a same-titled section in a
different document. Baked and rebuilt with this setting, the generated
project's own two-page docs stay clean.
**Cons:** A `:ref:` target now needs the document name as well as the
title. It also couples the target to the source file's name — renaming or
splitting a `.rst` file invalidates every prefixed label pointing into it,
caught by the next docs build rather than silently.
**Risks:** Prefixing disambiguates *across* documents, not within one, so
two sections sharing an identical title in the *same* document still
breaks the build; a generated project's docs need the same before-and-after
build check as any other docs change.

## Decision

Option 3. This is a starting-point decision for docs that don't yet exist:
a generated project's docs will grow the way its siblings' did, and Option
2 is what already broke for both of them. Prefixing costs a generated
project nothing today — it starts with two pages and no `:ref:` calls to
write in the new form — and buys the same protection the siblings had to
add after the fact.

## Consequences

- `{{ cookiecutter.github_project_name }}/docs/conf.py` gains
  `sphinx.ext.autosectionlabel` and `autosectionlabel_prefix_document = True`.
- `{{ cookiecutter.github_project_name }}/.readthedocs.yaml` gains
  `fail_on_warning: true`, matching both sibling projects — without it,
  neither this decision nor [`007`][]'s pre-commit check has a published
  build behind them to protect.
- A generated project's own future sections become reachable via
  `` :ref:`\<docname\>:\<Section Title\>` `` with no anchor needed.
- Two sections sharing an identical title *within the same document* still
  produce a `duplicate label` warning — prefixing does not reach that case.
- `autosectionlabel_maxdepth` stays unset, so every heading at every depth
  gets a registered label — the same unbounded growth this ADR is written
  for, not a gap in it.

[`002`]: 002-generate-projects-with-uv-and-hatchling.md
[`003`]: 003-manage-updates-with-renovate.md
[`007`]: 007-check-the-docs-build-in-the-pre-commit-hook.md
[`api.rst`]: ../../{{ cookiecutter.github_project_name }}/docs/api.rst
[`autosectionlabel`]: https://www.sphinx-doc.org/en/master/usage/extensions/autosectionlabel.html
[`class-registry`]: https://github.com/todofixthis/class-registry
[`filters`]: https://github.com/todofixthis/filters
[`index.rst`]: ../../{{ cookiecutter.github_project_name }}/docs/index.rst
