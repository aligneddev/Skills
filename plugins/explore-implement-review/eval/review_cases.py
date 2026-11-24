"""Reviewer test set: replay the plugin reviewer on diffs with known findings and score what it catches.

  python3 review_cases.py run <repo> [--repeat N] [--only CASE_ID]   # run.sh review per case, then score
  python3 review_cases.py score <run-dir> [<run-dir> ...]            # score finished review runs
  python3 review_cases.py baseline                                   # score the original reviewer reports

Cases live in review-cases/cases.json. An expected finding is caught when one item of the report
(a top-level list item or table row, with its indented continuation lines) matches every regex in
`all_of` and is marked must-fix; for kind=test, a test-table row marked NO also counts. Other must-fix
items are listed so you can judge whether they are real or noise.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

EVAL = Path(__file__).resolve().parent
CASES = json.loads((EVAL / "review-cases" / "cases.json").read_text())["cases"]
PLUGIN_VERSION = json.loads((EVAL.parent / ".claude-plugin" / "plugin.json").read_text())["version"]
ITEM_START = re.compile(r"^(\d+\.\s|[-*]\s|\||#+\s|\*\*)")
MUST_FIX = re.compile(r"(?<!no )must[- ]fix", re.I)
TABLE_NO = re.compile(r"\|\s*\**NO\**\s*\|")
VERDICT = re.compile(r"VERDICT:\s*(PASS|CHANGES REQUESTED)")


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(c.get("text", "") for c in content or [] if isinstance(c, dict))


def reviewer_reports(stream: Path) -> list[str]:
    """Reviewer reports from a stream: the main thread's Agent results for a reviewer spawn."""
    spawned, reports = set(), []
    for line in stream.read_text().splitlines():
        d = json.loads(line) if line.strip() else {}
        if d.get("parent_tool_use_id"):
            continue
        for c in (d.get("message") or {}).get("content") or []:
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use" and c["name"] in ("Agent", "Task"):
                if "reviewer" in (c.get("input") or {}).get("subagent_type", ""):
                    spawned.add(c["id"])
            elif c.get("type") == "tool_result" and c.get("tool_use_id") in spawned:
                text = text_of(c.get("content"))
                # Drop the harness's hand-back frame; the report after it is indented by two spaces.
                text = text.split("The report follows:", 1)[-1]
                reports.append("\n".join(l[2:] if l.startswith("  ") else l for l in text.splitlines()))
    return reports


def items(report: str) -> list[str]:
    out = []
    for line in report.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ITEM_START.match(stripped) and len(line) - len(line.lstrip()) == 0 or not out:
            out.append(stripped)
        else:
            out[-1] += "\n" + stripped
    return out


def score(case: dict, report: str) -> dict:
    report_items = items(report)
    caught, matched = {}, set()
    for exp in case["expected"]:
        hits = [i for i, it in enumerate(report_items) if all(re.search(p, it, re.I) for p in exp["all_of"])]
        matched.update(hits)
        ok = [i for i in hits if MUST_FIX.search(report_items[i])
              or (exp["kind"] == "test" and TABLE_NO.search(report_items[i]))]
        caught[exp["id"]] = {
            "caught": bool(ok),
            "evidence": [report_items[i][:300] for i in (ok or hits)][:2],
        }
    other = [it[:200] for i, it in enumerate(report_items) if i not in matched and MUST_FIX.search(it)]
    verdicts = VERDICT.findall(report)
    return {
        "case": case["id"],
        "caught": sum(v["caught"] for v in caught.values()),
        "expected": len(case["expected"]),
        "verdict": verdicts[-1] if verdicts else None,
        "verdict_ok": bool(verdicts) and verdicts[-1] == case["expected_verdict"],
        "findings": caught,
        "other_must_fix": other,
    }


def case_for(label: str) -> dict:
    for case in sorted(CASES, key=lambda c: -len(c["id"])):
        if case["id"] in label:
            return case
    sys.exit(f"no case id in label {label}")


def print_score(where: str, s: dict) -> None:
    print(f"\n## {where}: {s['case']}  caught {s['caught']}/{s['expected']}  "
          f"verdict {s['verdict']} ({'ok' if s['verdict_ok'] else 'WRONG'})  other must-fix {len(s['other_must_fix'])}")
    for fid, f in s["findings"].items():
        print(f"- [{'x' if f['caught'] else ' '}] {fid}")
        for e in f["evidence"]:
            print("      " + e.replace("\n", " ⏎ ")[:300])
    for o in s["other_must_fix"]:
        print("  other: " + o.replace("\n", " ⏎ "))


def score_runs(run_dirs: list[str]) -> list[dict]:
    results = []
    for rd in map(Path, run_dirs):
        reports = reviewer_reports(rd / "stream.jsonl")
        if not reports:
            print(f"\n## {rd.name}: no reviewer report in the stream (see stderr.log / meta.env)")
            continue
        s = score(case_for(rd.name), reports[-1])
        (rd / "review-score.json").write_text(json.dumps(s, indent=2))
        print_score(rd.name, s)
        results.append(s)
    return results


def main() -> None:
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "score":
        score_runs(args)
    elif cmd == "baseline":
        originals = {"it1-gas-grade": ("it1-pipeline", 0), "it2-avg-speed-round2": ("it2-pipeline", 1)}
        for case in CASES:
            run, idx = originals[case["id"]]
            print_score(f"original {run}", score(case, reviewer_reports(EVAL / "runs" / run / "stream.jsonl")[idx]))
    elif cmd == "run":
        repo = args[0]
        repeat = int(args[args.index("--repeat") + 1]) if "--repeat" in args else 1
        only = args[args.index("--only") + 1] if "--only" in args else None
        dirs = []
        for case in CASES:
            if only and case["id"] != only:
                continue
            for n in range(1, repeat + 1):
                label = f"review-{case['id']}-v{PLUGIN_VERSION}-{n}"
                prompt = EVAL / "review-cases" / case["prompt"]
                subprocess.run([str(EVAL / "run.sh"), "review", label, repo, case["base"], case["head"], str(prompt)],
                               check=False)
                dirs.append(str(EVAL / "runs" / label))
        results = score_runs(dirs)
        caught = sum(r["caught"] for r in results)
        total = sum(r["expected"] for r in results)
        print(f"\nTOTAL: caught {caught}/{total}, verdict ok {sum(r['verdict_ok'] for r in results)}/{len(results)}")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
