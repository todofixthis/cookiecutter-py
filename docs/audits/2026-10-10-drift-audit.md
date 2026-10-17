# todofixthis drift audit — 2026-10-10 (NZT)

> **Superseded as a plan; kept as a dated record.** The findings below describe the
> repositories as they stood on 2026-10-10 and aren't updated. The decisions they called for
> are made:
>
> - copier with Renovate, and no CI drift check (ADR 008);
> - the `gate` and `adrs` jobs and the phx pin (ADR 009);
> - the AGENTS.md split (ADR 010);
> - dynamic versioning for every library (ADR 005);
> - develop/main for filters-pydantic, and archiving data-providers and triggers, both
>   decided while planning #11 and not yet carried out.
>
> [todofixthis/cookiecutter-py#11](https://github.com/todofixthis/cookiecutter-py/pull/11) fixed the template's own findings. A library's findings in files the template owns are fixed by adopting it onto the template with `copier copy`, after moving its local AGENTS.md sections into `.agents/rules/project.md` (ADRs 008 and 010), not by hand. Findings in project-specific content still need fixing by hand: the filters and filters-pydantic AGENTS.md errors, section 8, and paddock's `tests/` and `phx-filters` skill. Before acting on any other finding, check whether a later change has already fixed it.

## Scope and method

**Audited (18):**
- Python libraries: filters, filters-django, filters-iso, filters-pydantic, class-registry, paddock
- Apps: forex-fee-calculator, portfolio, purrductivity
- Templates: cookiecutter-py, cookiecutter-browser-plugin
- Infra and config: terraform-github-repository (branch `feature/module-v1`), phx-claude-siat, config-claude, config-claude-code-cloud, config-paddock
- Dormant: data-providers, triggers

**Excluded:**
- forks and archived repos
- purrductivity-ctf: a deliberate prompt-injection demo, so its agent files are a payload rather than instructions
- config-leash, config-opencode and notion-data: these appear in search results but this session can't reach them

**Method:** shallow clones of each default branch, compared with scripts. `phx-adr check` (8.1.0) was run on every ADR corpus. Live settings came from the GitHub search API. Two subagents diffed the skills and the AGENTS.md files, and I spot-checked their key claims.

**Not checked:** rulesets, merge-method settings and branch protection. The GitHub tools available here can't read them, and that is exactly the layer the Terraform module manages. Run `terraform plan` against each repo once module v1 ships.

## The systemic finding

Most of the drift has one cause. **Fixes are made in leaf repos and never flow back upstream.** cookiecutter-py is meant to be the canonical source, but:

- It is behind the libraries on almost every axis in this report: ADR tooling, ReadTheDocs config, Sphinx version, the setup-uv pin, and the rotate-python-versions skill.
- Nothing carries a template change into projects that were baked earlier. Its own ADR 005 records "matching paddock rather than the template's other five siblings".

Each repo therefore re-solves the same problem in its own way: four repos keep the phx pin current four different ways (section 2). Every fix made locally widens the gap. Without a propagation mechanism, consolidating once will drift again within months.

ADR 008 records the propagation mechanism chosen in response. This finding doesn't explain sections 7 and 8 (settings, stale branches, dormant repos) or why Renovate isn't running in the templates. The Terraform module and housekeeping cover those.

## Findings, by severity

### 1. Defects (broken or will break)

| # | Finding | Where | Fix |
|---|---|---|---|
| 1.1 | **No repo that will adopt the Terraform module has a `gate` job.** The module requires a check called `gate` on `develop` and `main`. Only phx-claude-siat, config-paddock and terraform-github-repository have one. Applying the module to any library would block every PR. | 6 library repos, plus forex and cookiecutter-* | Add a `gate` aggregator job to the template's `build.yml` and to each repo **before** rolling out module v1 |
| 1.2 | **The template's ReadTheDocs config is wrong.** It runs `VIRTUAL_ENV=$READTHEDOCS_VIRTUALENV_PATH uv sync`, which `uv sync` ignores, so dependencies land in `.venv` rather than the ReadTheDocs env. Every library that ships `.readthedocs.yaml` independently fixed this with `UV_PROJECT_ENVIRONMENT=` (uv#10074). Unchanged since 2024-10. | `cookiecutter-py/{{…}}/.readthedocs.yaml` | Port the libraries' line. `generate-and-validate` builds docs locally, so it can't catch this |
| 1.3 | **The template's `rotate-python-versions` stray-reference `rg` silently misses CI.** Without `--hidden` it skips `.github/`, so it reports clean on filters while `build.yml` has 3 hits. | template, class-registry, filters, filters-django, filters-iso, filters-pydantic | Replace the skill wholesale with paddock's, minus its Dockerfile note. It adds `--hidden` and also: classifiers, `uv lock`, keeping the `<4` cap, refusing Pythons with no final release, required check names, and excluding ADRs |
| 1.4 | **ADR corpora fail `phx-adr check` 8.1.0.** cookiecutter-py has 6 errors and cookiecutter-browser-plugin 6, from quoted `scope` values. portfolio has 24 (`tags` instead of `scope`). None of these repos has an `adrs` CI job, so nothing flagged them. | cookiecutter-py, cookiecutter-browser-plugin, portfolio | Fix the frontmatter and add the CI job |
| 1.5 | **Worktree paths aren't gitignored.** paddock's AGENTS.md says `.agents/worktrees/`, filters-iso's says `.worktrees/`, and portfolio's says hand-roll `git worktree add`. The native `EnterWorktree` tool writes `.claude/worktrees/`, which neither paddock nor filters-iso ignores, so a native worktree shows as untracked files that are easy to commit. | paddock, filters-iso, portfolio | Standardise on `.claude/worktrees/` plus the skill (the template's text) |

### 2. The phx-claude-siat ADR-tool pin: one need, four mechanisms

Every repo with an `adrs` job pins `phx-adr` to a commit SHA. The ways of keeping that pin current:

| Mechanism | Repos |
|---|---|
| Hand-kept, no Renovate | filters, class-registry |
| Renovate `git-tags` regex keyed on a `# phx-claude-siat X.Y.Z` comment | filters-django |
| Renovate `git-refs` on the tip of `main` | filters-iso |
| Renovate `github-tags`, trailing `# X.Y.Z`, also bumping AGENTS.md | filters-pydantic, paddock |
| No job at all | template, cookiecutter-browser-plugin, forex, portfolio |

filters-pydantic's own `renovate.json` notes that `git-tags` yields annotated-tag object SHAs, not commit SHAs. If that's right, filters-django's next bump writes an unusable SHA (for 8.1.0 it would write `3045fbc` rather than `0725567`); I haven't verified it against Renovate. The job is named `adr` in filters-pydantic and `adrs` everywhere else. paddock is one release behind (8.0.0), with a Renovate PR open.

**Recommendation:** put the filters-pydantic/paddock form in the template: the `adrs` job, a trailing `# X.Y.Z`, and the `github-tags` manager covering both `build.yml` and AGENTS.md. Record it in a template ADR and propagate it.

### 3. The template lags its children

| Item | Template | Libraries |
|---|---|---|
| `astral-sh/setup-uv` | v10.0.1 (also both cookiecutters' own CI, and forex) | v10.3.0 (paddock v10.2.0) |
| Sphinx | `>=8,<9` | `>=9,<10` |
| `adrs` CI job, `docs/adr/` seed | absent | present |
| `rotate-python-versions` | `CLAUDE.md` reference, no `--hidden` | filters\* say `AGENTS.md`; paddock far ahead |
| release skill | no step that writes `release-<version>.md`, though step 7 reads it | paddock:38 has the step; class-registry has a worked `[!WARNING]` example |
| `.claude/rules` and `.agents/rules/testing.md` | absent | filters-pydantic, forex, phx-claude-siat |
| Code Comments section | short | filters has the long "reader who never saw the diff" text plus the `type: ignore` exception |

Even the cookiecutters' own non-templated `ci.yml` sits at setup-uv 10.0.1, so Renovate bumps aren't landing in either template repo at all. Check the Renovate installation and dashboard there. Separately, the `{% raw %}` blocks in the templated `build.yml` will stop Renovate parsing it even once it runs.

### 4. Python library configuration

| | filters | -django | -iso | -pydantic | class-registry | paddock | template |
|---|---|---|---|---|---|---|---|
| Version source | static | static | static | static | static | dynamic | dynamic (ADR 005) |
| Type check (CI and tox) | mypy and pyright | **none** | **none** | mypy strict | mypy strict | mypy | mypy strict |
| autohooks | full + docs_build | black, ruff only | black, ruff only | no docs_build | full + docs_build | full + docs_build | full + docs_build |
| CI jobs | test, typecheck, docs, adrs | adrs, test | adrs, test | test, type-check, docs, adr | adrs, build, type-check, docs | adrs, docs, lint, test, typecheck | test, type-check, docs |
| Test directory | test | test | test | test | test | **tests** | test |
| Licence file | LICENCE.txt | **LICENCE** | LICENCE.txt | LICENCE.txt | LICENCE.txt | LICENCE.txt | LICENCE.txt |
| Default branch | develop | develop | develop | **main** (main-only, documented) | develop | develop | (develop per module) |
| Leftovers | — | — | — | — | **`setup.py` shim (2023)** | — | — |

- **Job names drift:** `typecheck` vs `type-check`, and `adr` vs `adrs`. The module gates on `gate` alone, but anyone reading a PR's checks meets five vocabularies. Standardise on the template's names.
- **filters-django and filters-iso have no type checking**, and their autohooks run neither mypy nor pytest. They're the furthest behind on every axis, the release skill included (still on their March state).
- **The template's dynamic version vs the five static repos.** ADR 005 chose dynamic, and the five migrate to it. The release skills are correct for each repo as they stand.
- **filters-pydantic's main-only branching** is deliberate (its AGENTS.md), but it conflicts with the module, which sets `develop` as default and creates `trunk-develop`. It adopts develop.
- **paddock's `docs_build` hook also watches `README.rst`, `docs/*.md` and `pyproject.toml`.** That's worth upstreaming.

### 5. Agent instructions (AGENTS.md, skills)

Stale or incorrect:
- **"Getting Started" names directories that don't exist:** `docs/plans/` and `docs/future/` in filters, filters-django, filters-iso, class-registry and portfolio. The generated AGENTS.md of both templates points at `docs/adr/INDEX.md`, but neither template ships `docs/adr/`. paddock and phx-claude-siat use `docs/superpowers/plans/`, where superpowers actually writes plans. Use that everywhere.
- **The browser-plugin template's generated AGENTS.md:20 cites `docs/adr/004`**, which exists only in the template repo.
- **filters-pydantic AGENTS.md:48** says to put the Sphinx-compat comment *inline*, contradicting its own comment rule (line 62) and the filters fix.
- **filters AGENTS.md:**
  - It says the fixtures live in `test/conftest.py`; they come from the `filters.pytest` plugin (ADR 001).
  - Its stricter "always pass `expected`" rule is deliberate, but conftest's docstring says `expected` may be omitted. One should mention the other.
  - It lists no type-check command, though CI runs mypy and pyright (ADR 015).
- **The old "`ls docs/adr/` and increment" instruction** remains in both cookiecutters (their own and generated AGENTS.md), forex and portfolio. It contradicts the `phx-adr new` tooling the phx plugin provides.

Improvements that haven't propagated:
- **release skill:**
  - The template and class-registry carry the migration-guide gate (from class-registry, July). filters, filters-django, filters-iso, filters-pydantic and paddock never got it, though filters ships `upgrading_to_v4.rst`.
  - filters-django and filters-iso also lack "close related issues", "rebase develop onto main", the artefact-verification note and `uv sync` before build.
  - The same two pick the GPG key with an `awk` over `--list-keys`, where every other copy uses `git config user.email`.
  - The template could delegate its ~60-line release-notes guide to `phx:writing-release-notes`, as phx-claude-siat does.
- **phx-filters skill:** paddock's 230-line copy is mostly a general guide to using filters (chain composition, `Optional`/`FilterMapper` ordering, the pytest plugin). It belongs upstream in filters, as docs or a shipped skill. filters-pydantic's 76-line copy is legitimately pydantic-specific.

Duplicated from the global CLAUDE.md:
- "Writing for coding agents" in every Python repo is a cruder copy of the global section.
- Alphabetisation rules: filters-django, paddock, portfolio.
- Arrow functions and `creative-commits`: portfolio (without the `phx:` prefix).

Keep the comment-placement rule local, because AGENTS.md also serves non-Claude harnesses. Cut the rest.

### 6. Claude Code configuration

- **The same marketplace is registered under two keys.** Global `config-claude/settings.json` registers `obra/superpowers-marketplace` as `superpowers-marketplace`, while both cookiecutters (and so every project baked from them) register it as `obra`. The same plugin then appears under two IDs: `superpowers@superpowers-marketplace` and `superpowers@obra`. Pick one key (the global one) and fix the templates.
- **The marketplace pins the phx plugin to `ref: main`, while CI pins `phx-adr` to 8.1.0.** Sessions run the latest plugin, and CI validates against the pinned version. That's acceptable while `main` is releases-only, but a plugin release can make sessions' `phx-adr` disagree with CI until Renovate bumps the pin. Worth one line in the template ADR.
- **The workflows in config-claude and config-claude-code-cloud use floating tags** (`actions/checkout@v4`, `create-github-app-token@v2`); everything else pins a SHA. Neither repo has a `renovate.json`.
- **purrductivity has no AGENTS.md or CLAUDE.md**, only a vendored `playwright-cli` skill. That's fine for a demo.

### 7. Repository settings (from the API)

| Finding | Repos |
|---|---|
| The module disables wiki and projects; these have them on | purrductivity, purrductivity-ctf (settings only), terraform-github-repository (wiki and projects); filters-django, portfolio, triggers (projects) |
| Issues disabled | filters-django, data-providers, triggers |
| No description | cookiecutter-py, forex-fee-calculator, portfolio, purrductivity |
| No licence detected | phx-claude-siat, both cookiecutters, all config-\* (fine if intentional; the public ones accept contributions by default) |
| Topics set only on filters (11) | all others are empty |
| terraform-github-repository's default is `main` and `develop` is empty | it doesn't yet run on its own module |

The module will correct most of these on apply. Use this table as the expected first-plan diff for each repo.

### 8. Housekeeping

- **The release skill adds the checksums heading twice.** It runs `echo -e "\n# SHA256 Checksums"` and its notes template already ends with that heading (filters:89/196, filters-pydantic, paddock): delete the echo.
- **`.agents/agents/pre-commit-code-reviewer.md` is orphaned.** Claude Code stopped loading it when `.claude/` became a real directory that links only `skills` (filters 77a2944), in filters, filters-django, filters-iso and filters-pydantic: delete it, or symlink `.claude/agents` and put it in the template.
- **portfolio commits `.agents/settings.local.json`.** `.claude` is a symlink to the whole `.agents` directory, which the filters AGENTS.md says breaks the native worktree tool: untrack local settings and make `.claude` a real directory.
- **Stale branches:**
  - `test/pr-body-link-storage` in phx-claude-siat and config-claude-code-cloud; the commit says "safe to close/delete".
  - filters `claude/filters-pydantic-1-0-v5w5n7` (Sept 5).
  - two `claude/*` branches in paddock.
  - portfolio `feature/phase-7-prerequisites` (June).
  - phx-claude-siat `feature/detect-adr-number-collisions` (Sept 2).
- **Dormant repos:** data-providers (2023) and triggers (2018: Travis, `setup.py`, `LICENSE`) are neither archived nor modernised. Archive both.
- **class-registry's `setup.py` shim** is no longer needed with hatchling.
- **Web repos split three ways on package manager:** bun (portfolio), npm (purrductivity) and pnpm (browser template). portfolio has no CI, no Renovate and no ADR CI. Fine if it stays private and solo, but it's the largest ADR corpus that nothing validates.
