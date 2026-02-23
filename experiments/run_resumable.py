#!/usr/bin/env python3
"""Resumable runner — picks up where it left off from saved JSON files."""
import sys, os, json, glob, time
sys.path.insert(0, '.')
from run_latest_models import *
from run_hard28_multimodel import load_tasks, extract_code, run_pytest, categorize_task, build_prompt, RESULTS_DIR
from datetime import datetime

def find_existing(model_name, condition):
    """Find existing result file and return (path, completed_task_ids)."""
    pattern = f"{RESULTS_DIR}/{condition}_{model_name}_*.json"
    files = sorted(glob.glob(pattern))
    if not files:
        return None, set()
    with open(files[-1]) as f:
        data = json.load(f)
    done = {r["task_id"] for r in data["results"] if r.get("elapsed_ms", 0) > 0}
    return files[-1], done

def run_model_resumable(model_name, model_id, caller, tasks):
    for condition in ["STATELESS", "TEMPORAL"]:
        existing_file, done_ids = find_existing(model_name, condition)
        
        if existing_file and len(done_ids) == len(tasks):
            print(f"\n{model_name} {condition}: already complete ({len(done_ids)}/{len(tasks)}), skipping")
            continue
        
        # Load existing results or start fresh
        if existing_file and done_ids:
            with open(existing_file) as f:
                saved = json.load(f)
            results = saved["results"]
            history = [{"task_id": r["task_id"], "passed": r.get("passed", False), "category": r.get("category", ""), "fix_note": ""} for r in results if r.get("elapsed_ms", 0) > 0]
            run_id = saved["summary"]["run_id"]
            print(f"\n{'='*60}")
            print(f"{model_name} ({model_id}) — {condition} — RESUMING from {len(done_ids)}/{len(tasks)}")
            print(f"{'='*60}")
        else:
            results = []
            history = []
            run_id = f"{condition}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"\n{'='*60}")
            print(f"{model_name} ({model_id}) — {condition} — {len(tasks)} tasks")
            print(f"{'='*60}")

        work_dir = RESULTS_DIR / "work" / run_id
        work_dir.mkdir(parents=True, exist_ok=True)

        for i, task in enumerate(tasks, 1):
            if task["task_id"] in done_ids:
                continue

            print(f"[{i}/{len(tasks)}] {task['task_id']}...", end=" ", flush=True)
            category = categorize_task(task["task_id"], task["buggy_code"])
            prompt = build_prompt(task, history, condition)

            try:
                response, elapsed = caller(prompt, model_id)
                fixed_code = extract_code(response)
                test_result = run_pytest(fixed_code, task["test_suite"], work_dir / task["task_id"])

                result = {
                    "task_id": task["task_id"],
                    "difficulty": "easy" if int(task["task_id"].split("_")[1]) <= 10 else "medium" if int(task["task_id"].split("_")[1]) <= 20 else "hard",
                    "condition": condition, "model": model_id, "model_name": model_name,
                    "category": category, "passed": test_result["passed"],
                    "tests_passed": test_result["tests_passed"], "tests_total": test_result["tests_total"],
                    "elapsed_ms": round(elapsed * 1000), "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                history.append({"task_id": task["task_id"], "passed": test_result["passed"], "category": category, "fix_note": f"{category}: {'fixed' if test_result['passed'] else 'failed'}"})
                print(f"{'✓' if test_result['passed'] else '✗'} ({elapsed*1000:.0f}ms)")
            except Exception as e:
                print(f"ERROR: {e}")
                results.append({"task_id": task["task_id"], "condition": condition, "model": model_id, "model_name": model_name, "passed": False, "error": str(e)[:200], "elapsed_ms": 0, "timestamp": datetime.now().isoformat()})

            # Save incrementally
            passed = sum(1 for r in results if r.get("passed"))
            times = [r["elapsed_ms"] for r in results if r.get("elapsed_ms", 0) > 0]
            output = {"summary": {"run_id": run_id, "condition": condition, "model": model_id, "model_name": model_name, "total_tasks": len(results), "passed": passed, "success_rate": round(passed / len(results), 4), "avg_time_ms": round(sum(times) / len(times)) if times else 0}, "results": results}
            with open(RESULTS_DIR / f"{run_id}.json", "w") as f:
                json.dump(output, f, indent=2)

        passed = sum(1 for r in results if r.get("passed"))
        print(f"\nFINAL: {passed}/{len(results)} passed")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("model", choices=["gpt52pro", "gemini3pro", "opus46"])
    args = parser.parse_args()

    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks")

    callers = {
        "gpt52pro": ("gpt-5.2-pro", call_gpt52pro),
        "gemini3pro": ("gemini-3-pro-preview", call_gemini31),
        "opus46": ("claude-opus-4-6", call_opus46),
    }
    model_id, caller = callers[args.model]
    run_model_resumable(args.model, model_id, caller, tasks)
    print(f"\n{args.model} COMPLETE")
