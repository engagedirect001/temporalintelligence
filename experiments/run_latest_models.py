#!/usr/bin/env python3
"""Run hard-28 TI experiment on latest models: Opus 4.6, GPT-5.2 Pro, Gemini 3.1 Pro."""
import sys, os, json, time
sys.path.insert(0, '.')
from run_hard28_multimodel import load_tasks, extract_code, run_pytest, categorize_task, build_prompt, RESULTS_DIR
from datetime import datetime
from typing import Tuple

import anthropic
import openai
from google import genai

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY")
GEMINI_KEY = os.environ.get("GOOGLE_API_KEY") or "YOUR_GOOGLE_API_KEY"


def call_with_retry(fn, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if 'overloaded' in str(e).lower() or '529' in str(e):
                wait = 30 * (attempt + 1)
                print(f"[overloaded, retry in {wait}s]", end=" ", flush=True)
                time.sleep(wait)
            else:
                raise
    raise Exception(f"Failed after {max_retries} retries")


def call_opus46(prompt: str, model: str = "claude-opus-4-6") -> Tuple[str, float]:
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    def _call():
        start = time.time()
        msg = client.messages.create(model=model, max_tokens=4096, messages=[{"role": "user", "content": prompt}])
        elapsed = time.time() - start
        return msg.content[0].text.strip(), elapsed
    return call_with_retry(_call)


def call_gpt52pro(prompt: str, model: str = "gpt-5.2-pro") -> Tuple[str, float]:
    client = openai.OpenAI()
    start = time.time()
    resp = client.responses.create(model=model, input=prompt)
    elapsed = time.time() - start
    return resp.output_text.strip(), elapsed


def call_gemini31(prompt: str, model: str = "gemini-3.1-pro-preview") -> Tuple[str, float]:
    client = genai.Client(api_key=GEMINI_KEY)
    start = time.time()
    response = client.models.generate_content(model=model, contents=prompt)
    elapsed = time.time() - start
    return response.text.strip(), elapsed


def run_model(model_name, model_id, caller, tasks):
    for condition in ["STATELESS", "TEMPORAL"]:
        run_id = f"{condition}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        work_dir = RESULTS_DIR / "work" / run_id
        work_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"{model_name} ({model_id}) — {condition} — {len(tasks)} tasks")
        print(f"{'='*60}")

        results = []
        history = []

        for i, task in enumerate(tasks, 1):
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
                    "condition": condition,
                    "model": model_id,
                    "model_name": model_name,
                    "category": category,
                    "passed": test_result["passed"],
                    "tests_passed": test_result["tests_passed"],
                    "tests_total": test_result["tests_total"],
                    "elapsed_ms": round(elapsed * 1000),
                    "timestamp": datetime.now().isoformat()
                }
                results.append(result)
                history.append({
                    "task_id": task["task_id"],
                    "passed": test_result["passed"],
                    "category": category,
                    "fix_note": f"{category} bug in {task['task_id']}: {'fixed' if test_result['passed'] else 'failed'}"
                })
                status = "✓" if test_result["passed"] else "✗"
                print(f"{status} ({elapsed*1000:.0f}ms)")
            except Exception as e:
                print(f"ERROR: {e}")
                results.append({
                    "task_id": task["task_id"], "condition": condition, "model": model_id,
                    "model_name": model_name, "passed": False, "error": str(e)[:200],
                    "elapsed_ms": 0, "timestamp": datetime.now().isoformat()
                })

            # Save incrementally
            passed = sum(1 for r in results if r.get("passed"))
            times = [r["elapsed_ms"] for r in results if r.get("elapsed_ms", 0) > 0]
            output = {
                "summary": {
                    "run_id": run_id, "condition": condition, "model": model_id,
                    "model_name": model_name, "total_tasks": len(results), "passed": passed,
                    "success_rate": round(passed / len(results), 4),
                    "avg_time_ms": round(sum(times) / len(times)) if times else 0,
                },
                "results": results
            }
            with open(RESULTS_DIR / f"{run_id}.json", "w") as f:
                json.dump(output, f, indent=2)

        print(f"\nFINAL: {passed}/{len(results)} passed, avg {output['summary']['avg_time_ms']}ms")


if __name__ == "__main__":
    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks\n")

    # Test connectivity
    models = [
        ("opus46", "claude-opus-4-6", call_opus46),
        ("gpt52pro", "gpt-5.2-pro", call_gpt52pro),
        ("gemini31pro", "gemini-3.1-pro-preview", call_gemini31),
    ]

    for name, model_id, caller in models:
        print(f"Testing {name} ({model_id})...", end=" ")
        try:
            r, t = caller("Say OK", model_id)
            print(f"OK ({t*1000:.0f}ms)")
        except Exception as e:
            print(f"FAILED: {e}")

    print("\n" + "="*60)
    print("STARTING EXPERIMENTS")
    print("="*60)

    for name, model_id, caller in models:
        run_model(name, model_id, caller, tasks)

    print("\n\nALL DONE")
