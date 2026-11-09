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

**Review round**:
One reviewer pass over the diff since the Fixed point, ending in a Verdict.
_Avoid_: Iteration, cycle, pass

**Verdict**:
The reviewer's final call on a Review round: PASS or CHANGES REQUESTED.
_Avoid_: Result, outcome, approval

**Leak**:
Any route by which Standards reach the Blind implementer, such as an auto-loaded instruction file or a Brief.
_Avoid_: Contamination, exposure
