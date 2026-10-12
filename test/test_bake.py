"""Bakes the template with default answers and checks the output is well-formed."""

import os
import re
import shutil
import subprocess
import tomllib
from collections.abc import Iterator
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

# Anything of this shape surviving in a baked file means cookiecutter's Jinja
# pass missed it — the whole point of baking is that none of this remains.
RE_UNRENDERED_JINJA = re.compile(r"\{\{.*cookiecutter[^}]*\}\}")


def copy_tracked_files(checkout: Path, dest: Path) -> None:
    """Copies the files git tracks in a checkout, as they stand on disk.

    Args:
        checkout: Root of the git checkout to copy from.
        dest: Directory to copy into; created if missing.

    Note:
        Untracked files are left behind, including new template files not yet
        `git add`-ed.
    """
    ls_files = subprocess.run(
        ["git", "ls-files", "-z"],
        capture_output=True,
        check=True,
        cwd=checkout,
        text=True,
    )
    for rel_path in filter(None, ls_files.stdout.split("\0")):
        source = checkout / rel_path
        # Tracked but deleted in the working tree.
        if not os.path.lexists(source):
            continue
        target = dest / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target, follow_symlinks=False)


def bake(template_root: Path, workspace: Path) -> Path:
    """Bakes a template checkout's git-tracked files with their default answers.

    Because the template has a pre_prompt hook, cookiecutter copies the whole
    template directory before running it, and that copy fails on any dangling
    symlink — e.g. in a venv built on another machine. Baking from a copy of
    the tracked files keeps whatever else sits in the checkout out of reach.

    Args:
        template_root: Root of the template's git checkout.
        workspace: Empty directory to stage and bake in.

    Returns:
        The generated project's directory.
    """
    staged_template = workspace / "template"
    copy_tracked_files(template_root, staged_template)
    output_dir = cookiecutter(
        str(staged_template),
        no_input=True,
        output_dir=str(workspace / "baked"),
    )
    return Path(output_dir)


@pytest.fixture
def baked_project(tmp_path: Path) -> Iterator[Path]:
    """Bakes the template with its default answers into a temp directory."""
    yield bake(TEMPLATE_ROOT, tmp_path)


@pytest.fixture
def dirty_checkout(tmp_path: Path) -> Path:
    """A git checkout of the template holding venvs built on another machine."""
    checkout = tmp_path / "checkout"
    copy_tracked_files(TEMPLATE_ROOT, checkout)
    subprocess.run(["git", "init", "--quiet"], cwd=checkout, check=True)
    subprocess.run(["git", "add", "--all"], cwd=checkout, check=True)

    for venv_name in (".venv", ".venv.local"):
        venv_bin = checkout / venv_name / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "python").symlink_to("/nonexistent/uv/python/bin/python3")
    return checkout


def test_bakes_without_error(baked_project: Path) -> None:
    """The template renders into a directory that actually exists."""
    assert baked_project.is_dir()


def test_leaves_no_unrendered_jinja(baked_project: Path) -> None:
    """No `{{ cookiecutter.* }}` markers survive rendering in any generated file."""
    offenders = [
        str(path.relative_to(baked_project))
        for path in baked_project.rglob("*")
        if path.is_file()
        and RE_UNRENDERED_JINJA.search(path.read_text(encoding="utf-8"))
    ]
    assert offenders == []


def test_generates_valid_pyproject_toml(baked_project: Path) -> None:
    """The generated project's pyproject.toml parses and names the PyPI package."""
    with (baked_project / "pyproject.toml").open("rb") as f_in:
        data = tomllib.load(f_in)
    assert data["project"]["name"] == "phx-my-python-project"


def test_generates_expected_package_layout(baked_project: Path) -> None:
    """The generated package directory and its py.typed marker both exist."""
    package_dir = baked_project / "src" / "my_python_project"
    assert package_dir.is_dir()
    assert (package_dir / "py.typed").is_file()
    assert (package_dir / "__init__.py").is_file()


def test_generates_licence(baked_project: Path) -> None:
    """The generated project ships an MIT licence file."""
    licence_text = (baked_project / "LICENCE.txt").read_text(encoding="utf-8")
    assert "MIT" in licence_text


def test_claude_md_stays_a_symlink(baked_project: Path) -> None:
    """CLAUDE.md survives baking as a real symlink to AGENTS.md, not a copy.

    cookiecutter's own file-copy mechanism dereferences symlinks in the
    template into independent copies; hooks/post_gen_project.py restores
    this one so AGENTS.md stays the single canonical source.
    """
    claude_md = baked_project / "CLAUDE.md"
    assert claude_md.is_symlink()
    assert claude_md.readlink() == Path("AGENTS.md")


def test_claude_skills_stays_a_symlink(baked_project: Path) -> None:
    """.claude/skills survives baking as a real symlink into .agents/skills."""
    claude_skills = baked_project / ".claude" / "skills"
    assert claude_skills.is_symlink()
    assert claude_skills.readlink() == Path("..") / ".agents" / "skills"


def test_bakes_despite_untracked_junk(dirty_checkout: Path, tmp_path: Path) -> None:
    """Untracked venvs with dangling interpreter symlinks don't break the bake."""
    assert bake(dirty_checkout, tmp_path / "workspace").is_dir()
