# The next release entry must tell projects to delete Development Status

> Recorded 2026-11-25, from the review of the branch adding ADR 023. Never a GitHub issue.

## What

The next `CHANGELOG.md` entry needs a bullet telling each generated project to delete its own
`Development Status` classifier from `pyproject.toml`, citing cookiecutter-py ADR 023. The
release's diff of `template/pyproject.toml.jinja` shows only an added comment, so writing the
entry from that diff alone describes the comment and misses the removal.

The removal is optional cleanup, not a manual step a plain `copier update` needs, so it
doesn't by itself make the release major.

## Acceptance

- The entry has the bullet; delete this item on the release-entry branch.
