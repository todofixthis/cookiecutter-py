"""Checks the generated template-owned rule against the template and a bake."""

import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
import yaml

from scripts import template_owned

from .conftest import TEMPLATE_ROOT

RULE_TEMPLATE = TEMPLATE_ROOT / "template" / ".agents/rules/template-owned.md.jinja"


def baked_paths(project: Path) -> set[str]:
    """List every file in a baked project, symlinked spellings included."""
    paths = set()
    for root, dirs, files in os.walk(project, followlinks=True):
        dirs[:] = [d for d in dirs if d != ".git"]
        for name in files:
            paths.add((Path(root) / name).relative_to(project).as_posix())
    return paths


def rule_paths(project: Path) -> list[str]:
    """Read the `paths:` list from a baked project's template-owned rule."""
    text = (project / template_owned.RULE_RELPATH).read_text()
    frontmatter = text.split("---\n")[1]
    paths: list[str] = yaml.safe_load(frontmatter)["paths"]
    return paths


def test_committed_rule_is_current() -> None:
    """The committed rule matches what the generator writes from template/."""
    assert RULE_TEMPLATE.read_text() == template_owned.render()


def test_rule_lists_every_template_owned_file(baked_project: Path) -> None:
    """A bake's rule lists every baked file except the seeds and project.md."""
    seeds = {
        seed.replace("[[ package_name ]]", "my_python_project")
        for seed in template_owned.SEED_FILES
    }
    first_copy_only = {".agents/rules/project.md", ".claude/rules/project.md"}

    expected = baked_paths(baked_project) - seeds - first_copy_only

    assert set(rule_paths(baked_project)) == expected


@pytest.mark.parametrize("seed", ["docs/api.rst.jinja", "docs/typo.rst"])
def test_generator_rejects_a_seed_naming_no_file(
    monkeypatch: pytest.MonkeyPatch, seed: str
) -> None:
    """A seed spelled with `.jinja`, or naming no template file, fails generation."""
    monkeypatch.setattr(template_owned, "SEED_FILES", (seed,))
    with pytest.raises(ValueError, match="SEED_FILES"):
        template_owned.owned_paths()


def load_plugin(repo: Path) -> ModuleType:
    """Load the regenerating autohooks plugin from a copy of this repo."""
    path = repo / ".autohooks" / "regenerate_template_owned.py"
    spec = importlib.util.spec_from_file_location("regenerate_template_owned", path)
    assert spec is not None and spec.loader is not None
    plugin = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plugin)
    return plugin


@pytest.fixture
def repo_copy(tmp_path: Path) -> Path:
    """Copy the files the plugin and generator read into a scratch repo."""
    repo = tmp_path / "repo"
    for name in (".autohooks", "scripts", "template"):
        shutil.copytree(TEMPLATE_ROOT / name, repo / name, symlinks=True)
    shutil.copy2(TEMPLATE_ROOT / "copier.yml", repo / "copier.yml")
    # The generator lists only files in the git index.
    subprocess.run(["git", "init", "--quiet"], check=True, cwd=repo)
    subprocess.run(["git", "add", "--all"], check=True, cwd=repo)
    return repo


@pytest.mark.parametrize(
    ("staged", "stale", "regenerated"),
    [
        ("template/AGENTS.md", True, True),
        ("template/AGENTS.md", False, False),
        ("README.md", True, False),
    ],
)
def test_plugin_regenerates_a_stale_rule(
    repo_copy: Path,
    monkeypatch: pytest.MonkeyPatch,
    staged: str,
    stale: bool,
    regenerated: bool,
) -> None:
    """The plugin rewrites and stages a stale rule only when a relevant file is staged."""
    rule = repo_copy / "template" / ".agents/rules/template-owned.md.jinja"
    current = rule.read_text()
    if stale:
        rule.write_text(current + "stale\n")
    plugin = load_plugin(repo_copy)
    staged_files: list[Path] = []
    monkeypatch.setattr(
        plugin, "get_staged_status", lambda: [SimpleNamespace(path=Path(staged))]
    )
    monkeypatch.setattr(plugin, "stage_files", staged_files.extend)

    assert plugin.precommit() == 0

    assert (rule.read_text() == current) == (regenerated or not stale)
    assert staged_files == ([rule] if regenerated else [])


def test_rule_paths_are_all_rendered(baked_project: Path) -> None:
    """No path in a baked rule keeps a copier marker or `.jinja` suffix."""
    for path in rule_paths(baked_project):
        assert not any(m in path for m in ("[[", "[%", "[#")), path
        assert not path.endswith(".jinja"), path
