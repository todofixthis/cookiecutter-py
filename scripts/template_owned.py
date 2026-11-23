"""Generate the template-owned rule from the files under ``template/``.

copier can't list the template's files at render time without unsafe
features, so the list is generated here and committed (ADR 012). Run with
``--check`` to fail when the committed rule is stale.
"""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "template"
COPIER_YML = REPO_ROOT / "copier.yml"
RULE_RELPATH = ".agents/rules/template-owned.md"
TEMPLATE_SUFFIX = ".jinja"
ANSWERS_FILE = "[[ _copier_conf.answers_file ]]"
# A file name copier renders only when an answer holds, as in
# `docs/[% if docs_site %]conf.py[% endif %]`; copier skips a file whose name
# renders empty (ADR 016).
CONDITIONAL_NAME = re.compile(
    r"\[% if (?P<condition>.+?) %\](?P<name>.*?)\[% endif %\]"
)

# Written for the project to replace: listed in the rule's body, not in its
# `paths:`, so reading one doesn't load guidance that tells the agent to send
# its edits upstream.
SEED_FILES = (
    "README.rst",
    "docs/adr/INDEX.md",
    "docs/[% if docs_site %]api.rst[% endif %]",
    "docs/[% if docs_site %]index.rst[% endif %]",
    "src/[[ package_name ]]/__init__.py",
    "test/__init__.py",
    "test/test_placeholder.py",
)

RULE_BODY = """\
# Template-owned files

Every file in this rule's `paths:` list comes from the copier template
`todofixthis/cookiecutter-py`, which `.copier-answers.yml` records. Each
template release reaches this project as a Renovate PR running
`copier update`, which merges the release into those files.

The template also writes seed files for this project to replace:

{seeds}
Change those freely. copier still merges template changes into them, so a
release that edits a seed can conflict.

A value derived from a copier answer, such as the supported Python range,
changes by re-answering with `copier update --data`, as the
`rotate-python-versions` skill does: never by hand, and never upstream.

Before changing any other listed file, ask whether the reason for the change
depends on something specific to this project: its code, the dependencies it
added itself (not the template's tooling, such as pytest, ruff or mypy), or
its users. Answer from this project alone; don't go looking for
cookiecutter-py.

If it does, make the change here. A rule for this project goes in
`.agents/rules/project.md`, never in a templated rules file; an extra CI job
goes in `.github/workflows/project.yml`, which build.yml calls and `gate`
requires, so the job blocks merges. `project.md` and `project.yml` are this
project's own, written once by the template.

If it doesn't, the change is a template candidate, however local the symptom
that brought it up: a fix for a problem any generated project could hit is a
candidate even when only this one has hit it. Don't make it here: stop and
tell the person you're working with, giving the change as a proposal for the
same file under cookiecutter-py's `template/` directory (where it may carry a
`.jinja` suffix). Open the PR there yourself only if this session already has
it checked out.

Make a candidate here only when the rest of the task can't proceed without it
(the candidate is a step towards the task, not the task itself), or when the
person you're working with asks for it here knowing it's a candidate. Keep it
to what the task needs, and list each such file under a "Template candidates"
heading, with the reason: in the PR description, or in the commit message when
there's no PR. If you leave the change uncommitted, put the list in your
report and ask the person you're working with to carry it into the commit
message. The template's maintainer is then asked to port the committed
change upstream verbatim, placement included, so the release makes the same
change and the next update PR merges cleanly.

To resolve a conflict in a template-update PR, keep this project's
project-only changes and take the template's side for everything else,
including any hand copy of a change the template has now released. Where
both sides changed the same line for reasons of their own, ask the
maintainer. Never resolve a conflict by moving a project rule back into a
templated file.
"""


def _rendered(relpath: str) -> str:
    """Return the path a template file renders to in a generated project."""
    return relpath.removesuffix(TEMPLATE_SUFFIX)


def _listed(path: str, line: str) -> str:
    """Return a rule line for ``path``, rendered only when it renders a file.

    A path with a conditional name is listed without the condition, inside a
    copier block holding it, so a project lacking the file never lists it.
    """
    match = CONDITIONAL_NAME.search(path)
    if match is None:
        return line.format(path=path)
    plain = CONDITIONAL_NAME.sub(r"\g<name>", path)
    return f"[% if {match['condition']} %]{line.format(path=plain)}[% endif %]"


def _sort_key(path: str) -> str:
    """Sort a path as it renders, so a conditional or answers-file name sits
    among the paths it renders beside."""
    return CONDITIONAL_NAME.sub(r"\g<name>", path).replace(
        ANSWERS_FILE, ".copier-answers.yml"
    )


def _skip_if_exists() -> set[str]:
    """Return the paths copier writes only on first copy.

    Raises:
        ValueError: An entry is a glob or Jinja pattern, which copier allows
            but this exact-match exclusion would silently ignore.
    """
    with COPIER_YML.open() as f:
        config = yaml.safe_load(f)
    entries = set(config.get("_skip_if_exists", []))
    patterns = sorted(e for e in entries if any(c in e for c in "*?[{"))
    if patterns:
        raise ValueError(f"_skip_if_exists patterns aren't supported: {patterns}")
    return entries


def _tracked_files() -> set[Path]:
    """Return the files and symlinks git tracks under ``template/``, resolved.

    Reads the index rather than walking the disk alone, so untracked junk (a
    ``__pycache__``, a file not yet added) stays out of the rule, as it stays
    out of a release.
    """
    result = subprocess.run(
        ["git", "ls-files", "-z", "--", "template"],
        capture_output=True,
        check=True,
        cwd=REPO_ROOT,
        text=True,
    )
    return {(REPO_ROOT / p).resolve() for p in result.stdout.split("\0") if p}


def owned_paths() -> list[str]:
    """List every template-owned path, alias spellings included.

    Walks ``template/`` following symlinks, keeping files git tracks, so a file reached through a
    symlinked directory (``.claude/rules/``) or a symlinked file
    (``CLAUDE.md``) is listed under that spelling too. Seed files and the
    paths copier writes only on first copy are left out under every
    spelling. The rule itself is listed whether or not it exists yet, so
    generating it twice gives the same output.

    Raises:
        ValueError: A ``SEED_FILES`` entry names no file under ``template/``.
    """
    excluded = set(SEED_FILES) | _skip_if_exists()
    tracked = _tracked_files()
    rule_target = (TEMPLATE_DIR / (RULE_RELPATH + TEMPLATE_SUFFIX)).resolve()
    paths: set[str] = set()
    seen: set[str] = set()
    rule_dir_aliases: set[str] = set()

    for root, dirs, files in os.walk(TEMPLATE_DIR, followlinks=True):
        root_path = Path(root)
        if root_path.resolve() == rule_target.parent:
            rule_dir_aliases.add(root_path.relative_to(TEMPLATE_DIR).as_posix())
        for name in files:
            path = root_path / name
            target = path.resolve()
            if target == rule_target or target not in tracked:
                continue
            canonical = _rendered(target.relative_to(TEMPLATE_DIR).as_posix())
            seen.add(canonical)
            if canonical in excluded:
                continue
            paths.add(_rendered(path.relative_to(TEMPLATE_DIR).as_posix()))

    missing = set(SEED_FILES) - seen
    if missing:
        raise ValueError(
            f"SEED_FILES names no template file: {sorted(missing)}. Spell each "
            "entry as it renders (no `.jinja`), keeping `[[ … ]]` path markers."
        )

    for alias in rule_dir_aliases:
        paths.add(f"{alias}/{Path(RULE_RELPATH).name}")
    return sorted(paths, key=_sort_key)


def render() -> str:
    """Return the rule's full text, as committed under ``template/``."""
    entries = "".join(_listed(path, '  - "{path}"\n') for path in owned_paths())
    seeds = "".join(_listed(seed, "- `{path}`\n") for seed in SEED_FILES)
    return (
        f"---\npaths:\n{entries}---\n\n"
        "[# Generated by scripts/template_owned.py; don't edit by hand. #]\n"
        + RULE_BODY.format(seeds=seeds)
    )


def main() -> int:
    """Write the rule, or with ``--check`` report whether it is stale."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the committed rule differs from the generated one",
    )
    args = parser.parse_args()
    output = TEMPLATE_DIR / (RULE_RELPATH + TEMPLATE_SUFFIX)
    expected = render()

    if args.check:
        if not output.exists() or output.read_text() != expected:
            print(
                f"❌ {output.relative_to(REPO_ROOT)} is stale; run "
                "`uv run python scripts/template_owned.py`",
                file=sys.stderr,
            )
            return 1
        return 0

    output.write_text(expected)
    return 0


if __name__ == "__main__":
    sys.exit(main())
