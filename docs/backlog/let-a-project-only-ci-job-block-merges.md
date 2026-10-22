# Give a project-only CI job a way to block merges

> Recorded 2026-10-22, from the review of PR #16's `lint` job. Never a GitHub issue.

## What

The template-owned rule tells a generated project to put an extra CI job in its own
workflow file, so that template updates don't conflict with it. The rule's text lives in
`scripts/template_owned.py`, which generates `template/.agents/rules/template-owned.md.jinja`
(ADR 012), so edit the script, never the `.jinja`.

`docs/adr/009-gate-adr-ci-and-the-phx-pin.md` makes `gate` in
`template/.github/workflows/build.yml.jinja` the only required check, and its Consequences
say every job must sit in `gate`'s `needs` or it stops blocking merges. `needs` can't reach
a job in another workflow file, and the shared Terraform module requires `gate` alone. So a
project-only job, placed where the rule says, runs but never blocks a merge, and neither
document says so.

## Bounds on a fix

Two fixes break decisions already taken: a second required check needs the per-repository
list in shared Terraform that ADR 009 rejected, and making `build.yml` project-owned loses
template updates to it. One candidate keeps both: `build.yml` calls a project-owned
reusable workflow (`uses: ./.github/workflows/<name>.yml`), `gate` lists that call job in
`needs`, and the template ships a stub of it that copier writes only on first copy
(`_skip_if_exists`, as for `project.md` under ADR 010). The design is the implementer's
choice within those bounds.

## Acceptance

- A generated project has a documented way to add a job that blocks merges without editing
  a template-owned file.
- `scripts/template_owned.py`'s rule and ADR 009's Consequences agree on it.
