Review the uncommitted work against fixed point 40af278e98db509dbfed5df0b477f9bc8d2663fe.

## Spec
Add Midgrade and Diesel as fuel types the user can choose for the gas price lookup. Today the app supports Regular and Premium (`GasGradeRules`, the user's `GasGrade` setting, the `grade` query parameter on the gas-price endpoint, and the grade select on the Settings page). Extend it to four: Regular, Midgrade, Premium, Diesel.

Acceptance criteria:
1. The user can pick Midgrade or Diesel in Settings; it saves and reloads.
2. The gas-price endpoint accepts `grade=Midgrade` and `grade=Diesel` (case-insensitive) and rejects unknown grades with a validation error listing all four.
3. The EIA lookup uses product facet `EPMM` (data source `EIA_EPMM_NUS_Weekly`) for Midgrade and `EPD2D` (`EIA_EPD2D_NUS_Weekly`) for Diesel. Prices stay cached per ISO week and grade.
4. The database check constraint on the user's gas grade allows the new values (new EF migration).
5. Frontend types for grades include the new values. Existing Regular/Premium behaviour is unchanged.

## How to review
- Use `git diff --ignore-cr-at-eol 40af278` and also read the new untracked files from `git status --short -uall`.
- Pre-existing changes: 56 files were already modified before work started, all line-ending churn only. Skip them unless the implementer also made a real content change in them. Five of them did get real edits for this task: GasGradeRules.cs, GasPriceLookupService.cs, UserSettingsService.cs, RidesEndpoints.cs, BikeTrackingDbContext.cs.
- Run the build and test commands yourself:
  - `dotnet test BikeTracking.slnx`
  - Frontend, from `src/BikeTracking.Frontend`: `npm run lint`, `npm run build`, `npm run test:unit`. If the repo `node_modules` has Windows binaries, the implementer used the Linux copy at `$HOME/biketracking-frontend-linux`; copy the current `src` and `tests` into it first.
  - If a tool is missing, wrap it in `bash -l -c "..."`. If it still can't run, don't repair the environment; record the command and the error.
- For each new or changed test, check it would fail if the behaviour it covers were broken.
- End with `Tests: ...` and then the VERDICT line.

## Implementer's report (summary)
- Backend: 534 passed, 2 skipped, 0 failed. Frontend: lint and build pass, 246/246 unit tests pass. E2E (`npm run test:e2e`) not run because it needs Aspire.
- New migration: `20261112134614_AddMidgradeAndDieselGasGrades`. Down sets Midgrade/Diesel rows back to Regular before restoring the old constraint, because SQLite rebuilds the table on rollback.
- The facet switch now maps every grade explicitly and throws on an unmapped one; the old default-to-EPMR fallback is gone.
- The frontend now has a shared `GasGrade` type and a `GAS_GRADES` const in `users-api.ts`. `SettingsPage.test.tsx` uses `importOriginal` to pull the real `GAS_GRADES` into its mock.
- csharpier reformatted three existing lines in edited files. The migration tool bumped the snapshot's product version from 10.0.9 to 10.0.14.
- Screenshots: `/tmp/ui-preview-gas-grade/settings-{desktop,phone}.png`.
