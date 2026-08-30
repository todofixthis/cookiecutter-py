"""Fixes up files cookiecutter copies as independent files but should be symlinks.

cookiecutter's own file-copy mechanism doesn't preserve symlinks, so a
symlink in the template is baked into the generated project as an
independent duplicate of its target instead. This hook restores the
symlinks the generated project actually wants once generation finishes.
"""

import shutil
from pathlib import Path


def main() -> None:
    project_root = Path.cwd()

    claude_md = project_root / "CLAUDE.md"
    claude_md.unlink()
    claude_md.symlink_to("AGENTS.md")

    claude_skills = project_root / ".claude" / "skills"
    shutil.rmtree(claude_skills)
    claude_skills.symlink_to(Path("..") / ".agents" / "skills")


if __name__ == "__main__":
    main()
