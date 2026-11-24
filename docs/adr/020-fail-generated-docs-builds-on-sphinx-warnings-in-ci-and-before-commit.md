---
status: Accepted
date: 2026-11-23
scope: [.github/workflows/ci.yml, template/.agents/skills/release/, template/.autohooks/, template/.github/workflows/build.yml.jinja, template/AGENTS.md, template/README.rst.jinja, template/pyproject.toml.jinja]
summary: A generated project with its own docs site fails on any Sphinx warning both before commit, through the docs_build autohooks plugin running sphinx-build -W -E on staged docs and docstring changes only, and in CI, whose docs job runs make html with SPHINXOPTS=-W, as this repository's bake of the project and every documented docs-build command do; neither check alone, and never a lenient build left to ReadTheDocs' fail_on_warning after merge.
revisit-when: A generated project's autohooks pre-commit chain grows a cheaper way to catch a broken docs build than a full Sphinx rebuild; lock-refresh PRs repeatedly go red on warnings or intersphinx fetches unrelated to the project's own docs.
---

# 020: Fail Generated Docs Builds on Sphinx Warnings in CI and Before Commit

## Context

[ADR 007][] gave every generated project with a docs site a `docs_build`
autohooks plugin. It runs `sphinx-build -W --keep-going -E` when a staged
file under `docs/*.rst`, `docs/conf.py` or `src/*.py` could affect the docs,
matching ReadTheDocs' `fail_on_warning`, which runs only after merge. It
kept the project's CI docs job, and this repository's bake of it, lenient
(`make html`, which exits 0 on a warning), reasoning that `-W` there "would
only duplicate what this hook already caught one commit earlier".

That holds only for commits that run the hook. [ADR 013][] since made
Renovate refresh every project's `uv.lock` weekly and merge the refresh
unattended once CI passes. No Renovate PR runs a pre-commit hook, and nor
does an edit in GitHub's web editor. A refresh that bumps Sphinx or its
theme into a new warning passes `gate`, merges, and breaks the published
docs.

Verified in a project baked from this repository: an unresolved `:ref:`
fails `make html SPHINXOPTS=-W` with exit 2, while plain
`make html` exits 0; the unmodified docs pass both. An orphaned page, which
the release skill's migration-guide check exists to catch, also only warns.

## Options

Options 2 and 3 both make CI fail on a warning, so both turn an
`intersphinx` fetch that fails in CI into a red job unrelated to the
change; that shared cost does not rank them. ReadTheDocs' pull-request
preview builds are a dashboard setting a template can't ship or `gate`
require, so they are no option here.

### Option 1: Do nothing

Keep 007: the hook before commit, a lenient CI build.

**Pros:** CI never goes red on an upstream or network warning.
**Cons:** Every Renovate PR merges past a docs warning on a green `gate`,
the lock refresh unattended, which surfaces only as a failed ReadTheDocs
build on the default branch.

### Option 2: `-W` in CI as well as the hook (Accepted)

Keep 007's hook and add `SPHINXOPTS=-W` to the generated project's docs
job, to this repository's bake of it, and to every docs-build command the
template documents. Since Sphinx 8.1, `-W` finishes the build and reports
every warning before failing; `--keep-going`, which once did that, is a
hidden no-op the hook drops too.

**Cons:** The hook still fails a docs-affecting commit made offline, or
while `intersphinx` can't fetch its inventory, for a reason unrelated to
the change; `--no-verify` is the escape hatch.

### Option 3: `-W` in CI instead of the hook

Drop the `docs_build` plugin and rely on CI.

**Pros:** No Sphinx build at commit time, and none of the hook's offline
failures.
**Cons:** A human finds a broken docs build a push later, after the full CI
round trip, the delay 007 removed.

## Decision

Option 2. The hook stays the fast check for whoever commits by hand; CI
becomes the one check every PR meets, bots included, before anything
merges. 007's argument against `-W` in CI assumed every commit ran the
hook, which ADR 013's automerge no longer meets. A documented docs-build
command that ignores warnings would report success on a build CI fails,
so the commands in AGENTS.md, the README and the release skill pass `-W`
too.

What 007 decided about the hook stands, restated here:

- It runs only when a staged file is a docs source or a docstring's module,
  since nothing else can break a Sphinx build, so other commits pay
  nothing. Those patterns are an allowlist: a new kind of docs source needs
  adding by hand.
- It keeps `-E`, a full re-read: an incremental build keeps targets an
  unchanged file registered earlier, and can miss a warning another file
  now raises against them.

## Consequences

- The template's `docs` job, `ci.yml`'s build of the baked project's docs,
  and the docs-build commands in the template's AGENTS.md, README and
  release skill pass `SPHINXOPTS=-W`; the `docs_build`
  plugin and its `pyproject.toml` entry cite this ADR.
- A Sphinx or theme release that adds a warning, or an `intersphinx` fetch
  that fails, turns the weekly lock refresh red instead of merging it, and
  the refresh waits for someone to fix the docs or re-run the job. That
  holds back every transitive update meanwhile; if it keeps happening,
  ADR 013's trigger on refresh PRs that repeatedly fail CI has fired.
- Generated projects receive the change as a template update; a project
  whose docs already warn goes red on that update's PR, before merge, and
  fixes its docs there.
- A project without its own docs site has no `docs` job or hook, and is
  unaffected.

[ADR 007]: 007-check-the-docs-build-in-the-pre-commit-hook.md
[ADR 013]: 013-refresh-lock-files-with-renovate-not-direct-pins.md
