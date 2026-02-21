#!/usr/bin/env python3
"""
Run hard-28 TI experiment via Anthropic API (Opus 4.5) — fair comparison with GPT 5.2.
Both conditions: STATELESS and TEMPORAL.
"""

import os
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
import anthropic

MODEL = "claude-opus-4-5-20251101"
EXPERIMENT_DIR = Path(__file__).parent
TASKS_DIR = EXPERIMENT_DIR / "tasks_hard_28"
RESULTS_DIR = EXPERIMENT_DIR / "results_hard_28_api"

client = None


def init_client():
    global client
    client = anthropic.Anthropic()
    # Quick test
    msg = client.messages.create(model=MODEL, max_tokens=10, messages=[{"role": "user", "content": "hi"}])
    print(f"API connected. Model: {msg.model}")


def load_tasks() -> List[Dict]:
    tasks = []
    for task_dir in sorted(TASKS_DIR.iterdir()):
        if not task_dir.is_dir() or not task_dir.name.startswith("task_"):
            continue
        buggy = task_dir / "buggy_code.py"
        test = task_dir / "test_suite.py"
        if buggy.exists() and test.exists():
            tasks.append({
                "task_id": task_dir.name,
                "path": str(task_dir),
                "buggy_code": buggy.read_text(),
                "test_suite": test.read_text(),
            })
    return tasks


def run_pytest(code: str, test_code: str, work_dir: Path) -> dict:
    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "buggy_code.py").write_text(code)
    (work_dir / "test_suite.py").write_text(test_code)
    try:
        result = subprocess.run(
            ["python3", "-m", "pytest", "test_suite.py", "-v", "--tb=short", "-x"],
            capture_output=True, text=True, timeout=30, cwd=str(work_dir)
        )
        output = result.stdout + result.stderr
        passed = result.returncode == 0
        tp = output.count(" PASSED")
        tf = output.count(" FAILED") + output.count(" ERROR")
        return {"passed": passed, "tests_passed": tp, "tests_total": tp + tf or 1, "output": output[-500:]}
    except subprocess.TimeoutExpired:
        return {"passed": False, "tests_passed": 0, "tests_total": 1, "output": "TIMEOUT"}
    except Exception as e:
        return {"passed": False, "tests_passed": 0, "tests_total": 1, "output": str(e)}


def extract_code(response: str) -> str:
    if "```python" in response:
        start = response.find("```python") + 9
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    if "```" in response:
        start = response.find("```") + 3
        end = response.find("```", start)
        if end > start:
            return response[start:end].strip()
    return response.strip()


def build_prompt(task: Dict, history: List[Dict], condition: str) -> str:
    context = ""
    if condition == "TEMPORAL" and history:
        # Build pattern context from successful fixes
        patterns = {}
        for h in history:
            if h.get("passed"):
                cat = h.get("category", "general")
                if cat not in patterns:
                    patterns[cat] = []
                patterns[cat].append(h.get("fix_note", f"Fixed {h['task_id']}"))
        
        if patterns:
            context = "\n## Debugging patterns from previous tasks:\n"
            for cat, notes in list(patterns.items())[:10]:
                context += f"\n### {cat}:\n"
                for note in notes[-3:]:
                    context += f"- {note}\n"
            context += "\nApply relevant patterns to this task.\n"

    return f"""Fix this Python code. The code has multiple interacting bugs (2-4 bugs). 
Find and fix ALL of them. Return ONLY the complete corrected code, no explanations.

## Buggy Code
```python
{task['buggy_code']}
```

## Tests (all must pass)
```python
{task['test_suite']}
```
{context}
Fixed code:"""


def categorize_task(task_id: str, buggy_code: str) -> str:
    """Rough categorization for pattern tracking."""
    code = buggy_code.lower()
    if any(w in code for w in ["threading", "lock", "async", "await", "semaphore", "buffer"]):
        return "concurrency"
    if any(w in code for w in ["graph", "tree", "heap", "node", "binary_search", "dp", "lis"]):
        return "data_structure_algorithm"
    if any(w in code for w in ["state", "transition", "tcp", "elevator", "circuit", "raft"]):
        return "state_machine"
    if any(w in code for w in ["float", "variance", "kalman", "modular", "matrix", "rsa"]):
        return "math_numerical"
    if any(w in code for w in ["cache", "rate", "http", "pagination", "event", "mvcc"]):
        return "system_design"
    return "general"


def call_claude(prompt: str) -> Tuple[str, float]:
    start = time.time()
    msg = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = time.time() - start
    return msg.content[0].text.strip(), elapsed


def run_condition(condition: str, tasks: List[Dict]):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = f"{condition}_opus45api_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    work_dir = RESULTS_DIR / "work" / run_id
    work_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*60}")
    print(f"EXPERIMENT: {run_id}")
    print(f"Condition: {condition} | Model: {MODEL} | Tasks: {len(tasks)}")
    print(f"{'='*60}\n")

    results = []
    history = []

    for i, task in enumerate(tasks, 1):
        print(f"[{i}/{len(tasks)}] {task['task_id']}...", end=" ", flush=True)

        prompt = build_prompt(task, history, condition)
        category = categorize_task(task["task_id"], task["buggy_code"])

        try:
            response, elapsed = call_claude(prompt)
            fixed_code = extract_code(response)
            test_result = run_pytest(fixed_code, task["test_suite"], work_dir / task["task_id"])

            result = {
                "task_id": task["task_id"],
                "condition": condition,
                "model": MODEL,
                "category": category,
                "passed": test_result["passed"],
                "tests_passed": test_result["tests_passed"],
                "tests_total": test_result["tests_total"],
                "elapsed_ms": round(elapsed * 1000),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)

            # Build history for TEMPORAL
            fix_note = f"{category} bug in {task['task_id']}: {'fixed' if test_result['passed'] else 'failed'}"
            history.append({
                "task_id": task["task_id"],
                "passed": test_result["passed"],
                "category": category,
                "fix_note": fix_note
            })

            status = "✓" if test_result["passed"] else "✗"
            print(f"{status} ({elapsed*1000:.0f}ms) [{category}]")

            if not test_result["passed"]:
                print(f"    Tests: {test_result['tests_passed']}/{test_result['tests_total']}")

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                "task_id": task["task_id"],
                "condition": condition,
                "model": MODEL,
                "passed": False,
                "error": str(e)[:200],
                "timestamp": datetime.now().isoformat()
            })

        # Save incrementally
        _save_results(run_id, condition, results)

    return _save_results(run_id, condition, results)


def _save_results(run_id: str, condition: str, results: List[Dict]) -> dict:
    passed = sum(1 for r in results if r.get("passed"))
    times = [r["elapsed_ms"] for r in results if "elapsed_ms" in r]

    by_category = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in by_category:
            by_category[cat] = {"passed": 0, "total": 0, "times": []}
        by_category[cat]["total"] += 1
        if r.get("passed"):
            by_category[cat]["passed"] += 1
        if "elapsed_ms" in r:
            by_category[cat]["times"].append(r["elapsed_ms"])

    summary = {
        "run_id": run_id,
        "condition": condition,
        "model": MODEL,
        "total_tasks": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "success_rate": round(passed / len(results), 4) if results else 0,
        "avg_time_ms": round(sum(times) / len(times)) if times else 0,
        "total_time_ms": sum(times) if times else 0,
        "by_category": {
            cat: {
                "passed": info["passed"],
                "total": info["total"],
                "avg_time_ms": round(sum(info["times"]) / len(info["times"])) if info["times"] else 0
            }
            for cat, info in by_category.items()
        }
    }

    output = {"summary": summary, "results": results}
    filepath = RESULTS_DIR / f"{run_id}.json"
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)

    return summary


def compare():
    print(f"\n{'='*60}")
    print("COMPARISON")
    print(f"{'='*60}")
    
    summaries = {}
    for f in sorted(RESULTS_DIR.glob("*.json")):
        with open(f) as fp:
            data = json.load(fp)
        s = data.get("summary", {})
        cond = s.get("condition", "?")
        summaries[cond] = s
        
        print(f"\n{cond}:")
        print(f"  Pass: {s['passed']}/{s['total_tasks']} ({s['success_rate']*100:.1f}%)")
        print(f"  Avg time: {s['avg_time_ms']}ms")
        print(f"  Total time: {s['total_time_ms']}ms")
        for cat, info in s.get("by_category", {}).items():
            print(f"    {cat}: {info['passed']}/{info['total']} avg {info['avg_time_ms']}ms")

    if "STATELESS" in summaries and "TEMPORAL" in summaries:
        s = summaries["STATELESS"]
        t = summaries["TEMPORAL"]
        if s["avg_time_ms"] > 0:
            time_diff = (s["avg_time_ms"] - t["avg_time_ms"]) / s["avg_time_ms"] * 100
            print(f"\n→ TEMPORAL time improvement: {time_diff:+.1f}%")
        acc_diff = (t["success_rate"] - s["success_rate"]) * 100
        print(f"→ TEMPORAL accuracy improvement: {acc_diff:+.1f}%")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", default="all", choices=["STATELESS", "TEMPORAL", "all"])
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()

    if args.compare:
        compare()
    else:
        init_client()
        tasks = load_tasks()
        print(f"Loaded {len(tasks)} hard tasks")

        conditions = ["STATELESS", "TEMPORAL"] if args.condition == "all" else [args.condition]
        for cond in conditions:
            run_condition(cond, tasks)

        if len(conditions) > 1:
            compare()
