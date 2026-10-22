"""Fixtures and helpers shared across the bake and update tests."""

import os
import shutil
import subprocess
from collections.abc import Callable, Iterator
from pathlib import Path

import copier
import pytest
from plumbum import local

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def isolate_git_config(
    tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> Iterator[None]:
    """Keeps the git setup of whoever runs the tests away from them.

    A maintainer's setup changes what git does: commit signing fails for the
    test identity, and a global ignore file (read from ``XDG_CONFIG_HOME``
    whatever the config says) changes which files git ignores. CI has no
    such setup, so without this the suite passes there and fails or
    misleads locally. ``GIT_*`` variables go too, such as those the
    pre-commit hook exports while it runs pytest.

    copier runs git through plumbum, which copies the environment when it's
    imported and never reads ``os.environ`` again, so its copy is patched too.

    ``GIT_CONFIG_GLOBAL`` needs git 2.32; older versions silently ignore it.
    """
    isolated = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "XDG_CONFIG_HOME": str(tmp_path_factory.mktemp("xdg")),
    }
    for name in [name for name in os.environ if name.startswith("GIT_")]:
        monkeypatch.delenv(name)
    for name, value in isolated.items():
        monkeypatch.setenv(name, value)
    # Calling local.env restores plumbum's copy when the block exits
    with local.env(**isolated):
        inherited = [name for name, _ in local.env if name.startswith("GIT_")]
        for name in inherited:
            if name not in isolated:
                del local.env[name]
        yield


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


@pytest.fixture
def template_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copies the template into a fresh git repo tagged ``0.0.1``.

    Updating from this repo's own ``vcs_ref="HEAD"`` doesn't work: a dirty
    working tree records an ephemeral ``_commit`` that ``run_update`` can't
    check out, so an update test needs a clean repo with real tags.
    """
    # isolate_git_config hides any git identity, and the commits below need one.
    for var in ("GIT_AUTHOR", "GIT_COMMITTER"):
        monkeypatch.setenv(f"{var}_NAME", "Bake Test")
        monkeypatch.setenv(f"{var}_EMAIL", "bake-test@example.com")

    repo = tmp_path / "template-repo"
    repo.mkdir()
    shutil.copy2(TEMPLATE_ROOT / "copier.yml", repo / "copier.yml")
    shutil.copytree(TEMPLATE_ROOT / "template", repo / "template", symlinks=True)

    subprocess.run(["git", "init", "--quiet"], check=True, cwd=repo)
    subprocess.run(["git", "add", "--all"], check=True, cwd=repo)
    subprocess.run(["git", "commit", "--quiet", "-m", "0.0.1"], check=True, cwd=repo)
    subprocess.run(["git", "tag", "0.0.1"], check=True, cwd=repo)
    return repo


@pytest.fixture
def committed_bake(template_repo: Path, tmp_path: Path) -> Path:
    """Bakes ``template_repo`` at ``0.0.1`` into a git repo with one commit."""
    dst = tmp_path / "out"
    copier.run_copy(
        str(template_repo),
        dst,
        data={"copyright_year": 2026, "project_short_description": "x"},
        defaults=True,
        vcs_ref="0.0.1",
        unsafe=False,
    )
    subprocess.run(["git", "init", "--quiet"], check=True, cwd=dst)
    subprocess.run(["git", "add", "--all"], check=True, cwd=dst)
    subprocess.run(["git", "commit", "--quiet", "-m", "Bake"], check=True, cwd=dst)
    return dst


def release_template_change(
    template_repo: Path, relative_path: str, edit: Callable[[str], str]
) -> None:
    """Applies ``edit`` to a file under ``template/`` and tags it ``0.0.2``."""
    path = template_repo / "template" / relative_path
    path.write_text(edit(path.read_text(encoding="utf-8")), encoding="utf-8")
    subprocess.run(
        ["git", "commit", "--quiet", "--all", "-m", "0.0.2"],
        check=True,
        cwd=template_repo,
    )
    subprocess.run(["git", "tag", "0.0.2"], check=True, cwd=template_repo)


def update_project(project: Path) -> list[str]:
    """Runs ``copier update`` as Renovate does and returns the answers' lines."""
    copier.run_update(
        project, defaults=True, overwrite=True, skip_answered=True, unsafe=False
    )
    # Read line by line rather than with PyYAML, which ships no type stubs.
    return (project / ".copier-answers.yml").read_text(encoding="utf-8").splitlines()
