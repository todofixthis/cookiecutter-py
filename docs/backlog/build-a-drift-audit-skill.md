# A drift-audit skill would catch the drift copier and Renovate cannot

> Recorded 2026-10-16, from the maintainer's review of [todofixthis/cookiecutter-py#11][],
> which asked whether [`docs/audits/2026-10-10-drift-audit.md`][audit] should become a script,
> a CI check or a skill. Never a GitHub issue.

## What

Write a skill in this repository, at `.agents/skills/drift-audit/`, beside this repo's
`rotate-python-versions` skill; `.claude/skills` already links to `.agents/skills`. The
maintainer chose this repo over phx-claude-siat because the skill encodes how they structure
their repositories, which isn't general practice. That choice needs no ADR.

The skill records the audit's method and criteria, and writes a dated report in the audit's
shape under `docs/audits/`. It covers what copier and Renovate don't reach:

- repositories not generated from this template: apps, config repositories,
  cookiecutter-browser-plugin;
- agent instructions diverging across repositories;
- local edits to template-owned files in generated projects. Sort each into upstream or
  project-only using the criteria in the template-owned rule that `scripts/template_owned.py`
  generates (ADR 014): its project-specific-reason test, seed files and answer-derived
  values. Expect candidates a project's PR description or commit message listed under
  "Template candidates"; an unlisted one is the drift to report. Don't invent new criteria;
- repository settings, until something runs `terraform plan` for each repository on a
  schedule. The audit says only to run it once module v1 ships. The schedule condition comes
  from the #11 review.

## Why it is still worth doing

copier and Renovate carry template releases to generated projects. They don't reach
repositories outside the template, or a fix made in a leaf repository that should have gone
upstream. The 2026-10-10 audit found that pattern was the main cause of drift. Without a
recorded method, the next audit starts from scratch and its criteria differ.

## What shapes it

- **No CI check.** [ADR 008][] decides that drift shows as a Renovate PR, never as a CI job.
  Run the skill on demand, before a template release, say.
- **The re-bake diff is a report, not a gate.** For each generated library, re-bake at the
  `_commit` its `.copier-answers.yml` records, with its recorded answers, and diff the result
  against the library:

  ```bash
  copier copy --vcs-ref=<_commit> --data-file .copier-answers.yml --defaults <template> <tmp>
  ```

  Compare only the files the library tracks, and leave out `.copier-answers.yml`: its
  `_src_path` differs whenever the template is spelled differently from the recorded one. The
  agent sorts what the diff lists. Project-only edits to template-owned files are allowed,
  so a non-empty diff isn't a failure. On real libraries, this step waits until a library
  carries `.copier-answers.yml`. Libraries adopt the template after cookiecutter-py's `1.0.0`
  tag, as #11's description sets out. A fixture baked from this template tests the step now.
- **Reach is partial.** A session may be able to read only some repositories, and its GitHub
  tools may not read rulesets or branch protection. The report names what it couldn't check,
  as the audit's "Not checked" does.

## Acceptance

- `.agents/skills/drift-audit/SKILL.md` exists, stating the method, the criteria and the
  report's shape.
- A test under `test/` bakes a fixture project from a committed, tagged copy of this template,
  reusing `test/conftest.py`'s `template_repo` and `committed_bake` fixtures. A bake
  with `--vcs-ref=HEAD` from a dirty worktree records a `_commit` that a re-bake can't
  reproduce. The test makes one local edit to a
  template-owned file, and asserts that the re-bake diff lists that edit. The same test on an
  unedited bake asserts the diff lists nothing.
- One run against the todofixthis repositories writes a dated report under `docs/audits/`.
  Before any library carries `.copier-answers.yml`, the report lists the re-bake under "Not
  checked", and that run still counts.
- No CI job is added for drift.

[ADR 008]: ../adr/008-propagate-template-changes-with-copier-and-renovate.md
[audit]: ../audits/2026-10-10-drift-audit.md
[todofixthis/cookiecutter-py#11]: https://github.com/todofixthis/cookiecutter-py/pull/11
