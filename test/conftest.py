"""Fixtures shared across the bake tests."""

import shutil
import subprocess
from pathlib import Path

import pytest

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def template_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Copies the template into a fresh git repo tagged ``0.0.1``.

    Updating from this repo's own ``vcs_ref="HEAD"`` doesn't work: a dirty
    working tree records an ephemeral ``_commit`` that ``run_update`` can't
    check out, so an update test needs a clean repo with real tags.
    """
    # CI runners have no git identity, and the commits below need one.
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
