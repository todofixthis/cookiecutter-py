# cookiecutter-py

[![CI](https://github.com/todofixthis/cookiecutter-py/actions/workflows/ci.yml/badge.svg)](https://github.com/todofixthis/cookiecutter-py/actions/workflows/ci.yml)

A [copier](https://copier.readthedocs.io/) template for new Python projects, wired up with `uv`, `hatchling`, Sphinx/ReadTheDocs docs, and the shared `phx` agent tooling from the start.

## Usage

```bash
uvx "copier>=9,<10" copy https://github.com/todofixthis/cookiecutter-py.git my-python-project
```

copier prompts for each answer; all but the short description and copyright year have a default. Answering `docs_site` no (no Sphinx site of its own) also needs `readthedocs_slug` naming the site that documents the project, such as `filters` for filters-iso (ADR 016). `python_version` (default `3.14`, the template's `python_policy`) is the newest Python release the project supports, along with the two before it. A later release that raises the policy turns the project's non-blocking `python-policy` CI job red until an agent session rotates it (ADR 015). copier records the answers in `.copier-answers.yml`, so a later template release can reach the project as a Renovate PR. Use the full URL, not the `gh:` shorthand: copier records the source verbatim, and Renovate can't resolve `gh:`.

## Creating the GitHub repo

The project's `infra/github/` creates the GitHub repo and applies the todofixthis settings through the [todofixthis Terraform module](https://github.com/todofixthis/terraform-github-repository) (ADR 025). You need Terraform 1.9 or later, a GitHub token the provider can use (`GITHUB_TOKEN`, or `gh auth login`, whose token it falls back to), and SSH push access to GitHub; the module README's "Before the first apply" lists the rest. Check `infra/github/terraform.tfvars`, which copier seeded with the description and ReadTheDocs URL, then commit the project on a `main` branch, create `develop` from it, and apply:

```bash
git init -b main && git add -A && git commit -m "Generate from cookiecutter-py"
git branch develop
terraform -chdir=infra/github init -input=false
terraform -chdir=infra/github apply
```

The apply creates the repo, pushes `develop` and `main`, then protects both. If the push fails, say for SSH access, the repo exists with no branches: fix the cause and apply again, which pushes and finishes. Commit the `.terraform.lock.hcl` that `init` wrote, through a PR into `develop`. The state file stays on your machine: back it up, since the next plan needs it. To bring a repo that already exists under the module instead, follow the module README's "Adopting an existing repo".

## After creating the GitHub repo

- **Renovate.** If Renovate is installed for selected repositories only, add the repo at <https://github.com/settings/installations> → Renovate → Configure → Repository access. Until then the repo gets no dependency updates, nor the PRs that bring template releases, and nothing says so.
- **Watching.** Unless the repo already shows as watched, click Watch → All Activity on it. A watch belongs to a person, not the repo, so the todofixthis Terraform module leaves it out by design ([its ADR 005](https://github.com/todofixthis/terraform-github-repository/blob/develop/docs/adr/005-keep-personal-preferences-out-of-the-module.md)).

## What you get

- `uv` + `hatchling` packaging, `pytest` + `mypy --strict` + `ruff`/`black` (via `autohooks`, not the `pre-commit` framework)
- Sphinx docs on ReadTheDocs, GitHub Actions CI (test matrix, type-check, lint, docs build, ADR validation, and a `gate` job aggregating the rest as the one required check), Renovate for dependency/Action updates
- `AGENTS.md`/`CLAUDE.md`, an ADR workflow under `docs/adr/`, and the `phx@todofixthis` skill marketplace enabled out of the box
- A guided `release` skill covering version bumps, GPG-signed release artefacts, and PyPI publishing
- `infra/github/`, managing the repo's GitHub settings through the todofixthis Terraform module, planned and applied from the maintainer's machine (ADR 025)

## Developing this template

See `AGENTS.md` for the dev workflow, including how to bake your working tree into a project (`uv sync --group=dev`, `uv run pytest` bakes the template and checks the output, `uv run mypy test`, `uv run ruff check test`).
