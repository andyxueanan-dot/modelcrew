"""
Round 08: House Price Prediction with Multicollinearity
Methods: OLS, VIF, PCA, PCR, Forward Selection, 5-fold CV
"""

import os
import json
import numpy as np
from numpy.linalg import inv, pinv, eig
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

np.random.seed(42)

# ============================================================
# DATA GENERATION
# ============================================================

n = 50  # samples

# Base variables
X1_base = np.random.uniform(50, 200, n)     # area
X3_base = np.random.randint(1, 31, n).astype(float)  # floor
X5 = np.random.randint(1990, 2021, n).astype(float)  # year
X6 = np.random.uniform(0.1, 5.0, n)         # metro distance
X7_base = np.random.uniform(1, 10, n)       # school score

# Correlated variables
X2 = 0.02 * X1_base + np.random.normal(0, 0.3, n)  # rooms ~ area (r~0.85)
X4 = 0.5 * X3_base + np.random.normal(10, 3, n)     # total floors ~ floor (r~0.60)
X8 = 0.55 * X7_base + np.random.normal(2, 1, n)     # commerce ~ school (r~0.55)

# Clip to valid ranges
X2 = np.clip(X2, 1, 6)
X4 = np.clip(X4, 6, 35)
X8 = np.clip(X8, 1, 10)

# Target: house price (wan yuan/sqm)
Y = (2.0 
     + 0.02 * X1_base 
     + 0.3 * X2 
     - 0.05 * X3_base 
     + 0.15 * (X5 - 1990) 
     - 0.5 * X6 
     + 0.4 * X7_base 
     + np.random.normal(0, 0.8, n))

# Feature matrix
feature_names = ['Area', 'Rooms', 'Floor', 'TotalFloor', 'Year', 'MetroDist', 'School', 'Commerce']
X = np.column_stack([X1_base, X2, X3_base, X4, X5, X6, X7_base, X8])

print("=" * 60)
print("DATA SUMMARY")
print("=" * 60)
print(f"Samples: {n}, Features: {X.shape[1]}")
print(f"Y range: [{Y.min():.2f}, {Y.max():.2f}], mean={Y.mean():.2f}")

# ============================================================
# CORRELATION MATRIX
# ============================================================
print("\n" + "=" * 60)
print("CORRELATION MATRIX")
print("=" * 60)

corr = np.corrcoef(X.T)
print("Pairwise correlations:")
for i in range(8):
    for j in range(i+1, 8):
        if abs(corr[i, j]) > 0.4:
            print(f"  {feature_names[i]} vs {feature_names[j]}: r={corr[i,j]:.3f}")

# ============================================================
# STEP 1: OLS REGRESSION + VIF
# ============================================================
print("\n" + "=" * 60)
print("STEP 1: OLS REGRESSION + VIF")
print("=" * 60)

# Add intercept
X_design = np.column_stack([np.ones(n), X])

# OLS
beta_hat = inv(X_design.T @ X_design) @ X_design.T @ Y
Y_pred_ols = X_design @ beta_hat
SS_res = np.sum((Y - Y_pred_ols)**2)
SS_tot = np.sum((Y - Y.mean())**2)
R2_ols = 1 - SS_res / SS_tot
adj_R2_ols = 1 - (1 - R2_ols) * (n - 1) / (n - X.shape[1] - 1)

# Standard errors
sigma2 = SS_res / (n - X.shape[1] - 1)
SE_beta = np.sqrt(np.diag(sigma2 * inv(X_design.T @ X_design)))

# t-statistics and p-values
from scipy.stats import t as t_dist
t_stats = beta_hat / SE_beta
p_values = 2 * (1 - t_dist.cdf(np.abs(t_stats), df=n - X.shape[1] - 1))

print(f"\nR2 = {R2_ols:.4f}, Adjusted R2 = {adj_R2_ols:.4f}")
print(f"\nCoefficients:")
print(f"  {'Feature':<15} {'Coef':>8} {'SE':>8} {'t':>8} {'p-value':>10} {'Sig':>5}")
print("-" * 60)
for i, name in enumerate(['Intercept'] + feature_names):
    sig = '***' if p_values[i] < 0.001 else '**' if p_values[i] < 0.01 else '*' if p_values[i] < 0.05 else ''
    print(f"  {name:<15} {beta_hat[i]:>8.4f} {SE_beta[i]:>8.4f} {t_stats[i]:>8.3f} {p_values[i]:>10.4f} {sig:>5}")

n_sig = sum(1 for p in p_values[1:] if p < 0.05)
print(f"\nSignificant features (p<0.05): {n_sig}/{X.shape[1]}")

# VIF
print("\nVIF (Variance Inflation Factor):")
vif = np.zeros(X.shape[1])
for j in range(X.shape[1]):
    X_others = np.delete(X, j, axis=1)
    X_others_design = np.column_stack([np.ones(n), X_others])
    beta_j = inv(X_others_design.T @ X_others_design) @ X_others_design.T @ X[:, j]
    Y_j_pred = X_others_design @ beta_j
    R2_j = 1 - np.sum((X[:, j] - Y_j_pred)**2) / np.sum((X[:, j] - X[:, j].mean())**2)
    vif[j] = 1 / (1 - R2_j)
    flag = ' [!!!]' if vif[j] > 10 else ' [!]' if vif[j] > 5 else ''
    print(f"  {feature_names[j]}: VIF={vif[j]:.2f}{flag}")

max_vif = np.max(vif)
print(f"\nMax VIF: {max_vif:.2f}")

# ============================================================
# STEP 2: PCA + PCR
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: PCA + PCR")
print("=" * 60)

# Standardize
X_mean = X.mean(axis=0)
X_std_dev = X.std(axis=0, ddof=0)
X_std = (X - X_mean) / X_std_dev

# PCA via SVD
U, S, Vt = np.linalg.svd(X_std, full_matrices=False)
eigenvalues = S**2 / (n - 1)
total_var = np.sum(eigenvalues)
PVE = eigenvalues / total_var
CVE = np.cumsum(PVE)

print(f"\nPrincipal Components:")
print(f"  {'PC':<5} {'Eigenvalue':>12} {'PVE':>8} {'CVE':>8}")
print("-" * 35)
for k in range(8):
    print(f"  PC{k+1:<3} {eigenvalues[k]:>12.4f} {PVE[k]:>8.4f} {CVE[k]:>8.4f}")

# Find K for 90% variance
K_90 = np.searchsorted(CVE, 0.90) + 1
print(f"\nComponents for 90% variance: K={K_90}")

# PCR with K components
Z = X_std @ Vt.T  # principal component scores
Z_K = Z[:, :K_90]

# PCR regression
Z_K_design = np.column_stack([np.ones(n), Z_K])
gamma_hat = inv(Z_K_design.T @ Z_K_design) @ Z_K_design.T @ Y
Y_pred_pcr = Z_K_design @ gamma_hat
SS_res_pcr = np.sum((Y - Y_pred_pcr)**2)
R2_pcr = 1 - SS_res_pcr / SS_tot

print(f"\nPCR (K={K_90}): R2={R2_pcr:.4f}")

# ============================================================
# STEP 3: FORWARD SELECTION
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: FORWARD SELECTION")
print("=" * 60)

selected = []
remaining = list(range(8))
current_R2 = 0

for step in range(8):
    best_feature = None
    best_R2 = current_R2
    
    for j in remaining:
        test_features = selected + [j]
        X_test = X[:, test_features]
        X_test_design = np.column_stack([np.ones(n), X_test])
        beta_test = inv(X_test_design.T @ X_test_design) @ X_test_design.T @ Y
        Y_test_pred = X_test_design @ beta_test
        R2_test = 1 - np.sum((Y - Y_test_pred)**2) / SS_tot
        
        if R2_test > best_R2:
            best_R2 = R2_test
            best_feature = j
    
    if best_feature is not None and (best_R2 - current_R2) > 0.005:
        selected.append(best_feature)
        remaining.remove(best_feature)
        current_R2 = best_R2
        print(f"  Step {step+1}: Add {feature_names[best_feature]} -> R2={current_R2:.4f}")
    else:
        break

print(f"\nSelected features: {[feature_names[j] for j in selected]}")

# Final forward selection model
X_fwd = X[:, selected]
X_fwd_design = np.column_stack([np.ones(n), X_fwd])
beta_fwd = inv(X_fwd_design.T @ X_fwd_design) @ X_fwd_design.T @ Y
Y_pred_fwd = X_fwd_design @ beta_fwd
SS_res_fwd = np.sum((Y - Y_pred_fwd)**2)
R2_fwd = 1 - SS_res_fwd / SS_tot
adj_R2_fwd = 1 - (1 - R2_fwd) * (n - 1) / (n - len(selected) - 1)

print(f"Forward selection R2={R2_fwd:.4f}, Adjusted R2={adj_R2_fwd:.4f}")

# ============================================================
# STEP 4: 5-FOLD CROSS-VALIDATION
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: 5-FOLD CROSS-VALIDATION")
print("=" * 60)

def kfold_cv(X, Y, model_func, k=5):
    """K-fold cross-validation"""
    n = len(Y)
    indices = np.random.permutation(n)
    fold_size = n // k
    rmse_scores = []
    
    for i in range(k):
        test_idx = indices[i*fold_size:(i+1)*fold_size]
        train_idx = np.setdiff1d(indices, test_idx)
        
        X_train, Y_train = X[train_idx], Y[train_idx]
        X_test, Y_test = X[test_idx], Y[test_idx]
        
        Y_pred = model_func(X_train, Y_train, X_test)
        rmse = np.sqrt(np.mean((Y_test - Y_pred)**2))
        rmse_scores.append(rmse)
    
    return np.mean(rmse_scores), np.std(rmse_scores)

# OLS model
def ols_predict(X_train, Y_train, X_test):
    X_train_d = np.column_stack([np.ones(len(Y_train)), X_train])
    X_test_d = np.column_stack([np.ones(len(X_test)), X_test])
    beta = inv(X_train_d.T @ X_train_d) @ X_train_d.T @ Y_train
    return X_test_d @ beta

# PCR model
def pcr_predict(X_train, Y_train, X_test):
    X_mean_tr = X_train.mean(axis=0)
    X_std_tr = X_train.std(axis=0, ddof=0)
    X_train_std = (X_train - X_mean_tr) / X_std_tr
    X_test_std = (X_test - X_mean_tr) / X_std_tr
    
    U, S, Vt = np.linalg.svd(X_train_std, full_matrices=False)
    eigenvalues = S**2 / (len(Y_train) - 1)
    CVE = np.cumsum(eigenvalues / np.sum(eigenvalues))
    K = np.searchsorted(CVE, 0.90) + 1
    
    Z_train = X_train_std @ Vt.T
    Z_test = X_test_std @ Vt.T
    Z_train_K = Z_train[:, :K]
    Z_test_K = Z_test[:, :K]
    
    Z_train_d = np.column_stack([np.ones(len(Y_train)), Z_train_K])
    Z_test_d = np.column_stack([np.ones(len(X_test)), Z_test_K])
    gamma = inv(Z_train_d.T @ Z_train_d) @ Z_train_d.T @ Y_train
    return Z_test_d @ gamma

# Forward selection model
def fwd_predict(X_train, Y_train, X_test):
    SS_tot = np.sum((Y_train - Y_train.mean())**2)
    selected = []
    remaining = list(range(X_train.shape[1]))
    current_R2 = 0
    
    for step in range(X_train.shape[1]):
        best_feature = None
        best_R2 = current_R2
        for j in remaining:
            test_features = selected + [j]
            X_t = X_train[:, test_features]
            X_t_d = np.column_stack([np.ones(len(Y_train)), X_t])
            beta_t = inv(X_t_d.T @ X_t_d) @ X_t_d.T @ Y_train
            Y_t_pred = X_t_d @ beta_t
            R2_t = 1 - np.sum((Y_train - Y_t_pred)**2) / SS_tot
            if R2_t > best_R2:
                best_R2 = R2_t
                best_feature = j
        if best_feature is not None and (best_R2 - current_R2) > 0.005:
            selected.append(best_feature)
            remaining.remove(best_feature)
            current_R2 = best_R2
        else:
            break
    
    if not selected:
        return np.full(len(X_test), Y_train.mean())
    
    X_train_sel = X_train[:, selected]
    X_test_sel = X_test[:, selected]
    X_train_d = np.column_stack([np.ones(len(Y_train)), X_train_sel])
    X_test_d = np.column_stack([np.ones(len(X_test)), X_test_sel])
    beta = inv(X_train_d.T @ X_train_d) @ X_train_d.T @ Y_train
    return X_test_d @ beta

rmse_ols, std_ols = kfold_cv(X, Y, ols_predict)
rmse_pcr, std_pcr = kfold_cv(X, Y, pcr_predict)
rmse_fwd, std_fwd = kfold_cv(X, Y, fwd_predict)

print(f"\n5-Fold CV Results:")
print(f"  OLS:   RMSE={rmse_ols:.4f} (+/- {std_ols:.4f})")
print(f"  PCR:   RMSE={rmse_pcr:.4f} (+/- {std_pcr:.4f})")
print(f"  Fwd:   RMSE={rmse_fwd:.4f} (+/- {std_fwd:.4f})")

best_model = min([('OLS', rmse_ols), ('PCR', rmse_pcr), ('Forward', rmse_fwd)], key=lambda x: x[1])
print(f"\nBest model: {best_model[0]} (RMSE={best_model[1]:.4f})")

# ============================================================
# GENERATE FIGURES
# ============================================================
print("\n" + "=" * 60)
print("GENERATING FIGURES")
print("=" * 60)

# Fig 1: Correlation heatmap
fig, ax = plt.subplots(figsize=(10, 8))
im = ax.imshow(corr, cmap='RdBu_r', vmin=-1, vmax=1, aspect='auto')
ax.set_xticks(range(8))
ax.set_xticklabels(feature_names, rotation=45, ha='right')
ax.set_yticks(range(8))
ax.set_yticklabels(feature_names)
ax.set_title('Feature Correlation Matrix')

for i in range(8):
    for j in range(8):
        ax.text(j, i, f'{corr[i,j]:.2f}', ha='center', va='center', fontsize=9,
                color='white' if abs(corr[i,j]) > 0.5 else 'black')

plt.colorbar(im, label='Correlation')
plt.tight_layout()
plt.savefig('figures/fig1_correlation.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1")

# Fig 2: PCA scree plot
fig, ax = plt.subplots(figsize=(10, 6))
ax.bar(range(1, 9), PVE, color='steelblue', alpha=0.7, label='Individual PVE')
ax.plot(range(1, 9), CVE, 'ro-', linewidth=2, markersize=8, label='Cumulative CVE')
ax.axhline(y=0.90, color='green', linestyle='--', label='90% threshold')
ax.axvline(x=K_90+0.5, color='green', linestyle='--')
ax.set_xlabel('Principal Component')
ax.set_ylabel('Variance Explained')
ax.set_title('PCA Scree Plot')
ax.set_xticks(range(1, 9))
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figures/fig2_scree.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2")

# Fig 3: Model comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# RMSE comparison
models = ['OLS', 'PCR', 'Forward']
rmse_vals = [rmse_ols, rmse_pcr, rmse_fwd]
std_vals = [std_ols, std_pcr, std_fwd]
colors = ['steelblue', 'coral', 'seagreen']

axes[0].bar(models, rmse_vals, yerr=std_vals, capsize=10, color=colors, alpha=0.8)
axes[0].set_ylabel('RMSE (5-fold CV)')
axes[0].set_title('Prediction Accuracy Comparison')
axes[0].grid(True, alpha=0.3, axis='y')

for i, (m, r, s) in enumerate(zip(models, rmse_vals, std_vals)):
    axes[0].text(i, r + s + 0.02, f'{r:.3f}', ha='center', fontsize=11, fontweight='bold')

# R2 comparison
r2_vals = [R2_ols, R2_pcr, R2_fwd]
adj_r2_vals = [adj_R2_ols, R2_pcr, adj_R2_fwd]

x = np.arange(len(models))
width = 0.35
axes[1].bar(x - width/2, r2_vals, width, label='R2', color='steelblue')
axes[1].bar(x + width/2, adj_r2_vals, width, label='Adj R2', color='coral')
axes[1].set_xticks(x)
axes[1].set_xticklabels(models)
axes[1].set_ylabel('R-squared')
axes[1].set_title('Model Fit Comparison')
axes[1].legend()
axes[1].grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('figures/fig3_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3")

# ============================================================
# SAVE FROZEN NUMBERS
# ============================================================

frozen = {
    "numbers": [
        # Data
        {"id": "n_samples", "label": "Number of samples", "value": int(n), "tol": 0, "source": "input", "path": "data"},
        {"id": "n_features", "label": "Number of features", "value": 8, "tol": 0, "source": "input", "path": "data"},
        
        # Q1: OLS
        {"id": "R2_ols", "label": "OLS R-squared", "value": float(round(R2_ols, 4)), "tol": 0.001, "source": "ols", "path": "q1"},
        {"id": "adj_R2_ols", "label": "OLS adjusted R-squared", "value": float(round(adj_R2_ols, 4)), "tol": 0.001, "source": "ols", "path": "q1"},
        {"id": "n_significant", "label": "Number of significant features", "value": int(n_sig), "tol": 0, "source": "ols", "path": "q1"},
        {"id": "max_vif", "label": "Maximum VIF", "value": float(round(max_vif, 2)), "tol": 0.1, "source": "vif", "path": "q1"},
        {"id": "n_vif_gt10", "label": "Features with VIF > 10", "value": int(sum(vif > 10)), "tol": 0, "source": "vif", "path": "q1"},
        
        # Q2: PCR
        {"id": "K_90", "label": "Components for 90% variance", "value": int(K_90), "tol": 0, "source": "pca", "path": "q2"},
        {"id": "CVE_K", "label": "Cumulative variance at K", "value": float(round(CVE[K_90-1], 4)), "tol": 0.001, "source": "pca", "path": "q2"},
        {"id": "R2_pcr", "label": "PCR R-squared", "value": float(round(R2_pcr, 4)), "tol": 0.001, "source": "pcr", "path": "q2"},
        
        # Q3: Forward selection
        {"id": "n_selected", "label": "Features selected by forward", "value": int(len(selected)), "tol": 0, "source": "forward", "path": "q3"},
        {"id": "R2_fwd", "label": "Forward selection R-squared", "value": float(round(R2_fwd, 4)), "tol": 0.001, "source": "forward", "path": "q3"},
        
        # CV
        {"id": "RMSE_ols", "label": "OLS CV-RMSE", "value": float(round(rmse_ols, 4)), "tol": 0.01, "source": "cv", "path": "cv"},
        {"id": "RMSE_pcr", "label": "PCR CV-RMSE", "value": float(round(rmse_pcr, 4)), "tol": 0.01, "source": "cv", "path": "cv"},
        {"id": "RMSE_fwd", "label": "Forward CV-RMSE", "value": float(round(rmse_fwd, 4)), "tol": 0.01, "source": "cv", "path": "cv"},
    ]
}

# Add VIF for each feature
for j in range(8):
    frozen["numbers"].append({
        "id": f"VIF_{feature_names[j]}",
        "label": f"VIF of {feature_names[j]}",
        "value": float(round(vif[j], 2)),
        "tol": 0.1,
        "source": "vif",
        "path": "q1.vif"
    })

# Add PVE for each PC
for k in range(8):
    frozen["numbers"].append({
        "id": f"PVE_PC{k+1}",
        "label": f"PVE of PC{k+1}",
        "value": float(round(PVE[k], 4)),
        "tol": 0.001,
        "source": "pca",
        "path": "q2.pve"
    })

with open('frozen_numbers.json', 'w', encoding='utf-8') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)

print(f"\nSaved frozen_numbers.json ({len(frozen['numbers'])} entries)")

print("\n" + "=" * 60)
print("SOLVER COMPLETE")
print("=" * 60)
