# Coding Standards

note: this is an example, you should update it to make it specific for your project

Rules for **new or changed code in a diff**. Cite rules by ID (e.g. `P2`). Do not flag lines the diff does not touch. Anything a formatter, linter or compiler already enforces is not reviewed by hand; when a rule here can be automated, automate it and delete it.

## Functional design

Reference: *Grokking Simplicity* (Eric Normand).

- **P1** Classify code as data, calculations or actions. Calculations hold the logic; actions stay thin: gather inputs, call calculations, apply results.
- **P2** Calculations have no implicit inputs or outputs: no clock, I/O, network, config, randomness, logging, globals or ambient context. Everything comes in as parameters and goes out as the return value; never mutate arguments.
- **P3** Push actions to the edges. Time, I/O and external calls happen at the boundary; the core is pure.
- **P4** Immutable by default. Change data with copy-on-write and defensively copy what crosses a trust boundary. Persistence entities that an ORM requires to be mutable are mapped to immutable models at the boundary.
- **P5** Avoid null. Represent absence or failure with a type (Result, union, option), not a null return. No null-forgiving or non-null assertions in new code.
- **P6** Make illegal states unrepresentable: unions, closed hierarchies, or constructors that validate and return a Result.
- **P7** Return expected outcomes (validation, business, conflict) as values; throw only for unexpected failures.

## Architecture

- **A1** One kind of work per part (UI, domain, persistence, infrastructure); dependencies point inward only.
- **A2** Define ports in inner layers; adapters live at the edge. Translate third-party types at the boundary; they never reach the domain.
- **A3** Keep change-together code together; prefer composition over inheritance.
- **A4** DRY applies to knowledge, not similar-looking lines. Extract shared logic once it has repeated, not before.
- **A5** No speculative features, options or extension points (YAGNI).
- **A6** New runtime paths emit structured logs, metrics and traces.

## Backend (C# / F#)

- **B1** Nullable reference types enabled; no `null!` or `!` suppression.
- **B2** Inject `TimeProvider` for "now"; never call `DateTime.Now`/`UtcNow` (enforce with BannedApiAnalyzers).
- **B3** Models and DTOs are `sealed record`s with positional or `init` properties and read-only collections; change them with `with`.
- **B4** Services are `sealed` classes with primary constructors, registered in one composition root.
- **B5** F# domain code uses discriminated unions, `Result<'T,'E>` and immutable records.

## Frontend (React / TypeScript)

- **F1** TypeScript `strict`; no `any` (use `unknown` plus type guards) and no non-null `!`.
- **F2** Props, state and API types are `readonly`; update with spread, never mutate.
- **F3** Model state variants as discriminated unions, not optional fields and flags.
- **F4** Components render; calculations live in plain functions outside components and hooks; API calls live in a service module.
- **F5** Function components only, one per file, named exports.
- **F6** API types match the backend contracts; client validation mirrors the server's.
- **F7** Meet WCAG 2.1 AA, design mobile-first, and use design tokens instead of hard-coded values.
- **F8** Visual changes are checked in a real browser at desktop and phone width, with screenshots attached to the PR.

## Tests

- **T1** Write the failing test first and show the failure before implementing.
- **T2** Test calculations with plain unit tests; test actions with real collaborators at the boundary rather than mocks where practical.
- **T3** Control time and randomness through injected providers.
- **T4** Bug fixes do not change existing tests unless the intended behavior changed.
- **T5** User-facing changes add or update end-to-end tests; each test owns and discards its data.

## Data

- **D1** Writes are transactional; every migration has a test.
- **D2** Event and message contracts are immutable and versioned.

## Git

- **G1** Conventional Commits; mark breaking changes with `!` or a `BREAKING CHANGE` footer.
- **G2** Changes land through a reviewed PR/MR, never a direct push to the main branch.
- **G3** Unfinished work merged to main sits behind a feature flag.

## Repo-specific

Each repo fills these in; keep them short.

- **Known debt (do not copy):** existing violations by rule ID and path. Do not flag them unless the diff touches them, and never use them as precedent.
- **Verification commands:** the build, test, lint and format commands the reviewer expects to have passed.
