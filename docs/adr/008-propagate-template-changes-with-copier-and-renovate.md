---
status: Accepted
date: 2026-10-12
scope:
  - copier.yml
  - template/
  - test/
  - .github/workflows/
summary: Generate and update projects with copier, not cookiecutter, cruft or manual re-sync, using no copier unsafe features so Renovate's copier manager delivers each template release as a PR; projects support the three most recent Python minor releases through a recorded `python_version` answer, not one computed from the host interpreter, and the template is validated by baking a project and running its own lint, type-check, test and docs build.
revisit-when: Renovate's copier manager stops opening PRs for template releases; a library needs a template feature copier treats as unsafe.
---

# 008: Propagate Template Changes with Copier and Renovate

## Context

The [2026-10-10 drift audit][drift audit] found that most drift across the Python
libraries has one cause: fixes land in a leaf repository and never flow back.
This template is meant to be the canonical source, yet it lags its children on
ADR tooling, ReadTheDocs config, the Sphinx and setup-uv versions and the
`rotate-python-versions` skill. Nothing carries a template change into a
project baked earlier, so each repository re-solves the same problem its own
way: four mechanisms keep one phx-adr pin current. Consolidating once without a
propagation mechanism drifts again within months.

cookiecutter bakes once and keeps no link to the template. Two decisions rest on
that one-shot model:

- [ADR 001][] supports the three most recent Python minor releases, with the
  floor computed by `hooks/pre_prompt.py` from whichever interpreter runs
  cookiecutter.
- [ADR 004][] validates the template by baking it with cookiecutter and running
  the generated project's own lint, type-check, test and docs build.

Every library already carries a Renovate config (ADR 003), and Renovate has a
[copier manager][Renovate copier manager] that runs `copier update
--skip-answered --defaults` for each template release. It adds `--trust` only
where the Renovate operator sets `allowScripts` and the repository sets
`ignoreScripts: false`, so a template must not depend on it.

## Options

Options 2 and 3 both need each library linked to the template once, with its
local changes reconciled by hand; that cost doesn't rank them.

### Option 1: Do nothing

Keep cookiecutter; a fix reaches an existing library only if someone ports it
by hand.

**Pros:** No migration.
**Cons:** The audit's systemic finding stands, and each consolidation decays.
**Risks:** Leaf fixes keep diverging, so the next audit is larger than this one.

### Option 2: copier, with Renovate's copier manager (Accepted)

Port the template to [copier][]. Each project records its answers and the
template version in `.copier-answers.yml`; Renovate opens a PR running
`copier update` whenever the template tags a release.

**Cons:** A one-off port of every templated file and path. copier's unsafe
features (`_tasks`, `_migrations`, `_jinja_extensions`) are unavailable, so
anything a hook did must be expressible as a question or a template file.
**Risks:** An update that conflicts with local edits lands as a Renovate PR with
conflict markers, which a maintainer must resolve before merging.

### Option 3: cruft over the existing cookiecutter template

Link each library with `cruft link`, and add a CI `cruft check` so drift shows
as a red check.

**Pros:** Keeps the cookiecutter template as it is.
**Cons:** [cruft][]'s last release was 2.16.0, on 2024-12-25, and Renovate has
no cruft manager, so updates need a human or a scheduled job of our own. A
`cruft check` in CI turns every unrelated PR red the moment the template
releases.
**Risks:** Building propagation on a tool that may already be unmaintained.

### Option 4: Manual re-sync by convention

Make "fix it in the template first, then port it to each library" a written
rule, backed by a periodic audit.

**Pros:** No new tooling.
**Cons:** Six libraries times every fix, by hand; the rule is only as good as
the memory of whoever makes the fix.
**Risks:** The same as Option 1, delayed by however long the rule is followed.

## Decision

Option 2. copier is the only option where a template release reaches every
library without anyone remembering to send it, through a tool (Renovate) each
library already runs. Option 3 would need us to build that delivery ourselves,
on a tool with no release in nearly two years.

The template is bound by these constraints, each of which an update path
depends on:

- **No unsafe features**: no `_tasks`, `_migrations` or `_jinja_extensions`.
  Renovate's PRs run without `--trust`, and an unsafe template fails them.
- **Delimiters** are `[[ ]]`, `[% %]` and `[# #]`, set in `_envops`. GitHub's
  `${{ }}` then needs no `{% raw %}`, so templated workflows stay readable to
  Renovate's other managers. Bash in a templated `run:` block uses `[ ]` or
  `test`, never `[[ ]]`, which copier would read as a variable.
- **Templated files carry `.jinja`** (`_templates_suffix: .jinja`): only those
  files' contents are rendered, and every other file's contents copy verbatim.
  Path names are always rendered, suffix or not.
- **A value that must stay fixed after the first copy is a recorded question,
  never a computed variable**; computed values re-render on every update.
- **Symlinks are preserved** (`_preserve_symlinks: true`), replacing
  `hooks/post_gen_project.py`.
- **Releases are bare semver tags** (`1.0.0`), matching phx-claude-siat's.
- **Drift shows as a Renovate PR, never as a CI job**, so a template release
  blocks no unrelated PR.

This restates ADR 004 with copier in place of cookiecutter: `test/` bakes the
template with copier and checks the output, and CI bakes a project and runs its
own lint, type-check, test and docs build. CI bakes the template under every
supported Python version.

It restates ADR 001's policy, three most recent minor releases, with a different
mechanism. `python_version` becomes a recorded question with a static default,
which the `rotate-python-versions` skill bumps when a Python version rotates. A
value computed from the host interpreter would need an unsafe extension, and
would be re-derived on every `copier update`, moving a project's Python floor
unasked whenever Renovate's runner had a different Python. For the same reason
`this_year` gives way to a recorded `copyright_year`, alongside a recorded
`copyright_holder`, so a project's copyright notice doesn't change with each
update.

## Consequences

- ADRs 001 and 004 are superseded by this ADR. `phx-adr supersede` refuses
  while the corpus fails `phx-adr check`, so both are marked once their scopes
  are fixed in the copier port.
- `hooks/` and `cookiecutter.json` are deleted; `copier.yml` holds the questions
  and the template moves under `template/`.
- The recorded `version` answer seeds `__version__` in a new project only. After
  adoption the release skill moves the real version on, so the answer goes
  stale; that's expected, and nothing should read it.
- A project changes its Python floor by updating with a new `python_version`
  answer, not by waiting for Renovate, which keeps recorded answers.
- Every question added after 1.0.0 needs a default, or Renovate's
  `--defaults` run fails on it.
- Each library is adopted once with `copier copy` and a hand reconciliation;
  only after that do template releases arrive as PRs.

[ADR 001]: 001-support-three-most-recent-python-releases.md
[ADR 004]: 004-validate-the-template-by-baking-it.md
[copier]: https://copier.readthedocs.io/
[cruft]: https://pypi.org/project/cruft/
[drift audit]: ../audits/2026-10-10-drift-audit.md
[Renovate copier manager]: https://github.com/renovatebot/renovate/blob/main/lib/modules/manager/copier/readme.md
