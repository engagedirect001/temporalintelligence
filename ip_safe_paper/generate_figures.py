#!/usr/bin/env python3
"""Generate all 7 figures for the IP-Safe LLM Deployment paper."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
import os

OUT = '/root/clawd-publish/research/ip_safe_paper/figures'
os.makedirs(OUT, exist_ok=True)

# Color palette
C_GREEN = '#2ecc71'
C_GREEN_LIGHT = '#d5f5e3'
C_RED = '#e74c3c'
C_RED_LIGHT = '#fadbd8'
C_BLUE = '#3498db'
C_BLUE_LIGHT = '#d6eaf8'
C_ORANGE = '#f39c12'
C_ORANGE_LIGHT = '#fdebd0'
C_GRAY = '#95a5a6'
C_DARK = '#2c3e50'
C_PURPLE = '#9b59b6'

plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'figure.dpi': 300,
})


def fig1_architecture():
    """Three-layer Sovereign AI architecture diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(8, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    # Secure perimeter
    perimeter = FancyBboxPatch((0.3, 0.3), 6.4, 5.2, boxstyle="round,pad=0.15",
                                facecolor=C_GREEN_LIGHT, edgecolor=C_GREEN, linewidth=2.5, linestyle='--')
    ax.add_patch(perimeter)
    ax.text(3.5, 5.25, 'Secure Enterprise Perimeter', ha='center', fontsize=11,
            fontweight='bold', color=C_GREEN, style='italic')

    # Boxes inside perimeter
    boxes_inside = [
        (0.7, 3.5, 2.0, 1.2, 'Proprietary\nData Store', C_RED_LIGHT, C_RED),
        (0.7, 1.2, 2.0, 1.2, 'Domain-Trained\nLocal Model\n(8B–70B)', C_ORANGE_LIGHT, C_ORANGE),
        (3.5, 2.2, 2.0, 1.2, 'Local\nAgent', C_BLUE_LIGHT, C_BLUE),
    ]
    for x, y, w, h, label, fc, ec in boxes_inside:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                              facecolor=fc, edgecolor=ec, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2, label, ha='center', va='center', fontsize=8, fontweight='bold', color=C_DARK)

    # IP Masking Layer (on boundary)
    box = FancyBboxPatch((5.8, 1.8), 1.2, 2.0, boxstyle="round,pad=0.1",
                          facecolor='#fef9e7', edgecolor=C_ORANGE, linewidth=2)
    ax.add_patch(box)
    ax.text(6.4, 2.8, 'IP\nMasking\nLayer', ha='center', va='center', fontsize=8, fontweight='bold', color=C_DARK)

    # Frontier model outside
    box = FancyBboxPatch((7.8, 2.0), 1.8, 1.6, boxstyle="round,pad=0.1",
                          facecolor=C_BLUE_LIGHT, edgecolor=C_BLUE, linewidth=1.5)
    ax.add_patch(box)
    ax.text(8.7, 2.8, 'Frontier\nModel API\n(Cloud)', ha='center', va='center', fontsize=8, fontweight='bold', color=C_DARK)

    # Arrows
    arrow_kw = dict(arrowstyle='->', mutation_scale=15, linewidth=1.5)
    # Data -> Local Model (arrow points DOWN from data store to local model)
    ax.annotate('', xy=(1.7, 2.4), xytext=(1.7, 3.5), arrowprops=dict(**arrow_kw, color=C_RED))
    ax.text(2.3, 3.0, 'train', fontsize=7, color=C_RED, style='italic')
    # Local Model -> Local Agent
    ax.annotate('', xy=(3.5, 2.8), xytext=(2.7, 1.8), arrowprops=dict(**arrow_kw, color=C_ORANGE))
    ax.text(2.8, 2.5, 'inference', fontsize=7, color=C_ORANGE, style='italic')
    # Local Agent -> IP Masking
    ax.annotate('', xy=(5.8, 2.8), xytext=(5.5, 2.8), arrowprops=dict(**arrow_kw, color=C_DARK))
    ax.text(5.3, 3.15, 'uncertain\nqueries', fontsize=6, color=C_DARK, ha='center')
    # IP Masking -> Frontier
    ax.annotate('', xy=(7.8, 3.1), xytext=(7.0, 3.1), arrowprops=dict(**arrow_kw, color=C_GREEN))
    ax.text(7.4, 3.35, 'sanitized', fontsize=7, color=C_GREEN, fontweight='bold')
    # Frontier -> IP Masking (return)
    ax.annotate('', xy=(7.0, 2.5), xytext=(7.8, 2.5), arrowprops=dict(**arrow_kw, color=C_BLUE))
    ax.text(7.4, 2.2, 'response', fontsize=7, color=C_BLUE, style='italic')

    # Labels
    ax.text(0.5, 0.6, 'Layer 1: Domain Model', fontsize=8, color=C_ORANGE, fontweight='bold')
    ax.text(3.5, 0.6, 'Layer 2: IP Masking', fontsize=8, color=C_ORANGE, fontweight='bold')
    ax.text(7.8, 1.5, 'Layer 3: Frontier Advisory', fontsize=8, color=C_BLUE, fontweight='bold')

    # ~85% / ~15% labels
    ax.text(4.5, 1.5, '~85% handled\nlocally', fontsize=8, ha='center', color=C_GREEN, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=C_GREEN, alpha=0.8))
    ax.text(7.4, 4.0, '~15%\nescalated', fontsize=8, ha='center', color=C_BLUE, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor=C_BLUE, alpha=0.8))

    fig.tight_layout()
    fig.savefig(f'{OUT}/fig1_architecture.pdf', bbox_inches='tight', dpi=300)
    plt.close()


def fig2_capability_gap():
    """Bar chart: capability gap concept."""
    fig, ax = plt.subplots(figsize=(6, 4))
    categories = ['8B\nBase', '8B +\nPatterns', '70B\nBase', 'Frontier\nAPI']
    values = [42, 79, 72, 88]
    colors = [C_RED, C_GREEN, C_ORANGE, C_BLUE]

    bars = ax.bar(categories, values, color=colors, edgecolor=C_DARK, linewidth=0.8, width=0.6)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5, f'{v}%',
                ha='center', fontsize=10, fontweight='bold', color=C_DARK)

    # Capability gap annotation
    ax.annotate('', xy=(1, 79), xytext=(0, 42),
                arrowprops=dict(arrowstyle='<->', color=C_PURPLE, linewidth=2))
    ax.text(0.5, 60, 'Gap bridged\nby patterns', ha='center', fontsize=8, color=C_PURPLE,
            fontweight='bold', bbox=dict(boxstyle='round', facecolor='white', edgecolor=C_PURPLE, alpha=0.8))

    ax.set_ylabel('Task Performance (%)')
    ax.set_title('Bridging the Capability Gap with Domain Knowledge', fontweight='bold')
    ax.set_ylim(0, 100)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.text(0.5, -0.12, 'Based on Buffer of Thoughts (Yang et al., 2024) and cross-model findings (Karasi, 2026)',
            transform=ax.transAxes, fontsize=7, ha='center', style='italic', color=C_GRAY)
    fig.tight_layout()
    fig.savefig(f'{OUT}/fig2_capability_gap.pdf', bbox_inches='tight', dpi=300)
    plt.close()


def fig3_cost_comparison():
    """Grouped bar chart: cost comparison of 4 deployment scenarios."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    scenarios = ['Full Frontier\nAPI', 'Local 405B', 'Local 8B\n(no fallback)', 'Sovereign AI\n(Ours)']
    gpu = [0, 8000, 200, 200]
    api = [15000, 0, 0, 1300]
    training = [0, 500, 500, 500]
    maintenance = [200, 1500, 300, 500]

    x = np.arange(len(scenarios))
    w = 0.18
    bars1 = ax.bar(x - 1.5*w, gpu, w, label='GPU Hosting', color=C_BLUE, edgecolor=C_DARK, linewidth=0.5)
    bars2 = ax.bar(x - 0.5*w, api, w, label='API Calls', color=C_RED, edgecolor=C_DARK, linewidth=0.5)
    bars3 = ax.bar(x + 0.5*w, training, w, label='Training (amortized)', color=C_GREEN, edgecolor=C_DARK, linewidth=0.5)
    bars4 = ax.bar(x + 1.5*w, maintenance, w, label='Maintenance', color=C_ORANGE, edgecolor=C_DARK, linewidth=0.5)

    # Totals
    totals = [sum(t) for t in zip(gpu, api, training, maintenance)]
    for i, t in enumerate(totals):
        ax.text(i, max(gpu[i], api[i], training[i], maintenance[i]) + 800,
                f'Total: ${t:,}/mo', ha='center', fontsize=8, fontweight='bold', color=C_DARK)

    # Highlight ours
    ax.axvspan(2.6, 3.4, alpha=0.1, color=C_GREEN)
    ax.text(3, 13500, '90% savings\nvs. frontier', ha='center', fontsize=9, fontweight='bold', color=C_GREEN,
            bbox=dict(boxstyle='round', facecolor='white', edgecolor=C_GREEN))

    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=9)
    ax.set_ylabel('Monthly Cost (USD)')
    ax.set_title('Cost Comparison of Enterprise LLM Deployment Strategies', fontweight='bold')
    ax.legend(fontsize=8, loc='upper right')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_ylim(0, 16500)
    fig.tight_layout()
    fig.savefig(f'{OUT}/fig3_cost_comparison.pdf', bbox_inches='tight', dpi=300)
    plt.close()


def fig4_routing_flow():
    """Flowchart of confidence-based routing."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis('off')

    def draw_box(x, y, w, h, text, fc, ec, fs=9):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                              facecolor=fc, edgecolor=ec, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x+w/2, y+h/2, text, ha='center', va='center', fontsize=fs, fontweight='bold', color=C_DARK)

    def draw_diamond(cx, cy, text):
        diamond = plt.Polygon([(cx, cy+0.6), (cx+1, cy), (cx, cy-0.6), (cx-1, cy)],
                               facecolor='#fef9e7', edgecolor=C_ORANGE, linewidth=1.5)
        ax.add_patch(diamond)
        ax.text(cx, cy, text, ha='center', va='center', fontsize=8, fontweight='bold', color=C_DARK)

    akw = dict(arrowstyle='->', mutation_scale=15, linewidth=1.5, color=C_DARK)

    # Query input
    draw_box(0.3, 2.2, 1.5, 0.8, 'User\nQuery', C_BLUE_LIGHT, C_BLUE)
    # Local model
    draw_box(2.5, 2.2, 1.8, 0.8, 'Local Model\nProcesses', C_ORANGE_LIGHT, C_ORANGE)
    # Diamond: confidence
    draw_diamond(5.8, 2.6, 'Confidence\n≥ 85%?')

    # Yes path -> direct answer
    draw_box(5.0, 4.5, 1.6, 0.8, 'Return\nAnswer', C_GREEN_LIGHT, C_GREEN)
    # No path -> IP Masking
    draw_box(7.5, 2.2, 1.5, 0.8, 'IP Masking\nLayer', '#fef9e7', C_ORANGE)
    # Frontier
    draw_box(7.5, 0.5, 1.5, 0.8, 'Frontier\nAPI Query', C_BLUE_LIGHT, C_BLUE)
    # Response translation
    draw_box(5.0, 0.5, 1.8, 0.8, 'Response\nTranslation', C_GREEN_LIGHT, C_GREEN)
    # Final answer (from no path)
    draw_box(2.8, 0.5, 1.5, 0.8, 'Return\nAnswer', C_GREEN_LIGHT, C_GREEN)

    # Arrows
    ax.annotate('', xy=(2.5, 2.6), xytext=(1.8, 2.6), arrowprops=akw)
    ax.annotate('', xy=(4.8, 2.6), xytext=(4.3, 2.6), arrowprops=akw)
    # Yes arrow up
    ax.annotate('', xy=(5.8, 4.5), xytext=(5.8, 3.2), arrowprops=dict(arrowstyle='->', mutation_scale=15, linewidth=1.5, color=C_GREEN))
    ax.text(5.4, 3.7, 'Yes\n~85%', fontsize=8, color=C_GREEN, fontweight='bold')
    # No arrow right
    ax.annotate('', xy=(7.5, 2.6), xytext=(6.8, 2.6), arrowprops=dict(arrowstyle='->', mutation_scale=15, linewidth=1.5, color=C_RED))
    ax.text(7.0, 2.9, 'No\n~15%', fontsize=8, color=C_RED, fontweight='bold')
    # IP Masking -> Frontier
    ax.annotate('', xy=(8.25, 1.3), xytext=(8.25, 2.2), arrowprops=akw)
    ax.text(8.5, 1.7, 'sanitized', fontsize=7, color=C_GREEN, style='italic')
    # Frontier -> Translation
    ax.annotate('', xy=(6.8, 0.9), xytext=(7.5, 0.9), arrowprops=akw)
    # Translation -> Answer
    ax.annotate('', xy=(4.3, 0.9), xytext=(5.0, 0.9), arrowprops=akw)

    ax.set_title('Confidence-Based Query Routing', fontweight='bold', fontsize=12, y=0.98)
    fig.tight_layout()
    fig.savefig(f'{OUT}/fig4_routing_flow.pdf', bbox_inches='tight', dpi=300)
    plt.close()


def fig5_ip_masking_example():
    """Side-by-side IP masking example."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.5))

    for ax in [ax1, ax2]:
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

    # Left: Original query
    ax1.set_title('Original Query (Proprietary)', fontweight='bold', color=C_RED, fontsize=10)
    box1 = FancyBboxPatch((0.05, 0.1), 0.9, 0.75, boxstyle="round,pad=0.05",
                           facecolor=C_RED_LIGHT, edgecolor=C_RED, linewidth=2)
    ax1.add_patch(box1)

    lines = [
        ('Optimize our ', None), ('PatentScore™', C_RED), (' algorithm', None),
        ('\nfor the ', None), ('BioPharma-X', C_RED), (' portfolio.', None),
        ('\nWeighting: ', None), ('ClinicalTrial', C_RED), (' phase data', None),
        ('\nwith ', None), ('FDA-2847', C_RED), (' compliance scoring.', None),
    ]
    text = "Optimize our PatentScore™ algorithm\nfor the BioPharma-X portfolio.\nWeighting: ClinicalTrial phase data\nwith FDA-2847 compliance scoring."
    ax1.text(0.5, 0.5, text, ha='center', va='center', fontsize=9, color=C_DARK,
             bbox=dict(boxstyle='round', facecolor='white', edgecolor=C_RED, alpha=0.5))

    # Highlight sensitive terms
    for term, y_off in [('PatentScore™', 0.62), ('BioPharma-X', 0.52), ('ClinicalTrial', 0.42), ('FDA-2847', 0.32)]:
        ax1.text(0.92, y_off, 'X', fontsize=10, ha='center', va='center', color=C_RED, fontweight='bold')

    # Right: Sanitized query
    ax2.set_title('Sanitized Query (Safe)', fontweight='bold', color=C_GREEN, fontsize=10)
    box2 = FancyBboxPatch((0.05, 0.1), 0.9, 0.75, boxstyle="round,pad=0.05",
                           facecolor=C_GREEN_LIGHT, edgecolor=C_GREEN, linewidth=2)
    ax2.add_patch(box2)

    text2 = "Optimize a weighted scoring function\nover a hierarchical document collection.\nWeighting: multi-phase categorical data\nwith regulatory compliance scoring."
    ax2.text(0.5, 0.5, text2, ha='center', va='center', fontsize=9, color=C_DARK,
             bbox=dict(boxstyle='round', facecolor='white', edgecolor=C_GREEN, alpha=0.5))

    for term, y_off in [('scoring function', 0.62), ('hierarchical', 0.52), ('multi-phase', 0.42), ('regulatory', 0.32)]:
        ax2.text(0.92, y_off, 'OK', fontsize=8, ha='center', va='center', color=C_GREEN, fontweight='bold')

    # Arrow between
    fig.text(0.5, 0.5, '→\nIP Masking', ha='center', va='center', fontsize=11,
             fontweight='bold', color=C_ORANGE)

    fig.suptitle('IP Masking: Variable Abstraction + Problem Generalization', fontweight='bold', fontsize=11, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    fig.savefig(f'{OUT}/fig5_ip_masking_example.pdf', bbox_inches='tight', dpi=300)
    plt.close()


def fig6_security_spectrum():
    """Horizontal security spectrum."""
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis('off')

    # Gradient bar
    gradient = np.linspace(0, 1, 256).reshape(1, -1)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list('rg', [C_RED, C_ORANGE, C_GREEN])
    ax.imshow(gradient, aspect='auto', cmap=cmap, extent=[0.5, 9.5, 1.0, 1.6], alpha=0.8)
    ax.add_patch(FancyBboxPatch((0.5, 1.0), 9.0, 0.6, boxstyle="round,pad=0",
                                 facecolor='none', edgecolor=C_DARK, linewidth=1.5))

    # Markers
    markers = [
        (1.5, 'Full API\nExposure', C_RED, '100% IP\nat risk'),
        (5.0, 'Federated /\nDiff. Privacy', C_ORANGE, 'Partial\nprotection'),
        (8.5, 'Sovereign AI\n(Ours)', C_GREEN, 'Zero IP\nexposure'),
    ]
    for x, label, color, desc in markers:
        ax.plot(x, 1.3, 'v', color=color, markersize=15, markeredgecolor=C_DARK, markeredgewidth=1)
        ax.text(x, 2.2, label, ha='center', fontsize=9, fontweight='bold', color=color)
        ax.text(x, 0.5, desc, ha='center', fontsize=8, color=C_GRAY, style='italic')

    # Labels
    ax.text(0.3, 1.3, 'Low\nPrivacy', fontsize=7, ha='center', va='center', color=C_RED)
    ax.text(9.7, 1.3, 'High\nPrivacy', fontsize=7, ha='center', va='center', color=C_GREEN)

    ax.set_title('IP Protection Spectrum for Enterprise LLM Deployment', fontweight='bold', fontsize=11, y=1.05)
    fig.tight_layout()
    fig.savefig(f'{OUT}/fig6_security_spectrum.pdf', bbox_inches='tight', dpi=300)
    plt.close()


def fig7_performance_vs_privacy():
    """Scatter: performance vs privacy trade-off."""
    fig, ax = plt.subplots(figsize=(6, 4.5))

    points = {
        'Full Frontier API': (10, 95, C_RED, 's'),
        'Local 8B (raw)': (95, 42, C_GRAY, 'o'),
        'Local 8B + Patterns': (95, 79, C_ORANGE, '^'),
        'Local 405B': (90, 85, C_PURPLE, 'D'),
        'Sovereign AI (Ours)': (95, 92, C_GREEN, '*'),
    }

    for label, (x, y, color, marker) in points.items():
        s = 200 if marker == '*' else 100
        ax.scatter(x, y, c=color, marker=marker, s=s, edgecolors=C_DARK, linewidth=1, zorder=5)
        offset = (5, 5) if label != 'Local 8B + Patterns' else (5, -12)
        ax.annotate(label, (x, y), xytext=offset, textcoords='offset points',
                    fontsize=8, fontweight='bold', color=color)

    # Quadrant shading
    ax.axhspan(75, 100, xmin=0.7, xmax=1.0, alpha=0.08, color=C_GREEN)
    ax.text(85, 98, 'Best of Both Worlds', fontsize=9, ha='center', color=C_GREEN,
            fontweight='bold', style='italic', alpha=0.7)

    ax.set_xlabel('Privacy Level (0 = full exposure, 100 = fully private)')
    ax.set_ylabel('Performance (% relative to frontier)')
    ax.set_title('Performance–Privacy Trade-off', fontweight='bold')
    ax.set_xlim(0, 105)
    ax.set_ylim(30, 102)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(f'{OUT}/fig7_performance_vs_privacy.pdf', bbox_inches='tight', dpi=300)
    plt.close()


if __name__ == '__main__':
    print("Generating figures...")
    fig1_architecture()
    print("  fig1_architecture.pdf ✓")
    fig2_capability_gap()
    print("  fig2_capability_gap.pdf ✓")
    fig3_cost_comparison()
    print("  fig3_cost_comparison.pdf ✓")
    fig4_routing_flow()
    print("  fig4_routing_flow.pdf ✓")
    fig5_ip_masking_example()
    print("  fig5_ip_masking_example.pdf ✓")
    fig6_security_spectrum()
    print("  fig6_security_spectrum.pdf ✓")
    fig7_performance_vs_privacy()
    print("  fig7_performance_vs_privacy.pdf ✓")
    print("All figures generated!")
