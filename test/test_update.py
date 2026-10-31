"""Proves a template release reaches an already-baked project via copier update."""

from pathlib import Path

import yaml

from .conftest import (
    TEMPLATE_ROOT,
    release_template_change,
    run_python_policy_check,
    update_project,
)

# Questions the maintainer must answer on every bake; the template can't guess
# a copyright year or a one-line description.
QUESTIONS_WITHOUT_DEFAULT = {"copyright_year", "project_short_description"}

PYTHON_POLICY = yaml.safe_load(
    (TEMPLATE_ROOT / "copier.yml").read_text(encoding="utf-8")
)["python_policy"]["default"]


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
