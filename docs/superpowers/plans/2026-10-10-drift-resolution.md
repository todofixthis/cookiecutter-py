# todofixthis Drift Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve the discrepancies in the 2026-10-10 drift audit, and port `todofixthis/cookiecutter-py` to copier so that template fixes reach every Python library as Renovate PRs from then on.

**Architecture:** `todofixthis/cookiecutter-py` becomes the single source for the Python libraries. Phase 1 fixes the template, ports it to copier and tags `v1.0.0`. Phase 2 adopts each library onto that tag with `copier copy` and records its answers, so Renovate's `copier` manager opens a PR for every later template release. Each repo's own conventions move out of its templated `AGENTS.md` and into `.agents/rules/project.md`. Phases 3–5 are the changes that don't belong to the template: other repos' config, the Terraform module rollout, and housekeeping. Each phase is a separate branch and PR in the repo it names.

**Tech Stack:** copier 9.x, uv, hatchling, GitHub Actions, Renovate (Mend-hosted app), Terraform (`integrations/github` ~> 6.0), phx plugin 8.1.0 (`phx-adr`).

**Spec:** the audit report at `docs/superpowers/plans/2026-10-10-drift-audit.md` (section numbers below refer to it), plus the maintainer's decisions of 2026-10-10:
- propagate template changes with copier
- source versions dynamically from `__version__`
- filters-pydantic adopts develop/main
- archive data-providers and triggers
- leave portfolio alone (rewrite pending)

**Worktree:** `.claude/worktrees/copier-port` in `todofixthis/cookiecutter-py` (branch: `feature/copier-port`, off `develop`, which was created from `main` on 2026-10-12).

## Global Constraints

- **Python:** support the three most recent minor releases, today 3.12, 3.13 and 3.14 (cookiecutter-py ADR 001).
- **Template must be safe for Renovate.** It uses no copier unsafe features: no `_tasks`, `_migrations` or `_jinja_extensions`. Renovate's hosted app runs `copier update --skip-answered --defaults` without `--trust`.
- **Jinja delimiters:** `[[ ]]` for variables, `[% %]` for blocks and `[# #]` for comments, set in `_envops`. Bash in a templated `run:` block uses `[ ]`/`test`, never `[[ ]]`. GitHub's `${{ }}` then needs no `{% raw %}`, and templated YAML stays parseable by Renovate.
- **Templated files** carry the `.jinja` suffix (`_templates_suffix: .jinja`). Every other file copies verbatim.
- **Symlinks are preserved** (`_preserve_symlinks: true`): `CLAUDE.md` → `AGENTS.md`, `.claude/skills` → `../.agents/skills`, `.claude/rules` → `../.agents/rules`.
- **Template release tags** are bare semver (`1.0.0`), matching phx-claude-siat's tags.
- **The phx-adr pin** is the 40-character commit SHA of a phx-claude-siat release, with a trailing `# X.Y.Z`. Renovate bumps it with a `github-tags` regex manager over `.github/workflows/build.yml` and `AGENTS.md` (filters-pydantic's form). The current value is `0725567cec6bab6a227c2a3d569e64c226c33a4e # 8.1.0`.
- **The required check** is named `gate`. It aggregates every other job with `needs`, `if: always()`, and fails on any `failure`, `cancelled` or `skipped` (ADR 009).
- **CI job names:** `test`, `type-check`, `docs`, `adrs`, `gate`.
- **Worktrees** live in `.claude/worktrees/`. That path is gitignored, and AGENTS.md tells agents to use the `using-git-worktrees` skill.
- **The superpowers marketplace key** is `superpowers-marketplace` (plugin ID `superpowers@superpowers-marketplace`), matching `todofixthis/config-claude/settings.json`.
- **Spelling:** NZ English throughout, except external symbols.
- **Commits:** `uv run git commit` through `phx:creative-commits`; push after each commit.
- **Out of scope:** portfolio, purrductivity-ctf, and the web repos' package-manager split (informational in the audit; no repo is wrong). cookiecutter-browser-plugin gets its fixes here, but its own copier port is a follow-on plan.

## Review Focus

1. **A library's local AGENTS.md content gets overwritten by `copier copy`.** Adoption must leave every local rule present in `.agents/rules/project.md`. Task 9 diffs old against new AGENTS.md section by section, to show nothing local was lost.
2. **Renovate's `copier update --defaults` meets a new question with no default.** Every question added after 1.0.0 must have a default, or Renovate's PR fails. Task 7's test bakes with `defaults=True` and no `data` for every question except those with no possible default.
3. **The `gate` job passes while a needed job was skipped.** A job skipped by a failed dependency reports `skipped`, not `failure`. Task 4's gate must also fail on `skipped` for jobs that are never conditionally skipped. Its test asserts the `if` expression covers `skipped`.
4. **A template release turns every library's CI red.** The drift signal is a Renovate PR, never a CI job in `gate`, so unrelated PRs aren't blocked. Task 8 checks that no `gate` dependency inspects `.copier-answers.yml`.
5. **The ReadTheDocs build installs into the wrong venv.** A fixed `.readthedocs.yaml` still can't be tested in CI. Task 2 adds a bake test pinning `UV_PROJECT_ENVIRONMENT=`, and Phase 2 checks a real ReadTheDocs build for the first adopted library.

---

## Pre-work (phx convention: agent-facing docs first, committed before Task 1)

Done by the first executing session in `todofixthis/cookiecutter-py` on `feature/copier-port`, through `phx:writing-adrs`. ADRs 001–007 already fail `phx-adr check`. Paths under `template/` don't exist until Task 1, and `{{ … }}` paths can't be written as valid unquoted YAML. So Pre-work gives the new ADRs interim scopes of paths that exist now: `cookiecutter.json`, `hooks/`, `test/`, `.github/workflows/`. Run `phx-adr index` only; Task 1 Step 7 sets final scopes for every ADR and turns `phx-adr check` green.

- [ ] **ADR 008: Propagate template changes with copier and Renovate.**
  - Covers: copier over cruft (last release December 2024) and over manual re-sync.
  - Constraints: Renovate safety (no unsafe features), the delimiters, the `.jinja` suffix, preserved symlinks, semver tags, and the drift signal being Renovate PRs rather than a CI gate.
  - Supersedes ADR 004 in part: baking now uses copier.
  - The recorded `version` answer only seeds new projects. It goes stale after adoption, and that's expected.
  - Partly supersedes ADR 001: `python_version` becomes a recorded question with a static default, maintained by `rotate-python-versions`, rather than computed from the host interpreter. A computed value would be re-derived on every `copier update` and move a project's Python floor unasked.
  - Scope: `copier.yml`, `template/`, `test/`, `.github/workflows/`.
- [ ] **ADR 009: Gate, ADR CI and the phx pin.**
  - Covers: the `gate` aggregator job (required by `todofixthis/terraform-github-repository`'s rulesets), the `adrs` job, and the pin format and Renovate manager from Global Constraints.
  - Records the trailing `# X.Y.Z` as a sanctioned exception to the comment-placement rule, because Renovate's regex needs it on the same line.
  - Notes that the phx plugin itself tracks `main` while CI pins a tag.
- [ ] **ADR 010: Split AGENTS.md into templated and project parts.**
  - AGENTS.md is templated and identical across libraries.
  - Each project's own Architecture, Tests, Package and Troubleshooting sections live in `.agents/rules/project.md`, which copier never writes after the first copy (`_skip_if_exists`).
  - `.agents/rules/testing.md` carries the shared test conventions.
- [ ] **ADR 005:** revisit it: update its summary to say the template's dynamic versioning is now the standard every library adopts. Edit it in place; it isn't superseded.
- [ ] **Update cookiecutter-py's own AGENTS.md.**
  - Replace the "`ls docs/adr/` and increment" text with the `phx-adr` commands, pinned as in Global Constraints.
  - Describe the `copier.yml`/`template/` layout and the release-by-tag process.
  - Replace the trunk-based Branches section with develop/main: feature branches off `develop`, and `main` for releases only.
  - Add a Releases section: merge `develop` into `main` via PR, then tag `X.Y.Z` on `main`. Renovate does the rest.
- [ ] **Commit and push**, then record those commits in this plan's Architecture section as completed pre-work.

---

## Phase 1 — cookiecutter-py (branch `feature/copier-port`)

### File Map

| Path | Change |
|---|---|
| `copier.yml` | Create: questions, `_subdirectory: template`, `_envops`, `_templates_suffix`, `_preserve_symlinks`, `_skip_if_exists` |
| `cookiecutter.json`, `hooks/` | Delete |
| `LICENCE.txt` | Create: MIT, `Copyright (c) <first-commit year> Phoenix Zerin` |
| `{{ cookiecutter.github_project_name }}/` | `git mv` to `template/`. Rename templated files to `*.jinja` and paths to `[[ var ]]` |
| `template/[[ _copier_conf.answers_file ]].jinja` | Create: `[[ _copier_answers|to_nice_yaml -]]`. Without it copier writes no answers file, and neither `copier update` nor Renovate can find the project |
| `test/conftest.py` | Create: `template_repo` fixture |
| `template/.agents/rules/project.md.jinja` | Create: local-section stub |
| `template/.agents/rules/testing.md` | Create: shared test conventions |
| `template/.github/workflows/build.yml.jinja` | Add `adrs` and `gate` jobs, setup-uv 10.3.0, remove `{% raw %}` |
| `template/.readthedocs.yaml` | `UV_PROJECT_ENVIRONMENT=` |
| `template/.agents/skills/rotate-python-versions/SKILL.md` | Replace with paddock's, minus the Dockerfile note |
| `template/.agents/skills/release/SKILL.md.jinja` | Write-notes step and class-registry's additions |
| `template/.claude/settings.json` | Marketplace key |
| `template/renovate.json` | phx-adr custom manager |
| `template/docs/adr/INDEX.md` | Create: empty generated index |
| `test/test_bake.py` | Port to `copier.run_copy` and add tests |
| `.github/workflows/*.yml`, `renovate.json`, `pyproject.toml` | copier instead of cookiecutter; Renovate file patterns for `*.jinja` |

### Task 1: Port the template to copier, with no content changes

**Files:**
- Create: `copier.yml`
- Move: `{{ cookiecutter.github_project_name }}/` → `template/`
- Delete: `cookiecutter.json`, `hooks/`
- Modify: `test/test_bake.py`, `pyproject.toml`, `.github/workflows/generate-and-validate.yml`

**Interfaces:**
- Produces the copier questions every later task and every library's `.copier-answers.yml` uses.
- Each question, with its type and default:

  | Question | Type | Default |
  |---|---|---|
  | `project_name` | str | `My Python Project` |
  | `github_project_name` | str | `[[ project_name.lower().replace(' ', '-') ]]` |
  | `package_name` | str | `[[ project_name.lower().replace(' ', '_') ]]` |
  | `pypi_project_name` | str | `phx-[[ github_project_name ]]` |
  | `project_short_description` | str | — |
  | `author_name` | str | `Phoenix Zerin` |
  | `author_email` | str | `phx@phx.nz` |
  | `github_username` | str | `todofixthis` |
  | `copyright_year` | int | none; validator 4 digits |
  | `copyright_holder` | str | `[[ author_name ]]` |
  | `python_version` | str | `3.14`; validator `^3\.\d+$` |
  | `version` | str | `0.1.0` (seeds `__version__`; without it hatchling's dynamic version renders empty) |

- Quote every templated default in `copier.yml` (`default: "[[ project_name.lower().replace(' ', '-') ]]"`). Unquoted, YAML reads `[[ … ]]` as a flow sequence.
- Computed values:
  - `python_major` and `python_minor` are `when: false` and derived from `python_version`.
  - `copyright_year` and `copyright_holder` replace `this_year`, so that EFL Global-era repos keep their real notices.

- [ ] **Step 1: Port the bake fixture.** Port `baked_project` to `copier.run_copy(str(TEMPLATE_ROOT), tmp_path / "out", data={"copyright_year": 2026, "project_short_description": "x"}, defaults=True, vcs_ref="HEAD", unsafe=False)`. Change `RE_UNRENDERED_JINJA` to `\[\[ .*? \]\]|\[% .*? %\]|\{\{ *cookiecutter\.`. Template markers always carry inner spaces, so TOML's `[[tool.x]]` arrays of tables don't match, and the last branch catches a file the port forgot to rename to `.jinja`. Add `test_unrendered_regex`: the regex matches `[[ x ]]`, `[% if x %]` and `{{ cookiecutter.x }}`, and doesn't match `[[tool.x]]` or `${{ matrix.x }}`. Keep every existing test, including both symlink tests. Add `test_writes_answers_file`: `.copier-answers.yml` exists, and its `_src_path` equals the template path passed in. The fixture and regex can't run until `copier.yml` exists in Step 3, so they fail as expected now.
- [ ] **Step 2: Run** `uv run pytest`. Expected: FAIL, because there's no `copier.yml`. In `pyproject.toml`, add `filterwarnings = ["ignore::copier.errors.DirtyLocalWarning"]` to `[tool.pytest.ini_options]`, with a comment saying the bake reads the uncommitted worktree on purpose.
- [ ] **Step 3: Write `copier.yml`.**
  - Use the questions above plus `_subdirectory: template`, the `_envops` delimiters, `_templates_suffix: .jinja` and `_preserve_symlinks: true`.
  - `git mv` the template dir.
  - Rename each file that contains `{{ cookiecutter.` to `*.jinja`, and replace its markers with `[[ ... ]]`.
  - Replace `{% raw %}${{ … }}{% endraw %}` with `${{ … }}`.
  - Rename the path segments `{{ cookiecutter.package_name }}` → `[[ package_name ]]`.
  - Delete `hooks/`: preserved symlinks replace `post_gen_project.py`, and recorded questions replace `pre_prompt.py`.
  - Create `template/[[ _copier_conf.answers_file ]].jinja`.
  - Inside any `.jinja` file, wrap TOML arrays of tables (`[[tool.mypy.overrides]]`) in `[% raw %]…[% endraw %]`. Otherwise `[[` opens a Jinja expression and the bake aborts with `UndefinedError`.
- [ ] **Step 4: Swap the dependencies.** In `pyproject.toml`, swap `cookiecutter` for `copier>=9,<10` in `dev` and `ci`. Set `[tool.ruff] extend-exclude = ["template"]` and drop the old exclude. Delete the `cookiecutter.*` mypy override; copier ships `py.typed`. Update the ruff and autohooks comments that name the old directory.
- [ ] **Step 5: Port the bake workflow.** In `generate-and-validate.yml`, replace the bake step with `uvx --python "${{ matrix.python-version }}" "copier>=9,<10" copy --defaults --vcs-ref=HEAD --data copyright_year=2026 --data project_short_description=x --data python_version="${{ matrix.python-version }}" . /tmp/baked/my-python-project`. Keep the later steps.
- [ ] **Step 6: Run** `uv run pytest && uv run mypy test && uv run ruff check test`. Expected: exit 0, 9 passed. Drop `hooks` from AGENTS.md's mypy and ruff lines.
- [ ] **Step 7: Bake and validate locally,** exactly as the workflow does. Run `uvx "copier>=9,<10" copy --defaults --vcs-ref=HEAD --data copyright_year=2026 --data project_short_description=x . "$SCRATCH/baked"`, then in `"$SCRATCH/baked"` run `uv sync --group ci && uv run ruff check && uv run mypy src test && uv run pytest`. Expected: exit 0.
- [ ] **Step 8: Fix ADR scopes.** For ADRs 001–010, rewrite each `scope` as an unquoted block list of real paths. Use `copier.yml` and `template/…` paths, dropping `cookiecutter.json` and `hooks/`. Run `phx-adr index && phx-adr check` (pinned command from AGENTS.md). Expected: `10 decisions indexed`, exit 0.
- [ ] **Step 9: Commit.** Run `git status` to catch related unstaged or untracked files (e.g. `uv.lock`), then use the `creative-commits` skill.

### Task 2: Fix template defects 1.2 and 1.3, and the lagging versions

**Files:**
- Modify:
  - `template/.readthedocs.yaml`
  - `template/.agents/skills/rotate-python-versions/SKILL.md`
  - `template/pyproject.toml.jinja` (Sphinx `>=9,<10`, `sphinx_rtd_theme>=3.1,<4`)
  - every `astral-sh/setup-uv` pin under `template/` and `.github/` → `1c37ad07a6a961277cf70c0d37d6f313000f5884 # v10.3.0`
- Test: `test/test_bake.py`

- [ ] **Step 1: Write the failing tests.**
  - `test_readthedocs_syncs_into_rtd_env`: `.readthedocs.yaml` contains `UV_PROJECT_ENVIRONMENT=$READTHEDOCS_VIRTUALENV_PATH` and does not contain `VIRTUAL_ENV=$READTHEDOCS`.
  - `test_rotate_skill_searches_hidden_dirs`: every `rg` line in the rotate skill contains `--hidden`.
- [ ] **Step 2: Run** `uv run pytest -k "readthedocs or rotate"`. Expected: 2 FAIL.
- [ ] **Step 3: Fix the ReadTheDocs config.** Copy filters' `post_install` line and comment: `UV_PROJECT_ENVIRONMENT=$READTHEDOCS_VIRTUALENV_PATH uv sync --group ci`, citing uv#10074.
- [ ] **Step 4: Replace the rotate skill.** Use `todofixthis/paddock`'s `.agents/skills/rotate-python-versions/SKILL.md` with its Dockerfile `PYTHON_VERSION` note removed. Add a step: "update `python_version`'s default in the template's `copier.yml`" for this repo; for a generated project, "run `copier update --defaults --vcs-ref=:current: --data python_version=X.Y`" (`:current:` keeps the project on its current template version).
- [ ] **Step 5: Bump the versions** (Sphinx, setup-uv). Run `uv run pytest`. Expected: PASS.
- [ ] **Step 6: Prove the hidden-dirs test can fail.** Temporarily remove `--hidden` from one line, run it, and expect FAIL. Restore.
- [ ] **Step 7: Commit.** Run `git status` to catch related unstaged or untracked files, then use the `creative-commits` skill.

### Task 3: AGENTS.md split, rules, and settings

**Files:**
- Modify: `template/AGENTS.md.jinja`, `template/.claude/settings.json`, `template/.gitignore`, `copier.yml` (`_skip_if_exists: [".agents/rules/project.md"]`)
- Create:
  - `template/.agents/rules/project.md.jinja`
  - `template/.agents/rules/testing.md`
  - `template/.claude/rules` symlink → `../.agents/rules`
  - `template/docs/adr/INDEX.md`, generated with `phx-adr index` in an empty `docs/adr/`
- Test: `test/test_bake.py`

- [ ] **Step 1: Write the failing tests.**
  - `test_claude_rules_stays_a_symlink`: `.claude/rules` is a symlink to `../.agents/rules`.
  - `test_settings_use_shared_marketplace_key`: `.claude/settings.json` has `enabledPlugins` containing `superpowers@superpowers-marketplace` and not `superpowers@obra`.
  - `test_agents_md_names_only_existing_dirs`: every `docs/...` path in AGENTS.md's Getting Started section exists in the baked project, or is `docs/superpowers/plans/`, which is marked "if one exists".
  - Create the `template_repo(tmp_path, monkeypatch) -> Path` fixture in `test/conftest.py`.
    - It copies only `copier.yml` and `template/` into `tmp_path` (`shutil.copytree(..., symlinks=True)`), then `git init`s, commits, tags `0.0.1` and returns the path.
    - It sets `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` and `GIT_COMMITTER_EMAIL` with `monkeypatch.setenv`, because CI runners have no git identity. Updating from a dirty `vcs_ref="HEAD"` records an ephemeral `_commit` that `run_update` can't check out.
  - `test_project_rules_survive_update`:
    - Bake from `template_repo` at `0.0.1`, `git init` the bake, write `x` into `.agents/rules/project.md` and commit.
    - In `template_repo`, append a line to `template/.agents/rules/project.md.jinja`, commit, and tag `0.0.2`.
    - Run `copier.run_update(dst, defaults=True, overwrite=True, skip_answered=True, unsafe=False)`.
    - Assert the file still reads exactly `x`, and that `.copier-answers.yml`'s `_commit == "0.0.2"`.
- [ ] **Step 2: Run** `uv run pytest`. Expected: 4 FAIL.
- [ ] **Step 3: Rewrite AGENTS.md.jinja.**
  - Getting Started lists `docs/adr/INDEX.md`, `docs/superpowers/plans/` (if one exists) and `.agents/rules/`.
  - The ADR section is filters' current text, with its skill link in tag form (`blob/8.1.0/`, which the Renovate regex matches; filters' `blob/<SHA>/` doesn't) and its pinned `phx-adr` commands, including `for` and `supersede`, each with a trailing `# 8.1.0`.
  - The Commands section adds `uv run mypy src test`.
  - The Code Comments section is filters' long version, including the `type: ignore` exception and the Renovate-pin exception.
  - Worktrees is the current template text.
  - Delete "Writing for coding agents".
  - Move the Tests section into `.agents/rules/testing.md`, taking filters-pydantic's `testing.md` and adding the one-line-docstring rule.
  - `project.md.jinja` holds an empty Architecture heading with the existing placeholder sentence.
- [ ] **Step 4: Update settings and gitignore.** Settings: rename the marketplace key `obra` to `superpowers-marketplace`. Gitignore: keep only `.claude/worktrees/` under "Agent worktrees".
- [ ] **Step 5: Run** `uv run pytest`. Expected: PASS.
- [ ] **Step 6: Prove the update test can fail.** Temporarily remove `_skip_if_exists` from `copier.yml` and run `uv run pytest -k survive_update`. Expected: FAIL, with conflict markers in `project.md`. Restore it.
- [ ] **Step 7: Commit.** Run `git status` to catch related unstaged or untracked files, then use the `creative-commits` skill.

### Task 4: `adrs` and `gate` jobs, and the pin manager

**Files:**
- Modify: `template/.github/workflows/build.yml.jinja`, `template/renovate.json`
- Test: `test/test_bake.py`

- [ ] **Step 1: Write the failing tests**, parsing the baked `build.yml` with `yaml.safe_load`; add `pyyaml` to `dev` and `ci`.
  - `test_ci_has_gate_needing_every_job`: `jobs["gate"]["needs"]` equals the set of the other job names, `jobs["gate"]["if"] == "always()"`, and the fail step's `if` mentions `failure`, `cancelled` and `skipped`.
  - `test_ci_job_names`: the job set is `{"test", "type-check", "docs", "adrs", "gate"}`.
  - `test_adr_pin_is_sha_with_version`: the raw text of the baked `build.yml` matches, read as text because `yaml.safe_load` strips the trailing comment, and Renovate reads text anyway: `phx-claude-siat@[0-9a-f]{40}#subdirectory=skills/writing-adrs' phx-adr check # \d+\.\d+\.\d+`.
  - `test_renovate_manages_adr_pin`: `renovate.json`'s `customManagers[0]` has `datasourceTemplate == "github-tags"` and both file patterns.
- [ ] **Step 2: Run** `uv run pytest -k "ci_ or adr_pin or renovate"`. Expected: 4 FAIL.
- [ ] **Step 3: Add the `adrs` job.** Copy filters-pydantic's `adr` job, renamed `adrs`, with the pin from Global Constraints. Add `gate`, following phx-claude-siat's `pr.yml` gate, with the step condition `contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled') || contains(needs.*.result, 'skipped')`. Copy filters-pydantic's `customManagers` entry into the template's `renovate.json`, changing its ADR reference to "ADR 009 in todofixthis/cookiecutter-py".
- [ ] **Step 4: Run the tests.** Run `uv run pytest`. Expected: PASS. Bake (Task 1 Step 7), then run `phx-adr check` in the baked project. Expected: `0 decisions indexed`, exit 0.
- [ ] **Step 5: Commit.** Run `git status` to catch related unstaged or untracked files, then use the `creative-commits` skill.

### Task 5: Release skill reconciliation

**Files:**
- Modify: `template/.agents/skills/release/SKILL.md.jinja`
- Test: `test/test_bake.py`

- [ ] **Step 1: Write the failing tests.**
  - `test_release_skill_writes_notes_file`: the baked skill contains `release-<version>.md`, in a step before the first `--body-file`.
  - `test_release_skill_single_checksums_heading`: `echo -e "\n# SHA256 Checksums"` doesn't appear.
- [ ] **Step 2: Run them.** Expected: the first FAILS. The second passes already; it guards the regression.
- [ ] **Step 3: Edit the skill.**
  - Add paddock:38's write-the-notes-file sentence to step 3.
  - Port class-registry:248-258's worked `[!WARNING]` example, with its version made generic.
  - Port class-registry:265 and :291, with "v6" replaced by "the new major".
  - Leave the embedded notes guide in place. Delegating it to `phx:writing-release-notes` is a follow-on decision, not drift.
- [ ] **Step 4: Run** `uv run pytest`. Expected: PASS.
- [ ] **Step 5: Commit.** Run `git status` to catch related unstaged or untracked files, then use the `creative-commits` skill.

### Task 6: The template repo's own CI and Renovate

**Files:**
- Modify: `renovate.json`, `.github/workflows/ci.yml`, `.github/workflows/generate-and-validate.yml`

- [ ] **Step 1: Merge the workflows and add the gate.** Move `generate-and-validate.yml`'s job into `ci.yml` as job `generate`, and delete that file. Two workflows each with a `gate` would give two check runs of the same name. Add an `adrs` job running `phx-adr check` with the pinned SHA, and one `gate` (Task 4's form) needing `test`, `type-check`, `generate` and `adrs`.
- [ ] **Step 2: Make Renovate parse the templated files.**
  - In `renovate.json`, extend the `github-actions` manager with `"managerFilePatterns": ["/^template/\\.github/workflows/[^/]+\\.ya?ml(\\.jinja)?$/"]`, and `pep621` with `"/^template/pyproject\\.toml\\.jinja$/"`.
  - Add the phx-adr custom manager for `AGENTS.md`, `template/AGENTS.md.jinja` and the workflows.
  - In `template/renovate.json`, add `"constraints": {"copier": ">=9,<10"}`, so Renovate's copier PRs use the major version the template is tested with.
- [ ] **Step 3: Confirm Renovate is active on this repo.**
  - Open the repo's Dependency Dashboard issue.
  - If there isn't one, the Renovate app isn't installed here (the audit found setup-uv stuck at v10.0.1 even in the non-templated `ci.yml`). Ask the maintainer to add the repo to the installation: Renovate app settings → Repository access.
  - Record the outcome in the PR description.
- [ ] **Step 4: Validate the config.** Run `npx --yes --package renovate@41 renovate-config-validator renovate.json template/renovate.json`. Expected: exit 0. Then prove the validator can fail: copy `renovate.json` to `$SCRATCH/bad.json`, add `"notAnOption": true`, and run the validator on it. Expected: non-zero exit.
- [ ] **Step 5: Commit.** Run `git status` to catch related unstaged or untracked files, then use the `creative-commits` skill.

### Task 7: Prove the update path end to end

**Files:**
- Test: `test/test_update.py`

**Interfaces:**
- Consumes the questions from Task 1 and `template_repo` from Task 3.

- [ ] **Step 1: Write `test_update_applies_template_change`.**
  - Use Task 3's `template_repo` fixture (tagged `0.0.1`).
  - Bake from it with `run_copy(vcs_ref="0.0.1", defaults=True, data={"copyright_year": 2026, "project_short_description": "x"})`, then git-commit the bake.
  - Change one line in the template copy's `template/README.rst.jinja`, commit, and tag `0.0.2`.
  - Run `run_update(dst, defaults=True, overwrite=True, skip_answered=True, unsafe=False)`.
  - Assert the line changed and that `.copier-answers.yml`'s `_commit` is `0.0.2`.
- [ ] **Step 2: Write `test_every_question_has_default_or_is_documented`.** Load `copier.yml`. Every question has a `default`, except `copyright_year` and `project_short_description`.
- [ ] **Step 3: Run** `uv run pytest test/test_update.py`. Expected: PASS. If `run_update` raises `UnsafeTemplateError`, the template uses an unsafe feature, which breaks Global Constraints; remove it.
- [ ] **Step 4: Commit.** Run `git status` to catch related unstaged or untracked files, then use the `creative-commits` skill.

### Task 8: Release 1.0.0

- [ ] **Step 1: Check for drift jobs in `gate`.** Run `rg -n "copier-answers" template/.github` and expect no output, so that no job in `gate` checks for drift.
- [ ] **Step 2: Delete the plan file, if a session committed it to the branch,** then open the PR into `develop` and drive it to green.
- [ ] **Step 3: Carry Phases 2–5 into follow-on plans**, one in each target repo, taking the Phase 2 checklist into the first.
- [ ] **Step 4: Release.** Open a `develop` → `main` PR. After it merges, ask the maintainer to tag `1.0.0` on `main`; tag protection makes this a deliberate human action.

---

## Phase 2 — Adopt each library onto template 1.0.0

Order: class-registry (nearest the template, so it proves the procedure), then filters-iso, filters-django, filters-pydantic, paddock, filters. Each is one branch and PR (`feature/adopt-copier-template`) off that repo's `develop`.

### Task 9: Adoption procedure, the same for every library

- [ ] **Step 1: Preserve the local content.** Copy every local section of AGENTS.md into `.agents/rules/project.md`: Architecture, Tests specifics, Package, Troubleshooting, and Branches where it differs. Fix that repo's stale items from audit section 5 as they move:

  | Repo | Fixes |
  |---|---|
  | filters | fixtures come from the `filters.pytest` plugin; the "always pass `expected`" rule says why it's stricter than conftest's docstring; list the mypy and pyright commands |
  | filters-pydantic | Sphinx-compat comment on the preceding line |
  | all | drop the `docs/plans/` and `docs/future/` pointers, and drop rules duplicated from the global CLAUDE.md (alphabetisation in filters-django and paddock) |

- [ ] **Step 2: Copy the template over the repo.** Run `uvx "copier>=9,<10" copy --defaults --vcs-ref=1.0.0 --overwrite --data-file "$SCRATCH/answers.yml" https://github.com/todofixthis/cookiecutter-py.git .`. Use the full HTTPS URL: copier records the source verbatim, and Renovate can't resolve the `gh:` shortcut. Keep `answers.yml` outside the repo. It holds the repo's real values, e.g. filters: `project_name: Filters`, `package_name: filters`, `pypi_project_name: phx-filters`, `copyright_year: 2016`, `copyright_holder: EFL Global`, `version: <current version>`.
- [ ] **Step 3: Restore what the overwrite clobbers, then review.** Run `git restore src/<pkg>/__init__.py README.rst docs/conf.py docs/index.rst docs/api.rst LICENCE.txt` (paths that exist in that repo) and `rm test/test_placeholder.py`. Then review `git diff`, keeping these local:
  - extra pyproject dependencies and tool config: filters' pyright and ADR 015 settings, paddock's docs group, filters-django's pytest-django
  - extra CI jobs, added to `gate.needs`: paddock's `lint`
  - project ADRs, re-indexed with `phx-adr index`
  - existing skills, which take the template's and re-apply each repo's legitimate variations from the skills audit: paddock's release branch, merge-back and hotfix flow
  - paddock's `tests/` directory: `git mv tests test`, then update `pythonpath`/`testpaths` and any docs. The template's CI and tox run `test`.
  - paddock's wider `docs_build` INCLUDE: upstream it into the template in a follow-up instead
- [ ] **Step 4: Make the per-repo changes:**

  | Repo | Changes |
  |---|---|
  | filters, filters-django, filters-iso, filters-pydantic, class-registry | Switch to dynamic versioning: `__version__ = "<current>"` in `__init__.py`, `dynamic = ["version"]`, delete the static `version` |
  | class-registry | Delete `setup.py` |
  | filters-django | Rename `LICENCE` → `LICENCE.txt` and update `license`/sdist includes |
  | filters-django, filters-iso | Fix every `mypy src test` error the template's type-check job now runs; suppress inline with a reason only where a fix isn't local |
  | filters, filters-django, filters-iso, filters-pydantic | Delete `.agents/agents/pre-commit-code-reviewer.md` |
  | paddock, filters-iso | Delete the custom worktree dir from `.gitignore` |

- [ ] **Step 5: Verify.** Run `uv sync --group=dev && uv run tox -p && uv run ruff check && uv run make -C docs clean && uv run make -C docs html` (skip docs for filters-django and filters-iso, whose docs live in filters) and `phx-adr check`. Expected: all exit 0. `uv run pytest --collect-only -q | tail -1` matches the count before the copy.
- [ ] **Step 6: Commit.** Run `git status` to catch related unstaged or untracked files (`uv.lock`, `.copier-answers.yml`), then use the `creative-commits` skill.
- [ ] **Step 7: For the first adopted repo with docs (class-registry), confirm a real ReadTheDocs build** of the PR branch succeeds before adopting the rest.

### Task 10: filters-pydantic adopts develop/main (in its adoption PR)

- [ ] **Step 1: Create `develop`.** Push `develop` from `main` before the adoption branch, and base the adoption branch on it. The maintainer then sets the default branch to `develop`; the Terraform module will enforce it later.
- [ ] **Step 2: Drop the release-branch flow.** Remove the `release/<version>` flow and main-only text from `project.md` and the release skill, since the template's develop/main process now applies.

### Task 11: Upstream the generic filters guidance (filters repo, separate PR)

- [ ] **Step 1: Move the generic content to filters.** Move paddock's generic `phx-filters` content into filters' `docs/writing_filters.rst`: chain composition, `Optional`/`FilterMapper` ordering, `cast`, the pytest plugin and test naming.
- [ ] **Step 2: Fix the docs.** Fix `docs/extension_filters.rst`'s `pip install filters[django]` → `phx-filters[django]`. Build the docs; expect no warnings.
- [ ] **Step 3: Trim paddock's skill.** In a paddock PR, cut its skill to its own filters and link the docs. Move its class-registry notes into a class-registry doc or drop them.

---

## Phase 3 — Repos outside the Python template

### Task 12: cookiecutter-browser-plugin (one PR)

- [ ] **Step 1: Fix its 6 ADR frontmatter errors** (same fix as Pre-work), then add `adrs` and `gate` jobs to its own CI.
- [ ] **Step 2: Fix the generated project's agent files.**
  - Rename the marketplace key to `superpowers-marketplace`.
  - Replace the "`ls docs/adr/`" text with the phx-adr commands, in both the repo's own AGENTS.md and the generated one.
  - Drop the `docs/adr/004` citation and seed `docs/adr/INDEX.md`.
- [ ] **Step 3: Repeat Task 6 Steps 2–3** (Renovate file patterns, Renovate active), with its patterns adapted to this repo's `{{ cookiecutter.github_project_name }}/` directory. Remove the `{% raw %}` blocks around `${{ }}` that stop Renovate parsing its templated workflow, and escape GitHub expressions with Jinja string literals (`{{ '${{ matrix.x }}' }}`) instead, until this template's own copier port.
- [ ] **Step 4: Adopt develop/main.** Create `develop` from `main`, make it the default branch, and rewrite AGENTS.md's trunk-based Branches section to match cookiecutter-py's.
- [ ] **Step 5: Verify.** Run `uv run pytest` plus the generate-and-validate bake. Expected: exit 0.

### Task 13: forex-fee-calculator

- [ ] **Step 0: Adopt develop/main.** Supersede ADR 001's trunk-based branching with a new ADR (via `phx:writing-adrs`), keeping its decision not to publish. Then create `develop`, make it the default branch, and rewrite AGENTS.md's Branches section.
- [ ] **Step 1: Bring ADR tooling into line.** Replace AGENTS.md's ADR section with the phx-adr form, and add the `adrs` job plus the custom Renovate manager.
- [ ] **Step 2: Add a `gate` job** (Task 4's form) needing `test`, `lint`, `type-check` and `adrs`, then merge the open setup-uv Renovate PR.

### Task 14: config-claude and config-claude-code-cloud

- [ ] **Step 1: Pin the actions.** Pin every `uses:` to a SHA with a `# vX.Y.Z` comment.
- [ ] **Step 2: Add Renovate.** Add `renovate.json` (`config:recommended`, `helpers:pinGitHubActionDigests`) and add both repos to the Renovate installation.
- [ ] **Step 3: Fix the settings.** Add descriptions to cookiecutter-py, forex-fee-calculator and purrductivity (Settings → About), and turn off wiki and projects on purrductivity. The module will later own this for repos it manages.
- [ ] **Step 4: Add licences** (decided 2026-10-12). Add an MIT `LICENCE.txt` (`Copyright (c) <first-commit year> Phoenix Zerin`) to phx-claude-siat and cookiecutter-browser-plugin, each in its own PR; cookiecutter-py gets its own in Task 1. The config-\* repos are personal configuration and stay unlicensed.

### Task 15: paddock pin

- [ ] **Step 1: Merge paddock's open Renovate PR** for phx-claude-siat 8.1.0. If Task 9 already re-pinned it, close the PR.

---

## Phase 4 — Terraform module rollout (todofixthis/terraform-github-repository)

### Task 16: Ship module v1 and apply it repo by repo

**Decided 2026-10-12:** every repo the module manages uses develop/main, with `develop` as default; the module gets no trunk variable. cookiecutter-py adopts it in Pre-work, cookiecutter-browser-plugin in Task 12 and forex-fee-calculator in Task 13.

- [ ] **Step 1: Merge `feature/module-v1`** and tag `1.0.0`, under that repo's own plan.
- [ ] **Step 2: Add `infra/github/` to each repo** whose `gate` job is green on `develop`, in the Phase 2 order, then terraform-github-repository itself (its `infra/github/` exists), the cookiecutters, forex and phx-claude-siat. Pass `homepage_url` (ReadTheDocs URL), `topics` (copy filters' 11 where relevant), `renovate_installation_id` and `visibility`.
- [ ] **Step 3: Review each plan against audit section 7** before applying. Expected diffs: wiki and projects off, issues on (filters-django) and the default branch `develop`. Anything else is a finding to resolve before applying.
- [ ] **Step 4: Change the template.** Add `infra/github/main.tf.jinja` and the plan script, per terraform-github-repository ADR 001's consequences, in a template release after module 1.0.0.

## Phase 5 — Housekeeping

### Task 17: Branches and dormant repos

- [ ] **Step 1: Delete the stale branches**, after confirming with the maintainer that none carries unmerged work:
  - `test/pr-body-link-storage` in phx-claude-siat and config-claude-code-cloud
  - filters `claude/filters-pydantic-1-0-v5w5n7`
  - paddock `claude/filters-integration-paddock-0nvufx` and `claude/optimistic-lamport-ab0ti1-args`
  - phx-claude-siat `feature/detect-adr-number-collisions`
- [ ] **Step 2: Archive the dormant repos.** Archive data-providers and triggers (Settings → Archive). Add a one-line "Archived; unmaintained" note to each README first.

---

## Intentional Decisions

*(Populated during review — reviewers must not re-raise these)*

- **Clobbered files are restored with `git restore` in Task 9, not `_skip_if_exists`.** Adoption is a one-off. `_skip_if_exists` on `__init__.py` would also stop template fixes to it from ever reaching projects.
- **Pre-work ADRs carry interim scopes, and `phx-adr check` goes green only at Task 1 Step 8.** The real paths don't exist until the `git mv`, and Jinja-named paths can't be written as valid unquoted YAML.
- **Plan lives in the scratchpad, and Pre-work is deferred to the first executing session.** This session can't push to cookiecutter-py (Claude GitHub App not installed).

## Self-Review Checklist

- [ ] Every audit finding outside portfolio maps to a task, or to an explicit out-of-scope line.
- [ ] Does the plan header include a `**Worktree:**` field naming the existing worktree and branch?
- [ ] Does every commit step remind the agent to run `git status` first?
- [ ] Does the final Phase 1 task delete the plan file?
- [ ] Does the plan include an Intentional Decisions section?
