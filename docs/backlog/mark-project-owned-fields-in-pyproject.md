# Generated projects should know which pyproject.toml fields are theirs

> Recorded 2026-11-25, from the maintainer's review of the Development Status classifier
> (ADR 023), which found todofixthis/filters-django's hand-filled `classifiers` inside a
> template-owned `pyproject.toml`. Never a GitHub issue.

## What

`template/pyproject.toml.jinja` is template-owned as a whole, yet seeds `keywords` and
`classifiers` empty for each project to fill, and projects add `dependencies` and
entry points beside them. The template-owned rule that `scripts/template_owned.py`
generates allows those edits only through its general "depends on this project" test;
nothing names the fields a project owns.

Name them: in the generated rule, in comments in `template/pyproject.toml.jinja`, or both.

## Why it is still worth doing

An agent in a generated project re-derives the split on every edit, and a template release
touching lines next to a project's own fields can conflict on `copier update`.

## Acceptance

- A generated project's agent can tell from one place which `pyproject.toml` fields it may
  edit freely.
- A test bakes the template, fills those fields as a project would, and shows a later
  template change elsewhere in the file merging cleanly.
