"""Decide the release to tag from the top entry of ``CHANGELOG.md``.

The release workflow runs this on each push to ``main``, and on each PR into
``main`` to catch a bad version before merging (ADR 017). It validates the
whole changelog, checks the top entry's version against the repo's tags,
and prints ``version=…`` and ``tag=true|false`` lines for ``$GITHUB_OUTPUT``.
With ``--annotation-out``, ``--notes-out`` and ``--title-out`` it also writes
the tag annotation (``X.Y.Z: <theme>`` then the changes), the GitHub Release
notes and its title. Run with ``--check`` to validate the changelog alone.
"""

import argparse
import itertools
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CHANGELOG = REPO_ROOT / "CHANGELOG.md"

# Bare semver only: Renovate's copier manager reads tags in this form, and a
# `v` prefix or a pre-release suffix would reach every generated project.
VERSION = r"\d+\.\d+\.\d+"
RE_VERSION = re.compile(rf"^{VERSION}$")
RE_ENTRY = re.compile(rf"^## (?P<version>{VERSION}) - \d{{4}}-\d{{2}}-\d{{2}}$")
# A theme that opens like a list item is a missing theme, not a theme.
RE_LIST_ITEM = re.compile(r"^(#|[-*+](\s|$)|\d+[.)](\s|$))")


@dataclass(frozen=True)
class Release:
    """One changelog entry."""

    version: str
    theme: str
    changes: str

    @property
    def annotation(self) -> str:
        """The tag annotation, in the form the hand-made tags used."""
        return f"{self.version}: {self.theme}\n\n{self.changes}\n"

    @property
    def title(self) -> str:
        """The GitHub Release title."""
        return f"{self.version}: {self.theme}"


def version_key(version: str) -> tuple[int, ...]:
    """Sort key ordering versions numerically, so 1.10.0 follows 1.9.0."""
    return tuple(int(part) for part in version.split("."))


def parse(changelog: str) -> list[Release]:
    """Return every entry, newest first.

    Args:
        changelog: The changelog's full text.

    Returns:
        The entries, in file order.

    Raises:
        ValueError: An entry is malformed, or versions don't strictly descend.
    """
    blocks: list[tuple[str, list[str]]] = []
    for line in changelog.splitlines():
        if line.startswith("## "):
            match = RE_ENTRY.match(line)
            if not match:
                # Skipping it would tag the entry below under the wrong version.
                raise ValueError(
                    f"{line!r} is not '## X.Y.Z - YYYY-MM-DD' (bare semver, no"
                    " 'v' prefix or suffix); '## ' headings are for release"
                    " entries only"
                )
            blocks.append((match.group("version"), []))
        elif blocks:
            blocks[-1][1].append(line)
    if not blocks:
        raise ValueError("no '## X.Y.Z - YYYY-MM-DD' entry found")

    releases = [_release(version, lines) for version, lines in blocks]
    for newer, older in itertools.pairwise(releases):
        if version_key(newer.version) <= version_key(older.version):
            raise ValueError(
                f"{newer.version} sits above {older.version}; entries must be"
                " newest first, with no version repeated"
            )
    return releases


def _release(version: str, lines: list[str]) -> Release:
    """Split an entry's lines into its theme and changes."""
    text = "\n".join(lines).strip()
    theme, _, changes = text.partition("\n")
    if not theme or RE_LIST_ITEM.match(theme):
        raise ValueError(f"{version} has no one-line theme under its heading")
    # A theme wrapped onto a second line would otherwise lose that line to
    # the changes.
    if changes and not changes.startswith("\n"):
        raise ValueError(f"{version}'s theme must be one line, then a blank line")
    changes = changes.strip()
    if not changes:
        raise ValueError(f"{version} lists no changes under its theme")
    return Release(version=version, theme=theme.strip(), changes=changes)


def needs_tag(version: str, tags: dict[str, str], commit: str) -> bool:
    """Decide whether ``commit`` should be tagged ``version``.

    Args:
        version: The top changelog entry's version.
        tags: Each existing tag, mapped to the commit it points at.
        commit: The commit to release.

    Returns:
        False if ``version`` already tags ``commit`` (a re-run), else True.

    Raises:
        ValueError: ``version`` tags another commit, or isn't newer than
            every bare-semver tag.
    """
    if version in tags:
        if tags[version] == commit:
            return False
        raise ValueError(
            f"{version} already tags {tags[version]}; add a CHANGELOG.md entry"
            " for this release on develop"
        )
    released = [tag for tag in tags if RE_VERSION.match(tag)]
    newest = max(released, key=version_key, default=None)
    if newest is not None and version_key(version) <= version_key(newest):
        raise ValueError(f"{version} is not newer than the newest tag, {newest}")
    return True


def git_tags() -> dict[str, str]:
    """Map each tag in the working repo to the commit it points at."""
    listing = subprocess.run(
        [
            "git",
            "for-each-ref",
            "refs/tags",
            "--format=%(refname:short) %(*objectname) %(objectname)",
        ],
        capture_output=True,
        check=True,
        text=True,
    ).stdout
    tags = {}
    for line in listing.splitlines():
        name, *objects = line.split()
        # An annotated tag peels to its commit; a lightweight one has no peel.
        tags[name] = objects[0]
    return tags


def main() -> int:
    """Validate the changelog, then report and write the release to tag."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--changelog", type=Path, default=DEFAULT_CHANGELOG)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--commit", help="the commit to release")
    parser.add_argument("--annotation-out", type=Path)
    parser.add_argument("--notes-out", type=Path)
    parser.add_argument("--title-out", type=Path)
    args = parser.parse_args()

    try:
        releases = parse(args.changelog.read_text(encoding="utf-8"))
        if args.check:
            return 0
        if args.commit is None:
            parser.error("--commit is required unless --check is given")
        top = releases[0]
        tag = needs_tag(top.version, git_tags(), args.commit)
    except ValueError as error:
        print(f"❌ {args.changelog.name}: {error}", file=sys.stderr)
        return 1

    outputs = {
        args.annotation_out: top.annotation,
        args.notes_out: top.changes,
        args.title_out: top.title,
    }
    for path, content in outputs.items():
        if path is not None:
            path.write_text(content, encoding="utf-8")
    print(f"version={top.version}")
    print(f"tag={'true' if tag else 'false'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
