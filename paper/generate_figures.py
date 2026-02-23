#!/usr/bin/env python3
"""Generate all figures for the Temporal Pattern Augmentation paper."""

import json
import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy import stats

RESULTS_DIR = '/root/clawd-publish/research/experiments/temporal_acceleration/results_hard_28_multimodel'
FIG_DIR = '/root/clawd-publish/research/submission_package/arxiv_preprint/figures'
os.makedirs(FIG_DIR, exist_ok=True)

# Model configs: (display_name, stateless_file, temporal_file)
MODELS = [
    ('Opus 4.5', 'STATELESS_opus45_20260221_215041.json', 'TEMPORAL_opus45_20260221_215605.json'),
    ('Opus 4.6', 'STATELESS_opus46_20260222_051508.json', 'TEMPORAL_opus46_20260222_051957.json'),
    ('GPT-5.2', 'STATELESS_gpt52_20260221_165541.json', 'TEMPORAL_gpt52_20260221_165954.json'),
    ('GPT-5.2 Pro', 'STATELESS_gpt52pro_20260222_153423.json', 'TEMPORAL_gpt52pro_20260222_170144.json'),
    ('Gemini 2.5\nFlash', 'STATELESS_gemini_flash_20260221_171805.json', 'TEMPORAL_gemini_flash_20260221_180305.json'),
    ('Gemini 3.0\nPro', 'STATELESS_gemini3pro_20260222_154106.json', 'TEMPORAL_gemini3pro_20260222_164449.json'),
]

def load(fn):
    with open(os.path.join(RESULTS_DIR, fn)) as f:
        return json.load(f)

def get_times_by_difficulty(data):
    """Return dict: difficulty -> list of elapsed_ms."""
    by_diff = {}
    for r in data['results']:
        d = r.get('difficulty', 'unknown')
        by_diff.setdefault(d, []).append(r['elapsed_ms'])
    return by_diff

def get_paired_times(s_data, t_data):
    """Get paired times for matching task_ids (both must exist)."""
    s_map = {r['task_id']: r['elapsed_ms'] for r in s_data['results']}
    t_map = {r['task_id']: r['elapsed_ms'] for r in t_data['results']}
    common = sorted(set(s_map) & set(t_map))
    return [s_map[k] for k in common], [t_map[k] for k in common]

def cohens_d(a, b):
    na, nb = len(a), len(b)
    if na < 2 or nb < 2: return 0.0
    pooled = np.sqrt(((na-1)*np.std(a,ddof=1)**2 + (nb-1)*np.std(b,ddof=1)**2) / (na+nb-2))
    if pooled == 0: return 0.0
    return (np.mean(a) - np.mean(b)) / pooled  # positive = TI faster

# Load all data
all_data = []
for name, sf, tf in MODELS:
    sd, td = load(sf), load(tf)
    s_avg = sd['summary']['avg_time_ms'] / 1000
    t_avg = td['summary']['avg_time_ms'] / 1000
    effect = (s_avg - t_avg) / s_avg * 100  # positive = TI faster (speedup)
    s_pass = sd['summary']['passed']
    t_pass = td['summary']['passed']
    s_times, t_times = get_paired_times(sd, td)
    all_data.append({
        'name': name, 'sd': sd, 'td': td,
        's_avg': s_avg, 't_avg': t_avg, 'effect': effect,
        's_pass': s_pass, 't_pass': t_pass,
        's_times': s_times, 't_times': t_times,
        's_rate': s_pass / 28,
    })

plt.rcParams.update({'font.size': 12, 'font.family': 'serif'})

# ── Fig 1: TI Effect by Model ──
fig, ax = plt.subplots(figsize=(8, 5))
names = [d['name'] for d in all_data]
effects = [d['effect'] for d in all_data]
colors = ['#2ecc71' if e > 0 else '#e74c3c' for e in effects]
bars = ax.barh(range(len(names)), effects, color=colors, edgecolor='black', linewidth=0.5)
ax.set_yticks(range(len(names)))
ax.set_yticklabels(names, fontsize=11)
ax.set_xlabel('TI Effect on Response Time (%)', fontsize=12)
ax.axvline(0, color='black', linewidth=0.8)
for i, e in enumerate(effects):
    ax.text(e + (0.3 if e >= 0 else -0.3), i, f'{e:+.1f}%', va='center',
            ha='left' if e >= 0 else 'right', fontsize=10, fontweight='bold')
ax.set_title('Temporal Pattern Augmentation Effect by Model', fontsize=14, fontweight='bold')
ax.invert_yaxis()
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig1_ti_effect_by_model.pdf'), dpi=300, bbox_inches='tight')
plt.close()
print('Fig 1 done')

# ── Fig 2: Capability vs Effect ──
fig, ax = plt.subplots(figsize=(7, 5))
x = [d['s_rate']*100 for d in all_data]
y = [d['effect'] for d in all_data]
ax.scatter(x, y, s=120, c=['#2ecc71' if e > 0 else '#e74c3c' for e in y], edgecolors='black', zorder=5)
for d in all_data:
    ax.annotate(d['name'].replace('\n',' '), (d['s_rate']*100, d['effect']),
                textcoords='offset points', xytext=(8, 5), fontsize=9)
# Trend line
z = np.polyfit(x, y, 1)
xline = np.linspace(min(x)-2, max(x)+2, 100)
ax.plot(xline, np.polyval(z, xline), '--', color='gray', alpha=0.7, label=f'Trend (slope={z[0]:.2f})')
ax.axhline(0, color='black', linewidth=0.8)
ax.set_xlabel('STATELESS Pass Rate (%)', fontsize=12)
ax.set_ylabel('TI Effect (%)', fontsize=12)
ax.set_title('Model Capability vs. Augmentation Effect', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig2_capability_vs_effect.pdf'), dpi=300, bbox_inches='tight')
plt.close()
print('Fig 2 done')

# ── Fig 3: Timing by Difficulty ──
diffs = ['easy', 'medium', 'hard']
fig, axes = plt.subplots(1, 3, figsize=(14, 5), sharey=False)
for di, diff in enumerate(diffs):
    ax = axes[di]
    s_means, t_means, labels = [], [], []
    for d in all_data:
        s_by_d = get_times_by_difficulty(d['sd'])
        t_by_d = get_times_by_difficulty(d['td'])
        s_vals = [v/1000 for v in s_by_d.get(diff, [])]
        t_vals = [v/1000 for v in t_by_d.get(diff, [])]
        s_means.append(np.mean(s_vals) if s_vals else 0)
        t_means.append(np.mean(t_vals) if t_vals else 0)
        labels.append(d['name'])
    x = np.arange(len(labels))
    w = 0.35
    ax.bar(x - w/2, s_means, w, label='STATELESS', color='#3498db', edgecolor='black', linewidth=0.5)
    ax.bar(x + w/2, t_means, w, label='TEMPORAL', color='#e67e22', edgecolor='black', linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_title(f'{diff.capitalize()} Tasks', fontsize=13, fontweight='bold')
    ax.set_ylabel('Avg Time (s)' if di == 0 else '', fontsize=11)
    if di == 0: ax.legend(fontsize=9)
fig.suptitle('Response Time by Difficulty Level', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig3_timing_by_difficulty.pdf'), dpi=300, bbox_inches='tight')
plt.close()
print('Fig 3 done')

# ── Fig 4: Measurement Artifact ──
fig, ax = plt.subplots(figsize=(6, 5))
conditions = ['OpenClaw\nSessions', 'Direct API']
values = [47.0, all_data[0]['effect']]  # Opus 4.5
colors = ['#2ecc71', '#e74c3c']
bars = ax.bar(conditions, values, color=colors, edgecolor='black', linewidth=0.8, width=0.5)
for bar, v in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{v:+.1f}%', ha='center', fontsize=14, fontweight='bold')
ax.axhline(0, color='black', linewidth=0.8)
ax.set_ylabel('Measured TI Effect (%)', fontsize=12)
ax.set_title('Opus 4.5: Measurement Environment Matters', fontsize=14, fontweight='bold')
ax.set_ylim(-10, 55)
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig4_measurement_artifact.pdf'), dpi=300, bbox_inches='tight')
plt.close()
print('Fig 4 done')

# ── Fig 5: Effect Size Heatmap ──
model_names_short = [d['name'].replace('\n',' ') for d in all_data]
heatmap = np.zeros((len(all_data), 3))
for i, d in enumerate(all_data):
    for j, diff in enumerate(diffs):
        s_by_d = get_times_by_difficulty(d['sd'])
        t_by_d = get_times_by_difficulty(d['td'])
        s_vals = [v/1000 for v in s_by_d.get(diff, [])]
        t_vals = [v/1000 for v in t_by_d.get(diff, [])]
        heatmap[i, j] = cohens_d(s_vals, t_vals) if len(s_vals) > 1 and len(t_vals) > 1 else 0

fig, ax = plt.subplots(figsize=(7, 5))
vmax = max(abs(heatmap.min()), abs(heatmap.max()), 0.5)
im = ax.imshow(heatmap, cmap='RdYlGn_r', aspect='auto', vmin=-vmax, vmax=vmax)
ax.set_xticks(range(3))
ax.set_xticklabels(['Easy', 'Medium', 'Hard'], fontsize=11)
ax.set_yticks(range(len(model_names_short)))
ax.set_yticklabels(model_names_short, fontsize=10)
for i in range(heatmap.shape[0]):
    for j in range(heatmap.shape[1]):
        ax.text(j, i, f'{heatmap[i,j]:.2f}', ha='center', va='center', fontsize=10,
                color='white' if abs(heatmap[i,j]) > vmax*0.6 else 'black')
cbar = plt.colorbar(im, ax=ax)
cbar.set_label("Cohen's d (negative = slower with TI)", fontsize=10)
ax.set_title("Effect Size by Model and Difficulty", fontsize=14, fontweight='bold')
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig5_effect_size_heatmap.pdf'), dpi=300, bbox_inches='tight')
plt.close()
print('Fig 5 done')

# ── Fig 6: Experimental Design ──
fig, ax = plt.subplots(figsize=(10, 5))
ax.set_xlim(0, 10)
ax.set_ylim(0, 6)
ax.axis('off')

# Boxes
boxes = [
    (0.5, 2.5, '28 Code\nDebugging Tasks', '#ecf0f1'),
    (3.0, 3.5, 'STATELESS\nCondition', '#3498db'),
    (3.0, 1.5, 'TEMPORAL\nCondition', '#e67e22'),
    (6.0, 2.5, '6 Foundation\nModels', '#9b59b6'),
    (8.5, 2.5, 'Pass/Fail +\nResponse Time', '#2ecc71'),
]
for x, y, text, color in boxes:
    rect = mpatches.FancyBboxPatch((x-0.7, y-0.5), 1.4, 1.0, boxstyle='round,pad=0.1',
                                     facecolor=color, edgecolor='black', linewidth=1.5, alpha=0.8)
    ax.add_patch(rect)
    ax.text(x, y, text, ha='center', va='center', fontsize=10, fontweight='bold')

# Arrows
arrow_kw = dict(arrowstyle='->', lw=2, color='black')
from matplotlib.patches import FancyArrowPatch
for (x1, y1, x2, y2) in [(1.2, 2.5, 2.3, 3.5), (1.2, 2.5, 2.3, 1.5),
                           (3.7, 3.5, 5.3, 2.7), (3.7, 1.5, 5.3, 2.3),
                           (6.7, 2.5, 7.8, 2.5)]:
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1), arrowprops=arrow_kw)

# Model list
models_text = 'Opus 4.5 · Opus 4.6 · GPT-5.2\nGPT-5.2 Pro · Gemini Flash · Gemini Pro'
ax.text(6.0, 1.3, models_text, ha='center', va='center', fontsize=8, style='italic', color='#555')

ax.set_title('Experimental Design', fontsize=14, fontweight='bold')
plt.tight_layout()
fig.savefig(os.path.join(FIG_DIR, 'fig6_experimental_design.pdf'), dpi=300, bbox_inches='tight')
plt.close()
print('Fig 6 done')

# ── Print statistics for paper ──
print('\n=== Statistics for Paper ===')
for d in all_data:
    s, t = np.array(d['s_times'])/1000, np.array(d['t_times'])/1000
    tstat, pval = stats.ttest_rel(s, t) if len(s) > 1 else (0, 1)
    cd = cohens_d(list(s), list(t))
    print(f"{d['name'].replace(chr(10),' '):15s}: effect={d['effect']:+.1f}%, "
          f"t={tstat:.3f}, p={pval:.4f}, d={cd:.3f}, "
          f"S={d['s_avg']:.1f}s, T={d['t_avg']:.1f}s, "
          f"pass S={d['s_pass']}/28 T={d['t_pass']}/28")

print('\nAll figures generated.')
