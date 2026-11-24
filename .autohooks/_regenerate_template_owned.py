"""Autohooks plugin: regenerate the template-owned rule when it may be stale."""

import importlib.util
from pathlib import Path

from autohooks.api import error, ok
from autohooks.api.git import get_staged_status, stage_files
from autohooks.api.path import match
from autohooks.config import Config
from autohooks.precommit.run import ReportProgress

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GENERATOR = _REPO_ROOT / "scripts" / "template_owned.py"

# A change under template/ can add or remove a template-owned file, and
# copier.yml's `_skip_if_exists` decides what the rule leaves out.
INCLUDE = ("copier.yml", "scripts/template_owned.py", "template/*")


def precommit(
    config: Config | None = None,
    report_progress: ReportProgress | None = None,
    **kwargs: object,
) -> int:
    """Regenerate and stage the rule when a staged file could change it."""
    staged = [f for f in get_staged_status() if match(f.path, INCLUDE)]
    if not staged:
        ok("No staged files affect the template-owned rule.")
        return 0

    # Loaded by path: autohooks puts only .autohooks/ on sys.path.
    spec = importlib.util.spec_from_file_location("template_owned", _GENERATOR)
    if spec is None or spec.loader is None:
        error(f"Could not load {_GENERATOR}.")
        return 1
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)

    output: Path = generator.TEMPLATE_DIR / (
        generator.RULE_RELPATH + generator.TEMPLATE_SUFFIX
    )
    expected: str = generator.render()
    if output.exists() and output.read_text() == expected:
        ok("The template-owned rule is current.")
        return 0

    output.write_text(expected)
    stage_files([output])
    ok(f"Regenerated and staged {output.relative_to(_REPO_ROOT)}.")
    return 0
