import numpy as np
import os, json
os.chdir(os.path.dirname(os.path.abspath(__file__)))

np.random.seed(42)

# ============================================================
# DATA
# ============================================================
provinces = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']
n = len(provinces)

# Raw data: I1(GDP/cap), I2(Gini), I3(Carbon), I4(R&D%), I5(Urban%), I6(HDI)
raw = np.array([
    [14.2, 0.42, 1.85, 3.8, 89.3, 0.82],
    [11.5, 0.35, 1.20, 4.2, 76.1, 0.85],
    [ 9.8, 0.38, 0.95, 3.5, 71.4, 0.80],
    [ 8.3, 0.31, 0.72, 2.8, 65.2, 0.78],
    [12.8, 0.40, 1.65, 3.2, 82.7, 0.81],
    [ 7.5, 0.29, 0.55, 2.1, 58.3, 0.75],
    [10.2, 0.36, 1.10, 3.9, 73.8, 0.83],
    [ 6.8, 0.33, 0.48, 1.5, 52.1, 0.72],
    [13.5, 0.44, 1.92, 4.5, 86.5, 0.79],
    [ 5.2, 0.27, 0.38, 1.2, 45.6, 0.68],
    [ 9.1, 0.34, 0.88, 2.5, 68.9, 0.77],
    [11.8, 0.41, 1.55, 3.6, 78.4, 0.80],
    [ 7.9, 0.30, 0.62, 2.3, 61.7, 0.76],
    [10.8, 0.37, 1.05, 3.1, 74.5, 0.84],
    [ 6.1, 0.28, 0.42, 1.8, 49.8, 0.71],
])

indicators = ['I1_GDP', 'I2_Gini', 'I3_Carbon', 'I4_RD', 'I5_Urban', 'I6_HDI']
# Directions: +1 for benefit, -1 for cost
directions = [1, -1, -1, 1, 1, 1]

print("=" * 60)
print("STEP 1: DATA PREPROCESSING")
print("=" * 60)

# Step 1: Forward transformation (negate cost indicators)
data_fwd = raw.copy()
for j in range(6):
    if directions[j] == -1:
        # x' = max - x + min  (so higher is better)
        data_fwd[:, j] = raw[:, j].max() - raw[:, j] + raw[:, j].min()

print("\nAfter forward transformation:")
for i in range(n):
    vals = "  ".join(f"{data_fwd[i,j]:.3f}" for j in range(6))
    print(f"  {provinces[i]}: {vals}")

# Step 2: Min-max normalization to [0.001, 1.000]
mins = data_fwd.min(axis=0)
maxs = data_fwd.max(axis=0)
norm = (data_fwd - mins) / (maxs - mins + 1e-12) * 0.999 + 0.001

print("\nNormalized matrix:")
for i in range(n):
    vals = "  ".join(f"{norm[i,j]:.4f}" for j in range(6))
    print(f"  {provinces[i]}: {vals}")

# ============================================================
# STEP 2: ENTROPY WEIGHT METHOD
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: ENTROPY WEIGHT METHOD")
print("=" * 60)

# Proportion matrix
p = norm / norm.sum(axis=0)

# Information entropy
k = 1.0 / np.log(n)
e = -k * np.sum(p * np.log(p + 1e-12), axis=0)

# Redundancy
d = 1 - e

# Entropy weights
w_entropy = d / d.sum()

print("\nEntropy weights:")
for j in range(6):
    print(f"  {indicators[j]}: e={e[j]:.4f}, d={d[j]:.4f}, w={w_entropy[j]:.4f}")

# ============================================================
# STEP 3: TOPSIS (with entropy weights)
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: TOPSIS RANKING (Entropy Weights)")
print("=" * 60)

def topsis(norm_data, weights):
    """Compute TOPSIS scores and rankings."""
    v = norm_data * weights  # weighted normalized
    A_plus = v.max(axis=0)
    A_minus = v.min(axis=0)
    D_plus = np.sqrt(((v - A_plus)**2).sum(axis=1))
    D_minus = np.sqrt(((v - A_minus)**2).sum(axis=1))
    C = D_minus / (D_plus + D_minus)
    return C, np.argsort(-C)  # scores and ranking indices

scores_entropy, rank_entropy_idx = topsis(norm, w_entropy)
rank_entropy = np.empty(n, dtype=int)
rank_entropy[rank_entropy_idx] = np.arange(1, n+1)

print("\nTOPSIS Ranking (Entropy Weights):")
for idx in rank_entropy_idx:
    p_name = provinces[idx]
    print(f"  Rank {rank_entropy[idx]:2d}: {p_name} (C={scores_entropy[idx]:.4f})")

# ============================================================
# STEP 4: AHP
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: AHP (Analytic Hierarchy Process)")
print("=" * 60)

# AHP judgment matrix (4 dimensions: Econ, Innov, Social, Environ)
# Econ > Innov > Social > Environ
# Mapped to 6 indicators:
# I1(GDP)=Econ, I2(Gini)=Social, I3(Carbon)=Environ, I4(R&D)=Innov, I5(Urban)=Social, I6(HDI)=Social

# Dimension-level matrix
# Econ=1, Innov=2, Social=3, Environ=4
ahp_dim = np.array([
    [1,   2,   3,   5],
    [1/2, 1,   2,   3],
    [1/3, 1/2, 1,   2],
    [1/5, 1/3, 1/2, 1],
])

# Eigenvalue method
eigenvalues, eigenvectors = np.linalg.eig(ahp_dim)
max_idx = np.argmax(eigenvalues.real)
lambda_max = eigenvalues[max_idx].real
w_dim = eigenvectors[:, max_idx].real
w_dim = w_dim / w_dim.sum()

# Consistency check
RI_table = {1:0, 2:0, 3:0.58, 4:0.89, 5:1.12, 6:1.24, 7:1.32}
CI = (lambda_max - 4) / 3
CR = CI / RI_table[4]
print(f"\nAHP Dimension Weights: Econ={w_dim[0]:.4f}, Innov={w_dim[1]:.4f}, Social={w_dim[2]:.4f}, Environ={w_dim[3]:.4f}")
print(f"lambda_max = {lambda_max:.4f}, CI = {CI:.4f}, CR = {CR:.4f} {'PASS' if CR < 0.1 else 'FAIL'}")

# Map to 6 indicators
# Econ: I1 (full weight)
# Innov: I4 (full weight)
# Social: I2(40%), I5(30%), I6(30%)
# Environ: I3 (full weight)
w_ahp = np.array([
    w_dim[0],          # I1 = Econ
    w_dim[2] * 0.40,   # I2 = Social * 0.40
    w_dim[3],          # I3 = Environ
    w_dim[1],          # I4 = Innov
    w_dim[2] * 0.30,   # I5 = Social * 0.30
    w_dim[2] * 0.30,   # I6 = Social * 0.30
])
w_ahp = w_ahp / w_ahp.sum()  # renormalize

print("\nAHP Indicator Weights:")
for j in range(6):
    print(f"  {indicators[j]}: w={w_ahp[j]:.4f}")

# TOPSIS with AHP weights
scores_ahp, rank_ahp_idx = topsis(norm, w_ahp)
rank_ahp = np.empty(n, dtype=int)
rank_ahp[rank_ahp_idx] = np.arange(1, n+1)

print("\nTOPSIS Ranking (AHP Weights):")
for idx in rank_ahp_idx:
    p_name = provinces[idx]
    print(f"  Rank {rank_ahp[idx]:2d}: {p_name} (C={scores_ahp[idx]:.4f})")

# Compare rankings
print("\nRanking Comparison (Entropy vs AHP):")
print(f"  {'Province':>8} {'Entropy':>8} {'AHP':>8} {'Diff':>8}")
for i in range(n):
    diff = rank_entropy[i] - rank_ahp[i]
    flag = " ***" if abs(diff) >= 3 else ""
    print(f"  {provinces[i]:>8} {rank_entropy[i]:>8} {rank_ahp[i]:>8} {diff:>+8}{flag}")

# Spearman correlation
from scipy.stats import spearmanr
rho, p_sp = spearmanr(rank_entropy, rank_ahp)
print(f"\nSpearman rho = {rho:.4f}, p = {p_sp:.4e}")

# ============================================================
# STEP 5: SENSITIVITY ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: SENSITIVITY ANALYSIS (Environmental Weight)")
print("=" * 60)

w_env_range = np.arange(0.15, 0.36, 0.01)
sensitivity_ranks = []  # list of ranking arrays

for w_env in w_env_range:
    remaining = 1 - w_env
    # Distribute remaining: Econ 40%, Innov 30%, Social 30%
    w_econ = remaining * 0.40
    w_innov = remaining * 0.30
    w_social = remaining * 0.30
    
    w_sens = np.array([
        w_econ,              # I1
        w_social * 0.40,     # I2
        w_env,               # I3
        w_innov,             # I4
        w_social * 0.30,     # I5
        w_social * 0.30,     # I6
    ])
    w_sens = w_sens / w_sens.sum()
    
    sc, rk_idx = topsis(norm, w_sens)
    rk = np.empty(n, dtype=int)
    rk[rk_idx] = np.arange(1, n+1)
    sensitivity_ranks.append(rk)

sensitivity_ranks = np.array(sensitivity_ranks)  # shape: (21, 15)

# Find flip points for key provinces
print("\nRanking changes for key provinces as w_env increases:")
key_provs = {'A': 0, 'B': 1, 'I': 8, 'D': 3}
for name, idx in key_provs.items():
    ranks = sensitivity_ranks[:, idx]
    print(f"\n  Province {name}:")
    for k, w_env in enumerate(w_env_range):
        if k == 0 or ranks[k] != ranks[k-1]:
            print(f"    w_env={w_env:.2f}: rank={ranks[k]}")

# Find specific flip point: when does B overtake A?
ranks_A = sensitivity_ranks[:, 0]
ranks_B = sensitivity_ranks[:, 1]
flip_point = None
for k in range(1, len(w_env_range)):
    if ranks_A[k] > ranks_B[k] and ranks_A[k-1] <= ranks_B[k-1]:
        flip_point = w_env_range[k]
        break
if flip_point:
    print(f"\nFlip point: B overtakes A at w_env = {flip_point:.2f}")
else:
    print(f"\nNo flip point found: B never overtakes A in the scanned range")

# ============================================================
# STEP 6: BOOTSTRAP STABILITY TEST
# ============================================================
print("\n" + "=" * 60)
print("STEP 6: BOOTSTRAP STABILITY TEST (B=1000)")
print("=" * 60)

B = 1000
bootstrap_ranks = np.zeros((B, n), dtype=int)

for b in range(B):
    # Resample with replacement
    idx_sample = np.random.choice(n, size=n, replace=True)
    norm_b = norm[idx_sample]
    
    # Recompute entropy weights on resampled data
    p_b = norm_b / norm_b.sum(axis=0)
    e_b = -k * np.sum(p_b * np.log(p_b + 1e-12), axis=0)
    d_b = 1 - e_b
    w_b = d_b / d_b.sum()
    
    # TOPSIS on full data with resampled weights
    sc_b, rk_b_idx = topsis(norm, w_b)
    rk_b = np.empty(n, dtype=int)
    rk_b[rk_b_idx] = np.arange(1, n+1)
    bootstrap_ranks[b] = rk_b

# 95% CI for each province
print("\nBootstrap 95% CI for rankings:")
print(f"  {'Province':>8} {'Mean':>6} {'P2.5':>6} {'P50':>6} {'P97.5':>6} {'Width':>6}")
bootstrap_ci = []
for i in range(n):
    r = bootstrap_ranks[:, i]
    mean_r = r.mean()
    p25 = np.percentile(r, 2.5)
    p50 = np.percentile(r, 50)
    p975 = np.percentile(r, 97.5)
    width = p975 - p25
    bootstrap_ci.append((provinces[i], mean_r, p25, p50, p975, width))
    print(f"  {provinces[i]:>8} {mean_r:>6.1f} {p25:>6.0f} {p50:>6.0f} {p975:>6.0f} {width:>6.0f}")

# ============================================================
# STEP 7: VISUALIZATION
# ============================================================
print("\n" + "=" * 60)
print("STEP 7: GENERATING FIGURES")
print("=" * 60)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Figure 1: Ranking comparison (Entropy vs AHP)
fig, ax = plt.subplots(figsize=(10, 6))
x_pos = np.arange(n)
width_bar = 0.35
# Sort by entropy rank
sort_idx = rank_entropy_idx
ax.bar(x_pos - width_bar/2, rank_entropy[sort_idx], width_bar, label='Entropy-TOPSIS', color='steelblue')
ax.bar(x_pos + width_bar/2, rank_ahp[sort_idx], width_bar, label='AHP-TOPSIS', color='coral')
ax.set_xlabel('Province')
ax.set_ylabel('Rank (1=best)')
ax.set_title('Ranking Comparison: Entropy vs AHP Weights')
ax.set_xticks(x_pos)
ax.set_xticklabels([provinces[i] for i in sort_idx])
ax.invert_yaxis()
ax.legend()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('figures/fig1_ranking_comparison.png', dpi=150)
plt.close()
print("  Saved fig1_ranking_comparison.png")

# Figure 2: Sensitivity curves
fig, ax = plt.subplots(figsize=(10, 6))
colors = plt.cm.Set2(np.linspace(0, 1, n))
for i in range(n):
    ranks_i = sensitivity_ranks[:, i]
    ax.plot(w_env_range, ranks_i, 'o-', color=colors[i], markersize=3, label=f'{provinces[i]}', linewidth=1.5)
ax.set_xlabel('Environmental Weight (w_env)')
ax.set_ylabel('Rank')
ax.set_title('Sensitivity Analysis: Rankings vs Environmental Weight')
ax.invert_yaxis()
ax.set_yticks(range(1, n+1))
ax.legend(fontsize=7, ncol=3)
ax.grid(alpha=0.3)
# Mark flip point
if flip_point:
    ax.axvline(x=flip_point, color='red', linestyle='--', alpha=0.5, label=f'Flip at {flip_point:.2f}')
plt.tight_layout()
plt.savefig('figures/fig2_sensitivity.png', dpi=150)
plt.close()
print("  Saved fig2_sensitivity.png")

# Figure 3: Bootstrap boxplot
fig, ax = plt.subplots(figsize=(10, 6))
# Sort by median rank
median_ranks = [np.median(bootstrap_ranks[:, i]) for i in range(n)]
sort_order = np.argsort(median_ranks)
box_data = [bootstrap_ranks[:, i] for i in sort_order]
bp = ax.boxplot(box_data, vert=True, patch_artist=True,
                labels=[provinces[i] for i in sort_order])
for patch, color in zip(bp['boxes'], colors[sort_order]):
    patch.set_facecolor(color)
ax.set_xlabel('Province')
ax.set_ylabel('Rank (Bootstrap B=1000)')
ax.set_title('Bootstrap Ranking Stability (95% CI)')
ax.invert_yaxis()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('figures/fig3_bootstrap.png', dpi=150)
plt.close()
print("  Saved fig3_bootstrap.png")

# ============================================================
# STEP 8: FROZEN NUMBERS
# ============================================================
print("\n" + "=" * 60)
print("STEP 8: SAVING FROZEN NUMBERS")
print("=" * 60)

frozen = {"numbers": []}

# Entropy weights
for j in range(6):
    frozen["numbers"].append({
        "id": f"entropy_w_{indicators[j]}",
        "label": f"Entropy weight for {indicators[j]}",
        "value": float(w_entropy[j]),
        "tol": 0.001,
        "source": "entropy_method",
        "path": "solve.py"
    })

# TOPSIS scores (entropy)
for i in range(n):
    frozen["numbers"].append({
        "id": f"topsis_entropy_{provinces[i]}",
        "label": f"TOPSIS score (entropy) for province {provinces[i]}",
        "value": float(scores_entropy[i]),
        "tol": 0.001,
        "source": "topsis_entropy",
        "path": "solve.py"
    })

# TOPSIS ranks (entropy)
for i in range(n):
    frozen["numbers"].append({
        "id": f"rank_entropy_{provinces[i]}",
        "label": f"Entropy-TOPSIS rank for province {provinces[i]}",
        "value": int(rank_entropy[i]),
        "tol": 0,
        "source": "topsis_entropy",
        "path": "solve.py"
    })

# AHP weights
frozen["numbers"].append({
    "id": "ahp_lambda_max",
    "label": "AHP max eigenvalue",
    "value": float(lambda_max),
    "tol": 0.01,
    "source": "ahp",
    "path": "solve.py"
})
frozen["numbers"].append({
    "id": "ahp_CR",
    "label": "AHP consistency ratio",
    "value": float(CR),
    "tol": 0.001,
    "source": "ahp",
    "path": "solve.py"
})

# Spearman
frozen["numbers"].append({
    "id": "spearman_rho",
    "label": "Spearman correlation between entropy and AHP rankings",
    "value": float(rho),
    "tol": 0.01,
    "source": "spearman_test",
    "path": "solve.py"
})

# Flip point
if flip_point:
    frozen["numbers"].append({
        "id": "flip_w_env",
        "label": "Environmental weight at which B overtakes A",
        "value": float(flip_point),
        "tol": 0.01,
        "source": "sensitivity_analysis",
        "path": "solve.py"
    })

# Bootstrap CI widths for top 5
for i in range(5):
    prov_idx = rank_entropy_idx[i]
    frozen["numbers"].append({
        "id": f"bootstrap_ci_width_{provinces[prov_idx]}",
        "label": f"Bootstrap 95% CI width for province {provinces[prov_idx]}",
        "value": float(bootstrap_ci[prov_idx][5]),
        "tol": 1.0,
        "source": "bootstrap",
        "path": "solve.py"
    })

with open('frozen_numbers.json', 'w', encoding='utf-8') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)
print(f"Saved {len(frozen['numbers'])} frozen numbers")

print("\n" + "=" * 60)
print("ROUND 09 SOLVER COMPLETE")
print("=" * 60)
