---
status: Accepted
date: 2026-10-31
scope: [scripts/template_owned.py, template/.agents/rules/template-owned.md.jinja]
summary: The template-owned rule asks whether a change's reason depends on something specific to the generated project, which the agent can answer from that project alone, not whether it suits every project; a candidate is proposed upstream, or made and flagged under Template candidates only when the rest of the task depends on it or the person working with the agent asks for it.
revisit-when: A template-wide change turns up made in a generated project without a Template candidates flag; reviewing projects' PRs, the maintainer finds most flagged candidates were project-only after all; a generated project gets a maintainer who doesn't also maintain the template.
---

# 014: Decide Template Candidates from Local Knowledge

## Context

[012-generate-a-path-scoped-rule-naming-template-owned-files.md][] gives generated
projects a rule listing every template-owned file, and the rule's body tells an agent what
to do before editing one. It asked whether the change "would be right for every project
generated from the template", and told the agent not to go looking for this repository to
check. On [todofixthis/class-registry#142][], the maintainer pointed out that the question
needs knowledge of this template that an agent in a generated project doesn't have, and
shouldn't have to fetch. Its answer is a guess: guess "every project" and routine work
stops; guess "just this one" and a template-wide change lands in one project, which ADR 012
exists to prevent.

Conflicts are not the main cost. `copier update` merges three ways, so an edit to a
template-owned file conflicts only where a release changes the same or neighbouring lines.
The cost that matters is duplication: a fix every project needs, made in one.

012 also decides how the rule is generated, regenerated and checked. None of that changes
here; this ADR covers only what the rule's body tells the agent.

## Options

### Option 1: Do nothing

**Cons:** The agent answers a question it has no means to answer.
**Risks:** A template-wide change lands in one project whenever the agent guesses "just us".

### Option 2: Ask a question the project can answer (Accepted)

Ask whether the reason for the change depends on something specific to this project: its
code, the dependencies it added itself (not the template's tooling), or its users. If it
does, edit here. If not, it is a template candidate, however local its symptom: propose it
upstream instead. Only when the rest of the task can't proceed without it, or the person
working with the agent asks for it here knowing it's a candidate, does the agent make it
here. It then lists the file under "Template candidates" in the PR description, or the
commit message when there's no PR; an agent leaving the change uncommitted asks the person
to carry the list into the commit message. The template's maintainer is then asked to port
it.

**Pros:** Needs nothing beyond the project, and keeps 012's prevention for the normal case.
**Cons:** The exception lets a candidate land in a project before its release. A port that
differs from the committed change, in wording or placement, conflicts; the rule asks for
the committed change verbatim, and its existing conflict-resolution paragraph settles the
rest.
**Risks:** It assumes one person maintains the template and every generated project, so a
flag reaches someone who can port it. An agent can also frame a shared fix through its own
task ("our tests hang, so add a timeout") and treat it as project-specific. The rule names
that case, and the headless runs below test it.

### Option 3: Edit here and flag every template-owned edit

**Pros:** Never blocks work.
**Cons:** Gives up prevention for detection at review, and flags every routine edit, such
as an added dependency, so the flags become noise.

### Option 4: A CI check diffing template-owned files against the recorded template commit

**Pros:** Catches edits made by hand or through the shell, which the rule never sees.
**Cons:** `pyproject.toml` always differs, and one file mixes shared and project-only
lines, so the check needs per-file or per-section exemptions and still reports noise.

## Decision

Option 2. It replaces a judgement the agent can't make with one it can, without moving the
normal case from prevention to detection. Flagging only candidates keeps the flags rare
enough for the maintainer to act on. Each flag lives in a PR description or commit
message, so it outlasts the session and the maintainer can be asked to port the change.
Option 4 stays a possible later answer to edits the rule can't see, not a first step.

## Consequences

- The rule's body changes in `scripts/template_owned.py`; the generated rule follows, and
  each project picks it up at the next template release.
- A PR or commit in a generated project can carry a "Template candidates" list, which the
  maintainer turns into a PR here.
- 012's headless runs were repeated against this wording, each a Claude Code run in a
  freshly baked project with file edits auto-accepted and shell commands needing approval
  unless listed:
  - asked to add a 15-minute timeout to CI's test job because it hangs, the agent held
    off and proposed the change for `template/.github/workflows/build.yml`, citing the
    "however local the symptom" clause. It also offered to make the change here if told
    to, which that draft's wording didn't allow, so the exception now names that case;
  - asked to add a runtime dependency, it judged the change project-specific. The first
    run couldn't run `uv add`; with `uv add` allowed, the second added it to
    `pyproject.toml`;
  - asked to rewrite `README.rst`'s opening, it treated the file as a seed and rewrote it;
  - asked to silence one dependency's warning in pytest's config, it judged the change
    project-specific and planned it for `pyproject.toml`, but stopped to see the warning
    first, since the named dependency didn't exist;
  - with the exception added, the timeout case again proposed the change, now offering the
    in-project edit as a choice;
  - asked for the timeout here in the same prompt that called it a probable template change,
    it made the edit and listed it under "Template candidates", in its final report since
    there was no PR. That run predates the commit-message home for the flag.

  No run exercised a candidate needed as a step towards another task. The runs loaded the
  session's user-level instructions as well as the project's, so they weren't clean-room
  agents.

[012-generate-a-path-scoped-rule-naming-template-owned-files.md]: 012-generate-a-path-scoped-rule-naming-template-owned-files.md
[todofixthis/class-registry#142]: https://github.com/todofixthis/class-registry/pull/142
