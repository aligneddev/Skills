# AlignedDev Skills

**Ship code your reviewer would actually approve, without babysitting the agent.**

A Claude Code plugin marketplace. The first plugin, **explore-implement-review**, turns one "make this change" request into a three-agent pipeline: a scout that maps the code, a builder that works test-first, and a reviewer that holds the line on *your* coding standards. Nothing gets committed until the reviewer says `PASS`.

```text
/plugin marketplace add aligneddev/Skills
/plugin install explore-implement-review@aligneddev-skills
```

---

## Why a pipeline?

One agent that writes the code *and* knows the rules grades its own homework. It bends the rules to fit what it already wrote, and the context fills up with standards instead of your code.

explore-implement-review splits the job so each agent has one job and a clean context:

| Agent | Does | Can't |
|---|---|---|
| 🔎 **explorer** | Finds the spec, the files to touch, their callers, tests, fixtures, and the build/test commands. Hands back a brief under 400 words with `file:line` refs. | Edit anything. |
| 🛠️ **implementer** | Builds the change test-first (red → green → refactor), runs the suite, fixes review findings, commits when told. | See your coding standards. On purpose, and a hook blocks it. |
| ⚖️ **reviewer** | Owns the standards. Reviews the diff on two axes, **Standards** and **Spec**, and ends with `VERDICT: PASS` or `VERDICT: CHANGES REQUESTED`. | Edit anything. |

Your main Claude session orchestrates: pin a commit and check for leaked standards → explore → implement → review → fix loop (max 3 rounds) → commit with a Conventional Commits message → retro, when the run needed 2+ review rounds.

**What you get:**

- ✅ **A real review gate.** The reviewer never wrote the code, so it has nothing to defend.
- 🧪 **Tests first, every time.** The implementer drives the change with tests.
- 🎯 **Spec, not vibes.** Every review checks the diff against the task's spec, not just style.
- 🔁 **Standards that get better.** After a run that needed more than one review round, a retro turns repeat findings into rules (or lint checks) and trims rules nobody uses.
- 🧹 **Small, focused contexts.** Each agent sees only what it needs.

Inspired by [Matt Pocock's video](https://youtu.be/LlgiOCmFG_w) on separating implementation from review.

---

## Install

In Claude Code:

```text
/plugin marketplace add aligneddev/Skills
/plugin install explore-implement-review@aligneddev-skills
/plugin install mattpocock-skills@claude-plugins-official
```

The pipeline uses `mattpocock-skills` for `tdd`, `code-review` and `retro`, so install both.

**For a whole team**, commit this to `.claude/settings.json` so everyone who trusts the repo gets prompted to install:

```json
{
  "extraKnownMarketplaces": {
    "aligneddev-skills": {
      "source": { "source": "github", "repo": "aligneddev/Skills" }
    }
  },
  "enabledPlugins": {
    "explore-implement-review@aligneddev-skills": true,
    "mattpocock-skills@claude-plugins-official": true
  }
}
```

## Set up your repo (once)

The whole trick is that **only the reviewer reads the standards**. The plugin's hook stops the implementer opening them, but anything an agent auto-loads leaks them anyway, so:

1. **Write your standards** in `coding_standards.md` at the repo root. The reviewer also reads `docs/agent/*.md`, `.specify/memory/constitution.md` and `CONTRIBUTING.md` if they exist.
2. **Strip rules out of auto-loaded files**: `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, `.cursorrules`. Keep project intro and run commands there; move the rules into `coding_standards.md`. Every run checks these files at the start and reports any leaks it finds; it never edits them.
3. **Optional: override the agents.** Copy any of `plugins/explore-implement-review/agents/*.md` into your repo's `.claude/agents/` to hardcode your build commands or change the reviewer's sources. The skill prefers repo agents over the plugin's.

The skill's own Setup section has the full checklist, including Spec Kit.

## Use it

Just ask:

```text
> use the pipeline to add CSV export to the rides page (spec: specs/012-export/spec.md)
```

or call it directly:

```text
> /explore-implement-review:explore-implement-review fix the timezone bug in issue #42
```

What happens next:

```text
📌 pin       a1b2c3d, no leaks in auto-loaded files
🔎 explore   brief: 6 files, 2 test files, `npm test`, `dotnet test`
🛠️ implement 3 tests added, all green
⚖️ review    CHANGES REQUESTED: 1 must-fix (missing null check, coding_standards.md §4)
🛠️ fix       done, tests green
⚖️ review    PASS
✅ commit    feat: add CSV export to rides page (e4f5a6b)
🔁 retro     2 rounds: run /mattpocock-skills:retro to tune your standards
```

## What's inside

```text
.claude-plugin/marketplace.json          the marketplace catalog
plugins/explore-implement-review/
  .claude-plugin/plugin.json
  skills/explore-implement-review/       the orchestrating skill
  agents/explorer.md                     read-only scout
  agents/implementer.md                  test-first builder
  agents/reviewer.md                     standards owner, PASS/CHANGES REQUESTED
  hooks/guard-standards.sh               blocks the implementer from the standards
GLOSSARY.md                              the pipeline's vocabulary
```

## FAQ

**Does it work without `mattpocock-skills`?** The agents still run, but the implementer loses its TDD loop and the reviewer its two-axis review. Install it.

**Can the implementer cheat and read the standards?** Not by accident. A `PreToolUse` hook denies the implementer any Read, Grep, Glob, Edit or Write on the standards files, and any Bash command that names them. It's a guardrail, not a sandbox: a Bash command that reaches them without naming them, or a repo-wide search that matches lines inside them, still gets through. Keeping standards out of auto-loaded files matters just as much, and the hook can't help there.

**I added my own standards source. Is it guarded?** The hook only knows the four default sources. Add yours to the exclusion lists in your overridden `implementer.md` and `explorer.md`.

**Will it push or open a PR?** No. It commits to your current branch and stops.

## Contributing

Issues and PRs welcome. To try a change locally:

```text
/plugin marketplace add /path/to/your/clone/of/Skills
/plugin install explore-implement-review@aligneddev-skills
```

## License

[MIT](LICENSE)
