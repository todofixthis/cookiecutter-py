# Leave the Development Status classifier out of generated projects

Approved 2026-11-24.

## Intent

A reviewer of phx-filters' alpha releases found `4.0.0a2` on PyPI declaring
`Development Status :: 5 - Production/Stable`. The template never added that classifier;
projects carry it by hand from before the template, so it goes stale whenever the version
does. Stop stating the development status twice, so the classifier cannot contradict the
version.

## Evidence

Checked 2026-11-24:

- pip 24.0 and uv 0.13.10 both resolve `phx-filters` to `3.7.0`, and to `4.0.0a2` only
  with `--pre`/`--prerelease=allow` or a pre-release specifier.
- PyPI's templates (`warehouse/templates/includes/packaging/project-status.html` and
  `project-release-history.html`) label a release "Pre-release" from `is_prerelease`,
  which comes from the version, not the classifier.
- PyPI's search indexing (`warehouse/search/tasks.py`) indexes each project's latest
  stable release ahead of any pre-release, so the classifier's search facet never reflects
  a pre-release while a stable release exists.

## Goals and non-goals

- Goal: a generated project's `pyproject.toml` tells whoever edits `classifiers` to leave
  `Development Status` out, and why.
- Goal: a test fails if the template ever renders a `Development Status` classifier.
- Non-goal: removing the classifier from existing projects. Each project drops it in its
  own repository.
- Non-goal: marking which `pyproject.toml` fields a project owns. Deferred to
  `docs/backlog/`.

## Approaches

1. Have the release skill set the classifier from the version at each bump. Rejected: it
   maintains a value pip, uv and PyPI's labels ignore, and that search reads only from the
   stable release.
2. Derive it at build time with a Hatchling metadata hook. Rejected for the same reason,
   and because `classifiers` would become dynamic wholesale, moving every project's
   classifiers into a `[tool.…]` table: a breaking change and build-time code in every
   project.
3. Leave the classifier out (picked). The version's PEP 440 pre-release segment already
   carries the status, to every tool that acts on it.

## Design

- A comment above `classifiers` in `template/pyproject.toml.jinja`, where an editor meets
  it.
- A test in `test/test_bake.py` asserting no baked `classifiers` entry starts with
  `Development Status`.
- An ADR recording the decision, so options 1 and 2 aren't re-proposed.
- A backlog item for the field-level ownership of `pyproject.toml`.
- The next release's `CHANGELOG.md` entry gains a bullet telling projects to drop the
  classifier. Release prep writes it, not this change.
