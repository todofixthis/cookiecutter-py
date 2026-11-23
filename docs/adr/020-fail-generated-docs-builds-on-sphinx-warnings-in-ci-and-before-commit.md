---
status: Accepted
date: 2026-11-23
scope: [.github/workflows/ci.yml, template/.autohooks/, template/.github/workflows/build.yml.jinja, template/pyproject.toml.jinja]
summary: A generated project with its own docs site fails on any Sphinx warning both before commit, through the docs_build autohooks plugin running sphinx-build -W --keep-going -E on staged docs and docstring changes, and in CI, whose docs job runs make html with SPHINXOPTS="-W --keep-going", as this repository's bake of the project does; neither check alone, and never a lenient CI build left to ReadTheDocs' fail_on_warning after merge.
revisit-when: A generated project's autohooks pre-commit chain grows a cheaper way to catch a broken docs build than a full Sphinx rebuild; intersphinx fetches routinely fail CI's docs job for reasons unrelated to the change.
---

# 020: Fail Generated Docs Builds on Sphinx Warnings in CI and Before Commit

## Context

[ADR 007][] gave every generated project with a docs site a `docs_build`
autohooks plugin running `sphinx-build -W --keep-going -E` on staged docs
and docstring changes, matching ReadTheDocs' `fail_on_warning`, which runs
only after merge. It kept the project's CI docs job, and this repository's
bake of it, lenient (`make html`, which exits 0 on a warning), reasoning
that `-W` there "would only duplicate what this hook already caught one
commit earlier".

That holds only for commits that run the hook. [ADR 013][] since made
Renovate refresh every project's `uv.lock` weekly and automerge the refresh
once CI passes, and [ADR 015][] delivers template releases as Renovate PRs.
Neither runs a pre-commit hook. A refresh that bumps Sphinx or its theme
into a new warning passes `gate`, merges unattended, and breaks the
published docs. A PR edited in GitHub's web editor skips the hook the same
way.

Verified in a project baked from this repository: an unresolved `:ref:`
fails `make html SPHINXOPTS="-W --keep-going"` with exit 2, while plain
`make html` exits 0; the unmodified docs pass both.

## Options

### Option 1: Do nothing

Keep 007: the hook before commit, a lenient CI build.

**Cons:** Every automerged lock refresh and template update merges past a
docs warning, which surfaces only as a failed ReadTheDocs build on the
default branch.

### Option 2: `-W` in CI as well as the hook (Accepted)

Keep 007's hook unchanged and add `SPHINXOPTS="-W --keep-going"` to the
generated project's docs job and to this repository's bake of it.
`--keep-going` reports every warning in one run rather than stopping at
the first.

**Cons:** A docs warning is now checked twice for a human commit. An
`intersphinx` fetch that fails in CI fails the job for a reason unrelated
to the change; GitHub's runners have network access, so this should be
rare, and a re-run clears it.

### Option 3: `-W` in CI instead of the hook

Drop the `docs_build` plugin and rely on CI.

**Pros:** One check, no Sphinx build at commit time.
**Cons:** A human finds a broken docs build a push later, after the full
CI round trip, which is the delay 007 removed.

## Decision

Option 2. The hook stays the fast check for the people and agents who
commit by hand; CI becomes the one check every PR meets, bots included,
before anything merges. 007's argument against `-W` in CI assumed every
commit ran the hook, which ADR 013's automerge no longer meets.

007's hook decision carries over unchanged, `-E` included, since an
incremental build keeps targets an unchanged file registered earlier and
can miss a warning another file now raises against them.

## Consequences

- The template's `docs` job and `ci.yml`'s step building the baked
  project's docs run `make html SPHINXOPTS="-W --keep-going"`; the
  `docs_build` plugin and its `pyproject.toml` entry cite this ADR.
- Generated projects receive the change as a template update; a project
  whose docs already warn goes red on that update's PR, before merge,
  and fixes its docs there.
- A project without its own docs site has no `docs` job or hook, and is
  unaffected.

[ADR 007]: 007-check-the-docs-build-in-the-pre-commit-hook.md
[ADR 013]: 013-refresh-lock-files-with-renovate-not-direct-pins.md
[ADR 015]: 015-propagate-template-changes-with-copier-and-rotate-python-from-agent-sessions.md
