# Changelog

Template releases, newest first. Renovate quotes an entry in every generated project's
template-update PR, so list only what a generated project receives.

Each entry is a `## X.Y.Z - YYYY-MM-DD` heading, a one-line theme, a blank line, then the
changes. `## ` headings are for release entries only, so there is no `Unreleased` section.
Each version must be newer than every earlier one. When `develop` merges into `main`, the
release workflow tags the merge commit from the top entry, with `X.Y.Z: <theme>` and the
changes as the tag's annotation, and publishes a GitHub Release (ADR 017). The tag keeps
the text as merged; a later edit here changes only what later Renovate PRs quote.

## 1.3.2 - 2026-11-22

Correct the ADR citations generated projects carry

- AGENTS.md, renovate.json and the adrs job comment in build.yml cite cookiecutter-py ADR 018 for the phx-adr pins, not the superseded ADR 009, and ADR 019 for the rule against a repo-local ADR tool or pre-commit hook; comments only, no behaviour changes

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
