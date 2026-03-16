# Does Experience Make LLMs Faster?

**Temporal Pattern Augmentation Across Six Foundation Models**

*Anand Karasi (karasi@alum.mit.edu)*

📄 **[Read the Paper (PDF)](paper/main.pdf)** | 🔗 **[Zenodo (DOI: 10.5281/zenodo.19046131)](https://doi.org/10.5281/zenodo.19046131)**

## Key Finding

Temporal pattern augmentation — injecting historical problem-solving patterns into LLM prompts — **does not improve performance for 5 out of 6 frontier models tested**. Only Gemini 2.5 Flash benefits (+10.8%). Stronger models show slight degradation, suggesting a capability threshold below which augmentation helps and above which it becomes overhead.

| Model | Pass Rate (S→T) | TI Effect | Cohen's d | p-value |
|-------|-----------------|-----------|-----------|---------|
| Claude Opus 4.5 | 23/28 → 23/28 | −1.2% | −0.04 | 0.663 |
| Claude Opus 4.6 | 24/28 → 24/28 | −4.1% | −0.13 | 0.037* |
| GPT-5.2 | 25/28 → 26/28 | −3.2% | −0.09 | 0.333 |
| GPT-5.2 Pro | 27/28 → 27/28 | −2.2% | −0.03 | 0.704 |
| **Gemini 2.5 Flash** | **24/28 → 24/28** | **+10.8%** | **+0.22** | **0.144** |
| Gemini 3.0 Pro | 26/28 → 26/28 | −5.1% | −0.12 | 0.249 |

*336 total experiment runs across 3 providers, all via direct API.*

## Measurement Artifact Discovery

An initial dramatic result (+47% speedup for Opus 4.5) was traced to the **orchestration environment** (OpenClaw sessions) rather than the intervention itself. When tested via direct API under identical conditions, the effect disappeared (−1.2%). This finding serves as a methodological warning for LLM benchmarking research.

## Repository Structure

```
paper/
  main.tex              # LaTeX source
  main.pdf              # Compiled paper
  figures/              # All 6 figures (PDF)
  generate_figures.py   # Figure generation from data
experiments/
  tasks_hard_28/        # 28 code debugging tasks (buggy code + test suites)
  results_multimodel/   # Raw JSON results for all 6 models
  results/              # Earlier single-model results
  patterns/             # Temporal patterns used in TEMPORAL condition
  run_hard28_multimodel.py  # Main experiment runner
  run_resumable.py      # Resumable experiment runner
  run_latest_models.py  # Latest model experiment runner
```

## Reproducing the Experiments

### Requirements
```bash
pip install anthropic openai google-genai matplotlib scipy numpy
```

### Run experiments
```bash
cd experiments

# Set API keys
export ANTHROPIC_API_KEY="your-key"
export OPENAI_API_KEY="your-key"  
export GOOGLE_API_KEY="your-key"

# Run all models
python run_latest_models.py
```

### Regenerate figures
```bash
cd paper
python generate_figures.py
pdflatex main.tex && pdflatex main.tex
```

## Implications

1. **Don't blindly augment.** Adding historical context to prompts for frontier models wastes tokens and slightly degrades performance.
2. **Match scaffolding to capability.** Lighter models (Flash-tier) benefit from pattern injection; frontier models don't.
3. **Watch your measurement infrastructure.** Orchestration frameworks can introduce artifacts that look like genuine effects.

## Citation

```bibtex
@article{karasi2026experience,
  title={Does Experience Make LLMs Faster? Temporal Pattern Augmentation Across Six Foundation Models},
  author={Karasi, Anand},
  doi={10.5281/zenodo.19046131},
  url={https://doi.org/10.5281/zenodo.19046131},
  year={2026}
}
```

## License

MIT License
