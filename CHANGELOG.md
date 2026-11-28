# Changelog

Template releases, newest first. Renovate quotes an entry in every generated project's
template-update PR, so list only what a generated project receives.

Each entry is a `## X.Y.Z - YYYY-MM-DD` heading, a one-line theme, a blank line, then the
changes. `## ` headings are for release entries only, so there is no `Unreleased` section.
Each version must be newer than every earlier one. When `develop` merges into `main`, the
release workflow tags the merge commit from the top entry, with `X.Y.Z: <theme>` and the
changes as the tag's annotation, and publishes a GitHub Release (ADR 017). The tag keeps
the text as merged; a later edit here changes only what later Renovate PRs quote.

## 2.1.0 - 2026-11-28

Renovate config validation in CI, and module v1.2.0

- `infra/github/` pins the todofixthis Terraform module at v1.2.0 ([release notes](https://github.com/todofixthis/terraform-github-repository/releases/tag/v1.2.0)). Its tag ruleset's address moves to `module.repository.github_repository_ruleset.tags_release[0]`, and existing state moves by itself, so a repo already applied plans `tags_release has moved to …tags_release[0]` and no change. If its `infra/github/imports.tf` is still there, remove it first (2.0.0's step 6): an import naming the bare `tags_release` fails the plan with "The target resource is using count". Plan this update's PR by hand and apply from `develop` after it merges, as for any module update. A repo adopting on this update follows 2.0.0's steps, but imports a tag ruleset, if it has one, to `tags_release[0]`. The module also stops creating rulesets for a private repo, which GitHub Free refuses; `main.tf` still sets no visibility, so a private repo still can't adopt.
- `build.yml` gains a `renovate` job, which `gate` needs. It runs Renovate's own validator with `--strict` on `renovate.json`, at a version pinned in the workflow (cookiecutter-py ADR 026). If this update's `gate` fails on it, fix what the job's log names in `renovate.json` on the PR. `renovate.json` gains the manager and rule for that pin: Renovate bumps the validator pin's minor and patch releases monthly, merging once `gate` passes, and a major waits for review. npm packages also wait three days after release before Renovate offers them. AGENTS.md gains the command to run the validator locally.
- The `release` skill reads the signing key's fingerprint with `grep` and `cut` rather than `awk`. Claude Code replaced `awk`'s `$1` and `$2` field references when the skill was invoked with arguments, which left the fingerprint empty or broke the command. When the signing key looks unpublished, it also says to check for a `curl` error before reporting that.
- The `release` skill counts moving `[project] dependencies` to a new major of a runtime dependency as a breaking change, so the skill asks for a major bump, or an ADR recording why a smaller one stands, and a migration guide naming the dependency and its old and new majors.

## 2.0.0 - 2026-11-27

Manage the repo's GitHub settings with Terraform

- `infra/github/` manages the repo's GitHub settings through the todofixthis Terraform module, pinned to v1.1.0: merge methods, features, security settings, and the rulesets requiring `gate` (cookiecutter-py ADR 025). `main.tf` is template-owned. The project's own description, homepage and topics live in `terraform.tfvars`, which copier writes on first copy only, so template updates keep them. State stays on the maintainer's machine, gitignored, and CI runs no plan: plan by hand before merging a PR that changes `main.tf` or `terraform.tfvars`, or a Renovate PR updating the module or provider, and apply from `develop` after it merges. Renovate's weekly lock-file maintenance PR needs no plan. AGENTS.md's new "GitHub settings" section tells agents the same, and never to apply.
- Renovate no longer offers the GitHub provider's major versions, since the module owns that constraint.
- The phx-adr pin moves to 9.2.0.

Don't merge this update's PR until the repo is adopted on it, or the project carries `infra/github/` with no state behind it. A private repo can't adopt, since GitHub Free refuses rulesets on one, and `main.tf` sets no visibility, so its plan would make it public. On the PR, following the module README's "Adopting an existing repo":

1. Sync `develop` and `main` locally, and list the repo's rulesets: `gh api repos/<owner>/<repo>/rulesets -q '.[] | "\(.id) \(.name) \(.target)"'`.
2. Set `infra/github/terraform.tfvars` to the repo's live description, topics and homepage, writing any `\` in the description as `\\`, `"` as `\"`, `${` as `$${` and `%{` as `%%{`. The seeded docs URL may not exist yet; `homepage_url = null` keeps none.
3. Put the README's `import` blocks in a file of the project's own, `infra/github/imports.tf`, since `main.tf` is template-owned. Rulesets import as `<repo>:<id>`: the one on `develop` to `module.repository.github_repository_ruleset.trunk["develop"]`, the one on `main` to `trunk["main"]`, and a tag ruleset, if any, to `tags_release`.
4. Plan from the PR branch (`terraform -chdir=infra/github init -input=false` then `plan`). It should show six imports (the repo, its alert and Dependabot settings, its default branch and both trunk rulesets; seven with a tag ruleset), creates only for `terraform_data.push` and any ruleset you didn't import (usually `tags_release`), and in-place updates for the rest. Read the repo's own diff as closely as the rulesets', since an unintended description change shows as an ordinary update, and stop if anything is replaced or destroyed. Commit the `.terraform.lock.hcl` that `init` wrote, then merge.
5. Apply from an up-to-date `develop`, and delete any hand-made ruleset you didn't import.
6. Remove `imports.tf` in a follow-up PR, whose plan should show no changes.

A project already managing its settings with the module by hand, like filters-iso, has no imports to add: its `main.tf` conflicts, so take the template's, move its values into `terraform.tfvars`, and its plan should show no changes.

## 1.7.0 - 2026-11-26

Fail docs builds on unresolved cross-references

- Projects with their own docs site: `docs/conf.py` sets `nitpicky = True`, so the strict docs build (`-W`) also fails on a Python cross-reference Sphinx can't resolve, which otherwise renders as plain text (cookiecutter-py ADR 024). Run `uv run sphinx-build -E -n docs /tmp/nitpicky` to list the warnings this update's CI will fail on. Document your own TypeVars and aliases in your API docs (the comment above `nitpicky` says how) rather than ignoring them; that can land before this update. In this update's PR, add an `intersphinx_mapping` entry for a dependency with Sphinx docs, and list in the new `nitpick_ignore` only a third-party target no mapped inventory resolves, as `(role, target)` copied from the warning; committing to Renovate's branch stops it rebasing the PR, so merge it promptly. Those `conf.py` lines are your project's own: keep them through later template updates

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
