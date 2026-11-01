---
status: Accepted
date: 2026-10-31
scope: [.agents/skills/rotate-python-versions/, .github/workflows/, copier.yml, renovate.json, template/, test/]
summary: Update projects with copier and Renovate's copier manager, not cruft or manual re-sync, using no copier unsafe features, and validate by baking a project and running its own checks; Python rotates only from an agent session in the project, never by Renovate, to the template's computed python_policy, with a python-policy workflow outside gate failing while a project lags, skipped on every Renovate branch but the template update.
revisit-when: Renovate's copier manager stops opening PRs for template releases; a library needs a template feature copier treats as unsafe; a project's python-policy check stays red for more than three months; a Renovate PR in a project stops automerging because python-policy failed on it; Renovate gains a way to run an agent session on its update PRs.
---

# 015: Propagate Template Changes with Copier and Rotate Python from Agent Sessions

## Context

[ADR 008][] chose copier and Renovate's copier manager to carry each template
release to every project, over cruft and manual re-sync; that comparison isn't
reopened here. It also made `python_version` a recorded answer with a static
default, bumped by this repository's [`rotate-python-versions`][repo skill]
skill, so `copier update` never moves a project's Python floor. A released
default reached new projects only: an existing project had no way to learn the
template had moved on, so its maintainer had to notice a Python release and
rotate each library by hand.

The maintainer wants every rotation to start from an agent session in the
project, never from a Renovate PR. Dropping a version means removing compat code
(version checks, fallback imports, backports), which no update tool does.
Renovate would open such PRs today: its github-actions manager reads
`actions/setup-python`'s `python-version` as a dependency named `python`
([known actions][]), and the generated `build.yml` pins the newest version as a
literal in three jobs.

A nudge to rotate has to reach the maintainer without costing anything else.
Three forces bear on where it lives:
- A warning annotation notifies nobody.
- Renovate merges its own PRs (the Terraform module sets
  `allow_auto_merge = false`, so GitHub's auto-merge is off), and only once no
  check run on the branch has failed; it counts a skipped run as passing
  ([Renovate's GitHub platform][]). ADR 013 relies on that for the weekly lock
  refresh.
- `README.rst` shows `build.yml`'s badge, so a failing job there reads publicly
  as "build failing".

ADR 008 rejected cruft partly because "a `cruft check` in CI turns every
unrelated PR red the moment the template releases", and settled that drift
shows "as a Renovate PR, never as a CI job". Any CI nudge contradicts that
claim, so this ADR restates ADR 008 with the claim narrowed.

## Options

### Option 1: Do nothing

ADR 008 as it stands.

**Cons:** A project lags until someone notices; Renovate's `python-version` PRs
move CI without `requires-python` or compat code.
**Risks:** Libraries drift to different ranges, with nothing that records which
are behind.

### Option 2: A template policy, applied by agent sessions, with a separate nudge workflow (Accepted)

`copier.yml` gains `python_policy`, a `when: false` question, so every template
release re-renders it in every project and no answer records it.
`python_version` stays recorded and defaults to it. A `python-policy.yml`
workflow compares the two rendered values and fails while the project is
behind; it isn't part of `build.yml`, so `gate` doesn't need it. It skips every
branch under `renovate/` except the template-update one, whose name carries
`cookiecutter-py` from the recorded `_src_path`. A Renovate rule disables
updates to the `python` dependency, in generated projects and in this
repository.

**Cons:** The check stays red on every PR from the update that raises the policy
until the rotation lands. The skip matches branch names, so a project that
changes Renovate's `branchPrefix` loses it.
**Risks:** A red that lasts trains the maintainer to ignore it.

### Option 3: A computed `python_version`

Each template release moves every project's range in its update PR.

**Pros:** No lag and no separate step.
**Cons:** Compat code stays behind, and a project can't hold its range while a
dependency lacks wheels for a new version.

### Option 4: A recorded lag answer

Record how many releases a project lags the policy, defaulting to zero, and
derive its range from the policy minus the lag.

**Cons:** A default of zero rotates every project on update, as Option 3 does; a
high default leaves new projects behind. No default suits both.

### Option 5: The nudge as a `build.yml` job

As Option 2, but the job sits in `build.yml`, and `gate` either needs it or
tolerates its failure.

**Cons:** Needing it blocks every merge, a security fix's included, until a
session rotates. Tolerating it still stalls Renovate's automerge, which reads
every check run, and turns the README badge red.

## Decision

Option 2. It is the only option that leaves the rotation, and so the
compat-code removal, to an agent session, while still telling each project when
it is due. Options 3 and 4 move the range without the code, or can't default it,
and Option 5 costs merges, automerges or the badge.

The nudge is a failing check because a red check is what reaches the
maintainer: it shows on the template-update PR they review anyway, and every
later run they push notifies them. It is the one CI job that reports a project
lagging the template, and it takes on the cost ADR 008 rejected the `cruft
check` for: every PR goes red once the template releases. It accepts that for
one value, the one only a session can move, and keeps the rest of that check's
cost out: it blocks no merge, and Renovate's own PRs, which merge themselves
only while no check has failed, skip it.

Renovate's Python updates are disabled by dependency name rather than by file,
so a new workflow, or another manager that reports `python`, is covered without
a further rule.

ADR 008's decision otherwise stands, restated here. The template is bound by
these constraints, each of which an update path depends on:

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
  `python_policy` is computed because it must follow the template, and
  `python_version`, `copyright_year` and `copyright_holder` are recorded
  because they mustn't. `python_version` isn't read from the host interpreter
  either: that needs an unsafe extension, and would move the floor whenever
  Renovate's runner had a different Python.
- **Symlinks are preserved** (`_preserve_symlinks: true`).
- **Releases are bare semver tags** (`1.0.0`), matching phx-claude-siat's.
- **Drift in template files shows as a Renovate PR, never as a CI job**, so a
  template release blocks no unrelated PR. The `python-policy` workflow is the
  one exception, on the terms above.

`test/` bakes the template with copier and checks the output, and CI bakes a
project under every supported Python version and runs its own lint, type-check,
test and docs build. Projects support the policy's three most recent minor
releases. Both restate ADRs 004 and 001, which stay superseded.

## Consequences

- ADR 008 is superseded by this ADR.
- A template release that raises `python_policy` reaches every project as its
  usual update PR. That PR keeps `python_version` and turns `python-policy` red;
  the project's `rotate-python-versions` skill then re-answers with
  `copier update --data`, runs `uv lock` and removes compat code.
- This repository's rotation changes `python_policy`'s default, not
  `python_version`'s, which defaults to it.
- `gate` and ADR 009's job list are unchanged, since `python-policy` lives in a
  workflow of its own.
- A project that must lag on purpose, say for a dependency without wheels, stays
  red until it can rotate.
- The recorded `version` answer seeds `__version__` in a new project only, and
  goes stale once the release skill moves the real version on; nothing should
  read it.
- Every question added after 1.0.0 needs a default, or Renovate's `--defaults`
  run fails on it.
- Each library is adopted once with `copier copy` and a hand reconciliation;
  only after that do template releases arrive as PRs.

[ADR 008]: 008-propagate-template-changes-with-copier-and-renovate.md
[known actions]: https://github.com/renovatebot/renovate/blob/main/lib/modules/manager/github-actions/known-actions/github-releases.ts
[Renovate's GitHub platform]: https://github.com/renovatebot/renovate/blob/main/lib/modules/platform/github/index.ts
[repo skill]: ../../.agents/skills/rotate-python-versions/SKILL.md
