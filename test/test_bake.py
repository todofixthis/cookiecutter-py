"""Bakes the template with default answers and checks the output is well-formed."""

import json
import os
import re
import shutil
import subprocess
import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import copier
import pytest
import yaml

from .conftest import TEMPLATE_ROOT, release_template_change, update_project

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


def test_bake_leaves_out_ignored_junk(template_repo: Path, tmp_path: Path) -> None:
    """Gitignored venvs inside template/ stay out of a bake of the dirty tree."""
    # copier bakes a dirty checkout by committing its working tree in a clone,
    # so only .gitignore keeps a venv inside template/ out of the bake; their
    # dangling interpreter symlinks are copied as symlinks, so they never fail
    # the bake the way cookiecutter's copy did.
    shutil.copy2(TEMPLATE_ROOT / ".gitignore", template_repo / ".gitignore")
    subprocess.run(["git", "add", ".gitignore"], check=True, cwd=template_repo)
    subprocess.run(
        ["git", "commit", "--quiet", "-m", "Ignore"], check=True, cwd=template_repo
    )
    junk = (".venv", ".venv.local")
    for venv_name in junk:
        venv_bin = template_repo / "template" / venv_name / "bin"
        venv_bin.mkdir(parents=True)
        (venv_bin / "python").symlink_to("/nonexistent/uv/python/bin/python3")

    output_dir = tmp_path / "junk-bake"
    copier.run_copy(
        str(template_repo),
        output_dir,
        data={"copyright_year": 2026, "project_short_description": "x"},
        defaults=True,
        vcs_ref="HEAD",
        unsafe=False,
    )

    assert (output_dir / "pyproject.toml").is_file()
    assert not any(os.path.lexists(output_dir / name) for name in junk)


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


def test_project_rules_survive_update(
    committed_bake: Path, template_repo: Path
) -> None:
    """copier update leaves a project's own rules file as the project wrote it."""
    project_rules = committed_bake / ".agents" / "rules" / "project.md"
    project_rules.write_text("x", encoding="utf-8")
    subprocess.run(
        ["git", "commit", "--quiet", "--all", "-m", "Edit"],
        check=True,
        cwd=committed_bake,
    )

    release_template_change(
        template_repo,
        ".agents/rules/project.md.jinja",
        lambda text: text + "A line the template adds later.\n",
    )

    answers = update_project(committed_bake)

    assert project_rules.read_text(encoding="utf-8") == "x"
    assert "_commit: 0.0.2" in answers


def load_ci_jobs(project: Path) -> dict[str, dict[str, Any]]:
    """Parses the baked ``build.yml`` and returns its jobs by name."""
    workflow = yaml.safe_load(
        (project / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
    )
    jobs: dict[str, dict[str, Any]] = workflow["jobs"]
    return jobs


def test_ci_job_names(baked_project: Path) -> None:
    """CI runs exactly the jobs the template documents."""
    assert set(load_ci_jobs(baked_project)) == {
        "test",
        "type-check",
        "docs",
        "adrs",
        "gate",
    }


def test_ci_has_gate_needing_every_job(baked_project: Path) -> None:
    """The ``gate`` job aggregates every other job and fails on a non-success."""
    jobs = load_ci_jobs(baked_project)
    gate = jobs["gate"]
    assert set(gate["needs"]) == set(jobs) - {"gate"}
    assert gate["if"] == "always()"
    fail_conditions = [step.get("if", "") for step in gate["steps"]]
    assert any(
        all(result in condition for result in ("failure", "cancelled", "skipped"))
        for condition in fail_conditions
    )


def test_ci_never_checks_template_drift(baked_project: Path) -> None:
    """No file under the baked ``.github/`` mentions ``copier-answers``."""
    # A drift check behind `gate` would fail every PR once a template release
    # lands; Renovate's update PR is how template drift reaches a project.
    offenders = [
        path.relative_to(baked_project)
        for path in (baked_project / ".github").rglob("*")
        if path.is_file() and "copier-answers" in path.read_text(encoding="utf-8")
    ]
    assert not offenders


def test_adr_pin_is_sha_with_version(baked_project: Path) -> None:
    """The ``adrs`` job pins a commit SHA with a trailing version comment."""
    # Read as text: `yaml.safe_load` strips the trailing comment, which
    # Renovate matches on.
    text = (baked_project / ".github" / "workflows" / "build.yml").read_text(
        encoding="utf-8"
    )
    assert re.search(
        r"phx-claude-siat@[0-9a-f]{40}#subdirectory=skills/writing-adrs'"
        r" phx-adr check # \d+\.\d+\.\d+",
        text,
    )


def test_renovate_manages_adr_pin(baked_project: Path) -> None:
    """Renovate bumps the phx-adr pin in CI and AGENTS.md together."""
    config = json.loads((baked_project / "renovate.json").read_text(encoding="utf-8"))
    manager = config["customManagers"][0]
    assert manager["datasourceTemplate"] == "github-tags"
    assert manager["managerFilePatterns"] == [
        "/^\\.github/workflows/build\\.yml$/",
        "/^AGENTS\\.md$/",
    ]


def read_release_skill(project: Path) -> str:
    """Return the baked release skill's text."""
    path = project / ".agents" / "skills" / "release" / "SKILL.md"
    return path.read_text(encoding="utf-8")


def test_release_skill_writes_notes_file(baked_project: Path) -> None:
    """The release skill writes release-<version>.md before first reading it."""
    skill = read_release_skill(baked_project)
    notes_file = "release-<version>.md"
    assert notes_file in skill
    assert skill.index(f"write them to `{notes_file}`") < skill.index("--body-file")


def test_release_skill_single_checksums_heading(baked_project: Path) -> None:
    """The release skill does not append a second checksums heading."""
    skill = read_release_skill(baked_project)
    assert 'echo -e "\\n# SHA256 Checksums"' not in skill


@pytest.mark.parametrize(
    "name",
    ["release-2.0.0.md", "release-2.0.0-body.md", "release-2.0.0.md.asc"],
)
def test_gitignore_covers_release_files(baked_project: Path, name: str) -> None:
    """Git ignores the release skill's working files."""
    subprocess.run(["git", "init", "-q"], cwd=baked_project, check=True)
    result = subprocess.run(
        ["git", "check-ignore", "-q", name], cwd=baked_project, check=False
    )
    assert result.returncode == 0
