"""Bakes the template with default answers and checks the output is well-formed."""

import json
import re
import subprocess
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


def test_claude_rules_stays_a_symlink(baked_project: Path) -> None:
    """.claude/rules survives baking as a real symlink into .agents/rules."""
    claude_rules = baked_project / ".claude" / "rules"
    assert claude_rules.is_symlink()
    assert claude_rules.readlink() == Path("..") / ".agents" / "rules"


def test_settings_use_shared_marketplace_key(baked_project: Path) -> None:
    """Settings enable superpowers under the marketplace key config-claude uses."""
    settings = json.loads(
        (baked_project / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    plugins = settings["enabledPlugins"]
    assert "superpowers@superpowers-marketplace" in plugins
    assert "superpowers@obra" not in plugins


def test_agents_md_names_only_existing_dirs(baked_project: Path) -> None:
    """Every path Getting Started names exists, bar the optional plans dir."""
    agents_md = (baked_project / "AGENTS.md").read_text(encoding="utf-8")
    section = agents_md.split("## Getting Started", 1)[1].split("\n## ", 1)[0]
    entries = [line for line in section.splitlines() if line.startswith("- ")]
    assert entries
    for line in entries:
        for path in re.findall(r"`([^`\s]+/[^`\s]*)`", line):
            if path == "docs/superpowers/plans/":
                assert "if one exists" in line, line
            else:
                assert (baked_project / path).exists(), path


def test_project_rules_survive_update(template_repo: Path, tmp_path: Path) -> None:
    """copier update leaves a project's own rules file as the project wrote it."""
    dst = tmp_path / "out"
    copier.run_copy(
        str(template_repo),
        dst,
        data={"copyright_year": 2026, "project_short_description": "x"},
        defaults=True,
        vcs_ref="0.0.1",
        unsafe=False,
    )
    project_rules = dst / ".agents" / "rules" / "project.md"
    project_rules.write_text("x", encoding="utf-8")
    subprocess.run(["git", "init", "--quiet"], check=True, cwd=dst)
    subprocess.run(["git", "add", "--all"], check=True, cwd=dst)
    subprocess.run(["git", "commit", "--quiet", "-m", "Bake"], check=True, cwd=dst)

    stub = template_repo / "template" / ".agents" / "rules" / "project.md.jinja"
    with stub.open("a", encoding="utf-8") as f_out:
        f_out.write("A line the template adds later.\n")
    subprocess.run(
        ["git", "commit", "--quiet", "--all", "-m", "0.0.2"],
        check=True,
        cwd=template_repo,
    )
    subprocess.run(["git", "tag", "0.0.2"], check=True, cwd=template_repo)

    copier.run_update(
        dst, defaults=True, overwrite=True, skip_answered=True, unsafe=False
    )

    assert project_rules.read_text(encoding="utf-8") == "x"
    # Read line by line rather than with PyYAML, which ships no type stubs.
    answers = (dst / ".copier-answers.yml").read_text(encoding="utf-8").splitlines()
    assert "_commit: 0.0.2" in answers
