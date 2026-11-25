# Development Status Classifier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generated projects are told to leave out the `Development Status` classifier, and the template can never render one.

**Architecture:** A comment above `classifiers` in `template/pyproject.toml.jinja` and a bake test in `test/test_bake.py`. Completed pre-work, committed in `d9082b0`: ADR 023, its index row, the design doc and the backlog item `docs/backlog/mark-project-owned-fields-in-pyproject.md`.

**Tech Stack:** copier, pytest, tomllib.

**Worktree:** `/home/user/cookiecutter-py` (branch: `claude/elegant-dijkstra-25bwdw`; the cloud container is the isolation)

**Spec:** `docs/superpowers/specs/2026-11-24-development-status-classifier-design.md`

## Global Constraints

- Comments go on the line above the code they describe.
- Every test has a one-line docstring stating the behaviour it verifies.
- NZ English in prose.
- Commit with `uv run git commit` (runs autohooks), then push.

## Review Focus

- A project that hand-filled `classifiers` takes the new comment on `copier update` without a conflict. Checked during design with `git merge-file`: a comment line directly above `classifiers = [` merges cleanly. No test owns this; the backlog item covers a merge test.
- Both bakes (`docs_site` yes and no) render the comment, since the line sits outside any `[% if %]`. `each_bake` covers both.

---

### Task 1: Comment and bake test

**Files:**
- Modify: `template/pyproject.toml.jinja` (the `classifiers = [` line)
- Test: `test/test_bake.py` (after `test_generates_valid_pyproject_toml`)

**Interfaces:**
- Consumes: the `each_bake: Path` fixture from `test/conftest.py`.

- [ ] **Step 1: Write the test**

```python
def test_pyproject_has_no_development_status_classifier(each_bake: Path) -> None:
    """The generated pyproject.toml has no Development Status classifier (ADR 023)."""
    with (each_bake / "pyproject.toml").open("rb") as f_in:
        data = tomllib.load(f_in)
    statuses = [
        c for c in data["project"]["classifiers"] if c.startswith("Development Status")
    ]
    assert statuses == []
```

- [ ] **Step 2: Prove it can fail**

Temporarily add `"Development Status :: 5 - Production/Stable",` inside `classifiers = [` in `template/pyproject.toml.jinja`.

Run: `uv run pytest test/test_bake.py -k development_status -q`
Expected: 2 failed (one per bake). Then revert that line: `git diff template/` must show nothing.

- [ ] **Step 3: Add the comment directly above `classifiers = [`, after a blank line separating it from `keywords`'s closing `]`**

```toml
]

# Leave out `Development Status`: the version's pre-release segment states it,
# and a hand-kept classifier goes stale (see
# https://github.com/todofixthis/cookiecutter-py/blob/main/docs/adr/023-leave-the-development-status-classifier-out-of-generated-projects.md).
classifiers = [
```

- [ ] **Step 4: Run the full checks**

Run: `uv run pytest -q && uv run mypy test scripts .autohooks && uv run ruff check test scripts .autohooks`
Expected: all pass; the new test passes for both bakes.

Then bake and validate as CI does:

```bash
rm -rf /tmp/baked && uv run copier copy --defaults --vcs-ref=HEAD --data copyright_year=2026 --data project_short_description=x . /tmp/baked
cd /tmp/baked && uv sync --group ci && uv run ruff check && uv run mypy src test && uv run pytest
```

Expected: exit 0, and `rg -n -B1 '^classifiers' /tmp/baked/pyproject.toml` shows the comment's last line above `classifiers = [`.

- [ ] **Step 5: NZ English pass**

Run: `python3 /root/.claude/skills/phx/skills/nz-english/scan.py template/pyproject.toml.jinja test/test_bake.py`
Expected: exit 1 with 4 hits on external symbols, none in the added lines: `parametrize` ×3 in `test_bake.py` (pytest's API) and the `license` key in `pyproject.toml.jinja` (PEP 621). Change none of them.

- [ ] **Step 6: Commit**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

### Task 2: Remove branch scaffolding

- [ ] **Step 1: Delete the plan and spec**

`git rm docs/superpowers/plans/2026-11-25-development-status-classifier.md docs/superpowers/specs/2026-11-24-development-status-classifier-design.md`

- [ ] **Step 2: Commit and push**

Run `git status` to catch any related unstaged or untracked files, then use the `creative-commits` skill.

## Intentional Decisions

*(Populated during review — reviewers must not re-raise these)*

- No `CHANGELOG.md` entry: AGENTS.md's Releases section writes entries at release time, from the diff since the last tag.
- The spec is deleted with the plan: ADR 023 carries the reasoning, and a retained spec would be a second, staler source.
- The plan file is committed before execution (with the review fixes), so Task 2's `git rm` finds it.
- The blank line before the comment was merge-checked with `git merge-file` against a project with hand-filled `keywords` and `classifiers`: clean.
- No comment in the release skill: ADR 023's scope names `template/.agents/skills/release/`, so the phx hook shows the decision to anyone editing it.

## Self-Review Checklist

- [x] Spec coverage: comment (Task 1 Step 3), test (Steps 1–2), ADR and backlog item (pre-work), changelog (Intentional Decisions).
- [x] Header has a `**Worktree:**` field naming the existing worktree and branch.
- [x] Every commit step reminds the agent to run `git status` first.
- [x] The final task deletes the plan file.
- [x] The plan includes an Intentional Decisions section.
