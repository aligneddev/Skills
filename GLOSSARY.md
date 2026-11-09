# Explore-Implement-Review

A pipeline that takes one requested code change through a scout, a test-first builder and an independent reviewer, so the code is judged against rules its author never saw.

## Language

### Inputs

**Standards**:
The repo's coding rules, which only the reviewer may read.
_Avoid_: Rules, guidelines, conventions, style guide

**Spec**:
The statement of what the change must do, from a spec file or ticket.
_Avoid_: Requirements, story, task description

**Brief**:
The explorer's short, standards-free account of the code a change touches.
_Avoid_: Context, summary, report

### Roles

**Blind implementer**:
The implementer, defined by never seeing the Standards.
_Avoid_: Coder, builder, developer agent

### Process

**Fixed point**:
The commit recorded before work starts, against which the reviewer diffs.
_Avoid_: Base, baseline, starting commit

**Pre-existing changes**:
The paths already modified or untracked at the Fixed point, which the implementer leaves out of its commit and the reviewer leaves out of its review.
_Avoid_: Dirty files, local changes

**Override drift**:
Plugin agent instructions missing from a repo's own copy of that agent in `.claude/agents/`, because plugin updates never reach the copy.
_Avoid_: Stale override, out of sync

**Review round**:
One reviewer pass over the diff since the Fixed point, ending in a Verdict.
_Avoid_: Iteration, cycle, pass

**Verdict**:
The reviewer's final call on a Review round: PASS or CHANGES REQUESTED.
_Avoid_: Result, outcome, approval

**Leak**:
Any route by which Standards reach the Blind implementer, such as an auto-loaded instruction file or a Brief.
_Avoid_: Contamination, exposure
