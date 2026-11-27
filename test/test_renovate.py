"""Checks each Renovate config tracks the validator pin its CI runs (ADR 026)."""

import json
import re
from pathlib import Path

import pytest

from .conftest import TEMPLATE_ROOT

RE_VALIDATOR_PIN = re.compile(r"^\s+RENOVATE_VERSION: (\S+)$", re.MULTILINE)


def tracked_versions(config: Path, workflow: Path, relative: str) -> set[str]:
    """Returns the versions ``config``'s regex managers extract for ``renovate``.

    Args:
        config: The ``renovate.json`` to read.
        workflow: The workflow file to run its regex managers over.
        relative: The workflow's path from the config's repository root,
            which ``managerFilePatterns`` match against.
    """
    managers = json.loads(config.read_text(encoding="utf-8"))["customManagers"]
    text = workflow.read_text(encoding="utf-8")
    versions = set()
    for manager in managers:
        if not any(
            re.search(pattern.strip("/"), relative)
            for pattern in manager["managerFilePatterns"]
        ):
            continue
        for match_string in manager["matchStrings"]:
            # JavaScript names a group (?<name>…), Python (?P<name>…).
            regex = re.compile(re.sub(r"\(\?<(?=\w)", "(?P<", match_string))
            for match in regex.finditer(text):
                groups = match.groupdict()
                if groups.get("depName") == "renovate":
                    versions.add(groups["currentValue"])
    return versions


def pinned_version(workflow: Path) -> str:
    """Returns the one ``RENOVATE_VERSION`` pin in ``workflow``."""
    versions: list[str] = RE_VALIDATOR_PIN.findall(workflow.read_text(encoding="utf-8"))
    (version,) = versions
    return version


@pytest.mark.parametrize(
    "relative",
    [".github/workflows/ci.yml", "template/.github/workflows/build.yml.jinja"],
)
def test_root_config_tracks_validator_pin(relative: str) -> None:
    """This repo's renovate.json extracts each workflow's validator pin."""
    workflow = TEMPLATE_ROOT / relative
    assert tracked_versions(TEMPLATE_ROOT / "renovate.json", workflow, relative) == {
        pinned_version(workflow)
    }


def test_generated_config_tracks_validator_pin(baked_project: Path) -> None:
    """A generated project's renovate.json extracts build.yml's validator pin."""
    relative = ".github/workflows/build.yml"
    workflow = baked_project / relative
    assert tracked_versions(baked_project / "renovate.json", workflow, relative) == {
        pinned_version(workflow)
    }


def test_validator_pins_agree() -> None:
    """This repo's CI and the template's run the same validator version."""
    assert pinned_version(TEMPLATE_ROOT / ".github/workflows/ci.yml") == (
        pinned_version(TEMPLATE_ROOT / "template/.github/workflows/build.yml.jinja")
    )
