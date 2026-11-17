---
status: Accepted
date: 2026-11-17
scope: [.github/workflows/, AGENTS.md, CHANGELOG.md, scripts/release_notes.py, test/test_release_notes.py]
summary: Never tag by hand; every push to `main` is a release, which a workflow tags with the top CHANGELOG.md entry's bare-semver version as an unsigned annotated tag made with its own token, failing if that version already tags another commit, and publishes a matching GitHub Release; its advisory check on PRs into `main` stays outside `gate`; `## ` headings in CHANGELOG.md are release entries only, and the version is not read from the release PR or a manual dispatch.
revisit-when: Something that consumes this template starts verifying tag signatures; protecting tags needs a ruleset the workflow's token can't satisfy; a change needs to reach `main` other than by merging `develop`; a release needs to commit to `main` a file change `develop` lacks; a workflow needs to run when a release tag or GitHub Release is created.
---

# 017: Tag Releases from the Changelog in CI

## Context

Generated projects pick up a template release through Renovate's copier
manager, which reads bare-semver git tags (ADR 015). Each release so far,
1.0.0 to 1.3.0, followed the same steps: a `develop` → `main` PR, then the
maintainer writing a GPG-signed annotated tag on the merge commit by hand, in
the form `X.Y.Z: <theme>` followed by one bullet per change. AGENTS.md kept
agents away from tagging.

The hand step is drag, and it fails silently. On 2026-11-17 a `1.3.0` tag
briefly pointed at the 1.2.0 merge commit, before the 1.3.0 release PR had
merged. Renovate would have offered every project a "1.3.0" identical to
1.2.0. Nothing checks a hand-made tag, and the version and annotation existed
only in the maintainer's head and the release PR's prose.

[phx-claude-siat's release workflow][siat release] solves the same problem.
Its `releasing` skill prepends a CHANGELOG entry and bumps a manifest version
on `develop`. When the release PR merges, a workflow running as a GitHub App
reads the version from the CHANGELOG, makes an unsigned annotated tag,
publishes a GitHub Release and back-merges `main` into `develop`. The App
exists only so that back-merge can bypass `develop`'s ruleset. This repository
has no version file and no CHANGELOG, and `main` carries nothing `develop`
needs back.

## Options

### Option 1: Do nothing

The maintainer keeps hand-tagging each release merge.

**Pros:** Tags stay signed by the maintainer's key.
**Cons:** Every release waits on a manual step only the maintainer can do.
**Risks:** A wrong version or commit reaches every generated project as an
update PR, with nothing to catch it first.

### Option 2: Tag from the top CHANGELOG.md entry on push to `main` (Accepted)

A root `CHANGELOG.md` holds one entry per release: a
`## X.Y.Z - YYYY-MM-DD` heading, a one-line theme, then the changes.
`scripts/release_notes.py` parses it, rejecting a malformed heading or theme
and versions that don't strictly descend; a test runs it over the committed
file, so a bad entry fails `gate`. The same script checks the top version
against the repository's tags: it must be newer than every bare-semver tag,
or already tag the commit being released.

`.github/workflows/release.yml` runs that check on each PR into `main`, so a
bad version shows red before the merge. On each push to `main` it runs it
again, then tags the pushed commit with an annotated tag whose message is
`X.Y.Z: <theme>`, a blank line, then the changes, and publishes a GitHub
Release with the same title and changes. Each step skips work an earlier run
finished, so a re-run completes a partial release.

**Pros:** The version and annotation are reviewed in a PR, and checked
against the tags, before they ship.
**Cons:** A release needs a CHANGELOG entry committed to `develop` first.
Tags lose the maintainer's signature. Every push to `main` counts as a
release, so one carrying no new entry (a hotfix, or a PR opened against
`main` by mistake) fails the workflow.
**Risks:** The PR check is advisory, outside `gate`, so a bad version can
still merge. The bad commit then stays in `main`'s history, and fixing it
takes another release through `develop`.

### Option 3: Read the version and annotation from the release PR

The workflow finds the PR that produced the merge commit, takes the version
from its title (`Release X.Y.Z`) and the annotation from a marked block in its
body.

**Pros:** No new file, and no change to how release PRs are written today.
**Cons:** It parses free-form prose. The PR body stays editable after the
merge, so a re-run can tag different text. The workflow also needs to look up
which PR produced the commit.
**Risks:** The release history lives only in PR bodies, not in the
repository.

### Option 4: Tag from a manual `workflow_dispatch` with inputs

The maintainer runs the workflow after merging, typing the version and the
annotation.

**Pros:** No local signing setup is needed.
**Cons:** It keeps a manual step, and only moves it into a web form.
**Risks:** The same unchecked inputs as Option 1.

## Decision

Option 2, matching phx-claude-siat's model: the release history is a
reviewed file, and CI derives the tag from it. Options 3 and 4 keep the
inputs outside anything reviewed or tested. Unlike phx-claude-siat's workflow,
which skips a version already tagged, this one fails when that tag is on
another commit: skipping would turn a forgotten entry back into a silent
non-release.

**Tags are unsigned**, as phx-claude-siat's are. A workflow cannot sign with
the maintainer's key. A dedicated CI signing key would need storing,
rotating and registering, and would vouch only for the workflow. Nothing
downstream checks the signature: Renovate's copier manager resolves tags with
its `git-tags` datasource, and copier checks out the ref.

**The workflow publishes a GitHub Release** for people browsing the
repository, and as Renovate's fallback. Renovate first looks for release
notes in a changelog file on the default branch, `develop`, matching the
section whose heading names the version, and reads GitHub Releases only when
it finds none. So the template-update PR in each project quotes CHANGELOG.md.

**The workflow uses its own `GITHUB_TOKEN`, not a GitHub App.** The App in
phx-claude-siat serves its back-merge, and this repository has no back-merge:
the CHANGELOG entry is already on `develop`. The token cannot trigger other
workflows, and none needs to run on a tag.

**The PR check stays out of `gate`**, an exception to ADR 009's rule that
every job feeds it. `gate` runs on every push, and between releases
`develop`'s top entry legitimately tags an older commit. Requiring the check
on `main` alone would need a second ruleset beside the one
todofixthis/terraform-github-repository manages, which requires only `gate`.
The job is named `release-check` so that a ruleset can require it by a name
no other job takes.

**The workflow has no `concurrency` group.** With the default single pending
slot, a third run would cancel a pending one, silently dropping that release.
Runs on different commits tag different versions, and two racing for one
version fail the second push.

## Consequences

- AGENTS.md's Releases section changes: a release starts with a CHANGELOG.md
  entry on `develop`, then the `develop` → `main` PR, and nobody tags by hand.
- `CHANGELOG.md` is seeded with 1.0.0 to 1.3.0 from their tag annotations, so
  the parser's test runs on real entries. The workflow first tags the next
  template release after 1.3.0: the merge that brings it to `main` needs a
  new top entry.
- Tags after 1.3.0 are unsigned and made by `github-actions[bot]`. Earlier
  tags keep their signatures.
- No backport release is possible: a version must be newer than every tag.
- Editing an old entry on `develop` changes what later Renovate PRs quote, but
  not the tag or the GitHub Release made from it.
- A tag ruleset on `refs/tags/*` blocks deleting or force-moving a published
  tag, so a wrong tag can no longer be corrected in place: the fix is a new
  release. It doesn't restrict creation, so the workflow's token still tags.

[siat release]: https://github.com/todofixthis/phx-claude-siat/blob/main/.github/workflows/release.yml
