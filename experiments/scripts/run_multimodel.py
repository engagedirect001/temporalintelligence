#!/usr/bin/env python3
"""Run hard-28 TI experiment on GPT-5.2 and Gemini 3 Flash."""

import os, json, time, subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

EXPERIMENT_DIR = Path(__file__).parent
TASKS_DIR = EXPERIMENT_DIR / "tasks_hard_28"
RESULTS_DIR = EXPERIMENT_DIR / "results_hard_28_multimodel"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


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


def categorize_task(task_id: str, buggy_code: str) -> str:
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


def build_prompt(task: Dict, history: List[Dict], condition: str) -> str:
    context = ""
    if condition == "TEMPORAL" and history:
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


# === MODEL CALLERS ===

def call_openai(prompt: str, model: str = "gpt-5.2") -> Tuple[str, float]:
    import openai
    client = openai.OpenAI()
    start = time.time()
    resp = client.chat.completions.create(
        model=model,
        max_completion_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = time.time() - start
    return resp.choices[0].message.content.strip(), elapsed


def call_gemini(prompt: str, model: str = "gemini-2.5-flash") -> Tuple[str, float]:
    from google import genai
    api_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or "AIzaSyBpVoKAZaYW3S_Zg6HQ28VtHum35Uv5Hus"
    client = genai.Client(api_key=api_key)
    start = time.time()
    response = client.models.generate_content(
        model=model,
        contents=prompt,
    )
    elapsed = time.time() - start
    return response.text.strip(), elapsed


def run_experiment(model_name: str, model_id: str, caller, tasks: List[Dict]):
    for condition in ["STATELESS", "TEMPORAL"]:
        run_id = f"{condition}_{model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        work_dir = RESULTS_DIR / "work" / run_id
        work_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"{model_name} — {condition} — {len(tasks)} tasks")
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
                    "task_id": task["task_id"],
                    "condition": condition,
                    "model": model_id,
                    "model_name": model_name,
                    "passed": False,
                    "error": str(e)[:200],
                    "elapsed_ms": 0,
                    "timestamp": datetime.now().isoformat()
                })

        # Save
        passed = sum(1 for r in results if r.get("passed"))
        times = [r["elapsed_ms"] for r in results if r.get("elapsed_ms", 0) > 0]
        summary = {
            "run_id": run_id,
            "condition": condition,
            "model": model_id,
            "model_name": model_name,
            "total_tasks": len(results),
            "passed": passed,
            "success_rate": round(passed / len(results), 4) if results else 0,
            "avg_time_ms": round(sum(times) / len(times)) if times else 0,
        }
        output = {"summary": summary, "results": results}
        filepath = RESULTS_DIR / f"{run_id}.json"
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)
        print(f"\nSaved: {filepath}")
        print(f"Result: {passed}/{len(results)} passed, avg {summary['avg_time_ms']}ms")


if __name__ == "__main__":
    tasks = load_tasks()
    print(f"Loaded {len(tasks)} tasks")

    # Quick connectivity test
    print("\nTesting GPT-5.2...")
    try:
        r, t = call_openai("Say OK", "gpt-5.2")
        print(f"  GPT-5.2 OK ({t*1000:.0f}ms): {r[:50]}")
    except Exception as e:
        print(f"  GPT-5.2 FAILED: {e}")

    print("Testing Gemini Flash...")
    try:
        r, t = call_gemini("Say OK", "gemini-2.5-flash")
        print(f"  Gemini Flash OK ({t*1000:.0f}ms): {r[:50]}")
    except Exception as e:
        print(f"  Gemini Flash FAILED: {e}")

    print("\n--- Running GPT-5.2 ---")
    run_experiment("gpt52", "gpt-5.2", call_openai, tasks)

    print("\n--- Running Gemini Flash ---")
    run_experiment("gemini_flash", "gemini-2.5-flash", call_gemini, tasks)

    print("\n\nALL DONE")
