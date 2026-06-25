"""
Solver R3: City Livability Evaluation
Entropy Weight + TOPSIS + AHP + Rank Comparison
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
# DATA
# ============================================================
cities = ['A','B','C','D','E','F','G','H']
indicators = ['GDP','Green','Uni','Medical','Metro','Safety']
# Raw data: 8 cities x 6 indicators
raw = np.array([
    [8.5, 42, 12, 65, 180, 3.2],  # A
    [12.0, 38, 8, 48, 320, 5.1],  # B
    [6.2, 55, 20, 72, 45, 1.8],   # C
    [15.0, 35, 5, 40, 450, 6.5],  # D
    [9.8, 48, 15, 58, 120, 2.5],  # E
    [7.0, 52, 25, 80, 30, 1.5],   # F
    [11.5, 40, 10, 52, 280, 4.8],  # G
    [5.5, 60, 30, 85, 0, 1.2],   # H
], dtype=float)

n, m = raw.shape  # 8 cities, 6 indicators
# Safety is a NEGATIVE indicator (lower is better)
is_negative = [False, False, False, False, False, True]

# ============================================================
# STEP 1: NORMALIZATION (min-max)
# ============================================================
print("="*60)
print("STEP 1: MIN-MAX NORMALIZATION")
print("="*60)

norm = np.zeros_like(raw)
for j in range(m):
    col = raw[:, j]
    col_min, col_max = col.min(), col.max()
    if col_max == col_min:
        norm[:, j] = 1.0
    elif is_negative[j]:
        # Negative indicator: invert (lower raw -> higher normalized)
        norm[:, j] = (col_max - col) / (col_max - col_min)
    else:
        norm[:, j] = (col - col_min) / (col_max - col_min)

print("Normalized matrix (0-1):")
for i, city in enumerate(cities):
    vals = '  '.join(f'{norm[i,j]:.3f}' for j in range(m))
    print(f"  {city}: {vals}")

# ============================================================
# STEP 2: ENTROPY WEIGHT
# ============================================================
print("\n" + "="*60)
print("STEP 2: ENTROPY WEIGHT METHOD")
print("="*60)

# Avoid log(0): add small epsilon
eps = 1e-10
p = (norm + eps) / (norm + eps).sum(axis=0)  # proportion matrix
k = 1.0 / np.log(n)
entropy = -k * np.sum(p * np.log(p), axis=0)
d = 1 - entropy  # degree of divergence
w_entropy = d / d.sum()

print("Entropy weights:")
for j, name in enumerate(indicators):
    print(f"  {name:10s}: e={entropy[j]:.4f}, d={d[j]:.4f}, w={w_entropy[j]:.4f} ({w_entropy[j]*100:.1f}%)")

# ============================================================
# STEP 3: TOPSIS
# ============================================================
print("\n" + "="*60)
print("STEP 3: TOPSIS RANKING")
print("="*60)

# Weighted normalized matrix
v = norm * w_entropy

# Ideal and negative-ideal solutions
ideal = v.max(axis=0)
neg_ideal = v.min(axis=0)

# Distances
d_pos = np.sqrt(np.sum((v - ideal)**2, axis=1))
d_neg = np.sqrt(np.sum((v - neg_ideal)**2, axis=1))
closeness = d_neg / (d_pos + d_neg)

# Rank (higher closeness = better)
topsis_rank = np.argsort(closeness)[::-1]

print("TOPSIS Results:")
for rank, idx in enumerate(topsis_rank):
    print(f"  #{rank+1} {cities[idx]}: D+={d_pos[idx]:.4f}, D-={d_neg[idx]:.4f}, "
          f"C={closeness[idx]:.4f}")

# ============================================================
# STEP 4: AHP
# ============================================================
print("\n" + "="*60)
print("STEP 4: AHP (Analytic Hierarchy Process)")
print("="*60)

# Preference: GDP:Green:Uni:Medical:Metro:Safety = 3:2:2:2:2:1
# Construct pairwise comparison matrix
prefs = [3, 2, 2, 2, 2, 1]  # relative importance
ahp_matrix = np.zeros((m, m))
for i in range(m):
    for j in range(m):
        if i == j:
            ahp_matrix[i, j] = 1.0
        elif prefs[i] > prefs[j]:
            ahp_matrix[i, j] = prefs[i] / prefs[j]
        else:
            ahp_matrix[i, j] = prefs[j] / prefs[i]  # should be prefs[i]/prefs[j] but reciprocal

# Fix: proper reciprocal matrix
for i in range(m):
    for j in range(m):
        ahp_matrix[i, j] = prefs[i] / prefs[j]

print("AHP pairwise comparison matrix:")
for row in ahp_matrix:
    print('  ' + '  '.join(f'{v:.2f}' for v in row))

# Eigenvector method
eigenvalues, eigenvectors = np.linalg.eig(ahp_matrix)
max_idx = np.argmax(eigenvalues.real)
lambda_max = eigenvalues[max_idx].real
w_ahp = eigenvectors[:, max_idx].real
w_ahp = w_ahp / w_ahp.sum()

# Consistency check
CI = (lambda_max - m) / (m - 1)
RI_table = {1: 0, 2: 0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24}
RI = RI_table[m]
CR = CI / RI if RI > 0 else 0

print(f"\nAHP Results:")
print(f"  lambda_max = {lambda_max:.4f}")
print(f"  CI = {CI:.4f}, RI = {RI:.2f}, CR = {CR:.4f}")
print(f"  Consistency: {'PASS (CR<0.1)' if CR < 0.1 else 'FAIL (CR>=0.1)'}")
print(f"\nAHP weights:")
for j, name in enumerate(indicators):
    print(f"  {name:10s}: w={w_ahp[j]:.4f} ({w_ahp[j]*100:.1f}%)")

# AHP ranking (weighted sum on normalized data)
ahp_scores = norm @ w_ahp
ahp_rank = np.argsort(ahp_scores)[::-1]

print(f"\nAHP Ranking:")
for rank, idx in enumerate(ahp_rank):
    print(f"  #{rank+1} {cities[idx]}: score={ahp_scores[idx]:.4f}")

# ============================================================
# STEP 5: RANK COMPARISON
# ============================================================
print("\n" + "="*60)
print("STEP 5: RANK COMPARISON")
print("="*60)

# Create rank arrays (1-based)
topsis_pos = np.zeros(n, dtype=int)
ahp_pos = np.zeros(n, dtype=int)
for rank, idx in enumerate(topsis_rank):
    topsis_pos[idx] = rank + 1
for rank, idx in enumerate(ahp_rank):
    ahp_pos[idx] = rank + 1

# Spearman rank correlation
rho, p_spearman = stats.spearmanr(topsis_pos, ahp_pos)
print(f"Spearman rank correlation: rho={rho:.4f}, p={p_spearman:.4f}")
print(f"  {'Significant (p<0.05)' if p_spearman < 0.05 else 'Not significant'}")

# City-by-city comparison
print(f"\nCity-by-city rank comparison:")
print(f"  {'City':6s} {'Entropy-TOPSIS':>15s} {'AHP':>15s} {'|diff|':>8s} {'Stability':>10s}")
rank_diffs = np.abs(topsis_pos - ahp_pos)
for i, city in enumerate(cities):
    stability = 'STABLE' if rank_diffs[i] <= 1 else ('MODERATE' if rank_diffs[i] <= 2 else 'SENSITIVE')
    print(f"  {city:6s} {topsis_pos[i]:>15d} {ahp_pos[i]:>15d} {rank_diffs[i]:>8d} {stability:>10s}")

most_stable_idx = np.argmin(rank_diffs)
most_sensitive_idx = np.argmax(rank_diffs)
print(f"\nMost stable: {cities[most_stable_idx]} (diff={rank_diffs[most_stable_idx]})")
print(f"Most sensitive: {cities[most_sensitive_idx]} (diff={rank_diffs[most_sensitive_idx]})")

# ============================================================
# FIGURES
# ============================================================
print("\n" + "="*60)
print("GENERATING FIGURES")
print("="*60)

# Fig 1: Weight comparison
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(m)
w = 0.35
ax.bar(x - w/2, w_entropy, w, label='Entropy Weight', color='steelblue', edgecolor='black')
ax.bar(x + w/2, w_ahp, w, label='AHP Weight', color='coral', edgecolor='black')
ax.set_xticks(x)
ax.set_xticklabels(indicators)
ax.set_ylabel('Weight')
ax.set_title('Weight Comparison: Entropy vs AHP')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('artifacts/figures/fig1_weight_comparison.png', dpi=150)
plt.close()
print("Saved fig1")

# Fig 2: Rank comparison (dot plot)
fig, ax = plt.subplots(figsize=(10, 6))
for i, city in enumerate(cities):
    ax.plot([1, 2], [topsis_pos[i], ahp_pos[i]], 'o-', color='steelblue',
           markersize=10, linewidth=2)
    ax.annotate(f'{city}', (1.05, topsis_pos[i]), fontsize=11, va='center')
    ax.annotate(f'{city}', (2.05, ahp_pos[i]), fontsize=11, va='center')
ax.set_xticks([1, 2])
ax.set_xticklabels(['Entropy-TOPSIS', 'AHP'])
ax.set_ylabel('Rank (1=Best)')
ax.set_title('City Rank Comparison: Entropy-TOPSIS vs AHP')
ax.invert_yaxis()  # rank 1 at top
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('artifacts/figures/fig2_rank_comparison.png', dpi=150)
plt.close()
print("Saved fig2")

# Fig 3: Radar chart for top 3 cities
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
angles = np.linspace(0, 2*np.pi, m, endpoint=False).tolist()
angles += angles[:1]
top3 = topsis_rank[:3]
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
for k, idx in enumerate(top3):
    vals = norm[idx].tolist()
    vals += vals[:1]
    ax.plot(angles, vals, 'o-', linewidth=2, color=colors[k], label=f'{cities[idx]} (Rank #{k+1})')
    ax.fill(angles, vals, alpha=0.1, color=colors[k])
ax.set_xticks(angles[:-1])
ax.set_xticklabels(indicators)
ax.set_title('TOP 3 Cities: Normalized Indicator Profiles', y=1.08)
ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
plt.tight_layout()
plt.savefig('artifacts/figures/fig3_radar_top3.png', dpi=150)
plt.close()
print("Saved fig3")

# ============================================================
# FROZEN NUMBERS
# ============================================================
frozen = {"numbers": [
    {"id": "spearman_rho", "label": "Spearman rank correlation (TOPSIS vs AHP)",
     "value": round(float(rho), 4), "tol": 0.001,
     "source": "solve.py:Spearman", "path": "artifacts/solve.py"},
    {"id": "spearman_p", "label": "Spearman p-value",
     "value": round(float(p_spearman), 4), "tol": 0.001,
     "source": "solve.py:Spearman", "path": "artifacts/solve.py"},
    {"id": "ahp_lambda_max", "label": "AHP lambda_max",
     "value": round(float(lambda_max), 4), "tol": 0.001,
     "source": "solve.py:AHP", "path": "artifacts/solve.py"},
    {"id": "ahp_CR", "label": "AHP consistency ratio",
     "value": round(float(CR), 4), "tol": 0.001,
     "source": "solve.py:AHP", "path": "artifacts/solve.py"},
    {"id": "ahp_consistent", "label": "AHP consistency passed (1=yes)",
     "value": 1 if CR < 0.1 else 0, "tol": 0,
     "source": "solve.py:AHP", "path": "artifacts/solve.py"},
    {"id": "most_stable_city", "label": "Most rank-stable city index",
     "value": int(most_stable_idx), "tol": 0,
     "source": "solve.py:comparison", "path": "artifacts/solve.py"},
    {"id": "most_sensitive_city", "label": "Most rank-sensitive city index",
     "value": int(most_sensitive_idx), "tol": 0,
     "source": "solve.py:comparison", "path": "artifacts/solve.py"},
]}

for j, name in enumerate(indicators):
    frozen["numbers"].append({
        "id": f"entropy_w_{name}", "label": f"Entropy weight: {name}",
        "value": round(float(w_entropy[j]), 4), "tol": 0.001,
        "source": "solve.py:entropy", "path": "artifacts/solve.py"
    })
    frozen["numbers"].append({
        "id": f"ahp_w_{name}", "label": f"AHP weight: {name}",
        "value": round(float(w_ahp[j]), 4), "tol": 0.001,
        "source": "solve.py:AHP", "path": "artifacts/solve.py"
    })

for i, city in enumerate(cities):
    frozen["numbers"].append({
        "id": f"topsis_rank_{city}", "label": f"TOPSIS rank: {city}",
        "value": int(topsis_pos[i]), "tol": 0,
        "source": "solve.py:TOPSIS", "path": "artifacts/solve.py"
    })
    frozen["numbers"].append({
        "id": f"ahp_rank_{city}", "label": f"AHP rank: {city}",
        "value": int(ahp_pos[i]), "tol": 0,
        "source": "solve.py:AHP", "path": "artifacts/solve.py"
    })
    frozen["numbers"].append({
        "id": f"topsis_C_{city}", "label": f"TOPSIS closeness: {city}",
        "value": round(float(closeness[i]), 4), "tol": 0.001,
        "source": "solve.py:TOPSIS", "path": "artifacts/solve.py"
    })

with open('artifacts/frozen_numbers.json', 'w') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)
print(f"\nSaved frozen_numbers.json ({len(frozen['numbers'])} entries)")

print("\n" + "="*60)
print("SOLVER COMPLETE")
print("="*60)
