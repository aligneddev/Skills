---
name: explore-implement-review
description: Run a code change through the explorer, implementer, and reviewer subagents, then commit. Use for any code change the user wants done with the pipeline, e.g. "use the pipeline", "explore implement review".
---

Subagents cannot call each other, so you (the main session) orchestrate and relay between them.

**Which agents.** If the repo has its own `.claude/agents/explorer.md`, `implementer.md` or `reviewer.md`, spawn those (subagent type `explorer`, ...): they carry repo-specific commands and standards sources. Otherwise spawn this plugin's generic ones: `explore-implement-review:explorer`, `explore-implement-review:implementer`, `explore-implement-review:reviewer`.

## Setup (once per repo)

Background: [Matt Pocock's video](https://youtu.be/LlgiOCmFG_w).

The implementer must not learn the coding standards; only the reviewer reads them. Any agent file a tool auto-loads leaks them.

1. Put the standards in `coding_standards.md` at the repo root. The reviewer reads it plus `docs/agent/*.md`, `.specify/memory/constitution.md` and `CONTRIBUTING.md`. For other sources, copy the plugin's `agents/reviewer.md` into `.claude/agents/` and edit its list.
2. Clean up `AGENTS.md` (auto-loaded by Codex/Copilot-style agents): keep only the project intro, environment/run commands, the "Agent skills" section, and the speckit `SPECKIT START/END` plan pointer. Remove coding rules and links to standards docs; don't link `coding_standards.md` from it.
3. Remove standards from other auto-loaded instruction files: `.github/copilot-instructions.md`, `CLAUDE.md` (and no `@AGENTS.md` import that pulls standards back in), `.cursorrules` or similar.
4. The plugin ships a `PreToolUse` hook that blocks the implementer (this plugin's or a repo `implementer` override) from Read, Grep, Glob, Edit and Write calls on the four default sources, and from Bash commands that name them. It is a guardrail, not a sandbox: a Bash command that reaches them without naming them, or a broad search that matches lines inside them, still gets through. Sources you add in an overridden `reviewer.md` are not covered by the hook; add them to the exclusion lists in `implementer.md` (do not open) and `explorer.md` (do not include). Hooks load when a session starts: after installing or updating the plugin, restart Claude Code before a run.
5. Skills come from the `mattpocock-skills` plugin (`/plugin install mattpocock-skills@claude-plugins-official`), enabled in `.claude/settings.json`. The implementer calls `mattpocock-skills:tdd`, the reviewer calls `mattpocock-skills:code-review`, and the user runs `/mattpocock-skills:retro`. Nothing is copied into `.claude/skills/`.
6. Spec Kit (if used): set `context_file: AGENTS.md` in `.specify/extensions/agent-context/agent-context-config.yml`; its managed block is only a plan pointer. Re-check it after `specify init` or `specify integration install`, which can reset it (e.g. to `CLAUDE.md`, which Claude Code auto-loads).

## Steps

1. **Pin.** Confirm the task and its spec. Before any work starts:
   - Record the fixed point with `git rev-parse HEAD`.
   - Record the **pre-existing changes**: every path in `git status --short`. If `git diff --stat` lists files that `git diff --ignore-cr-at-eol --stat` does not, those are line-ending churn; count them.
   - Check for leaks: read `CLAUDE.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.cursorrules` and any files they `@`-import, and list every coding rule or link to a standards source you find there (Setup steps 2–3).
   - Check for **override drift**: for each repo agent in `.claude/agents/` that overrides one of this plugin's, diff it against the plugin's copy in `agents/` two levels above this skill's base directory (`git diff --no-index --ignore-cr-at-eol <plugin copy> <override>`). Repo-specific commands and sources are expected; plugin instructions missing from the override are drift. List the drift with the plugin version from `.claude-plugin/plugin.json`.

   Report leaks, drift and line-ending churn to the user and carry on; don't edit those files and don't wait for an answer.
2. **Explore.** Spawn `explorer` with the task. Keep its brief.
3. **Implement.** Spawn `implementer` with the task, the explorer brief and the pre-existing changes. Never paste coding standards into its prompt.
4. **Review.** Spawn `reviewer` with the fixed point, the spec, the pre-existing changes, the build and test commands from the brief, and the implementer's latest test report.
5. **Fix loop.** On `VERDICT: CHANGES REQUESTED`, send the findings to the same implementer with SendMessage, then spawn the reviewer again. Cap at 3 review rounds; if it still fails, stop and ask the user.
6. **Commit.** On `VERDICT: PASS`, tell the implementer "review passed, commit" and give it the exact commit message to use, with a Conventional Commits prefix (`feat:`, `fix:`, `docs:`, `chore:`, ...) that you choose, taking the reviewer's view into account. Also give it the pre-existing changes again: it commits only the files it changed for this task. If the visuals changed, view the implementer's screenshots yourself before committing (or take them with the `playwright-cli` skill if it didn't), and attach them to the PR.
7. **Retro (continuous improvement).** Only if the run took 2 or more review rounds, ask the user after the commit to run `/mattpocock-skills:retro` on this session; otherwise skip this step and just report. Retro is model-disabled, so only the user can start it; don't run its workflow yourself. Once it has presented its candidates, apply them yourself, since the implementer must not see the standards and the reviewer is read-only:
   - Turn reviewer findings that came up more than once, or that the reviewer had to invent, into rules in `coding_standards.md`. Prefer an automated check (lint rule, test, hook) for mechanical rules. Remove or clarify rules that misled the reviewer or were never cited.
   - Trim bloat: rules that tooling already enforces, duplicates, vague or unenforceable lines, and anything in `AGENTS.md` beyond the Setup step 2 allow-list.
   - Adapting retro to this pipeline: the file is `coding_standards.md` (retro says `CODING_STANDARDS.md`). Never add a standards pointer to `AGENTS.md`, despite retro's navigation-pointer advice. If a new standards source is added, update the reviewer's source list and the implementer and explorer exclusion lists.
   - Commit these edits separately with a `docs:` message. If there is nothing worth changing, say so and commit nothing.

At the end of every run, report: the commit SHA, the number of review rounds, any leaks, override drift and line-ending churn found at Pin, any hook blocks, whether the reviewer ran the tests itself (and why not, if it couldn't), and any judgement calls left unaddressed.

After applying retro's candidates, report what changed in `coding_standards.md` and `AGENTS.md` (or that nothing changed), with the reason for each change and the retro commit SHA.
