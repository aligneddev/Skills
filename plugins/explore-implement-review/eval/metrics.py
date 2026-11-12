"""Extract metrics from one eval run (eval/runs/<label>) into metrics.json.

Reads the headless stream (main session), the subagent transcripts Claude Code
writes under ~/.claude/projects/<cwd>/<session>/subagents/, and git.
Usage: python3 metrics.py <run-dir> [<run-dir> ...]
"""

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

STANDARDS = re.compile(
    r"coding_standards\.md|docs[/\\]+agent([/\\]|\b)|\.specify[/\\]+memory|contributing\.md", re.I
)
HOOK_BLOCK = "the coding standards are reviewer-only"
TEST_DECL = re.compile(r"^\+\s*(\[(Fact|Theory)\b|\[InlineData\b|(it|test)\(['\"`])")


def load_meta(run: Path) -> dict:
    meta = {}
    for line in (run / "meta.env").read_text().splitlines():
        k, _, v = line.partition("=")
        meta[k] = v
    return meta


def git(repo: str, *args: str) -> str:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True).stdout


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(text_of(c.get("text") or c.get("content") or "") for c in content)
    return ""


def tool_calls(entries):
    """Yield (name, input, result_text, is_error) for each tool call in a transcript."""
    pending = {}
    for d in entries:
        msg = d.get("message") or {}
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for c in content:
            if c.get("type") == "tool_use":
                pending[c["id"]] = (c["name"], c.get("input") or {})
            elif c.get("type") == "tool_result" and c.get("tool_use_id") in pending:
                name, inp = pending.pop(c["tool_use_id"])
                yield name, inp, text_of(c.get("content")), bool(c.get("is_error"))


def usage_sum(entries) -> dict:
    tot = Counter()
    seen = set()
    for d in entries:
        if d.get("type") != "assistant":
            continue
        msg = d["message"]
        if msg.get("id") in seen:  # one API message can span several transcript lines
            continue
        seen.add(msg.get("id"))
        for k, v in (msg.get("usage") or {}).items():
            if isinstance(v, int):
                tot[k] += v
    return dict(tot)


def agent_type(sub: Path, first_prompt: str, spawns: list) -> str:
    meta = sub.with_suffix(".meta.json")
    if meta.exists():
        m = json.loads(meta.read_text())
        for k in ("agentType", "subagent_type", "agent_type"):
            if m.get(k):
                return m[k]
    for s in spawns:  # fall back to matching the spawn prompt
        if s["prompt"][:200] and s["prompt"][:200] == first_prompt[:200]:
            return s["type"]
    return "unknown"


def analyse(run: Path) -> dict:
    meta = load_meta(run)
    repo = meta["REPO"]
    stream = [json.loads(l) for l in (run / "stream.jsonl").read_text().splitlines() if l.strip()]
    result = next((d for d in reversed(stream) if d.get("type") == "result"), {})
    sid = result.get("session_id") or next(
        (d.get("session_id") for d in stream if d.get("session_id")), meta["SESSION_ID"]
    )
    main = [d for d in stream if not d.get("parent_tool_use_id")]

    spawns, sends, verdicts = [], 0, []
    for name, inp, res, _ in tool_calls(main):
        if name in ("Task", "Agent"):
            spawns.append({"type": inp.get("subagent_type", "?"), "prompt": inp.get("prompt", "")})
            verdicts += re.findall(r"VERDICT:\s*(PASS|CHANGES REQUESTED)", res)
        elif name == "SendMessage":
            sends += 1

    proj = Path.home() / ".claude/projects" / re.sub(r"[^A-Za-z0-9]", "-", repo)
    subs = sorted((proj / sid / "subagents").glob("agent-*.jsonl")) if sid else []
    agents = []
    for sub in subs:
        entries = [json.loads(l) for l in sub.read_text().splitlines() if l.strip()]
        first = next((text_of(d["message"]["content"]) for d in entries if d.get("type") == "user"), "")
        calls = list(tool_calls(entries))
        std_attempts = [
            (n, json.dumps(i)[:160]) for n, i, _, _ in calls if STANDARDS.search(json.dumps(i))
        ]
        verdict = re.findall(
            r"VERDICT:\s*(PASS|CHANGES REQUESTED)",
            "\n".join(text_of(d["message"]["content"]) for d in entries if d.get("type") == "assistant"),
        )
        agents.append(
            {
                "file": sub.name,
                "type": agent_type(sub, first, spawns),
                "tool_calls": len(calls),
                "tools": dict(Counter(n for n, *_ in calls)),
                "standards_touches": len(std_attempts),
                "standards_examples": std_attempts[:5],
                "hook_blocks": sum(HOOK_BLOCK in r for *_, r, _ in calls),
                "skills": [i.get("skill") for n, i, *_ in calls if n == "Skill"],
                "verdicts": verdict,
                "usage": usage_sum(entries),
            }
        )

    start, end = meta["START_SHA"], meta.get("END_SHA", "")
    commits = git(repo, "log", "--format=%h %s", f"{start}..{end}").splitlines() if end else []
    raw = set(git(repo, "diff", "--name-only", start, end).split())
    real = set(git(repo, "diff", "--ignore-cr-at-eol", "--name-only", start, end).split())
    # --ignore-cr-at-eol still lists a file whose only change is EOL in --name-only, so compare numstat.
    numstat = [l.split("\t") for l in git(repo, "diff", "--ignore-cr-at-eol", "--numstat", start, end).splitlines()]
    eol_only = sorted(p for a, b, p in numstat if a == "0" and b == "0")
    patch = git(repo, "diff", "--ignore-cr-at-eol", start, end)
    added = sum(int(a) for a, b, p in numstat if a.isdigit())
    removed = sum(int(b) for a, b, p in numstat if b.isdigit())

    return {
        "label": meta["LABEL"],
        "mode": meta["MODE"],
        "branch": meta["BRANCH"],
        "plugin_version": meta.get("PLUGIN_VERSION"),
        "wall_minutes": round(int(meta.get("WALL_SECONDS", 0)) / 60, 1),
        "cost_usd": round(result.get("total_cost_usd", 0), 2),
        "main_turns": result.get("num_turns"),
        "is_error": result.get("is_error"),
        "spawns": dict(Counter(s["type"] for s in spawns)),
        "send_messages": sends,
        "review_rounds": sum(1 for s in spawns if s["type"].endswith("reviewer")),
        "verdicts": verdicts,
        "agents": agents,
        "hook_blocks": sum(a["hook_blocks"] for a in agents),
        "commits": commits,
        "files_changed": len(real) - len(eol_only),
        "lines_added": added,
        "lines_removed": removed,
        "eol_only_files_committed": eol_only,
        "raw_vs_real_files": [len(raw), len(real)],
        "test_decls_added": sum(1 for l in patch.splitlines() if TEST_DECL.match(l)),
        "final_text": (result.get("result") or "")[-3000:],
    }


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        run = Path(arg)
        m = analyse(run)
        (run / "metrics.json").write_text(json.dumps(m, indent=2))
        print(json.dumps({k: v for k, v in m.items() if k not in ("agents", "final_text")}, indent=2))
