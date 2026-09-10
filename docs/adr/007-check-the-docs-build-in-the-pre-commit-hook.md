---
status: Accepted
date: 2026-09-10
scope: ["{{ cookiecutter.github_project_name }}/docs/", "{{ cookiecutter.github_project_name }}/.autohooks/", "{{ cookiecutter.github_project_name }}/pyproject.toml"]
summary: Generate projects with a docs_build autohooks plugin that runs sphinx-build -W -E (full re-read, not incremental) on staged docs/docstring changes, matching ReadTheDocs' fail_on_warning rather than the generate-and-validate workflow's lenient build.
revisit-when: A generated project's autohooks pre-commit chain grows a cheaper way to catch a broken docs build than a full Sphinx rebuild.
---

# 007: Check the Docs Build in the Pre-Commit Hook

## Context

[`006`][] enables `autosectionlabel` in generated projects' docs. Neither
this template's own `generate-and-validate.yml` — which bakes a project and
runs `uv run make html` with no `-W` — nor a generated project's own CI
(the same command) would catch a `duplicate label` warning that setting can
produce as a project's docs grow: a warning still exits 0. Verified by
re-baking the template and running that exact command with
`autosectionlabel_prefix_document` temporarily reverted to `False` and a
duplicate heading added: the build reports success regardless. Only
`.readthedocs.yaml`'s `fail_on_warning: true` — which [`006`][] adds, and
which governs the actual published build — would have caught it, and that
build runs after merge, not before.

`class-registry` and `filters`, the two sibling projects this template
already tracks conventions from ([`002`][], [`003`][]), hit this same gap
after enabling `autosectionlabel` and closed it the same way: a
`docs_build` autohooks plugin, alongside each project's existing
`autohooks.plugins.*` pre-commit checks, that runs a strict
`sphinx-build -W` when a staged file could affect the docs.

## Options

### Option 1: Do nothing

**Pros:** No new dependency on Sphinx succeeding at commit time, and no
risk of a network hiccup (e.g. `intersphinx`'s fetch of the Python
inventory) blocking an unrelated commit.
**Cons:** The gap in Context stays open for every project this template
generates — a docs change can pass every check before merge and still
break the published build, caught only after merge, the way it did for
both sibling projects before they added this.

### Option 2: Mirror `generate-and-validate.yml`'s build (no `-W`)

Run `uv run make html` — the same command the template's own CI and a
generated project's CI both run — as a new pre-commit step.
**Pros:** Matches the existing CI check exactly, so there's one build
policy to reason about, not two.
**Cons:** Verified the same way as in Context — it still reports success
on a reintroduced collision. It would not have caught the problem this ADR
exists to prevent.

### Option 3: Run `sphinx-build -W -E` on staged docs/docstring changes (Accepted)

Add a `docs_build` autohooks plugin, matching both siblings' final design,
that runs `sphinx-build -b html -W --keep-going -E` into a dedicated
`docs/_build/precommit` directory — not `docs/_build/html`, which the
documented `make html` workflow also builds into — when a staged file
matches `docs/*.rst`, `docs/conf.py`, or `src/*.py`, the last because
autodoc pulls docstrings into the built API page. `-E` forces Sphinx to
re-read every file rather than trust its saved environment; a persistent
build directory needs this, verified by rebuilding twice in one directory
against the same reverted `docs/conf.py` — `-W --keep-going` alone catches
the reintroduced collision on the first build but, against the second,
warns on none of it, because Sphinx skips re-reading a file it judges
unchanged and reuses whatever it registered last time. `-E` restores the
warning on every build, cold or warm — reproducing exactly the false
negative both siblings' own review rounds found and fixed. The subprocess
carries a timeout, so an unresponsive host can't hang a commit indefinitely.
**Pros:** Verified the same way — `-W -E` turns the reintroduced collision
into a build failure on every run, matching what `fail_on_warning: true`
does on ReadTheDocs. Scoping to staged docs-affecting files, rather than
running on every commit, keeps an unrelated source change from paying for
a Sphinx build it can't break. `-E` discards Sphinx's own saved
environment but not `intersphinx`'s fetched-inventory file, which Sphinx
reads straight off disk under the build directory when present and still
within `intersphinx_cache_limit` days — so the dedicated directory
persisting across commits still caps the network dependency, rather than
paying it on every triggered run.
**Cons:** `-E` means every triggered run re-reads the whole docs tree
rather than only what changed, so this hook costs a full build every time,
not an incremental one. A network hiccup fetching `intersphinx`'s Python
inventory can still turn `-W` into a spurious failure on an otherwise-fine
commit; Sphinx caches that inventory for `intersphinx_cache_limit` days
(unset here, so the Sphinx default) once a fetch has succeeded at least
once, so this bites at most that often, not on every commit — but an
environment that can never reach the inventory URL at all (a firewalled
network, an air-gapped runner) never populates that cache, and fails this
hook on every docs-affecting commit indefinitely, not periodically.
**Risks:** The include patterns (`docs/*.rst`, `docs/conf.py`, `src/*.py`)
are an allowlist, not a rule Sphinx enforces — a future docs source outside
those three patterns (e.g. a generated `.rst` file) would need the list
extended by hand.

## Decision

Option 3, matching what both sibling projects converged on independently
once they hit the same gap [`006`][] opens for a generated project too.
Option 2 reproduces the exact gap this ADR is closing — verified, not
assumed, by replaying it in a freshly baked project. Scoping the check to
staged docs-affecting files, rather than running it on every commit like
`autohooks.plugins.mypy`/`ruff`/`pytest` already do, is deliberate: unlike
those checks, a Sphinx build can only be broken by changes under `docs/` or
by a docstring, so anything else pays nothing for this hook.

## Consequences

- Generated projects ship a new `.autohooks/docs_build.py`, following the
  same shape as each sibling's own plugin, and no-ops when nothing staged
  is relevant. It must keep `-E`: dropping it for speed would silently
  reopen the exact incremental-build gap this ADR verified and closed.
- `{{ cookiecutter.github_project_name }}/pyproject.toml`'s
  `[tool.autohooks]` `pre-commit` list gains `docs_build`.
- A docs or docstring change that would break the ReadTheDocs build is now
  caught at commit time in every generated project, not discovered after
  merge.
- `generate-and-validate.yml` and a generated project's own CI stay lenient
  rather than gaining `-W` themselves, since `-W` failing there would only
  duplicate what this hook already caught one commit earlier.
- A commit made offline, or during an `intersphinx` inventory cache miss,
  can fail this hook on a docs-affecting change for a reason unrelated to
  the change itself; `--no-verify` is the escape hatch, as for any
  pre-commit check.
- Unlike `class-registry`/`filters`, a generated project has no ADR
  tooling of its own (no `adr_index` plugin, no `docs/adr/`), so
  `docs_build.py`'s comments explain the `-E` rationale inline rather than
  citing a decision record a generated project doesn't carry.

[`002`]: 002-generate-projects-with-uv-and-hatchling.md
[`003`]: 003-manage-updates-with-renovate.md
[`006`]: 006-enable-autosectionlabel-with-document-prefixed-labels.md
