"""Bakes the template with default answers and checks the output is well-formed."""

import re
import tomllib
from collections.abc import Iterator
from pathlib import Path

import pytest
from cookiecutter.main import cookiecutter

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent

# Anything of this shape surviving in a baked file means cookiecutter's Jinja
# pass missed it — the whole point of baking is that none of this remains.
RE_UNRENDERED_JINJA = re.compile(r"\{\{.*cookiecutter[^}]*\}\}")


@pytest.fixture
def baked_project(tmp_path: Path) -> Iterator[Path]:
    """Bakes the template with its default answers into a temp directory."""
    output_dir = cookiecutter(
        str(TEMPLATE_ROOT),
        no_input=True,
        output_dir=str(tmp_path),
    )
    yield Path(output_dir)


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
