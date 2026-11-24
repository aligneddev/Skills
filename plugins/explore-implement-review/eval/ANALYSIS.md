# Eval analysis: iterations 1–3

Written 2026-11-18 from the runs in `eval/runs/` (2026-11-12): metrics, `verify.sh` output and the blind audits.

**Bottom line:** two iterations finished (plugin 1.3.0, then 1.4.0). In both, the pipeline produced slightly cleaner code than the single-agent control, but it cost about twice as much and took about 2.5× as long. The changes in 1.5.0 are aimed at exactly what the audits caught, but 1.5.0 has never been measured. Both it3 runs hit the 5-hour rate limit within 46 seconds and produced nothing.

## Results

| Run | Plugin | Time | Cost | Review rounds | Violations found by audit | Criteria met | Weak tests | Tests pass (verify.sh) |
|---|---|---|---|---|---|---|---|---|
| it1 control | 1.3.0 | 6.3 min | $1.88 | – | 4 | 5/5 | 3 | yes |
| it1 pipeline | 1.3.0 | 14.9 min | $3.96 | 1 (passed first time) | 2 | 5/5 | 2 | yes |
| it2 control | 1.4.0 | 7.2 min | $2.22 | – | 2 | 3/4 (phone width only partial) | 0 | yes |
| it2 pipeline | 1.4.0 | 18.2 min\* | $4.58\* | 2 | 1 | 4/4 | 0 | yes |
| it3 both | 1.5.0 | under 1 min | – | – | – | – | – | stopped by the rate limit |

\* Not counted: `it2-pipeline-aborted`, which was killed partway through its first review after about 13 minutes.

Tasks: it1 = `01-gas-grade-midgrade-diesel`, it2 = `02-ride-average-speed`, it3 = `03-record-ride-fuel-type`.

## What the runs show

### 1. The reviewer missed things the audit caught, and 1.5.0 is a fix for that

- **it1:** the reviewer passed a new `DateTime.UtcNow` in a test helper (`RidesEndpointsSqliteIntegrationTests.cs:407`). It called it a "judgement call" because "nearby helpers do the same". The audit counted it as two violations (B4 and T3).
- **it1:** the reviewer didn't flag 2 tests (`ridesService.test.ts`, `users-api.test.ts`) that only check a value passes through `fetch` or `JSON.stringify`. The audit marked them as weak tests that would pass even if the code were broken.
- **it2 round 2:** the reviewer softened an F11 type mismatch (`averageSpeedMph?: number` while the API sends `null`) into a "judgement call", again because the neighbouring fields do the same. The audit counted it as a violation.

All three were softened by pointing at existing code. 1.5.0 (`4905b46`) adds "existing code is never precedent", allows a judgement call only when the rule itself is ambiguous, adds the pass-through test patterns, and requires a test table and red-phase evidence. The new standards P8, T6 and the wider B2 cover the same ground. These are the right fixes, but they haven't been tested yet.

### 2. The review loop works when it runs

In it2 round 1, the reviewer caught a clock in a test, a missing E2E test and three badly named tests, and the implementer fixed them. The pipeline also kept the standards hidden from the explorer and implementer: neither opened them in any run, and no hook ever blocked anything.

### 3. The quality gain is small next to the cost

The pipeline was ahead by 2 and 1 violations and, in it2, one criterion; on weak tests it was 1 ahead in it1 and level in it2. That's one task per iteration with no repeats. From this data you can't tell a real improvement from run-to-run variation.

## Problems with the eval itself

- **The control isn't blind.** The `it2-control` run read `coding_standards.md`, so the comparison is "single agent with the standards" against "blind implementer plus reviewer". That is fine if it's what you want to measure, but say so when reporting results.
- **Runs interfere with each other.** Control and pipeline ran at the same time and share `~/biketracking-frontend-linux`. `it2-control` reported another session copying files into that folder and ruining its screenshots. That is probably why the first it2 pipeline run was killed (inferred, not recorded).
- **The two arms ran in different places.** The pipeline ran on the mounted `/c/git/...` checkout and the control in `/home/agent/work/bike-control-*`. The pipeline's commits kept failing with "Error building trees" on the mounted drive (up to 2 retries each). That adds time and noise to only one arm.
- **One run per task**, a different task each iteration, and a plugin change between them. Nothing separates the effect of the plugin change from the change of task.
- **The audit is model-graded with no repeats.** Each audit counts violations once, so a difference of 1–2 is within noise.
- **it3 baseline:** `base-it3` (`75f2d86`) passes cleanly, and the pipeline run reused the branch name `feat/gas-grade-options` from it1. Check that branch is in the state you expect before rerunning.

## Reviewer test set

`review_cases.py` replays the reviewer on diffs it has already seen, where the misses are known (`review-cases/cases.json`). Each case reuses the orchestrator's original reviewer prompt, and `run.sh review` recreates the uncommitted state in a temporary worktree. Run it after every reviewer change: it costs about $1 per case and needs no implementer.

```bash
python3 review_cases.py baseline                         # the original reports: 0/3 and 0/1, both PASS
python3 review_cases.py run ../../../neCodeBikeTracking  # replay with the current plugin, then score
python3 review_cases.py run <repo> --repeat 3            # spread across runs
```

Add every miss you find in real use as a new case.

**1.5.0 result (2026-11-24, one run per case, $2.04 in total):** caught 4/4, and both verdicts were `CHANGES REQUESTED`, compared with 0/4 and two PASS verdicts for the original reviewers. The reviewer ran the backend and frontend tests itself both times. The it1 case raised one extra must-fix: there was no red-phase evidence. That is expected, because the replayed 1.3.0 prompt predates that requirement. One run per case can't show consistency yet: run `--repeat 3` before trusting it fully.

## Next steps

1. Rerun it3 on 1.5.0 once the rate limit resets, and run the arms one after another (or give each its own frontend folder).
2. To actually test 1.5.0, rerun task 01 or 02, where the misses are known. Check whether the reviewer now flags the `DateTime.UtcNow` helper, the F11 null mismatch and the pass-through tests.
3. Run each arm 2–3 times per task, and add a short summary script next to `metrics.py` that reports the mean and spread.
4. Decide what the extra ~$2 and ~10 minutes per task buys. If the main value is catching what the audit catches, a cheaper option could be a single agent plus one blind review pass.
