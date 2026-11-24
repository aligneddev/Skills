Review round 2. Review the working-tree changes since fixed point `e6e73f71431ded0f3e4ad2f2e37ba9381047503e` (uncommitted; use `git diff --ignore-cr-at-eol` plus untracked files).

Spec:
Show each ride's average speed in the ride history. A ride has `Miles` and an optional `RideMinutes`. Average speed in mph is `Miles / (RideMinutes / 60)`, rounded to one decimal place.
1. The ride history API response includes `averageSpeedMph` for each ride: a number rounded to one decimal, or absent/null when `RideMinutes` is missing or not greater than zero.
2. The ride history CSV export has a new `AverageSpeedMph` column, placed right after `RideMinutes`, empty when the speed is unknown.
3. The ride history table on the History page shows an "Avg speed" column (e.g. `12.4 mph`, or `—` when unknown), readable at phone width.
4. The calculation lives in one place on the backend and is unit tested, including the missing and zero-minute cases.

Pre-existing changes (ignore): 46 files with line-ending-only CRLF churn, e.g. `.claude/skills/playwright-cli/**`, `.gitattributes`, `.github/agents/speckit.plan.agent.md`, `.gitignore`, `.playwright/cli.config.json`, `.specify/memory/constitution.md`, `AGENTS.md`, `docs/backend-stratified-call-graph.md`, `scripts/ui-preview-mocks/dashboard.json`, `skills-lock.json`, various `src/BikeTracking.Api/...` Dashboard/Imports/Endpoints/Security files, `src/BikeTracking.Frontend/.stylelintrc.json`, `package-lock.json`, `dashboard-page.test.tsx`.

Commands: `dotnet test BikeTracking.slnx`; frontend via `bash scripts/frontend-linux.sh <lint|build|test:unit>`; `dotnet csharpier check <files>`. E2E needs Aspire; not runnable here.

Round 1 findings you raised: (1) new service test used DateTime.UtcNow/Now and TimeProvider.System; (2) no E2E test for the new column; (3) three two-part test names. Judgement call on names.

Implementer's round-2 report:
<implementer-report>
1. `GetRideHistoryService_WithTimedAndUntimedRides_ProjectsAverageSpeedPerRow` now uses fixed dates (2026-06-14/15) and `new FakeTimeProvider(fixedNow)`; added `using BikeTracking.Api.Tests.TestSupport;`. Neighbouring tests unchanged.
2. New E2E test in `src/BikeTracking.Frontend/tests/e2e/edit-ride-history.spec.ts`: "shows average speed for timed rides and a dash for untimed rides" — beforeEach ride 5.0 mi/30 min, records 4.0 mi with no minutes, locates the "Avg speed" column by header, asserts `10.0 mph` and `—`. Passes `tsc -p tsconfig.node.json --noEmit` and eslint; NOT run (no aspire CLI; Playwright config's API path missing in the Linux frontend copy).
3. Renamed: `CalculateAverageSpeedMph_WithFractionalResult_RoundsToOneDecimalPlace`, `GetRideHistory_WithTimedAndUntimedRides_ReturnsAverageSpeedMphOrNull`, `GetRideHistoryService_WithTimedAndUntimedRides_ProjectsAverageSpeedPerRow`.
Red phase (re-captured by removing projection): service test "Assert.Equal() Failure: Values differ, Expected: 12.4, Actual: null"; endpoint test "System.InvalidOperationException : The requested operation requires an element of type 'Number', but the target element has type 'Null'." Round-1 red evidence for the other tests stands (RideSpeedRulesTests vs null stub, CSV header StartsWith, CSV column Contains, frontend "expected -1 to be greater than -1").
Results: dotnet test 524 passed/2 skipped; frontend lint, build pass; test:unit 241 passed. csharpier formatted only its 9 C# files.
Screenshots unchanged: `/tmp/ui-preview/rides-history-desktop.png`, `/tmp/ui-preview/rides-history-phone.png`.
</implementer-report>

Verify the fixes, check nothing regressed, run tests if you can, and return VERDICT: PASS or VERDICT: CHANGES REQUESTED.
