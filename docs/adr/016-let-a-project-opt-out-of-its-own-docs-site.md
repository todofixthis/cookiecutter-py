---
status: Accepted
date: 2026-11-16
scope: [copier.yml, template/, scripts/template_owned.py, test/, .github/workflows/ci.yml, AGENTS.md]
summary: A recorded docs_site question (default yes) decides whether a generated project gets its own Sphinx/ReadTheDocs site; answering no skips the Sphinx files, .readthedocs.yaml and docs_build hook through conditional file names (`[% if docs_site %]name[% endif %]`, the form any new docs-site file takes), drops the docs CI job and Sphinx dependencies, keeps readthedocs_slug as the ReadTheDocs site that documents the project (another project's, such as filters' for filters-iso), and makes every instruction to build, edit or link the site conditional, wherever it sits; not an unpublished Sphinx site, not one ReadTheDocs site per project, not local deletion.
revisit-when: A project wants its own docs site hosted somewhere other than ReadTheDocs; every project that answered docs_site no switches to yes or stops taking the template; copier stops skipping a file whose name renders empty, or stops removing on update a file the new answers no longer render.
---

# 016: Let a Project Opt Out of Its Own Docs Site

## Context

Every project the template generates gets a Sphinx site: `docs/conf.py`,
`docs/index.rst`, `docs/api.rst` and `docs/Makefile`, a `.readthedocs.yaml`, a
`docs` job in `build.yml` that `gate` needs, the `docs_build` pre-commit hook
([ADR 007][]), Sphinx in the `dev` and `ci` groups, and a `Documentation` URL
on `<readthedocs_slug>.readthedocs.io`. The README, the release skill (whose
migration guides are Sphinx pages linked from ReadTheDocs), the
rotate-python-versions skill and AGENTS.md all assume that site.

filters-iso is the next library to adopt the template, and has no docs site.
Its user docs are prose in filters' [`extension_filters.rst`][], beside the
django extension's, and its README and PyPI `Documentation` URL point there.
Nothing autodocs its docstrings.

## Options

### Option 1: Do nothing

Each project adopts the docs files as they are; an extension documented in
filters sets up its own ReadTheDocs project with an autodoc API page, and
filters' docs link to it.

**Pros:** No template change.
**Cons:** A ReadTheDocs project per extension to create and keep; a user
installing `phx-filters[iso]` reads half the story in filters' docs and the
API on another site.
**Risks:** The prose in filters and the extension's own site drift apart.

### Option 2: A recorded `docs_site` question (Accepted)

`docs_site` (bool, default yes) is recorded in `.copier-answers.yml`.
Answering no skips the Sphinx files, `.readthedocs.yaml` and
`.autohooks/docs_build.py` through conditional file names, which copier skips
when they render empty; drops the `docs` job from `build.yml` and `gate`, the
`docs_build` hook and Sphinx from `pyproject.toml`. Every project's docs are
on ReadTheDocs, so `readthedocs_slug` still sets the `Documentation` URL,
naming the site that documents a no project: filters-iso answers `filters`. Docs instructions elsewhere become conditional too:
Jinja blocks in the README and the release and rotate-python-versions skills,
and prose naming the condition ("where `.readthedocs.yaml` exists") in
AGENTS.md, which isn't rendered. A no project keeps migration guides as
`docs/upgrading_to_v<major>.rst`, linked from its README and read on GitHub.

**Pros:** Existing projects keep their sites, since `--defaults` answers yes
on update.
**Cons:** Every template file touching docs carries a condition, and the
template-owned rule must list a conditional file only when it renders. CI
bakes one more variant, on the newest Python only.
**Risks:** An instruction assuming a docs site passes both bakes unless a
test's pattern names it.

### Option 3: Make only the Documentation URL an answer

Keep every Sphinx file and the `docs` job as an unpublished check that
docstrings render, and let the `Documentation` URL and README badge point
elsewhere.

**Pros:** One question, no conditional files, no second bake.
**Cons:** A no project carries a `.readthedocs.yaml` and a two-page site
nobody reads, and the release skill still writes migration guides into it.

### Option 4: Projects delete the docs files locally

Each extension adopts the template, deletes the docs files and edits the rest,
and records the divergence in its own ADR.

**Pros:** No template change.
**Cons:** Every template release touching a deleted or edited file conflicts
in the update PR, in every such project.
**Risks:** A conflict resolved by taking the template's side quietly restores
the docs.

## Decision

Option 2. Where a project's docs live is a fact about the project, which is
what copier answers record. Option 4 encodes the same fact as a standing
conflict, Option 1 splits one library's docs across two sites to suit the
template, and Option 3 keeps machinery that publishes nothing while its
instructions still send migration guides into it.

AGENTS.md stays identical across projects, as [ADR 010][] decided, by naming
its condition in prose rather than becoming a rendered file.

## Consequences

- A template change touching docs must keep the no variant right: the bake
  tests and CI's `generate` job cover both answers. Tests fail when a no bake's
  `docs/` holds anything but `adr/`, or when a file other than AGENTS.md names
  the docs build, the index or conf page, the toctree or the default
  ReadTheDocs slug.
- `scripts/template_owned.py` wraps each conditional file's entry, in the
  rule's `paths:` and its seed list, in the same condition, so a project never
  lists a file it lacks ([ADR 012][]); `SEED_FILES` and this repo's AGENTS.md
  spell such a seed with its `[% if %]` marker.
- A `[` in a file name reads as a glob to the ADR tool, so ADRs naming these
  files scope `template/` instead: ADRs 002 and 006, which a lookup on any
  template file now returns.
- In a no project nothing checks that docstrings render in Sphinx; AGENTS.md's
  docstring rules still apply but go unenforced. Its sdist leaves out `docs/`,
  migration guides included.
- `copier update --data docs_site=…` switches a project's answer: copier adds
  or deletes the files, deleting a locally edited seed without a conflict and
  leaving any project-authored page in `docs/` behind. Switching to no also
  needs `--data readthedocs_slug=…` naming the site that documents it.
- A no project's `Documentation` URL is a ReadTheDocs site's root, not a page
  or anchor within it; a deeper link belongs in its README, which it owns.

[ADR 007]: 007-check-the-docs-build-in-the-pre-commit-hook.md
[ADR 010]: 010-split-agents-md-into-templated-and-project-parts.md
[ADR 012]: 012-generate-a-path-scoped-rule-naming-template-owned-files.md
[`extension_filters.rst`]: https://github.com/todofixthis/filters/blob/develop/docs/extension_filters.rst
