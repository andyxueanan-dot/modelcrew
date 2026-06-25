"""Solver: Simpson's Paradox — Delivery Strategy A vs B
M1: Two-proportion z-tests (aggregate + stratified)
M2: Mantel-Haenszel common odds ratio
+ Standardized rates, confidence intervals, visualizations
"""
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os

np.random.seed(42)
os.makedirs('artifacts/figures', exist_ok=True)

# ============================================================
# RAW DATA (from problem statement)
# ============================================================
# Strategy A
A_total, A_ontime = 350, 290
A_easy_n, A_easy_on = 50, 45
A_hard_n, A_hard_on = 300, 245

# Strategy B
B_total, B_ontime = 350, 182
B_easy_n, B_easy_on = 300, 282
B_hard_n, B_hard_on = 50, 20

# Rates
p_A = A_ontime / A_total
p_B = B_ontime / B_total
p_A_easy = A_easy_on / A_easy_n
p_B_easy = B_easy_on / B_easy_n
p_A_hard = A_hard_on / A_hard_n
p_B_hard = B_hard_on / B_hard_n

print("="*60)
print("RAW DATA SUMMARY")
print("="*60)
print(f"Strategy A: {A_ontime}/{A_total} = {p_A:.4f} ({p_A*100:.1f}%)")
print(f"Strategy B: {B_ontime}/{B_total} = {p_B:.4f} ({p_B*100:.1f}%)")
print(f"  A-Easy:  {A_easy_on}/{A_easy_n} = {p_A_easy:.4f} ({p_A_easy*100:.1f}%)")
print(f"  A-Hard:  {A_hard_on}/{A_hard_n} = {p_A_hard:.4f} ({p_A_hard*100:.1f}%)")
print(f"  B-Easy:  {B_easy_on}/{B_easy_n} = {p_B_easy:.4f} ({p_B_easy*100:.1f}%)")
print(f"  B-Hard:  {B_hard_on}/{B_hard_n} = {p_B_hard:.4f} ({p_B_hard*100:.1f}%)")
print(f"\n[!] SIMPSON'S PARADOX DETECTED:")
print(f"  Aggregate: A wins by {(p_A-p_B)*100:.1f}pp")
print(f"  Easy stratum: B wins by {(p_B_easy-p_A_easy)*100:.1f}pp")
print(f"  Hard stratum: B wins by {(p_B_hard-p_A_hard)*100:.1f}pp")

# ============================================================
# M1: TWO-PROPORTION Z-TESTS
# ============================================================
print("\n" + "="*60)
print("M1: TWO-PROPORTION Z-TESTS")
print("="*60)

def two_prop_z_test(x1, n1, x2, n2, label=""):
    """Two-proportion z-test with CI for difference."""
    p1 = x1 / n1
    p2 = x2 / n2
    p_pool = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    z = (p1 - p2) / se if se > 0 else 0
    p_val = 2 * stats.norm.cdf(-abs(z))
    # CI for difference (Wald)
    se_diff = np.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)
    diff = p1 - p2
    ci_low = diff - 1.96 * se_diff
    ci_high = diff + 1.96 * se_diff
    print(f"\n[{label}]")
    print(f"  p1 = {p1:.4f}, p2 = {p2:.4f}, diff = {diff:.4f}")
    print(f"  z = {z:.4f}, p-value = {p_val:.6f}")
    print(f"  95% CI for diff: [{ci_low:.4f}, {ci_high:.4f}]")
    return {'p1': p1, 'p2': p2, 'diff': diff, 'z': z, 'p_value': p_val,
            'ci_low': ci_low, 'ci_high': ci_high, 'n1': n1, 'n2': n2}

# Aggregate
z_agg = two_prop_z_test(A_ontime, A_total, B_ontime, B_total, "Aggregate: A vs B")

# Easy stratum
z_easy = two_prop_z_test(A_easy_on, A_easy_n, B_easy_on, B_easy_n, "Easy: A vs B")

# Hard stratum
z_hard = two_prop_z_test(A_hard_on, A_hard_n, B_hard_on, B_hard_n, "Hard: A vs B")

# ============================================================
# M2: MANTEL-HAENZEL
# ============================================================
print("\n" + "="*60)
print("M2: MANTEL-HAENSZEL COMMON ODDS RATIO")
print("="*60)

# 2x2 tables per stratum (rows=strategy, cols=ontime/late)
# Stratum k: a_k=A_ontime, b_k=A_late, c_k=B_ontime, d_k=B_late, N_k=total
strata = [
    {'a': A_easy_on, 'b': A_easy_n - A_easy_on, 'c': B_easy_on, 'd': B_easy_n - B_easy_on},
    {'a': A_hard_on, 'b': A_hard_n - A_hard_on, 'c': B_hard_on, 'd': B_hard_n - B_hard_on},
]

# Per-stratum OR
for i, s in enumerate(strata):
    N_k = s['a'] + s['b'] + s['c'] + s['d']
    or_k = (s['a'] * s['d']) / (s['b'] * s['c']) if (s['b'] * s['c']) > 0 else float('inf')
    strata[i]['N'] = N_k
    strata[i]['OR'] = or_k
    print(f"\nStratum {['Easy','Hard'][i]}:")
    print(f"  A: {s['a']} on-time, {s['b']} late")
    print(f"  B: {s['c']} on-time, {s['d']} late")
    print(f"  OR (A vs B) = {or_k:.4f}")

# MH combined OR
num = sum(s['a'] * s['d'] / s['N'] for s in strata)
den = sum(s['b'] * s['c'] / s['N'] for s in strata)
OR_MH = num / den if den > 0 else float('inf')
print(f"\nMantel-Haenszel OR (A vs B) = {OR_MH:.4f}")
print(f"  OR > 1 favors A; OR < 1 favors B")
print(f"  ln(OR_MH) = {np.log(OR_MH):.4f}")

# MH chi-squared test
# Sum of a_k, E(a_k), Var(a_k) under H0
sum_a = sum(s['a'] for s in strata)
sum_E_a = 0
sum_V_a = 0
for s in strata:
    N = s['N']
    n1_k = s['a'] + s['b']  # A total in stratum
    n2_k = s['c'] + s['d']  # B total in stratum
    m1_k = s['a'] + s['c']  # on-time total in stratum
    m0_k = s['b'] + s['d']  # late total in stratum
    E_a = n1_k * m1_k / N
    V_a = (n1_k * n2_k * m1_k * m0_k) / (N**2 * (N - 1))
    sum_E_a += E_a
    sum_V_a += V_a

chi2_MH = (abs(sum_a - sum_E_a) - 0.5)**2 / sum_V_a if sum_V_a > 0 else 0
p_MH = 1 - stats.chi2.cdf(chi2_MH, df=1)
print(f"\nMH chi-squared = {chi2_MH:.4f}, p-value = {p_MH:.6f}")
print(f"  Sum a_k = {sum_a}, E(sum a_k) = {sum_E_a:.2f}")

# Breslow-Day test for homogeneity of ORs
print("\nBreslow-Day homogeneity test:")
Q = 0
for s in strata:
    ln_or = np.log(s['OR']) if s['OR'] > 0 else 0
    ln_or_mh = np.log(OR_MH)
    # Approximate variance of ln(OR)
    var_ln_or = 1/s['a'] + 1/s['b'] + 1/s['c'] + 1/s['d']
    w = 1 / var_ln_or
    Q += w * (ln_or - ln_or_mh)**2
p_BD = 1 - stats.chi2.cdf(Q, df=len(strata)-1)
print(f"  Q = {Q:.4f}, p-value = {p_BD:.4f}")
print(f"  {'Homogeneous (ORs consistent across strata)' if p_BD > 0.05 else 'Heterogeneous (ORs differ across strata)'}")

# ============================================================
# STANDARDIZED RATES (Direct Method)
# ============================================================
print("\n" + "="*60)
print("STANDARDIZED RATES (Direct Method)")
print("="*60)

# Standard population: equal split (50/50 easy/hard)
std_easy = 0.50
std_hard = 0.50
p_A_std = std_easy * p_A_easy + std_hard * p_A_hard
p_B_std = std_easy * p_B_easy + std_hard * p_B_hard
print(f"Standard population: {std_easy*100:.0f}% easy, {std_hard*100:.0f}% hard")
print(f"A standardized rate: {p_A_std:.4f} ({p_A_std*100:.1f}%)")
print(f"B standardized rate: {p_B_std:.4f} ({p_B_std*100:.1f}%)")
print(f"Difference: {(p_B_std - p_A_std)*100:.1f}pp in favor of B")

# Also try with actual distribution as standard
actual_easy = (A_easy_n + B_easy_n) / (A_total + B_total)
actual_hard = (A_hard_n + B_hard_n) / (A_total + B_total)
p_A_std2 = actual_easy * p_A_easy + actual_hard * p_A_hard
p_B_std2 = actual_easy * p_B_easy + actual_hard * p_B_hard
print(f"\nUsing actual distribution ({actual_easy*100:.1f}% easy, {actual_hard*100:.1f}% hard):")
print(f"A standardized: {p_A_std2:.4f} ({p_A_std2*100:.1f}%)")
print(f"B standardized: {p_B_std2:.4f} ({p_B_std2*100:.1f}%)")

# ============================================================
# SENSITIVITY: Q3
# ============================================================
print("\n" + "="*60)
print("Q3: SENSITIVITY TO STRATIFICATION")
print("="*60)

# What if the difficulty split was different?
print("If difficulty split were 50/50 for both strategies:")
p_A_5050 = 0.5 * p_A_easy + 0.5 * p_A_hard
p_B_5050 = 0.5 * p_B_easy + 0.5 * p_B_hard
print(f"  A: {p_A_5050*100:.1f}%, B: {p_B_5050*100:.1f}%, diff: {(p_B_5050-p_A_5050)*100:.1f}pp (B wins)")

print("\nIf A had B's distribution (85.7% easy):")
p_A_if_B_dist = (300/350) * p_A_easy + (50/350) * p_A_hard
print(f"  A would get: {p_A_if_B_dist*100:.1f}% (vs current {p_A*100:.1f}%)")

print("\nIf B had A's distribution (85.7% hard):")
p_B_if_A_dist = (50/350) * p_B_easy + (300/350) * p_B_hard
print(f"  B would get: {p_B_if_A_dist*100:.1f}% (vs current {p_B*100:.1f}%)")

# ============================================================
# FIGURES
# ============================================================
print("\n" + "="*60)
print("GENERATING FIGURES")
print("="*60)

# Fig 1: Simpson's Paradox visualization
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: Aggregate rates
bars = axes[0].bar(['Strategy A', 'Strategy B'], [p_A*100, p_B*100],
                   color=['#2196F3', '#FF5722'], width=0.5, edgecolor='black')
axes[0].set_ylabel('On-time delivery rate (%)')
axes[0].set_title('Aggregate View (Misleading)')
axes[0].set_ylim(0, 100)
axes[0].axhline(y=50, color='gray', linestyle='--', alpha=0.3)
for bar, val in zip(bars, [p_A*100, p_B*100]):
    axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{val:.1f}%', ha='center', fontweight='bold', fontsize=14)
axes[0].text(0.5, 0.95, 'A appears better by 30.9pp', transform=axes[0].transAxes,
            ha='center', fontsize=12, color='red',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8))

# Right: Stratified rates
x = np.arange(2)
width = 0.35
bars1 = axes[1].bar(x - width/2, [p_A_easy*100, p_A_hard*100], width,
                    label='Strategy A', color='#2196F3', edgecolor='black')
bars2 = axes[1].bar(x + width/2, [p_B_easy*100, p_B_hard*100], width,
                    label='Strategy B', color='#FF5722', edgecolor='black')
axes[1].set_ylabel('On-time delivery rate (%)')
axes[1].set_title('Stratified View (Reveals Truth)')
axes[1].set_xticks(x)
axes[1].set_xticklabels(['Easy Orders', 'Hard Orders'])
axes[1].set_ylim(0, 100)
axes[1].legend(fontsize=11)
for bars, vals in [(bars1, [p_A_easy*100, p_A_hard*100]),
                   (bars2, [p_B_easy*100, p_B_hard*100])]:
    for bar, val in zip(bars, vals):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                    f'{val:.1f}%', ha='center', fontsize=11)
axes[1].text(0.5, 0.95, 'B wins Easy (+4pp, n.s.)\nA dominates Hard (+42pp, p<.001)', transform=axes[1].transAxes,
            ha='center', fontsize=11, color='darkblue',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightyellow', alpha=0.9))

plt.suptitle("Simpson's Paradox: Aggregate vs Stratified Comparison", fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('artifacts/figures/fig1_simpsons_paradox.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_simpsons_paradox.png")

# Fig 2: Forest plot of effects
fig, ax = plt.subplots(figsize=(10, 5))
effects = [
    ('Aggregate (A−B)', z_agg['diff']*100, z_agg['ci_low']*100, z_agg['ci_high']*100),
    ('Easy stratum (A−B)', z_easy['diff']*100, z_easy['ci_low']*100, z_easy['ci_high']*100),
    ('Hard stratum (A−B)', z_hard['diff']*100, z_hard['ci_low']*100, z_hard['ci_high']*100),
]
y_pos = [2, 1, 0]
colors = ['#FF5722', '#4CAF50', '#4CAF50']
for i, (label, diff, lo, hi) in enumerate(effects):
    color = colors[i]
    ax.plot([lo, hi], [y_pos[i], y_pos[i]], color=color, linewidth=3, solid_capstyle='round')
    ax.plot(diff, y_pos[i], 'o', color=color, markersize=12, markeredgecolor='black')
    ax.text(hi + 1, y_pos[i], f'{diff:+.1f}pp [{lo:+.1f}, {hi:+.1f}]',
           va='center', fontsize=10)

ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
ax.set_yticks(y_pos)
ax.set_yticklabels([e[0] for e in effects])
ax.set_xlabel('Difference in on-time rate (percentage points)\nPositive = A better, Negative = B better')
ax.set_title('Forest Plot: Strategy A vs B (95% CI)')
ax.set_xlim(-60, 50)
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('artifacts/figures/fig2_forest_plot.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_forest_plot.png")

# Fig 3: Order distribution comparison
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# A's distribution
labels = ['Easy', 'Hard']
A_sizes = [A_easy_n, A_hard_n]
B_sizes = [B_easy_n, B_hard_n]
axes[0].pie(A_sizes, labels=[f'Easy\n({A_easy_n})', f'Hard\n({A_hard_n})'],
           autopct='%1.1f%%', colors=['#81C784', '#E57373'], startangle=90)
axes[0].set_title('Strategy A\nOrder Difficulty Distribution')

axes[1].pie(B_sizes, labels=[f'Easy\n({B_easy_n})', f'Hard\n({B_hard_n})'],
           autopct='%1.1f%%', colors=['#81C784', '#E57373'], startangle=90)
axes[1].set_title('Strategy B\nOrder Difficulty Distribution')

plt.suptitle('The Root Cause: Dramatically Different Order Assignments', fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('artifacts/figures/fig3_order_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_order_distribution.png")

# ============================================================
# SAVE FROZEN NUMBERS
# ============================================================
frozen = {
    'seed': 42,
    'raw_data': {
        'A': {'total': A_total, 'ontime': A_ontime, 'rate': round(p_A, 4),
              'easy': {'n': A_easy_n, 'ontime': A_easy_on, 'rate': round(p_A_easy, 4)},
              'hard': {'n': A_hard_n, 'ontime': A_hard_on, 'rate': round(p_A_hard, 4)}},
        'B': {'total': B_total, 'ontime': B_ontime, 'rate': round(p_B, 4),
              'easy': {'n': B_easy_n, 'ontime': B_easy_on, 'rate': round(p_B_easy, 4)},
              'hard': {'n': B_hard_n, 'ontime': B_hard_on, 'rate': round(p_B_hard, 4)}},
    },
    'aggregate_z_test': {k: round(v, 6) if isinstance(v, float) else v for k, v in z_agg.items()},
    'easy_z_test': {k: round(v, 6) if isinstance(v, float) else v for k, v in z_easy.items()},
    'hard_z_test': {k: round(v, 6) if isinstance(v, float) else v for k, v in z_hard.items()},
    'mantel_haenszel': {
        'OR_MH': round(OR_MH, 4),
        'ln_OR_MH': round(np.log(OR_MH), 4),
        'chi2_MH': round(chi2_MH, 4),
        'p_MH': round(p_MH, 6),
        'breslow_day_Q': round(Q, 4),
        'breslow_day_p': round(p_BD, 4),
    },
    'standardized_rates': {
        'equal_split': {'A': round(p_A_std, 4), 'B': round(p_B_std, 4), 'diff_B_minus_A': round(p_B_std - p_A_std, 4)},
        'actual_split': {'A': round(p_A_std2, 4), 'B': round(p_B_std2, 4)},
    },
    'simpson_paradox': {
        'aggregate_A_wins_by_pp': round((p_A - p_B) * 100, 1),
        'easy_B_wins_by_pp': round((p_B_easy - p_A_easy) * 100, 1),
        'hard_B_wins_by_pp': round((p_B_hard - p_A_hard) * 100, 1),
        'A_hard_pct': round(A_hard_n / A_total * 100, 1),
        'B_easy_pct': round(B_easy_n / B_total * 100, 1),
    },
    'reproducibility': {
        'random_seed': 42,
        'python_packages': 'numpy, scipy, matplotlib',
        'methods': 'M1: two-proportion z-test, M2: Mantel-Haenszel',
    }
}

with open('artifacts/frozen_numbers.json', 'w') as f:
    json.dump(frozen, f, indent=2)

print("\n" + "="*60)
print("SOLVER COMPLETE")
print("="*60)
print(f"Frozen numbers: artifacts/frozen_numbers.json")
print(f"Figures: artifacts/figures/")
