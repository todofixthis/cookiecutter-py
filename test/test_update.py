"""Proves a template release reaches an already-baked project via copier update."""

import subprocess
from pathlib import Path
from typing import Any

import copier
import yaml

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

# Questions the maintainer must answer on every bake; the template can't guess
# a copyright year or a one-line description.
QUESTIONS_WITHOUT_DEFAULT = {"copyright_year", "project_short_description"}


def find_questions_without_default(config: dict[str, Any]) -> set[str]:
    """Returns the names of questions in a copier config that lack a default."""
    return {
        name
        for name, question in config.items()
        # Underscore keys are copier settings, not questions.
        if not name.startswith("_") and "default" not in question
    }


def test_update_applies_template_change(template_repo: Path, tmp_path: Path) -> None:
    """A change in a new template release lands in an already-baked project."""
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

    readme_template = template_repo / "template" / "README.rst.jinja"
    old_line = "TODO"
    new_line = "A line from template release 0.0.2."
    text = readme_template.read_text(encoding="utf-8")
    assert text.count(f"\n{old_line}\n") == 1
    readme_template.write_text(text.replace(old_line, new_line), encoding="utf-8")
    subprocess.run(
        ["git", "commit", "--quiet", "--all", "-m", "0.0.2"],
        check=True,
        cwd=template_repo,
    )
    subprocess.run(["git", "tag", "0.0.2"], check=True, cwd=template_repo)

    copier.run_update(
        dst, defaults=True, overwrite=True, skip_answered=True, unsafe=False
    )

    readme = (dst / "README.rst").read_text(encoding="utf-8").splitlines()
    assert new_line in readme
    assert old_line not in readme
    # Read line by line rather than with PyYAML, which ships no type stubs.
    answers = (dst / ".copier-answers.yml").read_text(encoding="utf-8").splitlines()
    assert "_commit: 0.0.2" in answers


def test_default_check_finds_missing_default() -> None:
    """The default check flags a question without one and skips settings."""
    config = {
        "_subdirectory": "template",
        "has_default": {"type": "str", "default": "x"},
        "computed": {"type": "str", "default": "y", "when": False},
        "no_default": {"type": "str"},
    }
    assert find_questions_without_default(config) == {"no_default"}


def test_every_question_has_default_or_is_documented() -> None:
    """Only the documented questions lack a default, so Renovate can answer the rest."""
    config = yaml.safe_load((TEMPLATE_ROOT / "copier.yml").read_text(encoding="utf-8"))
    assert find_questions_without_default(config) == QUESTIONS_WITHOUT_DEFAULT
