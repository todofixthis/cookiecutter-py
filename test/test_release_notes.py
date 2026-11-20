"""Checks the changelog parser and version checks the release workflow uses."""

import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

from scripts import release_notes

ENTRY_120 = """## 1.2.0 - 2026-11-17

Python policy

- First change
- Second change
"""

ENTRY_110 = """## 1.1.0 - 2026-10-24

Earlier theme

- Older change
"""

SCRIPT = str(Path(release_notes.__file__))


def git(repo: Path, *args: str) -> str:
    """Run git in ``repo`` with a throwaway identity, returning its output."""
    return subprocess.run(
        ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com", *args],
        capture_output=True,
        check=True,
        cwd=repo,
        text=True,
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """A repo with 1.1.0 tagged on its first commit and a second, untagged one."""
    path = tmp_path / "repo"
    path.mkdir()
    git(path, "init", "-q")
    git(path, "commit", "-q", "--allow-empty", "-m", "first")
    git(path, "tag", "-a", "1.1.0", "-m", "1.1.0: Earlier theme")
    git(path, "commit", "-q", "--allow-empty", "-m", "second")
    return path


def run_script(
    repo: Path, changelog: str, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run the script in ``repo`` against ``changelog``."""
    path = repo.parent / "CHANGELOG.md"
    path.write_text(changelog, encoding="utf-8")
    return subprocess.run(
        [sys.executable, SCRIPT, "--changelog", str(path), *args],
        capture_output=True,
        check=False,
        cwd=repo,
        text=True,
    )


def test_top_entry_builds_the_annotation() -> None:
    """The annotation is 'X.Y.Z: <theme>', a blank line, then the changes."""
    top = release_notes.parse(f"# Changelog\n\nIntro.\n\n{ENTRY_120}\n{ENTRY_110}")[0]
    assert top.version == "1.2.0"
    assert top.title == "1.2.0: Python policy"
    assert top.annotation == "1.2.0: Python policy\n\n- First change\n- Second change\n"


def test_changes_keep_paragraphs_and_wrapped_bullets() -> None:
    """Everything after the theme line, up to the next entry, is the changes."""
    entry = "## 1.0.0 - 2026-10-17\n\nTheme\n\nA paragraph.\n\n- A bullet\n  wrapped.\n"
    assert release_notes.parse(entry)[0].changes == (
        "A paragraph.\n\n- A bullet\n  wrapped."
    )


@pytest.mark.parametrize(
    "heading",
    [
        "## v1.3.0 - 2026-11-20",
        "## 1.3.0-rc.1 - 2026-11-20",
        "## 1.3.0",
        "## [1.3.0] - 2026-11-20",
        "## Unreleased",
    ],
)
def test_malformed_heading_fails(heading: str) -> None:
    """A heading other than bare semver and a date fails rather than being skipped."""
    with pytest.raises(ValueError, match="is not"):
        release_notes.parse(f"{heading}\n\nTheme\n\n- Change\n\n{ENTRY_120}")


@pytest.mark.parametrize(
    "theme", ["- Change", "+ Change", "1. Change", "2) Change", "### Added"]
)
def test_entry_without_theme_fails(theme: str) -> None:
    """An entry whose first line opens like a list item or heading has no theme."""
    with pytest.raises(ValueError, match="no one-line theme"):
        release_notes.parse(f"## 1.3.0 - 2026-11-20\n\n{theme}\n\n- Change\n")


@pytest.mark.parametrize("theme", ["3.15 support", "+3 questions", "1.x clean-up"])
def test_theme_opening_with_a_number_or_sign_passes(theme: str) -> None:
    """A theme only fails when it opens like a list item, marker then a space."""
    entry = f"## 1.3.0 - 2026-11-20\n\n{theme}\n\n- Change\n"
    assert release_notes.parse(entry)[0].theme == theme


def test_wrapped_theme_fails() -> None:
    """A theme spilling onto a second line fails rather than losing that line."""
    with pytest.raises(ValueError, match="must be one line"):
        release_notes.parse("## 1.3.0 - 2026-11-20\n\nA theme\nwrapped\n\n- Change\n")


def test_entry_without_changes_fails() -> None:
    """An entry with a theme but nothing under it fails."""
    with pytest.raises(ValueError, match="lists no changes"):
        release_notes.parse("## 1.3.0 - 2026-11-20\n\nTheme\n")


def test_no_entry_fails() -> None:
    """A changelog with no entry has nothing to release."""
    with pytest.raises(ValueError, match="no '## X.Y.Z"):
        release_notes.parse("# Changelog\n")


@pytest.mark.parametrize("newer", ["1.1.0", "1.0.9"])
def test_versions_must_descend(newer: str) -> None:
    """A repeated or lower version above an entry fails."""
    entry = f"## {newer} - 2026-11-20\n\nTheme\n\n- Change\n\n"
    with pytest.raises(ValueError, match="newest first"):
        release_notes.parse(entry + ENTRY_110)


def test_versions_compare_numerically() -> None:
    """1.10.0 sorts above 1.9.0, not below it as text would."""
    entry = "## 1.10.0 - 2026-11-20\n\nTheme\n\n- Change\n\n"
    older = "## 1.9.0 - 2026-11-01\n\nTheme\n\n- Change\n"
    assert release_notes.parse(entry + older)[0].version == "1.10.0"


def test_repo_changelog_is_valid() -> None:
    """The committed changelog parses, so a malformed entry fails CI before release."""
    release_notes.parse(release_notes.DEFAULT_CHANGELOG.read_text(encoding="utf-8"))


def test_new_version_needs_a_tag() -> None:
    """A version newer than every bare-semver tag, numerically, needs tagging."""
    tags = {"1.9.0": "aaa", "1.40.0-rc1": "bbb", "notes": "ccc"}
    assert release_notes.needs_tag("1.10.0", tags, "ddd")


def test_version_already_on_this_commit_needs_no_tag() -> None:
    """A re-run on the commit the version already tags does nothing."""
    assert not release_notes.needs_tag("1.2.0", {"1.2.0": "aaa"}, "aaa")


def test_version_on_another_commit_fails() -> None:
    """A top entry already tagged elsewhere means the release has no entry."""
    with pytest.raises(ValueError, match="already tags aaa"):
        release_notes.needs_tag("1.2.0", {"1.2.0": "aaa"}, "bbb")


@pytest.mark.parametrize("version", ["1.1.9", "1.0.0"])
def test_version_older_than_newest_tag_fails(version: str) -> None:
    """A version below the newest tag fails, so no backport is released."""
    with pytest.raises(ValueError, match="not newer than the newest tag, 1.2.0"):
        release_notes.needs_tag(version, {"1.2.0": "aaa"}, "bbb")


def test_cli_writes_the_release(repo: Path) -> None:
    """The script prints outputs for a new version and writes all three files."""
    head = git(repo, "rev-parse", "HEAD")
    out = repo.parent
    result = run_script(
        repo,
        ENTRY_120 + "\n" + ENTRY_110,
        "--commit",
        head,
        "--annotation-out",
        str(out / "annotation.txt"),
        "--notes-out",
        str(out / "notes.md"),
        "--title-out",
        str(out / "title.txt"),
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "version=1.2.0\ntag=true\n"
    assert (out / "annotation.txt").read_text().startswith("1.2.0: Python policy\n")
    assert (out / "notes.md").read_text() == "- First change\n- Second change"
    assert (out / "title.txt").read_text() == "1.2.0: Python policy"


def test_cli_reads_annotated_tags_as_their_commit(repo: Path) -> None:
    """An annotated tag on the given commit reads as a re-run, not a clash."""
    first = git(repo, "rev-parse", "HEAD~1")
    result = run_script(repo, ENTRY_110, "--commit", first)
    assert result.returncode == 0, result.stderr
    assert result.stdout == "version=1.1.0\ntag=false\n"


def test_cli_fails_on_an_already_tagged_entry(repo: Path) -> None:
    """A release whose top entry is tagged on another commit exits 1."""
    head = git(repo, "rev-parse", "HEAD")
    result = run_script(repo, ENTRY_110, "--commit", head)
    assert result.returncode == 1
    assert "1.1.0 already tags" in result.stderr


def test_cli_fails_on_a_malformed_changelog(repo: Path) -> None:
    """A malformed changelog exits 1 and writes nothing."""
    annotation = repo.parent / "annotation.txt"
    result = run_script(
        repo,
        "## v1.2.0 - 2026-11-17\n\nTheme\n\n- Change\n",
        "--commit",
        "abc",
        "--annotation-out",
        str(annotation),
    )
    assert result.returncode == 1
    assert not annotation.exists()


def test_cli_check_validates_without_git() -> None:
    """``--check`` validates the committed changelog alone."""
    result = subprocess.run(
        [sys.executable, SCRIPT, "--check"], capture_output=True, check=False
    )
    assert result.returncode == 0


def test_pyproject_version_matches_changelog() -> None:
    """``pyproject.toml``'s version is the top changelog entry's, so neither drifts."""
    pyproject = tomllib.loads(
        (release_notes.REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    )
    top = release_notes.parse(
        release_notes.DEFAULT_CHANGELOG.read_text(encoding="utf-8")
    )[0]
    assert pyproject["project"]["version"] == top.version
