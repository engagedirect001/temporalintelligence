# Temporal Intelligence: From Learning Velocity to Learning Acceleration

[![Paper](https://img.shields.io/badge/Paper-PDF-red)](paper/main.pdf)
[![License](https://img.shields.io/badge/License-MIT-blue)](LICENSE)
[![arXiv](https://img.shields.io/badge/arXiv-cs.LG-green)](https://arxiv.org/)

**Author:** Anand Karasi (karasi@alum.mit.edu)  
**Affiliation:** DisruptWithAI Research  
**Website:** [disruptwithai.com](https://disruptwithai.com)

---

## Abstract

Current approaches to machine learning optimization focus on improving *learning velocity* — the rate at which performance improves over time. We argue this framing misses a crucial opportunity: achieving *learning acceleration*, where the rate of improvement itself increases. We introduce **Temporal Intelligence (TI)**, a framework that enables positive learning acceleration through pattern extraction, hierarchical storage, and strategic transfer. In controlled experiments across three frontier models (Claude Opus 4.5, GPT-5.2, Gemini 2.5 Flash), we demonstrate model-dependent acceleration effects, with Claude Opus 4.5 showing 47% faster performance on complex tasks (Cohen's d = 0.95).

## Key Results

### Cross-Model Comparison (28 debugging tasks)

| Model | Hard Task Speedup | Cohen's d | Pass Rate (S→T) |
|-------|:-----------------:|:---------:|:----------------:|
| **Claude Opus 4.5** | **+47.2%** | **0.95** | 28/28 → 28/28 |
| Gemini 2.5 Flash | +5.6% | 0.14 | 24/28 → 24/28 |
| GPT-5.2 | +1.5% | 0.06 | 25/28 → 26/28 |

### Key Findings

1. **TI effect is model-dependent** — strongest on Opus 4.5, modest on Gemini, negligible on GPT-5.2
2. **Compression invariance** — distilled pattern summaries match full-history performance
3. **Complexity threshold** — benefits manifest primarily on hard tasks (d = 0.95) vs easy tasks (d = −0.36)
4. **Pattern transfer, not raw retrieval** — TI stores abstracted strategies, not verbatim context

## Repository Structure

```
├── paper/
│   ├── main.tex                    # LaTeX source
│   ├── main.pdf                    # Compiled paper
│   ├── figures/                    # All 8 figures (300+ DPI)
│   └── supplementary/
│       ├── PROTOCOL.md             # Full experimental protocol
│       ├── statistics.py           # Statistical analysis code
│       ├── ANALYSIS.md             # Detailed statistical analysis
│       ├── THEORETICAL_FRAMEWORK.md
│       └── RESULTS_SUMMARY.md
│
├── experiments/
│   ├── tasks_hard_28/              # All 28 task definitions
│   │   ├── task_01/
│   │   │   ├── buggy_code.py       # Code with injected bugs
│   │   │   └── test_suite.py       # Pytest test suite
│   │   ├── task_02/
│   │   └── ...
│   │
│   ├── scripts/
│   │   ├── run_opus45.py           # Anthropic API experiment runner
│   │   └── run_multimodel.py       # Multi-model runner (GPT-5.2 + Gemini)
│   │
│   ├── patterns/
│   │   └── patterns.md             # Accumulated debugging patterns (SUMMARY condition context)
│   │
│   └── results/
│       ├── opus45/                 # Claude Opus 4.5 results
│       │   ├── STATELESS_opus45.json
│       │   ├── TEMPORAL_opus45.json
│       │   ├── STATELESS_api.json
│       │   └── TEMPORAL_api.json
│       ├── gpt52/                  # GPT-5.2 results
│       │   ├── STATELESS.json
│       │   └── TEMPORAL.json
│       └── gemini_flash/           # Gemini 2.5 Flash results
│           ├── STATELESS.json
│           └── TEMPORAL.json
│
└── README.md
```

## Reproducing the Experiments

### Prerequisites

```bash
# Python dependencies
pip install anthropic openai google-genai scipy numpy pytest

# API keys (set at least one)
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"  
export GOOGLE_API_KEY="your-key"
```

### Running the Experiments

**Single model (Opus 4.5):**
```bash
cd experiments/scripts
python run_opus45.py                    # Runs STATELESS + TEMPORAL
python run_opus45.py --condition STATELESS  # Run one condition
python run_opus45.py --compare          # Compare results
```

**Multi-model (GPT-5.2 + Gemini):**
```bash
cd experiments/scripts
python run_multimodel.py
```

### Experiment Design

Each experiment runs 28 debugging tasks in three conditions:

| Condition | Description |
|-----------|-------------|
| **STATELESS** | Each task solved in isolation, no prior context |
| **TEMPORAL** | Accumulated pattern history from all previous tasks |
| **SUMMARY** | Pre-distilled pattern summary (fixed context) |

**Task difficulty distribution:**
- Easy (tasks 1–10): Single-bug fixes — off-by-one, type errors
- Medium (tasks 11–20): Two-bug fixes — type conversion + logic
- Hard (tasks 21–28): Multi-bug complex algorithms — LRU cache, Dijkstra, MVCC, etc.

### Experimental Infrastructure

All experiments were orchestrated using [OpenClaw](https://github.com/openclaw/openclaw), an open-source framework for managing persistent AI agent sessions. OpenClaw provided:

- **Session isolation** between experimental conditions
- **API orchestration** with rate limiting and response logging
- **Multi-agent coordination** for the experimental pipeline
- **Memory management** for the TEMPORAL condition's accumulated context

Infrastructure: Hostinger KVM 2 VPS (Linux), Node.js v22, OpenClaw v1.x

## The Pattern Context (SUMMARY Condition)

The [`patterns.md`](experiments/patterns/patterns.md) file contains the accumulated debugging patterns used in the SUMMARY condition. These were extracted from the TEMPORAL condition's successful runs and organized into categories:

- **Algorithm Bugs**: LIS path recovery, B-Tree splits, interval merging
- **State Machine Bugs**: TCP transitions, circuit breaker, Raft consensus
- **Concurrency Bugs**: Bounded buffers, async propagation, ring buffers
- **Meta-Patterns**: Off-by-one initialization, incomplete state updates, shallow vs deep copy

## Statistical Analysis

Run the full analysis:
```bash
cd paper/supplementary
python statistics.py
```

Key statistics:
- Overall: t(27) = 2.14, p = 0.041 (significant)
- Hard tasks: t(7) = 2.00, p = 0.086 (underpowered, but d = 0.95)
- Compression invariance: t(27) = −0.42, p = 0.677 (no difference)

## Citation

```bibtex
@article{karasi2026temporal,
  title={Temporal Intelligence: From Learning Velocity to Learning Acceleration},
  author={Karasi, Anand},
  journal={arXiv preprint},
  year={2026}
}
```

## License

MIT License. See [LICENSE](LICENSE) for details.

## Contact

- **Email:** karasi@alum.mit.edu
- **Web:** [disruptwithai.com](https://disruptwithai.com)
- **Blog:** [medium.com/@anandglider](https://medium.com/@anandglider)
