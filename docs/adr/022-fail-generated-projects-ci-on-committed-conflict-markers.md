---
status: Accepted
date: 2026-11-24
scope: [template/.github/workflows/build.yml.jinja, test/]
summary: A generated project's lint CI job fails when any tracked file has a line starting with a seven-character conflict marker (<<<<<<< or >>>>>>>), so a conflicted template update fails gate; it leaves out the ======= separator, which a reStructuredText heading underline matches, and it is not done by requiring Renovate's renovate/artifacts status or by a pre-commit hook.
revisit-when: A generated project needs to commit a line starting with seven < or > characters, such as a reStructuredText heading underlined with them; copier writes its conflict markers in another size or form; lint stops being a job that gate needs.
---

# 022: Fail Generated Projects' CI on Committed Conflict Markers

## Context

[ADR 008][] accepted a risk: a template update that conflicts with a project's local
edits lands as a Renovate PR with the conflict markers committed, and a maintainer must
resolve them before merging. Nothing enforces that. Renovate marks such a PR with a
failing `renovate/artifacts` commit status and a comment, but [ADR 018][] makes `gate` the
only required check in a generated project, and no job that `gate` needs reads file
contents for markers.

This happened in [todofixthis/filters-pydantic#79][], the 1.4.0 update. copier
conflicted on the docs-build step in `README.rst`, and Renovate committed both sides
between `before updating` and `after updating` markers. Every job passed, `gate`
included. `README.rst` is not part of the Sphinx build, and the Python tooling doesn't
validate it, so only a reviewer reading the diff would have caught the markers.

## Options

### Option 1: Do nothing

**Pros:** No new CI step.
**Cons:** A conflicted update is mergeable on a green `gate`, guarded only by Renovate's
comment and a status no ruleset requires.
**Risks:** Markers reach `develop`, and from there a release, in a file no tool validates.

### Option 2: A conflict-marker step in the generated lint job (Accepted)

The `lint` job in `build.yml` gains a step, before it installs anything, that runs
`git grep` over tracked files for a line starting with seven `<` or seven `>` characters,
followed by a space or the end of the line. It fails on a match, and also when
`git grep` itself errors, so a broken check never passes.

**Pros:** It catches markers from any source: copier, a hand merge, or a rebase.
**Cons:** None worth naming: it runs before anything is installed.
**Risks:** A project cannot commit a line the check matches, including a
reStructuredText heading underlined with seven `<` or `>` characters, which RST allows.
The `=======` separator is left out because a heading underlined with seven `=` is
common, so the check relies on the two outer markers, which copier always writes at
seven characters, as git does unless the `conflict-marker-size` attribute is set.

### Option 3: Require the `renovate/artifacts` status

**Pros:** It uses Renovate's own signal, with no template change.
**Cons:** The status exists only on Renovate's PRs, so requiring it blocks every other PR
forever. It is also a second required check, which ADR 018 rules out.
**Risks:** None beyond its Cons.

### Option 4: A pre-commit hook

**Pros:** It fails before the commit, on a maintainer's machine.
**Cons:** Renovate's commits never run a project's hooks, so it misses the case that
prompted this ADR. [ADR 020][] makes the same point about the docs build.
**Risks:** As Option 1.

## Decision

Option 2. Only a CI job reaches a Renovate commit, and only `gate` blocks a merge, so the
check must sit in a job that `gate` needs. `lint` already holds the checks on file
contents that don't run the project's code, so a step there adds no job.

## Consequences

- A conflicted template update fails `gate` until someone resolves the markers on the
  update's branch. A commit there by anyone but Renovate stops Renovate rebasing the PR,
  so the project's maintainer merges it promptly or brings it up to date by hand.
- The step reaches existing projects with the next template release, not an update PR
  already open.
- `test/` runs the baked step against a real conflicted `copier update`, against an RST
  heading underline it must ignore, and against a directory outside git, where it must
  fail.

[ADR 008]: 008-propagate-template-changes-with-copier-and-renovate.md
[ADR 018]: 018-require-gate-everywhere-and-the-release-check-on-main.md
[ADR 020]: 020-fail-generated-docs-builds-on-sphinx-warnings-in-ci-and-before-commit.md
[todofixthis/filters-pydantic#79]: https://github.com/todofixthis/filters-pydantic/pull/79
