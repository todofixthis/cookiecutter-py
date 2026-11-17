"""Proves a template release reaches an already-baked project via copier update."""

import subprocess
from pathlib import Path

import copier
import yaml

from .conftest import (
    PYTHON_POLICY,
    TEMPLATE_ROOT,
    release_template_change,
    run_python_policy_check,
    update_project,
)

# Questions the maintainer must answer on every bake; the template can't guess
# a copyright year or a one-line description.
QUESTIONS_WITHOUT_DEFAULT = {"copyright_year", "project_short_description"}


def test_update_applies_template_change(
    committed_bake: Path, template_repo: Path
) -> None:
    """A change in a new template release lands in an already-baked project."""
    old_line = "TODO"
    new_line = "A line from template release 0.0.2."
    release_template_change(
        template_repo,
        "template/README.rst.jinja",
        lambda text: text.replace(f"\n{old_line}\n", f"\n{new_line}\n"),
    )

    answers = update_project(committed_bake)

    readme = (committed_bake / "README.rst").read_text(encoding="utf-8").splitlines()
    assert new_line in readme
    assert old_line not in readme
    assert "_commit: 0.0.2" in answers


def test_policy_release_keeps_python_version_and_fails_check(
    committed_bake: Path, template_repo: Path
) -> None:
    """A release raising ``python_policy`` keeps the answer and turns the check red."""
    assert run_python_policy_check(committed_bake) == 0
    policy = f'python_policy:\n  type: str\n  default: "{PYTHON_POLICY}"'
    release_template_change(
        template_repo,
        "copier.yml",
        lambda text: text.replace(policy, policy.replace(PYTHON_POLICY, "3.99")),
    )

    answers = update_project(committed_bake)

    assert f"python_version: '{PYTHON_POLICY}'" in answers
    assert run_python_policy_check(committed_bake) == 1


def test_every_question_has_default_or_is_documented() -> None:
    """Only the documented questions lack a default, so Renovate can answer the rest."""
    config = yaml.safe_load((TEMPLATE_ROOT / "copier.yml").read_text(encoding="utf-8"))
    missing = {
        name
        for name, question in config.items()
        # Underscore keys are copier settings, not questions; `when: false`
        # questions are computed, so each carries a default.
        if not name.startswith("_")
        and question.get("when") is not False
        and "default" not in question
    }
    assert missing == QUESTIONS_WITHOUT_DEFAULT


def test_update_keeps_a_project_without_docs_site(
    template_repo: Path, tmp_path: Path
) -> None:
    """A release reaching a no-docs-site project keeps its answer and leaves the
    Sphinx files out."""
    project = tmp_path / "no-docs"
    copier.run_copy(
        str(template_repo),
        project,
        data={
            "copyright_year": 2026,
            "docs_site": False,
            "project_short_description": "x",
            "readthedocs_slug": "parent-project",
        },
        defaults=True,
        vcs_ref="0.0.1",
        unsafe=False,
    )
    for args in (
        ["init", "--quiet"],
        ["add", "--all"],
        ["commit", "--quiet", "-m", "Bake"],
    ):
        subprocess.run(["git", *args], check=True, cwd=project)
    release_template_change(
        template_repo, "template/README.rst.jinja", lambda text: text + "\nNew.\n"
    )

    answers = update_project(project)

    assert "_commit: 0.0.2" in answers
    assert "docs_site: false" in answers
    assert "readthedocs_slug: parent-project" in answers
    assert not (project / "docs" / "conf.py").exists()
    assert not (project / ".readthedocs.yaml").exists()
