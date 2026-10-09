# GitHub repo IaC for generated projects — design

## Goal

Every project baked from `todofixthis/cookiecutter-py` or `todofixthis/cookiecutter-browser-plugin` ships Terraform for its own GitHub repo. After baking, `terraform -chdir=infra/github init` then `apply`, run from the maintainer's machine, creates the repo, pushes the boilerplate, and applies the standard configuration. A second `apply` with no changes plans nothing.

## Scope

In scope:

- A new shared module repo, `todofixthis/terraform-github-repository`.
- Both templates: a root module, post-gen hook steps, CI changes, a plan script and hooks, docs, ADRs, and a `renovate.json` rule in both the template repo and the generated project.

Out of scope:

- The template repos' own GitHub config.
- Adopting the module in `todofixthis/filters` or `todofixthis/phx-claude-siat`.
- `phx-claude-siat`-style release automation (release App, `release.yml`, App secrets). That's the next iteration. This one releases `filters`-style, by hand.
- CI running `plan` or `apply`. The CI `infra-plan` job below only checks for a plan comment.

## The standard

Taken from `todofixthis/phx-claude-siat`'s live config (2026-09), with wiki and projects off. Those were GitHub defaults, not choices.

Repo settings:

- Public by default; private when the `visibility` input says so.
- `develop` is the default branch.
- Merge commits only; squash and rebase off. Merge commit title is `PR_TITLE` and message is `PR_BODY`.
- `delete_branch_on_merge` on; `allow_auto_merge` and `allow_update_branch` off.
- Issues on. Wiki, projects and discussions off.
- Downloads: not set, because `has_downloads` is deprecated in the provider.
- Secret scanning and push protection on for public repos. For private repos the module omits the `security_and_analysis` block, because on a personal account without GitHub Advanced Security those settings can't be enabled. The API presumably rejects the attempt, but that's unverified here.
- Dependabot alerts on, via `github_repository_vulnerability_alerts`, because Renovate reads them to raise security PRs. The repo attribute `vulnerability_alerts` is deprecated.
- Dependabot security updates managed and off, via `github_repository_dependabot_security_updates`. Renovate is the only thing that opens PRs.
- `archive_on_destroy = true`, so a stray `destroy` archives rather than deletes.

Rulesets:

| Name | Target | Rules | Bypass |
|---|---|---|---|
| `trunk-develop` | `refs/heads/develop` | `deletion`, `non_fast_forward`, `pull_request` (0 approvals, thread resolution required, merge only), `required_status_checks` (`gate`, integration `15368`, strict) | `RepositoryRole` 5 (Admin), `always` |
| `trunk-main` | `refs/heads/main` | as `trunk-develop` | none |
| `tags-release` | tags, `~ALL` | `deletion`, `non_fast_forward` | none |

`require_extra_approval_for_unattributed_changes` is `true` on `phx-claude-siat`, but the provider can't set it. New repos get GitHub's default, and drift goes undetected.

## Module: `todofixthis/terraform-github-repository`

A public repo. Projects reference it as `github.com/todofixthis/terraform-github-repository?ref=vX.Y.Z`.

Inputs:

- `name` and `description` are required.
- `homepage_url` defaults to `null`.
- `topics` defaults to `[]`.
- `visibility` defaults to `"public"`; validation allows only `"public"` or `"private"`.
- `local_path` defaults to `null`; the module uses `coalesce(var.local_path, path.root)`. That resolves to `infra/github/`, and git finds the repo by walking up.
- `renovate_installation_id` defaults to `null`.

Resources, in dependency order:

1. `github_repository`, with no `auto_init`. As unconfirmed but cheap insurance against a perpetual diff, it ignores changes to:
   - `security_and_analysis[0].advanced_security`: the provider stores it on read, but it can't be set for public repos.
   - `has_downloads`: the provider always sends `false`, and the API may keep returning `true`.

   `security_and_analysis` is a `dynamic` block whose `for_each` is exactly `local.enable_security_and_analysis ? [1] : []`, where `enable_security_and_analysis = var.visibility == "public"`. Keeping that exact form is what lets the tests assert the local in place of the block.
2. `github_repository_vulnerability_alerts` and `github_repository_dependabot_security_updates`.
3. `terraform_data` push step. Its `local-exec` adds `origin` (the SSH URL) if it's missing, then runs `git push --no-verify origin develop main`. `--no-verify` keeps the pre-push hook out of `apply`. Both local branches must exist. The step is replaced only when the repo is.
4. `github_branch_default` → `develop`.
5. The three rulesets. They come after the push because `trunk-main` has no bypass and `do_not_enforce_on_create` is off, so creating `main` while the ruleset existed would fail the required check.
   The rulesets are created whatever the visibility. The maintainer is on GitHub Free, where rulesets on a private repo presumably need Pro (unverified), and has accepted that a private repo's rulesets may exist but not be enforced. Keeping them means they start enforcing as soon as the repo goes public. The other possible outcome, also unverified, is that GitHub refuses them outright. Then a private `apply` fails after the repo is created, pushed and given its default branch, and on an existing repo every later `plan` fails at refresh. If a private `apply` ever shows refusal, the follow-up is to create the rulesets only for public repos. The module ADR records this with that revisit-when; nothing forces a private bake to happen sooner.
6. `github_app_installation_repository` for Renovate, only when `renovate_installation_id` is set. Renovate is installed on selected repos only. Untested: whether the endpoint accepts `gh auth token`'s OAuth token. If not, fall back to `GITHUB_TOKEN`.

Outputs: `html_url`, `ssh_clone_url`, `http_clone_url`.

Auth: the provider falls back to `gh auth token` when `GITHUB_TOKEN` is unset.

The module repo provisions itself. Its `infra/github/` uses `source = "../.."`. It follows the same standard: `develop`/`main`, a `gate` job, the `infra-plan` guard, and releases tagged by hand on `main`. Its root `*.tf` files change what it applies, so its infra paths include them (see Path logic). It ships the same `scripts/infra-plan`, plus a `.githooks/pre-push` activated once per clone with `git config core.hooksPath .githooks`, since it has no uv or pnpm hook manager.

Bootstrap, once:

1. Create the repo empty from a Claude Code session and push both branches.
2. The maintainer clones it and runs `git branch main origin/main`, so both local branches exist for the push step.
3. The maintainer runs `terraform import 'module.repository.github_repository.this' terraform-github-repository`.
4. The maintainer runs `apply`. The push step re-runs harmlessly.

## Templates

### Root module: `infra/github/`

- `main.tf` declares `integrations/github` in `required_providers`, so Renovate maintains it and its lock hashes. The constraint is a major-version range (`~> X.0`), never an exact pin, so a module release that raises the floor within that major only needs `init -upgrade`. A module release that moves to a new provider major also needs this constraint edited on the bump branch. It sets the provider `owner` to `github_username` and calls the module pinned to a tag, passing:
  - `name` and `description`.
  - `homepage_url`: the project's ReadTheDocs URL for `public`, `null` for `private`, because RTD's community tier can't build private repos. The root module derives it in HCL from a single `visibility` local, so changing visibility later is a one-line edit. The baked RTD config and badges stay either way; for a private project they're inert until it goes public.
  - `visibility = local.visibility`. That local is the only place the new cookiecutter choice variable `github_visibility` is rendered (`public` first, so it's the default), as a string literal. Both the module argument and `homepage_url` read the local, so editing it changes both.
  - `renovate_installation_id`, from a new cookiecutter variable with an empty default. The maintainer sets it once in `~/.cookiecutterrc`'s `default_context`.
- Jinja in `infra/github/` appears only inside HCL string literals, so the unrendered template is still valid HCL. That lets the template repo's own Renovate run `terraform` there. The empty Renovate ID becomes `null` with an HCL conditional, not `{% if %}`.
- State is local. `.terraform/` and `terraform.tfstate*` are gitignored. Backups are the maintainer's.
- `.terraform.lock.hcl` is committed, with hashes for at least `darwin_arm64`, `darwin_amd64`, `linux_arm64` and `linux_amd64`. Renovate's own lock updates add every platform the registry lists, so tests mustn't assert exactly four. It has to ship in the template because the post-gen hook commits before `init` runs. Renovate keeps each copy current for provider bumps; module bumps that move the provider constraint need a manual lock update (see Updates).

### Post-gen hook

Both templates already have `hooks/post_gen_project.py` (symlink restore). After that step, it:

1. Runs `git init -b develop`.
2. Commits everything with the maintainer's global identity and signing config.
3. Runs `git branch main`.

Any failure fails the bake.

### CI (`build.yml`)

- The trigger changes from `push: ~` to `pull_request` on `develop` and `main`. Pushes to a PR's branch still run CI, as `synchronize` events.
- A `concurrency` group per PR, with `cancel-in-progress`.
- A `changes` job runs `scripts/infra-plan changed "$BASE_SHA" "$HEAD_SHA"` and outputs `infra=true|false` (see Path logic). There's no workflow-level `paths` filter, because a skipped workflow never reports `gate`.
- An `infra-plan` job runs when `infra == 'true'` and the PR's base is `develop`. Infra is applied from `develop` after merge, so release PRs to `main` aren't gated on it. It:
  - checks out `pull_request.head.sha`, not the merge ref;
  - computes `scripts/infra-plan hash`;
  - passes if a PR comment has the plan marker for that infra hash and its `author_association` is `OWNER` or `COLLABORATOR`.

  It uses only the default `GITHUB_TOKEN`, with `pull-requests: read` added to the workflow's `contents: read` so it can list comments. The guard catches a forgotten plan, not intent: a cloud agent posts as the maintainer, so `AGENTS.md` forbids writing the marker by hand.
- A `gate` job `needs` every other job, runs `if: always()`, and fails on any `failure` or `cancelled`. It's the only required check.

### `scripts/infra-plan`

| Situation | Behaviour | Exit |
|---|---|---|
| `terraform` not on `PATH` | ⚠️ "terraform not installed; cannot plan" | 0 |
| `init` fails, in any row below | ⚠️ "init failed; on a module bump, run `terraform init -upgrade` then `terraform providers lock` for the four platforms, and commit the lock". Any `init` failure prints this; no error-text matching. Nothing is posted | `init`'s |
| `init` succeeds but changes `.terraform.lock.hcl`, in any row below | ⚠️ "init changed the lock file; commit it and re-run". The script hashes the lock just before `init` and compares after, so a lock edit the maintainer hasn't committed yet doesn't count. Nothing is posted | 1 |
| No `infra/github/terraform.tfstate` | ⚠️ "state not available; plan must run on the maintainer's machine", then `init -input=false -backend=false` and `validate` | `validate`'s |
| State present, the infra paths have uncommitted or untracked changes (checked before `init`) | `init -input=false`, `plan -input=false`, printed; ⚠️ "infra paths are dirty; comment not posted" | `plan`'s |
| State present, clean | `init -input=false`, then `plan -input=false`, printed. If the branch has a PR, create or update the plan comment. Posting a comment doesn't trigger CI, so if a completed, failed `pull_request` run exists for `HEAD`'s SHA (`gh run list --commit "$(git rev-parse HEAD)" --event pull_request`), it reruns that run with `gh run rerun --failed`. If the run for `HEAD` is still in progress, it prints ⚠️ "CI run still in progress; if it fails, rerun with `gh run rerun --failed <id>`". It doesn't wait, since it runs in pre-push. If there's no run for `HEAD` yet, it reruns nothing: the push being guarded triggers a fresh run, which finds the comment. Otherwise ⏭️ "no PR yet; re-run once one exists" | `plan`'s |

#### Path logic

**One implementation.** The **infra paths** are an anchored regex read from `.infra-paths` at the repo root:
- generated projects: `^infra/`;
- module repo: `^(infra/|[^/]+\.tf$)`.

`scripts/infra-plan` is the same file in every repo when it ships (generated projects can fall behind; see Updates). The templates ship a verbatim copy of the module repo's script at the pinned tag, and only `.infra-paths` differs. Both templates list `scripts/infra-plan` and `.infra-paths` in `cookiecutter.json`'s `_copy_without_render`, so Jinja never touches them (`${#arr[@]}` alone would start a Jinja comment). When a module release changes the script, the template's Renovate PR bumping the ref fails the byte-identical check until the script is copied across. That failure is the intended drift signal. Its subcommands:

- `hash` prints the **infra hash**: `git ls-tree -r -z HEAD`, filtered on the path column, piped to `git hash-object --stdin`. It reads the committed tree only.
- `changed <base> <head>` computes `merge-base(base, head)` itself, then diffs it against `head` with `git diff -z --name-only --no-renames`, filtered. Callers pass raw SHAs: CI passes `base.sha` and `head.sha`; pre-push passes the remote and local SHAs, or `origin/develop` and the local SHA for a new branch. It exits 0 if anything changed, 1 if nothing did, and 2 or more on any error (unknown SHA, missing merge-base). CI and the pre-push hook treat an error as a failure, never as "unchanged". CI checks out with `fetch-depth: 0` so the merge-base exists.
- The dirty check (internal to plan mode) reads `git status --porcelain=v1 -z --no-renames --untracked-files=all` and strips each entry's three-character status prefix, so untracked files count.

The script is the only place the path logic lives: CI and the pre-push hook call these subcommands rather than reimplementing them.

How the filtering works:
- **Regex, not pathspecs.** `git ls-tree` doesn't glob, and `'*.tf'` in `git diff` also matches test fixtures.
- **`-z` everywhere.** Git output is NUL-separated, so non-ASCII paths are never C-quoted in a way that depends on `core.quotePath`.
- **`--no-renames` on the change listings,** so a file moved out of `infra/` appears under its old path as well.
- **Filtering uses `perl -0`,** which behaves the same on macOS and on Ubuntu runners. BSD awk's `RS='\0'` and `grep -z` don't. Each record is `chomp`ed before matching, because Perl's `$` doesn't match before a trailing NUL, and `[^/]+\.tf$` would otherwise drop every root `.tf` file.

The plan comment holds a marker, the infra hash, and the plan in a collapsed block. "Update" means editing the existing marker comment, not posting a new one.

### Pre-push hook

It runs `scripts/infra-plan` only when the pushed commits change the infra paths. The hook reads git's ref list from stdin first, then calls the script with stdin from `/dev/null`. For each pushed ref:
- **Deletion** (local SHA all zeros): skipped.
- **A ref that isn't the checked-out branch:** ⏭️ skipped with a warning, because the script plans and hashes `HEAD` and posts to the current branch's PR.
- **Otherwise:** it runs `scripts/infra-plan changed <remote> <local>`, or `changed origin/develop <local>` for a new branch (remote SHA all zeros). Exit 2 or more blocks the push. So does a non-zero exit from the plan-mode run that follows; the rows that exit 0 by design, such as terraform not installed, don't block.

- Browser plugin: `.husky/pre-push`, installed by `pnpm install`.
- Python: autohooks manages `pre-commit` only. The hook is committed as `scripts/git-hooks/pre-push`, and the "once per clone" step that runs `autohooks activate` also symlinks it into `$(git rev-parse --git-path hooks)`, which works in worktrees.

Cloud sessions install neither hook, so the pre-push hook is the maintainer's signal, not Claude's.

### Generated project docs

- README, "Change visibility" (edit the `visibility` local in `infra/github/main.tf`):
  - **Public to private:** plan and apply. It's lossy (unverified here: GitHub erases stars and watchers, and detaches forks), so the plan comment is the moment to check it's intended. See "Private repos on GitHub Free".
  - **Private to public:** first run `gh repo edit --visibility public --accept-visibility-change-consequences`, then plan and apply. A single `apply` can't do it: the provider sends `security_and_analysis` in its first API call, while the repo is still private, and only changes visibility in a second call. `plan` succeeds, so only `apply` would fail.
- README, "Create the GitHub repo": bake, then `terraform -chdir=infra/github init`, then `apply`. For a private project, see "Private repos on GitHub Free". Afterwards, `apply` from `develop` after each merged PR that changes `infra/`. To unblock a PR you didn't push yourself (Renovate bumping the module ref or the lock, or a cloud agent's PR), run `gh pr checkout <n>` and then `scripts/infra-plan`.
- README, "Private repos on GitHub Free", referenced by both bullets above:
  - Rulesets may exist without being enforced. That's accepted, and they enforce once the repo is public.
  - Or GitHub may refuse them. Then a fresh `apply` stops half-applied, after the repo is created and pushed, and on an existing repo every `plan` fails, so the `infra-plan` guard can't pass.
  - While refusal holds, the pre-push hook blocks every push touching `infra/`; `git push --no-verify` gets past it, and the CI guard still holds the PR.
  - The ways out of refusal: upgrade to Pro and apply again, or make the repo public via "Private to public". A free fix that keeps the repo private is the pending follow-up; link the module repo's ADR that names it.
- Release skill (`.agents/skills/release/`): step 15 ("Rebase `develop` onto `main`") is replaced, not supplemented. The new step merges `origin/main` into `develop` (fast-forward when it can) and pushes, using the Admin bypass. Without a back-merge, each release's merge commit on `main` leaves the next release PR out of date, and the strict check blocks it (`allow_update_branch` is off). A rebase would rewrite any commits `develop` gained during the release, so the push would be rejected. The module repo's release docs carry the same step.
- `AGENTS.md`:
  - `infra/github/` is the source of truth for repo settings. Never change them in the UI.
  - Before opening a PR that touches `infra/`, run `scripts/infra-plan`, check the plan matches the intended change, and report it. If it warns that terraform isn't installed or state isn't available, tell the user the PR needs a local plan before CI goes green. If `init` fails on a PR that doesn't bump the module, report the error rather than following the script's module-bump hint.
  - Never write the plan marker comment by hand.
  - Never put secrets in Terraform. Set them with `gh secret set`.

## Updates

Renovate opens the module-bump PRs in every dependent repo, with no extra config. Its Terraform manager recognises `github.com/<owner>/<repo>?ref=<tag>` module sources and looks up new versions from the module repo's tags. `config:recommended`, which all three `renovate.json` files extend, enables that manager. Renovate is installed on both template repos, and on each generated project through `renovate_installation_id`.

- A module release is a semver tag (`vX.Y.Z`) on the module repo's `main`. Renovate picks it up on its next scheduled run in each dependent repo.
- **Generated projects:** every module-bump PR changes `infra/`, so the `infra-plan` guard holds it until the maintainer runs `scripts/infra-plan`. That plan shows what the new version would change on that repo. Module bumps are never auto-merged.
- **Template repos:** they have no `infra-plan` guard. `generate-and-validate` gates their bump PRs: `init`, `validate` and the byte-identical check.
- **The module repo:** it uses `source = "../.."`, so it gets no bump PRs.
- **The module `source` stays a literal string,** with no Jinja: `github.com/todofixthis/terraform-github-repository?ref=vX.Y.Z`. Renovate takes everything after `ref=` as the tag, so templating it would silently break updates. CI reads the pinned tag by parsing `main.tf`.
- **A new provider major arrives only through a module release.** Both template repos' own `renovate.json`, and the generated project's, disable major updates for `integrations/github` with a `packageRule` (`matchPackageNames: ["integrations/github"]`, `matchUpdateTypes: ["major"]`, `enabled: false`). Otherwise Renovate would open root-constraint PRs that conflict with the module's own constraint and can't pass. The module repo's `renovate.json` keeps major updates, because that's where the major move happens. Renovate gives provider deps `packageName: "integrations/github"` and `depName: "github"` (from its Terraform manager source). The plan confirms with a Renovate dry run that the rule matches.
- **Renovate never touches the lock file on a module bump.** It only updates `.terraform.lock.hcl` for provider dependencies. If a release raises the `integrations/github` constraint beyond what the lock holds, plain `init` fails, in `generate-and-validate` and in `scripts/infra-plan` alike. Even when the locked version still satisfies the new constraint, `init` may rewrite the lock's `constraints` line, which leaves the infra paths dirty. Either way, the fix is on the bump branch: run `terraform init -upgrade`, then `terraform providers lock` for the four platforms, and commit the result. `scripts/infra-plan` keeps plain `init`, and its table covers both cases. Where the table's warning differs from this paragraph, the table governs: when `init` only rewrote the lock, committing that rewrite is enough, and safer than `-upgrade`, which would also move the locked provider version. `generate-and-validate` fails a template's bump PR when the lock is stale. Module release notes call out any provider-constraint change.
- When a release changes `scripts/infra-plan`, each template's bump PR fails the byte-identical check until the script is copied across by hand. Automating the copy is out of scope: the Mend-hosted app blocks `postUpgradeTasks` commands by default, and a commit pushed by a workflow with the default token doesn't re-trigger CI.
- Generated projects have no byte-identical check, so after a script-changing release they keep their old copy. That's harmless, because the copy still agrees with the project's own CI; the project just misses improvements until someone copies the new script in.

## ADRs

- Module repo:
  - Share the repo standard as a versioned module. Covers distributing updates through Renovate (see Updates), creating rulesets on private repos on GitHub Free, accepting non-enforcement (revisit when a private `apply` shows refusal: create rulesets for public repos only). Also covers `archive_on_destroy`, and the deferred release App: Terraform can't create Apps (no provider resource), so the next iteration takes one existing shared App, by slug for the App ID plus its installation ID.
  - No secrets in Terraform state. Secrets go through `gh secret set`. Breach signals: a `sensitive` input, or a `github_actions_secret` resource. Revisit-when records remote state plus OIDC as the route to CI-run plans.
- Each template: provision the generated project's GitHub repo through the module, including the PR-comment plan guard and why CI can't plan with local state.

## Testing

- Module repo CI:
  - `terraform fmt -check`, `validate`, and `terraform test` with `mock_provider "github"`.
  - Every test run uses `command = plan`. The `terraform_data` push step is built in, so the mock doesn't cover it, and an `apply` run would really push.
  - The tests assert that `local.enable_security_and_analysis` is true for `public` and false for `private`. They assert the local rather than the block, because the attribute is `Optional`+`Computed`, so its absence is unknown at plan time. For `public` they also assert `security_and_analysis[0].secret_scanning[0].status == "enabled"`, which is known at plan time from config. The broken-fixture rule covers both assertions: inverting the local must fail the first, and a `for_each` that never emits the block must fail the second. A `for_each` that always emits the block can't be caught at plan time, because the block's absence for `private` is unknown. That's why the exact `for_each` form above is required, and why code review checks it. The tests also assert that `visibility` rejects any other value, and that the `trunk-main` bypass is empty, the `trunk-develop` bypass is Admin only, both branch rulesets require strict `gate` from `15368` with merge only, and the Renovate resource count follows its input.
  - Each assertion is shown to fail against a deliberately broken fixture.
  - Fixture tests for the script's three code paths (`hash`, `changed`, the dirty check), run under both patterns (`^infra/` and the module repo's own). All three paths must:
    - catch a root `.tf` change (module pattern), a file moved out of `infra/`, and a non-ASCII infra path;
    - ignore a `tests/**/*.tf` change.

    Only the dirty check must also catch an untracked infra file, because `hash` and `changed` read commits only.

    `changed` must return 2 or more for an unknown base SHA. A golden value pins the hash of a fixed fixture tree for each pattern, and runs on both `ubuntu-latest` and `macos-latest`, so a platform difference fails CI rather than silently never matching.
- Template `test/`:
  - `test_leaves_no_unrendered_jinja` skips `.git/`, since the hook's commit puts binary objects there.
  - No leftover Jinja in `.tf` files.
  - The baked project is a git repo with `develop` and `main` at the same commit.
  - The `.gitignore` entries are present.
  - Each bake runs with `GIT_CONFIG_GLOBAL` pointing at a temp file that sets an identity and `commit.gpgsign=false`, so the maintainer's own config never signs or blocks a test bake.
- Template `generate-and-validate.yml`:
  - Sets a git identity before baking.
  - Runs `terraform init`, `validate` and `fmt -check` on the baked `infra/github/`, which proves the pinned module ref resolves.
  - Checks that `scripts/infra-plan` exits 0 with its warning in the no-state case, and that `init` left the baked `infra/github/.terraform.lock.hcl` unchanged (`git diff --exit-code`), so a stale lock in the template fails its bump PR rather than shipping.
  - Checks that the baked `scripts/infra-plan` is byte-identical to the module repo's at the pinned tag, so the template copy can't drift. The fixture tests live in the module repo only.
- Not testable here: a real `apply`. The first end-to-end run is the maintainer's, on the first project baked.

## Delivery order

1. Module repo: code, ADRs, CI, bootstrap, tag `v1.0.0`.
2. `cookiecutter-py`.
3. `cookiecutter-browser-plugin`.

Each template's CI needs the tag to exist.
