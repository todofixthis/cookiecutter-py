"""Bakes the template with default answers and checks the output is well-formed."""

import re
import tomllib
from collections.abc import Iterator
from pathlib import Path

import copier
import pytest

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

# Anything of this shape surviving in a baked file means copier's Jinja pass
# missed it — the whole point of baking is that none of this remains. Template
# markers always carry inner spaces, so TOML's `[[tool.x]]` arrays of tables
# don't match; the last branch catches a file the port forgot to rename to
# `.jinja`, whose cookiecutter markers would otherwise copy through verbatim.
RE_UNRENDERED_JINJA = re.compile(r"\[\[ .*? \]\]|\[% .*? %\]|\{\{ *cookiecutter\.")


@pytest.fixture
def baked_project(tmp_path: Path) -> Iterator[Path]:
    """Bakes the template with its default answers into a temp directory."""
    output_dir = tmp_path / "out"
    copier.run_copy(
        str(TEMPLATE_ROOT),
        output_dir,
        data={"copyright_year": 2026, "project_short_description": "x"},
        defaults=True,
        vcs_ref="HEAD",
        unsafe=False,
    )
    yield output_dir


def test_unrendered_regex() -> None:
    """The regex catches template markers but not TOML tables or GitHub expressions."""
    for marker in ("[[ x ]]", "[% if x %]", "{{ cookiecutter.x }}"):
        assert RE_UNRENDERED_JINJA.search(marker), marker
    for non_marker in ("[[tool.x]]", "${{ matrix.x }}"):
        assert not RE_UNRENDERED_JINJA.search(non_marker), non_marker


def test_bakes_without_error(baked_project: Path) -> None:
    """The template renders into a directory that actually exists."""
    assert baked_project.is_dir()


def test_leaves_no_unrendered_jinja(baked_project: Path) -> None:
    """No template markers survive rendering in any generated file."""
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


def test_writes_answers_file(baked_project: Path) -> None:
    """The generated project records the template it came from."""
    answers_file = baked_project / ".copier-answers.yml"
    assert answers_file.is_file()
    # Read line by line rather than with PyYAML, which ships no type stubs.
    lines = answers_file.read_text(encoding="utf-8").splitlines()
    assert f"_src_path: {TEMPLATE_ROOT}" in lines


def test_claude_md_stays_a_symlink(baked_project: Path) -> None:
    """CLAUDE.md survives baking as a real symlink to AGENTS.md, not a copy."""
    claude_md = baked_project / "CLAUDE.md"
    assert claude_md.is_symlink()
    assert claude_md.readlink() == Path("AGENTS.md")


def test_claude_skills_stays_a_symlink(baked_project: Path) -> None:
    """.claude/skills survives baking as a real symlink into .agents/skills."""
    claude_skills = baked_project / ".claude" / "skills"
    assert claude_skills.is_symlink()
    assert claude_skills.readlink() == Path("..") / ".agents" / "skills"


def test_readthedocs_syncs_into_rtd_env(baked_project: Path) -> None:
    """ReadTheDocs syncs into its own virtualenv via UV_PROJECT_ENVIRONMENT."""
    config = (baked_project / ".readthedocs.yaml").read_text(encoding="utf-8")
    assert "UV_PROJECT_ENVIRONMENT=$READTHEDOCS_VIRTUALENV_PATH" in config
    assert "VIRTUAL_ENV=$READTHEDOCS" not in config


def test_rotate_skill_searches_hidden_dirs(baked_project: Path) -> None:
    """Every rg command in the rotate skill passes --hidden to reach .github."""
    skill = baked_project / ".agents" / "skills" / "rotate-python-versions" / "SKILL.md"
    rg_lines = [
        line
        for line in skill.read_text(encoding="utf-8").splitlines()
        if line.lstrip().startswith("rg ")
    ]
    assert rg_lines
    assert all("--hidden" in line for line in rg_lines), rg_lines
