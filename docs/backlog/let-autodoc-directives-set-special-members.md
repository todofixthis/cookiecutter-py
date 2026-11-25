# Generated docs should let an autodoc directive document special members

> Recorded 2026-11-25, found making class-registry's docs build under `nitpicky` (ADR
> 024). Never a GitHub issue.

## What

`template/docs/[% if docs_site %]conf.py[% endif %].jinja` sets `"special-members": False`
(and `"members": True`) in `autodoc_default_options`. Sphinx 9.2 lets a bool default
override the directive's own option, so `:special-members:` on an `automodule` is
silently ignored. class-registry had to exclude two classes from their `automodule` and
re-add each with `autoclass` and `automethod` to document `__getitem__` and `__len__`.
Dropping `"special-members"` from the defaults, or setting it to a value Sphinx treats as
unset, would let a directive opt in.

## Acceptance

- A bake's `automodule` with `:special-members: __getitem__` documents `__getitem__`.
- No generated project's docs change unless it opts in.
