# terraform-github-repository v1.0.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and release `v1.0.0` of `todofixthis/terraform-github-repository`, the shared Terraform module both cookiecutter templates will pin, and bring the module repo's own GitHub settings under its management.

**Architecture:** The repo root is the module: `github_repository`, alert settings, a `terraform_data` push step, the default branch, three rulesets and an optional Renovate installation, in that dependency order. `infra/github/` provisions the module repo itself (`source = "../.."`). `scripts/infra-plan` and `.githooks/pre-push` implement the plan-comment guard that CI's `infra-plan` job checks; the template repos will later ship byte-identical copies of the script.

Pre-work note: the skill would normally commit agent guidance and ADRs before the plan. The ADR tool refuses a `scope` naming files that don't exist yet, and the repo held only a README when this plan was written, so `AGENTS.md` lands in Task 1 and the ADRs in Task 5, once their scoped files exist.

**Tech Stack:** Terraform ≥ 1.9, `integrations/github` provider `~> 6.13` (v6.13.0 is the latest release as of writing), bash (must run under macOS's bash 3.2), Perl, git, `gh`, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-02-github-repo-iac-design.md` in `todofixthis/cookiecutter-py`, on branch `claude/awesome-albattani-l890v5` ([todofixthis/cookiecutter-py#5](https://github.com/todofixthis/cookiecutter-py/pull/5)). This plan covers the spec's delivery step 1 (the module repo) only.

**Worktree:** a local clone of `todofixthis/terraform-github-repository` on branch `feature/module-v1` (already pushed; it branches from `develop`, which equals `main`). Create it with `git clone git@github.com:todofixthis/terraform-github-repository.git && git -C terraform-github-repository checkout feature/module-v1`, or a worktree of an existing clone.

## State at handoff

- `todofixthis/terraform-github-repository` exists: public, `main` and `develop` each hold one README commit, `feature/module-v1` exists. No settings or rulesets are applied yet (GitHub defaults: wiki and projects on, all merge methods allowed).
- Every file below was written and checked in a cloud session that couldn't reach the Terraform registry. `scripts/infra-plan`, `.githooks/pre-push` and `tests/infra-plan/test.sh` were run there (all 37 fixture tests pass on Linux with bash 5.2), and mutating each safeguard was shown to turn a test red. All HCL passed `terraform fmt -check`. The plan reviewer built provider v6.13.0 from source in that session and ran `validate` and `terraform test` (10 passed) against it, before the `try()` wrappers were added to the tests; Task 2 is still the first run against a registry-installed provider.

## Global Constraints

- Provider constraint in the module: `~> 6.13`. In a root module: `~> 6.0` (a major-version range, never an exact pin).
- `required_version = ">= 1.9"`.
- Rulesets: `trunk-develop` and `trunk-main` on `refs/heads/<branch>`; rules `deletion`, `non_fast_forward`, `pull_request` (0 approvals, `required_review_thread_resolution = true`, `allowed_merge_methods = ["merge"]`), `required_status_checks` (context `gate`, `integration_id = 15368`, strict, `do_not_enforce_on_create = false`). `trunk-develop` bypass: `RepositoryRole` 5, `always`. `trunk-main`: no bypass. `tags-release`: tags, `~ALL`, `deletion` + `non_fast_forward`, no bypass.
- Repo settings: merge commits only, `merge_commit_title = "PR_TITLE"`, `merge_commit_message = "PR_BODY"`, `delete_branch_on_merge = true`, `allow_auto_merge = false`, `allow_update_branch = false`, issues on, wiki/projects/discussions off, `archive_on_destroy = true`, Dependabot alerts on, Dependabot security updates off, secret scanning + push protection on for public repos only.
- Never put secrets in Terraform state.
- Every `terraform test` run is `command = plan`.
- Scripts run under bash 3.2: no associative arrays, `mapfile`, `${var,,}`, or empty-array expansion under `set -u`.
- GitHub Actions are pinned by commit SHA with a version comment.
- CI log lines use the markers ✅ ❌ ⏭️ ▶️ ⏳ ⚠️.
- NZ English in prose; comments on the line above the code; alphabetise unordered collections.

## Review Focus

- **The maintainer's Mac runs bash 3.2.** The script and hook must work under `/bin/bash`; Task 4's CI runs the fixture tests there via the `scripts` job's macOS leg.
- **Paths with non-ASCII characters, or moved out of `infra/`,** must still count as infra changes. Covered by the `*_non_ascii` and `*_moved_out` fixture tests (Task 3).
- **First push of a new branch when `origin/develop` is stale or missing.** The hook must block with "fetch and retry", not pass silently. Covered by `test_hook_blocks_without_origin_develop` (Task 3).
- **Huge plans** must be truncated under GitHub's 65,536-character comment limit rather than failing the post. Covered by `test_plan_truncates_huge_plan` (Task 3).
- **Re-running the script** must edit the existing plan comment, not stack a new one. Covered by `test_plan_updates_existing_comment` (Task 3).

## File Map

| Path | Responsibility |
|---|---|
| `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf` | The module |
| `tests/repository.tftest.hcl` | Module tests, mock provider, plan only |
| `scripts/infra-plan` | Canonical plan script: plan mode plus `hash`, `changed`, `dirty` |
| `.githooks/pre-push` | Runs the script when a push changes the infra paths |
| `tests/infra-plan/test.sh` | Fixture tests for the script and hook |
| `.infra-paths` | This repo's infra path regex |
| `infra/github/main.tf` | This repo's own GitHub config |
| `.github/workflows/ci.yml` | `changes`, `terraform`, `scripts`, `infra-plan`, `gate` |
| `AGENTS.md`, `CLAUDE.md` (symlink) | Agent guidance |
| `README.md` | Human docs |
| `docs/adr/` | ADRs 001–003 and the generated index |
| `.gitignore`, `renovate.json` | Repo config |

---

### Task 1: Repo scaffolding and agent guidance

**Files:**
- Create: `AGENTS.md`, `CLAUDE.md` (symlink to `AGENTS.md`), `.gitignore`, `.infra-paths`, `renovate.json`

**Interfaces:**
- Produces: `.infra-paths` holding `^(infra/|[^/]+\.tf$)`, read by `scripts/infra-plan` (Task 3).

- [ ] **Step 1: Write `AGENTS.md`**

`AGENTS.md`:

````markdown
## Getting Started

Before writing code, check `docs/adr/INDEX.md` for prior decisions (don't re-litigate).

## Architecture Decision Records

When making significant decisions — choosing between libraries, patterns, tools, or conventions — you **must** write an ADR before implementing the decision. Use the `phx:writing-adrs` skill for the format and conventions. ADRs live in `docs/adr/`.

## Commands

```bash
git config core.hooksPath .githooks                       # install the pre-push hook (once per clone)
terraform fmt -recursive                                  # format
terraform init -backend=false && terraform validate       # validate the module
terraform test                                            # module tests (mock provider, plan only)
tests/infra-plan/test.sh                                  # scripts/infra-plan and pre-push fixture tests
scripts/infra-plan                                        # plan infra/github and post it to the branch's PR
```

## Architecture

- Repo root `*.tf` — the module: one GitHub repo with the todofixthis standard settings and rulesets.
- `infra/github/` — this repo's own configuration, provisioned by the module via `source = "../.."`. Source of truth for this repo's GitHub settings; never change them in the GitHub UI.
- `scripts/infra-plan` — canonical copy of the plan script. Each template repo ships a byte-identical copy, so a change here needs copying into `todofixthis/cookiecutter-py` and `todofixthis/cookiecutter-browser-plugin`; only `.infra-paths` differs between repos.
- `tests/` — `terraform test` files, plus fixture tests for the script and hook.

## Infra changes

- Before opening a PR that touches `infra/` or a root `*.tf` file, run `scripts/infra-plan`, check the plan matches the intended change, and report it. If it warns that terraform isn't installed or state isn't available, tell the user the PR needs a local plan before CI goes green. If `init` fails on a PR that doesn't bump the provider, report the error rather than following the script's hint.
- After an infra PR merges, the maintainer runs `terraform -chdir=infra/github apply` from an up-to-date `develop`.
- Never write the plan marker comment by hand.
- Never put secrets in Terraform: no `sensitive` inputs, no `github_actions_secret`. Set secrets with `gh secret set`.
- Keep the `security_and_analysis` block's `for_each` exactly `local.enable_security_and_analysis ? [1] : []`; the tests rely on it.
- `terraform test` runs must stay `command = plan`: the push step is built in and unmocked.

## Releases

Tag `vX.Y.Z` on `main` after merging a release PR from `develop`, then merge `origin/main` into `develop` (fast-forward when it can) and push. Release notes call out any change to `scripts/infra-plan` (template repos need the copy) and any provider-constraint change (dependents need a lock update).

## Code Comments

Place comments on the line preceding the code they document, not as trailing comments.

## Language and Style

NZ English; incorporate Te Reo Māori where natural (e.g. "mahi", "kaupapa").

## Branches

- `main` — releases only; merge from `develop` via PR
- `develop` — main development branch
- Feature branches off `develop` for all new work
````

- [ ] **Step 2: Link `CLAUDE.md`**

Run: `ln -s AGENTS.md CLAUDE.md`

- [ ] **Step 3: Write `.gitignore`, `.infra-paths` and `renovate.json`**

`.gitignore`:

```text
# Agent worktrees
.claude/worktrees/

# Terraform
# The module's own lock file isn't committed (modules don't pin providers for
# their callers); infra/github's is.
/.terraform.lock.hcl
.terraform/
.terraform.tfstate.lock.info
terraform.tfstate*
```

`.infra-paths`:

```text
^(infra/|[^/]+\.tf$)
```

`renovate.json`:

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "helpers:pinGitHubActionDigests"
  ]
}
```

- [ ] **Step 4: Verify**

Run: `test -L CLAUDE.md && test "$(readlink CLAUDE.md)" = AGENTS.md && python3 -m json.tool renovate.json >/dev/null && echo ok`
Expected: `ok`

- [ ] **Step 5: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill. Don't push: Task 6 makes the first push, so the pre-push hook runs on it.

---

### Task 2: The module

**Files:**
- Create: `tests/repository.tftest.hcl`, `versions.tf`, `variables.tf`, `main.tf`, `outputs.tf`

**Interfaces:**
- Produces: module inputs `description`, `homepage_url`, `local_path`, `name`, `renovate_installation_id`, `topics`, `visibility`; outputs `html_url`, `http_clone_url`, `ssh_clone_url`; resource address `github_repository.this` (the bootstrap import target, as `module.repository.github_repository.this`); `local.enable_security_and_analysis`.

- [ ] **Step 1: Write the failing tests**

`tests/repository.tftest.hcl`:

```hcl
# Index lookups go through try() so one regression fails its own run instead
# erroring and skipping every run after it.
#
# Plan-only: the mock provider doesn't cover the built-in terraform_data push
# step, so `command = apply` would really run `git push`.
mock_provider "github" {}

variables {
  description = "Test repository"
  name        = "test-repository"
}

run "repo_settings_match_the_standard" {
  command = plan

  assert {
    condition = (
      github_repository.this.allow_merge_commit
      && !github_repository.this.allow_squash_merge
      && !github_repository.this.allow_rebase_merge
      && !github_repository.this.allow_auto_merge
      && !github_repository.this.allow_update_branch
      && github_repository.this.delete_branch_on_merge
    )
    error_message = "Merge settings must be merge-commit only, with branch deletion on merge."
  }

  assert {
    condition = (
      github_repository.this.has_issues
      && !github_repository.this.has_wiki
      && !github_repository.this.has_projects
      && !github_repository.this.has_discussions
    )
    error_message = "Only issues may be enabled among the repo features."
  }

  assert {
    condition     = github_repository.this.archive_on_destroy
    error_message = "A destroy must archive the repo, not delete it."
  }
}

run "public_repo_enables_secret_scanning" {
  command = plan

  assert {
    condition     = local.enable_security_and_analysis
    error_message = "A public repo must enable security_and_analysis."
  }

  assert {
    condition     = try(github_repository.this.security_and_analysis[0].secret_scanning[0].status, null) == "enabled"
    error_message = "A public repo must enable secret scanning."
  }

  assert {
    condition     = try(github_repository.this.security_and_analysis[0].secret_scanning_push_protection[0].status, null) == "enabled"
    error_message = "A public repo must enable push protection."
  }
}

run "private_repo_omits_secret_scanning" {
  command = plan

  variables {
    visibility = "private"
  }

  assert {
    condition     = !local.enable_security_and_analysis
    error_message = "A private repo must omit security_and_analysis."
  }
}

run "visibility_rejects_other_values" {
  command = plan

  variables {
    visibility = "internal"
  }

  expect_failures = [var.visibility]
}

run "trunk_main_has_no_bypass" {
  command = plan

  assert {
    condition     = length(github_repository_ruleset.trunk["main"].bypass_actors) == 0
    error_message = "trunk-main must have no bypass actor."
  }
}

run "trunk_develop_bypass_is_admin_only" {
  command = plan

  assert {
    condition     = length(github_repository_ruleset.trunk["develop"].bypass_actors) == 1
    error_message = "trunk-develop must have exactly one bypass actor."
  }

  assert {
    condition = (
      try(github_repository_ruleset.trunk["develop"].bypass_actors[0].actor_id, null) == 5
      && try(github_repository_ruleset.trunk["develop"].bypass_actors[0].actor_type, null) == "RepositoryRole"
      && try(github_repository_ruleset.trunk["develop"].bypass_actors[0].bypass_mode, null) == "always"
    )
    error_message = "trunk-develop's bypass actor must be the Admin role, always."
  }
}

run "trunk_rulesets_require_strict_gate_and_merge_only" {
  command = plan

  assert {
    condition = alltrue([
      for branch in ["develop", "main"] :
      one(github_repository_ruleset.trunk[branch].conditions[0].ref_name[0].include) == "refs/heads/${branch}"
    ])
    error_message = "Each trunk ruleset must target its own branch."
  }

  assert {
    condition = alltrue([
      for branch in ["develop", "main"] :
      github_repository_ruleset.trunk[branch].rules[0].required_status_checks[0].strict_required_status_checks_policy
    ])
    error_message = "Both trunk rulesets must require branches to be up to date."
  }

  assert {
    condition = alltrue([
      for branch in ["develop", "main"] :
      length(github_repository_ruleset.trunk[branch].rules[0].required_status_checks[0].required_check) == 1
      && anytrue([
        for check in github_repository_ruleset.trunk[branch].rules[0].required_status_checks[0].required_check :
        check.context == "gate" && check.integration_id == 15368
      ])
    ])
    error_message = "Both trunk rulesets must require exactly the gate check from GitHub Actions."
  }

  assert {
    condition = alltrue([
      for branch in ["develop", "main"] :
      toset(github_repository_ruleset.trunk[branch].rules[0].pull_request[0].allowed_merge_methods) == toset(["merge"])
    ])
    error_message = "Both trunk rulesets must allow merge commits only."
  }
}

run "tags_ruleset_covers_all_tags" {
  command = plan

  assert {
    condition = (
      github_repository_ruleset.tags_release.target == "tag"
      && one(github_repository_ruleset.tags_release.conditions[0].ref_name[0].include) == "~ALL"
      && length(github_repository_ruleset.tags_release.bypass_actors) == 0
    )
    error_message = "tags-release must cover every tag with no bypass actor."
  }
}

run "renovate_absent_without_installation_id" {
  command = plan

  assert {
    condition     = length(github_app_installation_repository.renovate) == 0
    error_message = "No Renovate installation ID must mean no installation resource."
  }
}

run "renovate_present_with_installation_id" {
  command = plan

  variables {
    renovate_installation_id = "12345"
  }

  assert {
    condition     = length(github_app_installation_repository.renovate) == 1
    error_message = "A Renovate installation ID must add the repo to that installation."
  }
}
```

Then write `versions.tf` alone, so `init` has a provider to fetch:

`versions.tf`:

```hcl
terraform {
  required_version = ">= 1.9"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.13"
    }
  }
}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `terraform init -input=false -backend=false && terraform test`
Expected: FAIL, with errors about references to undeclared resources (`github_repository.this` and the rest).

- [ ] **Step 3: Write the module**

`variables.tf`:

```hcl
variable "description" {
  description = "Repository description."
  type        = string
}

variable "homepage_url" {
  default     = null
  description = "Repository homepage URL, or null for none."
  type        = string
}

variable "local_path" {
  default     = null
  description = "A path inside the local git checkout to push from. Null means the root module's directory; git finds the checkout by walking up."
  type        = string
}

variable "name" {
  description = "Repository name."
  type        = string
}

variable "renovate_installation_id" {
  default     = null
  description = "Installation ID of the Renovate GitHub App, or null to leave the repo out of Renovate's installation."
  type        = string
}

variable "topics" {
  default     = []
  description = "Repository topics."
  type        = list(string)
}

variable "visibility" {
  default     = "public"
  description = "Repository visibility: public or private."
  type        = string

  validation {
    condition     = contains(["private", "public"], var.visibility)
    error_message = "visibility must be \"public\" or \"private\"."
  }
}
```

`main.tf`:

```hcl
locals {
  # GitHub's numeric ID for the Admin repository role, used as a ruleset bypass actor
  admin_repository_role_id = 5
  # Secret scanning and push protection need GitHub Advanced Security on a private repo
  enable_security_and_analysis = var.visibility == "public"
  # The GitHub Actions app, which reports the `gate` check
  github_actions_integration_id = 15368
  push_path                     = coalesce(var.local_path, path.root)
  trunk_branches                = toset(["develop", "main"])
}

resource "github_repository" "this" {
  allow_auto_merge       = false
  allow_merge_commit     = true
  allow_rebase_merge     = false
  allow_squash_merge     = false
  allow_update_branch    = false
  archive_on_destroy     = true
  delete_branch_on_merge = true
  description            = var.description
  has_discussions        = false
  has_issues             = true
  has_projects           = false
  has_wiki               = false
  homepage_url           = var.homepage_url
  merge_commit_message   = "PR_BODY"
  merge_commit_title     = "PR_TITLE"
  name                   = var.name
  topics                 = var.topics
  visibility             = var.visibility

  # Keep this exact for_each form: the tests assert the local, because the
  # block's absence is unknown at plan time
  dynamic "security_and_analysis" {
    for_each = local.enable_security_and_analysis ? [1] : []

    content {
      secret_scanning {
        status = "enabled"
      }

      secret_scanning_push_protection {
        status = "enabled"
      }
    }
  }

  lifecycle {
    # The provider always sends has_downloads=false, and stores advanced_security
    # on read though it can't be set for public repos; either could otherwise
    # show a diff on every plan
    ignore_changes = [
      has_downloads,
      security_and_analysis[0].advanced_security,
    ]
  }
}

resource "github_repository_vulnerability_alerts" "this" {
  enabled    = true
  repository = github_repository.this.name
}

resource "github_repository_dependabot_security_updates" "this" {
  enabled    = false
  repository = github_repository.this.name

  depends_on = [github_repository_vulnerability_alerts.this]
}

# Pushes the local develop and main branches. Runs once per repo: it's
# replaced only when the repo is.
resource "terraform_data" "push" {
  triggers_replace = [github_repository.this.repo_id]

  provisioner "local-exec" {
    command = <<-EOT
      set -eu
      git remote get-url origin >/dev/null 2>&1 || git remote add origin "$SSH_URL"
      git push --no-verify origin develop main
    EOT
    environment = {
      SSH_URL = github_repository.this.ssh_clone_url
    }
    interpreter = ["/bin/sh", "-c"]
    working_dir = local.push_path
  }
}

resource "github_branch_default" "this" {
  branch     = "develop"
  repository = github_repository.this.name

  depends_on = [terraform_data.push]
}

# Created after the push: trunk-main has no bypass, so it would block the push
# that creates main
resource "github_repository_ruleset" "trunk" {
  for_each = local.trunk_branches

  enforcement = "active"
  name        = "trunk-${each.key}"
  repository  = github_repository.this.name
  target      = "branch"

  dynamic "bypass_actors" {
    for_each = each.key == "develop" ? [1] : []

    content {
      actor_id    = local.admin_repository_role_id
      actor_type  = "RepositoryRole"
      bypass_mode = "always"
    }
  }

  conditions {
    ref_name {
      exclude = []
      include = ["refs/heads/${each.key}"]
    }
  }

  rules {
    deletion         = true
    non_fast_forward = true

    pull_request {
      allowed_merge_methods             = ["merge"]
      dismiss_stale_reviews_on_push     = false
      require_code_owner_review         = false
      require_last_push_approval        = false
      required_approving_review_count   = 0
      required_review_thread_resolution = true
    }

    required_status_checks {
      do_not_enforce_on_create             = false
      strict_required_status_checks_policy = true

      required_check {
        context        = "gate"
        integration_id = local.github_actions_integration_id
      }
    }
  }

  depends_on = [github_branch_default.this]
}

resource "github_repository_ruleset" "tags_release" {
  enforcement = "active"
  name        = "tags-release"
  repository  = github_repository.this.name
  target      = "tag"

  conditions {
    ref_name {
      exclude = []
      include = ["~ALL"]
    }
  }

  rules {
    deletion         = true
    non_fast_forward = true
  }

  depends_on = [github_branch_default.this]
}

resource "github_app_installation_repository" "renovate" {
  count = var.renovate_installation_id == null ? 0 : 1

  installation_id = var.renovate_installation_id
  repository      = github_repository.this.name
}
```

`outputs.tf`:

```hcl
output "html_url" {
  description = "The repository's web URL."
  value       = github_repository.this.html_url
}

output "http_clone_url" {
  description = "The repository's HTTPS clone URL."
  value       = github_repository.this.http_clone_url
}

output "ssh_clone_url" {
  description = "The repository's SSH clone URL."
  value       = github_repository.this.ssh_clone_url
}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `terraform fmt -check -recursive && terraform validate && terraform test`
Expected: `Success! 10 passed, 0 failed.`

The plan reviewer built provider v6.13.0 from source and got exactly this result. If a comparison assertion fails on a type mismatch rather than a wrong value, fix the assertion's types, never the expected value.

- [ ] **Step 5: Prove each assertion can fail**

Run `git add main.tf` once, so the index holds a clean copy. Then for each mutation below: apply it, run `terraform test`, confirm the named run fails, and restore with `git checkout -- main.tf`.

| Mutation in `main.tf` | Run that must fail |
|---|---|
| `for_each = each.key == "develop" ? [1] : []` → `for_each = [1]` | `trunk_main_has_no_bypass` |
| `bypass_mode = "always"` → `bypass_mode = "pull_request"` | `trunk_develop_bypass_is_admin_only` |
| `strict_required_status_checks_policy = true` → `false` | `trunk_rulesets_require_strict_gate_and_merge_only` |
| `allowed_merge_methods             = ["merge"]` → `["merge", "squash"]` | `trunk_rulesets_require_strict_gate_and_merge_only` |
| `enable_security_and_analysis = var.visibility == "public"` → `= var.visibility != "public"` | `public_repo_enables_secret_scanning`, `private_repo_omits_secret_scanning` |
| `for_each = local.enable_security_and_analysis ? [1] : []` → `for_each = []` | `public_repo_enables_secret_scanning` |
| `count = var.renovate_installation_id == null ? 0 : 1` → `count = 0` | `renovate_present_with_installation_id` |
| `allow_squash_merge     = false` → `true` | `repo_settings_match_the_standard` |
| `has_wiki               = false` → `true` | `repo_settings_match_the_standard` |
| `archive_on_destroy     = true` → `false` | `repo_settings_match_the_standard` |
| `include = ["refs/heads/${each.key}"]` → `include = ["refs/heads/main"]` | `trunk_rulesets_require_strict_gate_and_merge_only` |
| `context        = "gate"` → `"build"` | `trunk_rulesets_require_strict_gate_and_merge_only` |
| `include = ["~ALL"]` → `include = ["v*"]` | `tags_ruleset_covers_all_tags` |
| In `variables.tf` (`git add` it first, restore with `git checkout -- variables.tf`): `contains(["private", "public"]` → `contains(["internal", "private", "public"]` | `visibility_rejects_other_values` |

A `for_each` that always emits the `security_and_analysis` block can't be caught at plan time (its absence for `private` is unknown); that's why the exact `for_each` form is required and reviewed instead.

- [ ] **Step 6: Commit**

Run `git status` to catch any related unstaged or untracked files (the root `.terraform.lock.hcl` shouldn't appear; it's ignored), then use the `creative-commits` skill. Don't push: Task 6 makes the first push, so the pre-push hook runs on it.

---

### Task 3: Plan script, pre-push hook and fixture tests

**Files:**
- Create: `tests/infra-plan/test.sh`, `scripts/infra-plan`, `.githooks/pre-push` (all executable)

**Interfaces:**
- Consumes: `.infra-paths` (Task 1).
- Produces: `scripts/infra-plan` with plan mode (no args) and subcommands `hash` (prints the infra hash), `changed BASE HEAD` (exit 0 changed / 1 unchanged / ≥2 error), `dirty` (exit 0 dirty / 1 clean). Plan comments start with `<!-- infra-plan -->` and carry `<!-- infra-hash: HASH -->`, which CI matches (Task 4).

- [ ] **Step 1: Write the fixture tests**

`tests/infra-plan/test.sh`:

```bash
#!/usr/bin/env bash
# Fixture tests for scripts/infra-plan and .githooks/pre-push. Each test builds
# a throwaway git repo, so nothing here touches this checkout or the network.
set -euo pipefail

here=$(cd "$(dirname "$0")" && pwd)
repo_root=$(cd "$here/../.." && pwd)
module_pattern='^(infra/|[^/]+\.tf$)'
project_pattern='^infra/'
# Pinned per pattern; a mismatch on one platform means the hash isn't portable
golden_module_hash=b69ad3327bdbcd34bd061429df19e5d9999c0f89
golden_project_hash=2a10bd4297bb11b363727d9c77c879fbcbacf2e3

# Keep the maintainer's own git config (signing, hooks) out of the fixtures
export GIT_CONFIG_GLOBAL=/dev/null
export GIT_CONFIG_NOSYSTEM=1

failures=0
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

pass() {
  echo "✅ $1"
}

fail() {
  echo "❌ $1"
  failures=$((failures + 1))
}

check() {
  local name=$1
  shift
  if "$@"; then
    pass "$name"
  else
    fail "$name"
  fi
}

# A PATH with the script's dependencies and nothing else, so a terraform or gh
# on the maintainer's machine can't leak into a test
minimal_bin="$work/bin"
mkdir -p "$minimal_bin"
for tool in bash cat git head mktemp perl rm tail tee tr wc; do
  ln -s "$(command -v "$tool")" "$minimal_bin/$tool"
done

stub_bin="$work/stubs"
mkdir -p "$stub_bin"
cat > "$stub_bin/terraform" <<'STUB'
#!/usr/bin/env bash
case " $* " in
  *" init "*)
    case "${STUB_INIT:-ok}" in
      fail)
        echo "Error: stub init failure" >&2
        exit 7
        ;;
      rewrite-lock)
        echo "# rewritten by init" >> infra/github/.terraform.lock.hcl
        ;;
    esac
    ;;
  *" validate "*)
    echo "Success! The configuration is valid."
    ;;
  *" plan "*)
    if [[ -n "${STUB_PLAN_BYTES:-}" ]]; then
      head -c "$STUB_PLAN_BYTES" /dev/zero | tr '\0' 'x'
    else
      echo "No changes."
    fi
    ;;
esac
STUB
cat > "$stub_bin/gh" <<'STUB'
#!/usr/bin/env bash
log() {
  echo "$*" >> "$STUB_LOG"
}
case "$1 $2" in
  "pr view")
    if [[ -z "${STUB_PR:-}" ]]; then
      exit 1
    fi
    echo "$STUB_PR"
    ;;
  "run list")
    case "$*" in
      *databaseId,status*)
        echo "${STUB_RUN_PENDING:-}"
        ;;
      *)
        echo "${STUB_RUN_FAILED:-}"
        ;;
    esac
    ;;
  "run rerun")
    log "RERUN $4"
    ;;
  *)
    case "$*" in
      *"--method PATCH"*|*"--method POST"*)
        for arg in "$@"; do
          case "$arg" in
            body=*)
              body=${arg#body=}
              ;;
          esac
        done
        log "$3 ${#body}"
        printf '%s' "$body" > "$STUB_LOG.body"
        ;;
      *--paginate*)
        echo "${STUB_COMMENT_ID:-}"
        ;;
    esac
    ;;
esac
STUB
chmod +x "$stub_bin/terraform" "$stub_bin/gh"

# Builds a fixture repo with a fixed tree and one commit, on branch develop
new_repo() {
  local pattern=$1 dir
  dir=$(mktemp -d "$work/repo.XXXXXX")
  (
    cd "$dir"
    git init -q -b develop
    git config user.email test@example.com
    git config user.name Test
    mkdir -p .githooks infra/github scripts tests/fx
    printf '%s\n' "$pattern" > .infra-paths
    printf '.terraform/\nterraform.tfstate*\n' > .gitignore
    printf 'resource "x" "y" {}\n' > main.tf
    printf 'module "m" {}\n' > infra/github/main.tf
    printf '# lock\n' > infra/github/.terraform.lock.hcl
    printf 'run "t" {}\n' > tests/fx/broken.tf
    cp "$repo_root/scripts/infra-plan" scripts/infra-plan
    cp "$repo_root/.githooks/pre-push" .githooks/pre-push
    git add -A
    git commit -q -m fixture
  )
  echo "$dir"
}

commit_all() {
  (cd "$1" && git add -A && git commit -q -m change)
}

infra_plan() {
  local repo=$1
  shift
  (cd "$repo" && scripts/infra-plan "$@")
}

hash_of() {
  infra_plan "$1" hash
}

# Runs `changed` from the fixture's first commit to HEAD; prints the exit code
changed_status() {
  local repo=$1 first
  first=$(cd "$repo" && git rev-list --max-parents=0 HEAD)
  set +e
  infra_plan "$repo" changed "$first" HEAD >/dev/null 2>&1
  echo $?
  set -e
}

dirty_status() {
  set +e
  infra_plan "$1" dirty >/dev/null
  echo $?
  set -e
}

# Runs plan mode with the stubs on PATH; prints combined output, then the exit
# code on the last line
plan_with_stubs() {
  local repo=$1
  set +e
  (cd "$repo" && PATH="$stub_bin:$minimal_bin" STUB_LOG="$repo/.stub-log" scripts/infra-plan 2>&1)
  echo "exit=$?"
  set -e
}

state_present() {
  printf '{}\n' > "$1/infra/github/terraform.tfstate"
}

# --- hash -------------------------------------------------------------------

test_hash_golden_module() {
  [[ "$(hash_of "$(new_repo "$module_pattern")")" == "$golden_module_hash" ]]
}

test_hash_golden_project() {
  [[ "$(hash_of "$(new_repo "$project_pattern")")" == "$golden_project_hash" ]]
}

test_hash_root_tf_module() {
  local repo before
  repo=$(new_repo "$module_pattern")
  before=$(hash_of "$repo")
  printf 'resource "x" "z" {}\n' > "$repo/main.tf"
  commit_all "$repo"
  [[ "$(hash_of "$repo")" != "$before" ]]
}

test_hash_root_tf_project() {
  local repo before
  repo=$(new_repo "$project_pattern")
  before=$(hash_of "$repo")
  printf 'resource "x" "z" {}\n' > "$repo/main.tf"
  commit_all "$repo"
  [[ "$(hash_of "$repo")" == "$before" ]]
}

test_hash_moved_out() {
  local repo before
  repo=$(new_repo "$project_pattern")
  before=$(hash_of "$repo")
  (cd "$repo" && git mv infra/github/main.tf moved.txt)
  commit_all "$repo"
  [[ "$(hash_of "$repo")" != "$before" ]]
}

test_hash_non_ascii() {
  local repo before
  repo=$(new_repo "$project_pattern")
  before=$(hash_of "$repo")
  printf 'x\n' > "$repo/infra/github/fü.tf"
  commit_all "$repo"
  [[ "$(hash_of "$repo")" != "$before" ]]
}

test_hash_ignores_test_fixture() {
  local repo before
  repo=$(new_repo "$module_pattern")
  before=$(hash_of "$repo")
  printf 'run "u" {}\n' > "$repo/tests/fx/broken.tf"
  commit_all "$repo"
  [[ "$(hash_of "$repo")" == "$before" ]]
}

# --- changed ----------------------------------------------------------------

test_changed_root_tf_module() {
  local repo
  repo=$(new_repo "$module_pattern")
  printf 'resource "x" "z" {}\n' > "$repo/main.tf"
  commit_all "$repo"
  [[ "$(changed_status "$repo")" == 0 ]]
}

test_changed_root_tf_project() {
  local repo
  repo=$(new_repo "$project_pattern")
  printf 'resource "x" "z" {}\n' > "$repo/main.tf"
  commit_all "$repo"
  [[ "$(changed_status "$repo")" == 1 ]]
}

test_changed_moved_out() {
  local repo
  repo=$(new_repo "$project_pattern")
  (cd "$repo" && git mv infra/github/main.tf moved.txt)
  commit_all "$repo"
  [[ "$(changed_status "$repo")" == 0 ]]
}

test_changed_non_ascii() {
  local repo
  repo=$(new_repo "$project_pattern")
  printf 'x\n' > "$repo/infra/github/fü.tf"
  commit_all "$repo"
  [[ "$(changed_status "$repo")" == 0 ]]
}

test_changed_ignores_test_fixture() {
  local repo
  repo=$(new_repo "$module_pattern")
  printf 'run "u" {}\n' > "$repo/tests/fx/broken.tf"
  commit_all "$repo"
  [[ "$(changed_status "$repo")" == 1 ]]
}

test_changed_unknown_base() {
  local repo status
  repo=$(new_repo "$project_pattern")
  set +e
  infra_plan "$repo" changed 0123456789abcdef0123456789abcdef01234567 HEAD >/dev/null 2>&1
  status=$?
  set -e
  [[ "$status" -ge 2 ]]
}

# --- dirty ------------------------------------------------------------------

test_dirty_clean() {
  [[ "$(dirty_status "$(new_repo "$module_pattern")")" == 1 ]]
}

test_dirty_untracked_infra() {
  local repo
  repo=$(new_repo "$project_pattern")
  printf 'x\n' > "$repo/infra/github/new.tf"
  [[ "$(dirty_status "$repo")" == 0 ]]
}

test_dirty_root_tf_module() {
  local repo
  repo=$(new_repo "$module_pattern")
  printf 'resource "x" "z" {}\n' > "$repo/main.tf"
  [[ "$(dirty_status "$repo")" == 0 ]]
}

test_dirty_root_tf_project() {
  local repo
  repo=$(new_repo "$project_pattern")
  printf 'resource "x" "z" {}\n' > "$repo/main.tf"
  [[ "$(dirty_status "$repo")" == 1 ]]
}

test_dirty_ignores_test_fixture() {
  local repo
  repo=$(new_repo "$module_pattern")
  printf 'run "u" {}\n' > "$repo/tests/fx/new.tf"
  [[ "$(dirty_status "$repo")" == 1 ]]
}

test_dirty_moved_out() {
  local repo
  repo=$(new_repo "$project_pattern")
  (cd "$repo" && git mv infra/github/main.tf moved.txt)
  [[ "$(dirty_status "$repo")" == 0 ]]
}

test_dirty_non_ascii() {
  local repo
  repo=$(new_repo "$project_pattern")
  printf 'x\n' > "$repo/infra/github/fü.tf"
  [[ "$(dirty_status "$repo")" == 0 ]]
}

# --- plan mode --------------------------------------------------------------

test_plan_without_terraform() {
  local repo output
  repo=$(new_repo "$project_pattern")
  set +e
  output=$(cd "$repo" && PATH="$minimal_bin" scripts/infra-plan 2>&1; echo "exit=$?")
  set -e
  [[ "$output" == *"terraform not installed"* && "$output" == *"exit=0" ]]
}

test_plan_without_state() {
  local output
  output=$(plan_with_stubs "$(new_repo "$project_pattern")")
  [[ "$output" == *"state not available"* && "$output" == *"configuration is valid"* && "$output" == *"exit=0" ]]
}

test_plan_init_failure() {
  local output
  output=$(STUB_INIT=fail plan_with_stubs "$(new_repo "$project_pattern")")
  [[ "$output" == *"init failed"* && "$output" == *"exit=7" ]]
}

test_plan_init_rewrites_lock() {
  local repo output
  repo=$(new_repo "$project_pattern")
  state_present "$repo"
  output=$(STUB_INIT=rewrite-lock plan_with_stubs "$repo")
  [[ "$output" == *"init changed the lock file"* && "$output" == *"exit=1" ]]
}

test_plan_no_pr() {
  local repo output
  repo=$(new_repo "$project_pattern")
  state_present "$repo"
  output=$(plan_with_stubs "$repo")
  [[ "$output" == *"no PR yet"* && "$output" == *"exit=0" && ! -f "$repo/.stub-log" ]]
}

test_plan_posts_new_comment() {
  local repo output
  repo=$(new_repo "$project_pattern")
  state_present "$repo"
  output=$(STUB_PR=5 plan_with_stubs "$repo")
  [[ "$output" == *"exit=0" ]] \
    && [[ "$(cat "$repo/.stub-log")" == POST* ]] \
    && [[ "$(cat "$repo/.stub-log.body")" == *"<!-- infra-hash: $(hash_of "$repo") -->"* ]]
}

test_plan_updates_existing_comment() {
  local repo
  repo=$(new_repo "$project_pattern")
  state_present "$repo"
  STUB_PR=5 STUB_COMMENT_ID=99 plan_with_stubs "$repo" >/dev/null
  [[ "$(cat "$repo/.stub-log")" == PATCH* ]]
}

test_plan_truncates_huge_plan() {
  local repo length
  repo=$(new_repo "$project_pattern")
  state_present "$repo"
  STUB_PR=5 STUB_PLAN_BYTES=70000 plan_with_stubs "$repo" >/dev/null
  [[ -f "$repo/.stub-log" ]] || return 1
  length=$(cut -d' ' -f2 < "$repo/.stub-log")
  [[ "$length" -gt 60000 && "$length" -le 65536 ]] \
    && [[ "$(cat "$repo/.stub-log.body")" == *"Plan truncated"* ]]
}

test_plan_dirty_skips_comment() {
  local repo output
  repo=$(new_repo "$project_pattern")
  state_present "$repo"
  printf 'x\n' > "$repo/infra/github/new.tf"
  output=$(STUB_PR=5 plan_with_stubs "$repo")
  [[ "$output" == *"comment not posted"* && ! -f "$repo/.stub-log" ]]
}

test_plan_reruns_failed_run() {
  local repo
  repo=$(new_repo "$project_pattern")
  state_present "$repo"
  STUB_PR=5 STUB_RUN_FAILED=42 plan_with_stubs "$repo" >/dev/null
  [[ "$(cat "$repo/.stub-log")" == *"RERUN 42"* ]]
}

test_plan_reports_pending_run() {
  local repo output
  repo=$(new_repo "$project_pattern")
  state_present "$repo"
  output=$(STUB_PR=5 STUB_RUN_PENDING=43 STUB_RUN_FAILED=42 plan_with_stubs "$repo")
  [[ "$output" == *"still in progress"* && "$(cat "$repo/.stub-log")" != *RERUN* ]]
}

# --- pre-push hook ----------------------------------------------------------

zero=0000000000000000000000000000000000000000

# Feeds one ref line to the fixture's hook with no terraform on PATH, so a plan
# run shows up as the "terraform not installed" warning; prints output and exit
run_hook() {
  local repo=$1 line=$2
  set +e
  (cd "$repo" && printf '%s\n' "$line" | PATH="$minimal_bin" .githooks/pre-push origin url 2>&1)
  echo "exit=$?"
  set -e
}

test_hook_skips_deletion() {
  local repo output
  repo=$(new_repo "$project_pattern")
  output=$(run_hook "$repo" "(delete) $zero refs/heads/old $(cd "$repo" && git rev-parse HEAD)")
  [[ "$output" != *"terraform not installed"* && "$output" == *"exit=0" ]]
}

test_hook_skips_other_branch() {
  local repo head output
  repo=$(new_repo "$project_pattern")
  head=$(cd "$repo" && git rev-parse HEAD)
  output=$(run_hook "$repo" "refs/heads/other $head refs/heads/other $zero")
  [[ "$output" == *"isn't the checked-out branch"* && "$output" != *"terraform not installed"* ]]
}

test_hook_plans_infra_change() {
  local repo first head output
  repo=$(new_repo "$project_pattern")
  first=$(cd "$repo" && git rev-parse HEAD)
  printf 'module "n" {}\n' > "$repo/infra/github/main.tf"
  commit_all "$repo"
  head=$(cd "$repo" && git rev-parse HEAD)
  output=$(run_hook "$repo" "refs/heads/develop $head refs/heads/develop $first")
  [[ "$output" == *"terraform not installed"* && "$output" == *"exit=0" ]]
}

test_hook_skips_unrelated_change() {
  local repo first head output
  repo=$(new_repo "$project_pattern")
  first=$(cd "$repo" && git rev-parse HEAD)
  printf 'readme\n' > "$repo/README.md"
  commit_all "$repo"
  head=$(cd "$repo" && git rev-parse HEAD)
  output=$(run_hook "$repo" "refs/heads/develop $head refs/heads/develop $first")
  [[ "$output" != *"terraform not installed"* && "$output" == *"exit=0" ]]
}

test_hook_new_branch_uses_origin_develop() {
  local repo first head output
  repo=$(new_repo "$project_pattern")
  first=$(cd "$repo" && git rev-parse HEAD)
  (cd "$repo" && git update-ref refs/remotes/origin/develop "$first" && git checkout -q -b feature)
  printf 'module "n" {}\n' > "$repo/infra/github/main.tf"
  commit_all "$repo"
  head=$(cd "$repo" && git rev-parse HEAD)
  output=$(run_hook "$repo" "refs/heads/feature $head refs/heads/feature $zero")
  [[ "$output" == *"terraform not installed"* ]]
}

test_hook_blocks_without_origin_develop() {
  local repo head output
  repo=$(new_repo "$project_pattern")
  (cd "$repo" && git checkout -q -b feature)
  head=$(cd "$repo" && git rev-parse HEAD)
  output=$(run_hook "$repo" "refs/heads/feature $head refs/heads/feature $zero")
  [[ "$output" == *"fetch and retry"* && "$output" != *"exit=0" ]]
}

# ONLY="test_a test_b" runs a subset
for test_name in ${ONLY:-$(declare -F | awk "{print \$3}" | grep "^test_")}; do
  check "$test_name" "$test_name"
done

if [[ "$failures" -gt 0 ]]; then
  echo "❌ $failures test(s) failed"
  exit 1
fi
echo "✅ all tests passed"
```

Run: `chmod +x tests/infra-plan/test.sh`

- [ ] **Step 2: Run the tests to verify they fail**

Run: `tests/infra-plan/test.sh`
Expected: FAIL, ending `❌ N test(s) failed`, with `cp` reporting that `scripts/infra-plan` doesn't exist. A few tests may pass vacuously at this point (two empty hashes compare equal); Step 5's mutations are what prove the suite.

- [ ] **Step 3: Write the script and the hook**

`scripts/infra-plan`:

````bash
#!/usr/bin/env bash
# Plans this repo's infra changes and posts the plan to the branch's PR.
#
# Canonical copy: todofixthis/terraform-github-repository. Template repos ship
# it verbatim; only .infra-paths differs between repos.
#
# Usage:
#   scripts/infra-plan                     plan, then post to the PR
#   scripts/infra-plan hash                print the infra hash
#   scripts/infra-plan changed BASE HEAD   exit 0 if the infra paths changed
#                                          since merge-base(BASE, HEAD), 1 if
#                                          not, 2 or more on error
#   scripts/infra-plan dirty               exit 0 if the infra paths have
#                                          uncommitted or untracked changes,
#                                          1 if not
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

infra_dir=infra/github
lock_file="$infra_dir/.terraform.lock.hcl"
marker='<!-- infra-plan -->'
# GitHub rejects comment bodies over 65,536 characters
max_plan_bytes=60000

usage() {
  echo "usage: scripts/infra-plan [hash | changed BASE HEAD | dirty]" >&2
}

read_pattern() {
  if [[ ! -s .infra-paths ]]; then
    echo "❌ .infra-paths is missing or empty" >&2
    return 2
  fi
  head -n 1 .infra-paths
}

# Reads NUL-separated repo-relative paths on stdin and prints those matching
# the infra pattern, NUL-separated. chomp matters: Perl's $ doesn't match
# before a trailing NUL, so an anchored pattern would silently miss paths.
filter_paths() {
  perl -0 -ne 'chomp; print "$_\0" if m/$ENV{INFRA_PATH_PATTERN}/'
}

infra_hash() {
  git ls-tree -r -z HEAD \
    | perl -0 -ne 'chomp; my (undef, $path) = split /\t/, $_, 2; print "$_\0" if $path =~ m/$ENV{INFRA_PATH_PATTERN}/' \
    | git hash-object --stdin
}

changed() {
  local base=$1 head=$2 merge_base matches
  if ! git rev-parse --verify --quiet "$base^{commit}" >/dev/null; then
    echo "❌ unknown base: $base (fetch first?)" >&2
    return 2
  fi
  if ! git rev-parse --verify --quiet "$head^{commit}" >/dev/null; then
    echo "❌ unknown head: $head" >&2
    return 2
  fi
  if ! merge_base=$(git merge-base "$base" "$head"); then
    echo "❌ no merge-base between $base and $head" >&2
    return 2
  fi
  matches=$(git diff -z --name-only --no-renames "$merge_base" "$head" | filter_paths | tr '\0' '\n')
  if [[ -n "$matches" ]]; then
    printf '%s\n' "$matches"
    return 0
  fi
  return 1
}

dirty_paths() {
  git status --porcelain=v1 -z --no-renames --untracked-files=all \
    | perl -0 -ne 'chomp; my $path = substr($_, 3); print "$path\0" if $path =~ m/$ENV{INFRA_PATH_PATTERN}/' \
    | tr '\0' '\n'
}

dirty() {
  local paths
  paths=$(dirty_paths)
  if [[ -n "$paths" ]]; then
    printf '%s\n' "$paths"
    return 0
  fi
  return 1
}

lock_digest() {
  if [[ -f "$lock_file" ]]; then
    git hash-object "$lock_file"
  else
    echo absent
  fi
}

run_init() {
  local output status
  if output=$(terraform -chdir="$infra_dir" init -input=false -no-color "$@" 2>&1); then
    return 0
  else
    status=$?
  fi
  printf '%s\n' "$output" >&2
  echo "⚠️ init failed; on a module bump, run \`terraform init -upgrade\` then \`terraform providers lock -platform=darwin_amd64 -platform=darwin_arm64 -platform=linux_amd64 -platform=linux_arm64\`, and commit the lock" >&2
  return "$status"
}

check_lock() {
  if [[ "$(lock_digest)" != "$1" ]]; then
    echo "⚠️ init changed the lock file; commit it and re-run" >&2
    return 1
  fi
}

rerun_failed_ci() {
  local sha pending failed
  sha=$(git rev-parse HEAD)
  pending=$(gh run list --commit "$sha" --event pull_request --json databaseId,status \
    --jq '[.[] | select(.status != "completed")][0].databaseId // empty')
  if [[ -n "$pending" ]]; then
    echo "⚠️ CI run still in progress; if it fails, rerun with \`gh run rerun --failed $pending\`"
    return 0
  fi
  failed=$(gh run list --commit "$sha" --event pull_request --json databaseId,conclusion \
    --jq '[.[] | select(.conclusion == "failure")][0].databaseId // empty')
  if [[ -n "$failed" ]]; then
    gh run rerun --failed "$failed"
    echo "✅ reran failed jobs in run $failed"
  fi
}

post_comment() {
  local plan_file=$1 branch pr hash body comment_id
  if ! command -v gh >/dev/null 2>&1; then
    echo "⚠️ gh not installed; comment not posted"
    return 0
  fi
  if ! branch=$(git symbolic-ref --quiet --short HEAD); then
    echo "⏭️ detached HEAD; comment not posted"
    return 0
  fi
  if ! pr=$(gh pr view "$branch" --json number --jq .number 2>/dev/null) || [[ -z "$pr" ]]; then
    echo "⏭️ no PR yet; re-run once one exists"
    return 0
  fi
  hash=$(infra_hash)
  body=$(
    printf '%s\n<!-- infra-hash: %s -->\n### Terraform plan\n\nInfra hash `%s`.\n\n<details><summary>Plan</summary>\n\n```\n' "$marker" "$hash" "$hash"
    head -c "$max_plan_bytes" "$plan_file"
    printf '\n```\n\n</details>\n'
    if [[ "$(wc -c < "$plan_file")" -gt "$max_plan_bytes" ]]; then
      printf '\nPlan truncated; run `scripts/infra-plan` locally for the full output.\n'
    fi
  )
  comment_id=$(gh api --paginate "repos/{owner}/{repo}/issues/$pr/comments" \
    --jq ".[] | select(.body | startswith(\"$marker\")) | .id" | tail -n 1)
  if [[ -n "$comment_id" ]]; then
    gh api --method PATCH "repos/{owner}/{repo}/issues/comments/$comment_id" -f body="$body" >/dev/null
  else
    gh api --method POST "repos/{owner}/{repo}/issues/$pr/comments" -f body="$body" >/dev/null
  fi
  echo "✅ plan posted to PR #$pr"
  rerun_failed_ci
}

plan_mode() {
  local is_dirty="" lock_before plan_file status
  if ! command -v terraform >/dev/null 2>&1; then
    echo "⚠️ terraform not installed; cannot plan"
    return 0
  fi
  if [[ -n "$(dirty_paths)" ]]; then
    is_dirty=1
  fi
  lock_before=$(lock_digest)
  if [[ ! -f "$infra_dir/terraform.tfstate" ]]; then
    echo "⚠️ state not available; plan must run on the maintainer's machine"
    run_init -backend=false || return $?
    check_lock "$lock_before" || return $?
    terraform -chdir="$infra_dir" validate -no-color
    return $?
  fi
  run_init || return $?
  check_lock "$lock_before" || return $?
  plan_file=$(mktemp)
  set +e
  terraform -chdir="$infra_dir" plan -input=false -no-color | tee "$plan_file"
  status=${PIPESTATUS[0]}
  set -e
  if [[ "$status" -ne 0 ]]; then
    rm -f "$plan_file"
    return "$status"
  fi
  if [[ -n "$is_dirty" ]]; then
    echo "⚠️ infra paths are dirty; comment not posted"
  else
    post_comment "$plan_file"
  fi
  rm -f "$plan_file"
}

main() {
  INFRA_PATH_PATTERN=$(read_pattern)
  export INFRA_PATH_PATTERN
  case "${1:-}" in
    "")
      plan_mode
      ;;
    changed)
      if [[ $# -ne 3 ]]; then
        usage
        return 2
      fi
      changed "$2" "$3"
      ;;
    dirty)
      dirty
      ;;
    hash)
      infra_hash
      ;;
    *)
      usage
      return 2
      ;;
  esac
}

main "$@"
````

`.githooks/pre-push`:

```bash
#!/usr/bin/env bash
# Runs scripts/infra-plan when a push changes the infra paths. A non-zero exit
# from it blocks the push.
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
script="$repo_root/scripts/infra-plan"
current_branch=$(git symbolic-ref --quiet --short HEAD || true)
needs_plan=""

while read -r local_ref local_sha _remote_ref remote_sha; do
  # Deleting a branch pushes no commits to plan
  if [[ "$local_sha" =~ ^0+$ ]]; then
    continue
  fi
  # The script plans and hashes HEAD, so it can only speak for the checked-out branch
  if [[ "$local_ref" != "refs/heads/$current_branch" ]]; then
    echo "⏭️ $local_ref isn't the checked-out branch; skipping its infra plan"
    continue
  fi
  # A new branch has no remote SHA; compare against where it branched from
  if [[ "$remote_sha" =~ ^0+$ ]]; then
    base=origin/develop
  else
    base=$remote_sha
  fi
  set +e
  "$script" changed "$base" "$local_sha" </dev/null >/dev/null
  status=$?
  set -e
  case "$status" in
    0)
      needs_plan=1
      ;;
    1)
      ;;
    *)
      echo "❌ couldn't tell whether $local_ref changes the infra paths (exit $status); fetch and retry"
      exit "$status"
      ;;
  esac
done

if [[ -n "$needs_plan" ]]; then
  "$script" </dev/null
fi
```

Run: `chmod +x scripts/infra-plan .githooks/pre-push`

- [ ] **Step 4: Run the tests to verify they pass**

Run: `tests/infra-plan/test.sh | tail -n 1`
Expected: `✅ all tests passed`.
On macOS, also run it under the system bash 3.2: `d=$(mktemp -d) && ln -s /bin/bash "$d/bash" && PATH="$d:$PATH" tests/infra-plan/test.sh | tail -n 1`. Fix anything that fails there without dropping a test.

If the golden-hash tests fail, don't re-pin them: the hashes were computed on Linux and must match everywhere. Find what made your platform's `git ls-tree` output differ.

- [ ] **Step 5: Prove the safeguards are tested**

Run `git add scripts/infra-plan` once, so the index holds a clean copy. Then for each mutation: apply it, run `tests/infra-plan/test.sh`, confirm the named test fails, and restore with `git checkout -- scripts/infra-plan`.

| Mutation | Test that must fail |
|---|---|
| Remove `chomp; ` from the `infra_hash` Perl one-liner | `test_hash_root_tf_module` |
| `--name-only --no-renames` → `--name-only` | `test_changed_moved_out` |
| `--porcelain=v1 -z --no-renames` → `--porcelain=v1 -z` | `test_dirty_moved_out` |
| `head -c "$max_plan_bytes" "$plan_file"` → `cat "$plan_file"` | `test_plan_truncates_huge_plan` |
| `if [[ -n "$comment_id" ]]; then` → `if false; then` | `test_plan_updates_existing_comment` |
| `if [[ -n "$is_dirty" ]]; then` → `if false; then` | `test_plan_dirty_skips_comment` |

- [ ] **Step 6: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill. Don't push: Task 6 makes the first push, so the pre-push hook runs on it.

---

### Task 4: Self-provisioning root and CI

**Files:**
- Create: `infra/github/main.tf`, `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: the module (Task 2); `scripts/infra-plan hash` and `changed` (Task 3).
- Produces: the `gate` check context the rulesets require.

- [ ] **Step 1: Get the Renovate installation ID**

Ask the maintainer for the Renovate GitHub App's installation ID (GitHub → Settings → Applications → Renovate → Configure; it's the number at the end of the URL). It isn't secret. Also ask them to add `todofixthis/terraform-github-repository` to Renovate's selected repos only if they want that before bootstrap; the module adds it at apply either way.

- [ ] **Step 2: Write `infra/github/main.tf`**

Replace `RENOVATE_INSTALLATION_ID` with the ID from Step 1.

`infra/github/main.tf`:

```hcl
# This repo's own GitHub configuration, provisioned by the module it holds.
terraform {
  required_version = ">= 1.9"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

provider "github" {
  owner = "todofixthis"
}

module "repository" {
  source = "../.."

  description              = "Terraform module for the standard GitHub repo configuration of todofixthis projects"
  name                     = "terraform-github-repository"
  renovate_installation_id = "RENOVATE_INSTALLATION_ID"
}
```

- [ ] **Step 3: Write the workflow**

`.github/workflows/ci.yml`:

```yaml
name: CI

on:
  pull_request:
    branches: [develop, main]

# The plan-comment check lists PR comments; nothing here writes
permissions:
  contents: read
  issues: read
  pull-requests: read

concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number }}
  cancel-in-progress: true

# Log lines are prefixed to be scannable: ✅ done, ❌ failed, ⏭️ skipped, ▶️ starting.
jobs:
  # Does this PR change the infra paths? scripts/infra-plan owns that logic.
  changes:
    runs-on: ubuntu-latest
    outputs:
      infra: ${{ steps.filter.outputs.infra }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0
          ref: ${{ github.event.pull_request.head.sha }}

      - id: filter
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
        run: |
          set +e
          scripts/infra-plan changed "$BASE_SHA" "$HEAD_SHA"
          status=$?
          set -e
          case "$status" in
            0)
              echo "infra=true" >> "$GITHUB_OUTPUT"
              echo "✅ infra paths changed"
              ;;
            1)
              echo "infra=false" >> "$GITHUB_OUTPUT"
              echo "⏭️ no infra paths changed"
              ;;
            *)
              echo "❌ change detection failed (exit $status)"
              exit "$status"
              ;;
          esac

  terraform:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1

      - name: Check formatting
        run: terraform fmt -check -diff -recursive

      - name: Initialise the module
        run: terraform init -input=false -backend=false

      - name: Validate the module
        run: terraform validate

      - name: Test the module
        run: terraform test

      # A committed lock that init rewrites is stale
      - name: Validate the self-provisioning root
        run: |
          terraform -chdir=infra/github init -input=false -backend=false
          terraform -chdir=infra/github validate
          git diff --exit-code infra/github/.terraform.lock.hcl

  scripts:
    strategy:
      fail-fast: false
      matrix:
        os: [macos-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1

      # The maintainer's Mac runs these under the system bash, 3.2
      - name: Use the system bash on macOS
        if: runner.os == 'macOS'
        run: |
          mkdir -p "$RUNNER_TEMP/system-bash"
          ln -s /bin/bash "$RUNNER_TEMP/system-bash/bash"
          echo "$RUNNER_TEMP/system-bash" >> "$GITHUB_PATH"
          echo "✅ using $(/bin/bash --version | head -n 1)"

      - name: Run the script fixture tests
        run: tests/infra-plan/test.sh

  # Passes when the PR holds a plan comment for its current infra hash. Release
  # PRs into main are exempt: infra is applied from develop after merge.
  infra-plan:
    needs: changes
    if: needs.changes.outputs.infra == 'true' && github.event.pull_request.base.ref == 'develop'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          ref: ${{ github.event.pull_request.head.sha }}

      - name: Look for a plan comment matching the infra hash
        env:
          GH_TOKEN: ${{ github.token }}
          PR_NUMBER: ${{ github.event.pull_request.number }}
        run: |
          hash=$(scripts/infra-plan hash)
          echo "▶️ looking for a plan comment for infra hash $hash"
          found=$(gh api --paginate "repos/$GITHUB_REPOSITORY/issues/$PR_NUMBER/comments" \
            --jq ".[] | select((.author_association == \"OWNER\" or .author_association == \"COLLABORATOR\") and (.body | contains(\"<!-- infra-hash: $hash -->\"))) | .id")
          if [ -n "$found" ]; then
            echo "✅ plan comment found"
          else
            echo "❌ no plan comment for infra hash $hash; run scripts/infra-plan locally"
            exit 1
          fi

  # The single required status check. Skipped jobs would deadlock a ruleset that
  # required them directly; depending on them here collapses that into one result.
  gate:
    needs: [changes, infra-plan, scripts, terraform]
    if: always()
    runs-on: ubuntu-latest
    steps:
      - name: Fail if any check failed
        if: contains(needs.*.result, 'failure') || contains(needs.*.result, 'cancelled')
        run: |
          echo "❌ a required job failed or was cancelled"
          exit 1

      - name: Report success
        run: echo "✅ every required job passed or was skipped"
```

- [ ] **Step 4: Verify**

Run: `terraform fmt -check -recursive && terraform -chdir=infra/github init -input=false -backend=false && terraform -chdir=infra/github validate && uv run --no-project --with pyyaml python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))" && echo ok`
Expected: `Success! The configuration is valid.` then `ok`. `init` creates `infra/github/.terraform.lock.hcl`; leave it uncommitted for now (Task 7 generates the committed one for all four platforms).

- [ ] **Step 5: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill. Don't push: Task 6 makes the first push, so the pre-push hook runs on it.

---

### Task 5: README and ADRs

**Files:**
- Create: `README.md` (replaces the one-line README), `docs/adr/001-*.md`, `docs/adr/002-*.md`, `docs/adr/003-*.md`, `docs/adr/INDEX.md` (generated)

- [ ] **Step 1: Write `README.md`**

`README.md`:

````markdown
# terraform-github-repository

A Terraform module that creates a GitHub repo with the standard configuration of todofixthis projects, pushes its first commits, and applies its branch and tag rulesets.

## What it configures

- **Merging:** merge commits only, titled from the PR title and described from its body. Branches are deleted on merge; auto-merge and the "Update branch" button are off.
- **Features:** issues on; wiki, projects and discussions off.
- **Security:** secret scanning and push protection on for public repos; Dependabot alerts on; Dependabot security updates off (Renovate opens update PRs).
- **Branches:** `develop` is the default. `trunk-develop` and `trunk-main` block deletion and force-pushes, and require a PR with resolved threads and a passing, up-to-date `gate` check. The Admin role can bypass `trunk-develop`; nothing bypasses `trunk-main`.
- **Tags:** `tags-release` blocks deleting or moving any tag.
- **Destroy:** archives the repo rather than deleting it.

## Usage

```hcl
provider "github" {
  owner = "todofixthis"
}

module "repository" {
  source = "github.com/todofixthis/terraform-github-repository?ref=v1.0.0"

  description = "A short description of the project"
  name        = "my-project"
}
```

Run it from a checkout whose local `develop` and `main` branches hold the commits to push. The provider uses `GITHUB_TOKEN`, or `gh auth token` when that's unset.

| Input | Default | Notes |
|---|---|---|
| `name` | — | Repository name |
| `description` | — | Repository description |
| `homepage_url` | `null` | |
| `topics` | `[]` | |
| `visibility` | `"public"` | `"public"` or `"private"`. Private repos skip secret scanning and push protection. On GitHub Free, a private repo's rulesets may not be enforced. |
| `renovate_installation_id` | `null` | Adds the repo to that Renovate installation |
| `local_path` | root module directory | Where to run `git push` from |

Going from private to public takes two steps, because the provider can't do it in one apply: run `gh repo edit --visibility public --accept-visibility-change-consequences`, then plan and apply.

## Previewing infra changes

State is local, so CI can't plan. `scripts/infra-plan` plans on your machine and posts the plan to the branch's PR, and CI's `infra-plan` job fails until a plan comment matches the PR's current infra files. Run `git config core.hooksPath .githooks` once per clone, and the pre-push hook runs the script whenever a push changes them. After an infra PR merges, run `terraform -chdir=infra/github apply` from an up-to-date `develop`.
````

- [ ] **Step 2: Write the three ADRs with the `phx:writing-adrs` skill**

Scaffold each with the skill's `adr.py new`, then fill the body from the spec and this table, and run the skill's two review passes. Each ADR's Option 1 is "Do nothing".

| # | Title | `scope` | `summary` | `revisit-when` | Options beyond "Do nothing" (accepted first) |
|---|---|---|---|---|---|
| 001 | Share the GitHub repo standard as a versioned Terraform module | `[main.tf, variables.tf, versions.tf, outputs.tf]` | Provision every todofixthis repo through this versioned module, pinned by tag and updated by Renovate, not through per-template HCL copies or one central repo. | A private repo's apply shows GitHub refusing rulesets. Release automation needs the shared release App. | Shared module, pinned `?ref=vX.Y.Z` (accepted); HCL copied into each template; one central repo managing every repo in one state |
| 002 | Keep secrets out of Terraform state | `[main.tf, variables.tf, infra/]` | Never pass a secret through Terraform (no `sensitive` inputs, no `github_actions_secret`); set secrets with `gh secret set`. | Repo config moves to remote, encrypted state with CI-run plans. | `gh secret set` outside Terraform (accepted); remote encrypted state (S3/GCS with KMS, or HCP Terraform) holding secrets |
| 003 | Gate infra PRs on a locally posted plan comment | `[scripts/, .githooks/, .github/workflows/, .infra-paths]` | Gate PRs into develop that change infra paths on a plan comment posted by scripts/infra-plan from the maintainer's machine and matched by infra hash, since local state means CI can't plan. | Repo config moves to remote, encrypted state with CI-run plans. | Plan comment posted locally, checked by CI (accepted); remote state plus OIDC so CI plans; no preview at all |

What each ADR must carry beyond the table:
- **001:** why one shared App is the release-App design for the next iteration (Terraform has no resource for creating Apps; one key to rotate, one bypass identity), and that it will be passed by slug (for the App ID) plus installation ID. `archive_on_destroy` and why. The accepted non-enforcement of rulesets on private repos on GitHub Free, with "create rulesets for public repos only" as the answer if refusal shows up. Renovate distribution: module bumps arrive as Renovate PRs; script-changing releases need the template copies updated by hand; provider-constraint changes need a manual lock update on the bump branch.
- **002:** the breach signals (a `sensitive` input, a `github_actions_secret` resource) and why committed or unencrypted local state rules secrets out.
- **003:** the three layers (AGENTS.md rule for agents, pre-push hook for the maintainer, CI backstop), that the guard catches a forgotten plan rather than intent (a cloud agent posts as the maintainer), why the hash covers infra paths only, and that `scripts/infra-plan` is shared byte-identical with the template repos.

- [ ] **Step 3: Verify**

Run the skill's `adr.py check`.
Expected: exit 0.

- [ ] **Step 4: Run the writing passes**

`AGENTS.md` (Task 1), `README.md` and the ADRs are durable docs. Run the global writing passes on them: `phx:nz-english`, a surrogate review of `AGENTS.md` (agent audience) and `README.md` (human audience), and a conciseness pass. The ADR skill's own review passes cover the ADRs.

- [ ] **Step 5: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill. Don't push: Task 6 makes the first push, so the pre-push hook runs on it.

---

### Task 6: Open the PR

- [ ] **Step 1: Push and open a PR into `develop`**

`infra/github/.terraform.lock.hcl` from Task 4 must still be present (untracked); if it's gone, run `terraform -chdir=infra/github init -input=false -backend=false` first, or the script stops the push with "init changed the lock file".
Run: `git config core.hooksPath .githooks && git push -u origin feature/module-v1`
The pre-push hook runs `scripts/infra-plan`, which warns "state not available" (no state until Task 7) and validates. Open a PR from `feature/module-v1` into `develop`.

- [ ] **Step 2: Check CI**

Expected: `changes`, `terraform` and both `scripts` legs green; `infra-plan` red with "no plan comment", which is correct until Task 7 posts one; `gate` red because of it. Fix any other failure before going on. A failure in the macOS `scripts` leg is a bash 3.2 incompatibility; fix the script, not the test.

---

### Task 7: Bootstrap with the maintainer

Every step that writes to GitHub runs only after the maintainer has seen its plan and said yes.

- [ ] **Step 1: Generate and commit the lock file**

Run: `terraform -chdir=infra/github init -input=false && terraform -chdir=infra/github providers lock -platform=darwin_amd64 -platform=darwin_arm64 -platform=linux_amd64 -platform=linux_arm64`
Commit `infra/github/.terraform.lock.hcl` (run `git status` first, then the `creative-commits` skill). Don't push yet.

- [ ] **Step 2: Import the repo**

Run: `git fetch origin && git branch --force main origin/main && git branch --force develop origin/develop`
(The push step pushes local `develop` and `main`, so both must exist and match origin. Neither may be checked out in another worktree, or `git branch --force` refuses.)
Run: `terraform -chdir=infra/github import 'module.repository.github_repository.this' terraform-github-repository`

- [ ] **Step 3: Plan and apply**

Run: `terraform -chdir=infra/github plan -input=false`
Expected: in-place update of `github_repository.this` (wiki and projects off, merge settings; secret scanning may already be on), and creation of the alert settings, `terraform_data.push`, `github_branch_default.this`, both trunk rulesets, `tags_release` and the Renovate installation. Nothing destroyed. Show the plan to the maintainer; on their yes:
Run: `terraform -chdir=infra/github apply -input=false`
Expected: apply completes. The push step reports `develop` and `main` up to date.
If `github_app_installation_repository.renovate` fails with 403 or 404, re-run apply with `GITHUB_TOKEN` set to a classic PAT with `repo` scope (the spec's fallback). If apply fails on `security_and_analysis`, report it to the maintainer: it's a module fix on this branch before release. Renovate will probably open an onboarding PR, because `develop` has no `renovate.json` until this branch merges; close it after the merge.

- [ ] **Step 4: Confirm a second plan is empty**

Run: `terraform -chdir=infra/github plan -input=false -detailed-exitcode`
Expected: exit 0 ("No changes"). Exit 2 means drift: report the diff to the maintainer. If it's `has_downloads` or `advanced_security` despite `ignore_changes`, or an attribute the spec didn't anticipate, that's a module fix on this branch before release.

- [ ] **Step 5: Post the plan and pass the guard**

Run: `git push`
The pre-push hook sees the lock commit changed `infra/`, runs `scripts/infra-plan` with state present, and posts the "No changes" plan to the PR. Expected in CI: `infra-plan` and `gate` green.

- [ ] **Step 6: Merge, release, back-merge**

With the maintainer's approval, merge the PR into `develop`. Open a release PR from `develop` into `main`; once `gate` is green, merge it. Then:
Run: `git fetch origin && git checkout main && git merge --ff-only origin/main && git tag -a v1.0.0 -m "Release v1.0.0" && git push origin v1.0.0`
Run: `git checkout develop && git merge --ff-only origin/develop && git merge --no-edit origin/main && git push origin develop`
(The direct push to `develop` uses the Admin bypass, which is what it's for.) Publish a GitHub release for `v1.0.0`, drafting its notes with the `phx:writing-release-notes` skill.

---

### Task 8: Hand back

- [ ] **Step 1: Delete this plan**

In `todofixthis/cookiecutter-py`, on `claude/awesome-albattani-l890v5`: delete `docs/superpowers/plans/2026-10-02-terraform-github-repository-module.md`, run `git status`, commit with the `creative-commits` skill, and push.

- [ ] **Step 2: Report what's next**

Tell the maintainer `v1.0.0` is out, and that the next step is writing the `cookiecutter-py` plan from the spec with `phx:writing-plans` (spec delivery step 2), then `cookiecutter-browser-plugin` (step 3). The template plans copy `scripts/infra-plan` and the hook from the module repo at `v1.0.0`, change only `.infra-paths` (`^infra/`), and must cover the spec's template sections: root module, post-gen hook, `build.yml` changes, generated-project docs, the Renovate `packageRule`, the release-skill step 15 change, and the template tests.

## Intentional Decisions

*(Populated during review — reviewers must not re-raise these)*

- `scripts/infra-plan` has a `dirty` subcommand that the spec lists as internal to plan mode. It's exposed so the fixture tests can exercise the dirty check directly.
- The module repo gets a third ADR (003, the plan-comment guard), beyond the two the spec lists for it: the script's canonical home is this repo, so the decision binding it lives here too.
- `AGENTS.md` and the ADRs aren't committed before the plan (see the pre-work note under Architecture).
- The workflow grants `issues: read` alongside `pull-requests: read`: PR comments are listed through the issues endpoint.
- The module root's `.terraform.lock.hcl` is gitignored; only `infra/github/`'s is committed.
- `tests/infra-plan/test.sh` honours `ONLY="test_a test_b"` to run a subset.
- `renovate_absent_without_installation_id` has no clean mutation: forcing `count = 1` with a null ID makes the plan error, which skips every later run. The plan erroring is its backstop.
- Plan comments past 60,000 bytes are truncated with a note, and the cut can land inside a UTF-8 character; plans that size are rare enough to accept it.

## Self-Review Checklist

- [ ] Does the plan header include a `**Worktree:**` field naming the existing worktree and branch?
- [ ] Does every commit step remind the agent to run `git status` first?
- [ ] Does the final task delete the plan file?
- [ ] Does the plan include an Intentional Decisions section?
