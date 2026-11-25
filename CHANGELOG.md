# Changelog

Template releases, newest first. Renovate quotes an entry in every generated project's
template-update PR, so list only what a generated project receives.

Each entry is a `## X.Y.Z - YYYY-MM-DD` heading, a one-line theme, a blank line, then the
changes. `## ` headings are for release entries only, so there is no `Unreleased` section.
Each version must be newer than every earlier one. When `develop` merges into `main`, the
release workflow tags the merge commit from the top entry, with `X.Y.Z: <theme>` and the
changes as the tag's annotation, and publishes a GitHub Release (ADR 017). The tag keeps
the text as merged; a later edit here changes only what later Renovate PRs quote.

## 1.6.1 - 2026-11-25

Release steps that work with a dynamic version

- `README.rst`'s release steps set `__version__`, merge it into `main` through `develop`, then build and tag from an up-to-date `main`. The old steps ran `uv version`, which fails on the template's dynamic version, and tagged without committing the bump. The update also adds the blank line that makes the checklist under "Write a description" render as a list. If your project already rewrote these steps, the hunk may conflict: keep your steps if they already commit the bump before tagging, adding that blank line, otherwise take the template's

## 1.6.0 - 2026-11-25

A release skill that works under pull-request-only rulesets

- The `release` skill bumps the version through a pull request into `develop`, stopping until it merges, then opens the release PR with `--head develop`; its last step, rebasing `develop` onto `main`, is gone. A ruleset requiring pull requests and allowing only merge commits rejected both the direct push and the rebase. If your `.agents/rules/project.md` overrides either step, delete that override; if the skill's hunks conflict, take the template's side
- Projects with their own docs site: the `release` skill links a migration guide from `README.rst` by its ReadTheDocs URL rather than a relative path, which breaks on PyPI. Existing upgrade notices in `README.rst` keep their links, so check them
- New projects' `.github/workflows/project.yml` says a conditional step skips only on an explicit `'false'`, so a missing or misspelt output runs it. The file is written once, so an existing project's copy is unchanged: check its own skip conditions

## 1.5.1 - 2026-11-25

Leave out the Development Status classifier

- `pyproject.toml` gains a comment above `classifiers` saying to leave out `Development Status`: the version's pre-release segment already states it, and a hand-kept classifier goes stale, as `5 - Production/Stable` does on an alpha (cookiecutter-py ADR 023). The template never adds that classifier, so delete any `Development Status` entry your project added itself; `copier update` won't remove it. If that hunk conflicts, keep your own entries and take the comment above `classifiers`
- The `rotate-python-versions` skill no longer says the template derives Python version classifiers, since it renders none, and tells the agent to update any version classifiers the project added itself

## 1.5.0 - 2026-11-25

Fail CI on committed conflict markers

- The `lint` CI job gains a step that fails when a tracked file has a line starting with `<<<<<<<` or `>>>>>>>`, so a template update whose merge conflicted, this one included, fails `gate` until someone resolves the markers on its branch (cookiecutter-py ADR 022). A commit there by anyone but Renovate stops Renovate rebasing the PR, so merge it promptly. The step ignores `=======`, a common reStructuredText heading underline. If it fails on this update, resolve the conflict markers it lists, and underline any heading drawn with seven `<` or `>` characters with another character. The step has no exclusion list, so a project that must commit such a line raises it upstream
- In `pyproject.toml`, the comments on the autohooks `pre-commit` array sit above it, where `autohooks activate --force`, which rewrites the array sorted onto one line, can't drop them; the comment on `docs_build` moves there from inside the array. The comments also note that no hook may rely on running before another. A project that edited its `pre-commit` list, or ran `autohooks activate --force`, may see that hunk conflict: keep its own entries, and take the comments above the array

## 1.4.0 - 2026-11-23

Strict docs CI, a project-owned CI workflow, and a docs admonitions rule

- Projects with their own docs site: the docs CI job and the documented docs-build commands build with `-W`, so a Sphinx warning fails `gate` before merge rather than only on ReadTheDocs, and the docs pre-commit hook drops `--keep-going`, which Sphinx 9 ignores (cookiecutter-py ADR 020). If the `docs` job fails on this update, fix the warnings it reports; ReadTheDocs was already failing on them
- `build.yml` gains a `project` job that `gate` needs, calling a new `.github/workflows/project.yml`: a reusable workflow written once with a placeholder job, which the project then owns, so a job of the project's own blocks merges (cookiecutter-py ADR 021)
- The template-owned rule sends a project's extra CI jobs to `project.yml`; move any job you put in a workflow of your own there to make it block merges. `project.yml` may ask for no permission beyond `contents: read`. A project that already had a `.github/workflows/project.yml` keeps it, and if it isn't a `workflow_call` workflow every CI job fails: rename it on the update's branch and re-run `copier update` to get the stub
- Projects with their own docs site get `.agents/rules/docs-admonitions.md`, on when and how to use RST admonitions in `docs/`
- The seed docs index's Python-support note becomes prose; a project that changed its `docs/index.rst` may see that hunk conflict, so keep its own version. `.gitignore` spells "optimised"

## 1.3.2 - 2026-11-22

Correct the ADR citations generated projects carry

- AGENTS.md, renovate.json and the adrs job comment in build.yml cite cookiecutter-py ADR 018 for the phx-adr pins, not the superseded ADR 009
- AGENTS.md and the adrs job comment cite ADR 019 for the rule against a repo-local ADR tool, vendored copy or pre-commit hook running ADR tooling
- Comments and descriptions only, no behaviour changes

## 1.3.1 - 2026-11-21

phx-adr 9.1.0 and setup-uv 10.4.0 for generated projects

- phx-adr 9.1.0 in the adrs job and AGENTS.md (skill link included), and setup-uv 10.4.0 in build.yml

## 1.3.0 - 2026-11-18

Let a project do without its own docs site

- docs_site question: no leaves out the Sphinx site, .readthedocs.yaml, the docs CI job and the docs_build hook (ADR 016)
- readthedocs_slug names the site that documents a project without its own; no default then
- Docs instructions in the README, the release and rotate-python-versions skills and AGENTS.md follow docs_site
- phx-adr 9.0.1 in the adrs job and AGENTS.md

## 1.2.0 - 2026-11-17

Python policy and answerable template-edit rule

- Template-owned rule asks whether a change's reason is project-specific (ADR 014)
- .gitignore replaces venv/ with .venv.*/
- python_policy sets the Python range; agent sessions rotate to it (ADR 015)
- python-policy workflow fails while a project lags, outside gate
- Renovate no longer bumps Python
- phx-adr 9.0.0 in the adrs job and AGENTS.md

## 1.1.0 - 2026-10-24

Template gaps from class-registry's adoption

- readthedocs_slug question (PyPI name without phx-)
- Release skill publishes the signing key's fingerprint
- CI and ReadTheDocs leave out the dev group
- lint job: ruff check and black --check
- Renovate lock-file maintenance, automerged on green, behind a 3-day uv release delay (ADR 013)

## 1.0.0 - 2026-10-17

First copier release

cookiecutter-py moves from cookiecutter to copier, so template releases now
reach generated projects as Renovate PRs (ADR 008).

- Projects record their answers in .copier-answers.yml, including
  python_version, copyright_year and copyright_holder, so updates never
  move them unasked.
- Generated CI gains `adrs` and `gate` jobs; `gate` is the single required
  check, and one Renovate manager keeps the phx-adr pin current (ADR 009).
- AGENTS.md is fully templated; each project's own rules live in
  .agents/rules/project.md, which copier writes only once (ADR 010).
- A generated, path-scoped rule names every template-owned file, so agents
  send template-wide changes upstream (ADR 012).
- Fixes from the 2026-10-10 drift audit: ReadTheDocs syncs into its own
  environment, the rotate skill searches hidden directories, and the
  release skill writes its notes file. Sphinx moves to 9 and setup-uv to
  10.3.0.

Existing libraries adopt this release with `copier copy`, after moving
their local AGENTS.md sections into .agents/rules/project.md.
