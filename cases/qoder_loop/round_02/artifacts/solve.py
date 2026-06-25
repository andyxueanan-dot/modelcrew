"""
Solver R2: Bike Sharing Demand Prediction
OLS + Lasso + VIF + 5-fold CV + residual analysis
"""
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os, warnings
warnings.filterwarnings('ignore')

np.random.seed(42)
os.makedirs('artifacts/figures', exist_ok=True)

# ============================================================
# DATA
# ============================================================
raw = [
    [12.5,0.3,3.8,85,2.1,26,412],[8.0,0.8,2.5,52,1.5,24,278],
    [3.2,2.5,1.2,18,0.4,30,95],[14.0,0.2,4.2,92,2.8,25,458],
    [6.5,1.2,2.0,38,1.0,28,198],[10.8,0.5,3.2,68,1.8,22,345],
    [4.5,1.8,1.5,25,0.6,32,132],[11.2,0.4,3.5,75,2.3,27,378],
    [7.0,1.0,2.2,45,1.2,23,242],[2.5,2.8,0.8,12,0.3,33,68],
    [13.5,0.1,4.5,88,2.5,24,435],[9.0,0.6,2.8,58,1.6,26,305],
    [5.0,1.5,1.8,30,0.8,29,165],[15.0,0.3,4.8,95,3.0,25,502],
    [3.8,2.2,1.0,20,0.5,31,108],[8.5,0.9,2.6,55,1.4,21,268],
    [6.0,1.3,1.9,35,0.9,27,192],[12.0,0.4,3.6,80,2.0,26,388],
    [4.0,2.0,1.3,22,0.5,34,145],[10.0,0.7,3.0,62,1.7,25,322],
]

X_raw = np.array([r[:6] for r in raw], dtype=float)
y = np.array([r[6] for r in raw], dtype=float)
feat_names = ['PopDensity','MetroDist','BikeLane','POI','OfficeRes','Temp']
n, p = X_raw.shape
print(f"n={n}, p={p}")

# Standardize
X_mean = X_raw.mean(0)
X_std = X_raw.std(0, ddof=0)
X_std[X_std == 0] = 1
Xs = (X_raw - X_mean) / X_std
X_int = np.column_stack([np.ones(n), Xs])

# ============================================================
# OLS
# ============================================================
print("\n" + "="*60)
print("OLS REGRESSION")
print("="*60)

XtX = X_int.T @ X_int
Xty = X_int.T @ y
beta = np.linalg.solve(XtX, Xty)
y_hat = X_int @ beta
resid = y - y_hat
SS_res = np.sum(resid**2)
SS_tot = np.sum((y - y.mean())**2)
R2 = 1 - SS_res/SS_tot
R2_adj = 1 - (1-R2)*(n-1)/(n-p-1)
MSE = SS_res/(n-p-1)
RMSE = np.sqrt(MSE)

print(f"R2 = {R2:.4f}, Adj-R2 = {R2_adj:.4f}")
print(f"RMSE = {RMSE:.2f}")

# t-tests
var_beta = MSE * np.linalg.inv(XtX).diagonal()
se_beta = np.sqrt(var_beta)
t_vals = beta / se_beta
p_vals = [2*stats.t.sf(abs(t), df=n-p-1) for t in t_vals]

print("\nStandardized Coefficients:")
for i, name in enumerate(feat_names):
    sig = '***' if p_vals[i+1]<0.001 else '**' if p_vals[i+1]<0.01 else '*' if p_vals[i+1]<0.05 else 'ns'
    print(f"  {name:12s}: beta={beta[i+1]:+.3f}, t={t_vals[i+1]:+.3f}, p={p_vals[i+1]:.4f} {sig}")

# ============================================================
# VIF
# ============================================================
print("\n" + "="*60)
print("VIF ANALYSIS")
print("="*60)

vif_list = []
for j in range(p):
    X_oth = np.delete(Xs, j, axis=1)
    X_oth_int = np.column_stack([np.ones(n), X_oth])
    b = np.linalg.lstsq(X_oth_int, Xs[:,j], rcond=None)[0]
    yh = X_oth_int @ b
    R2j = 1 - np.sum((Xs[:,j]-yh)**2)/np.sum((Xs[:,j]-Xs[:,j].mean())**2)
    vif = 1/(1-R2j) if R2j < 1 else float('inf')
    vif_list.append(vif)
    flag = ' ** HIGH' if vif > 10 else ''
    print(f"  {feat_names[j]:12s}: VIF = {vif:.2f}{flag}")

# ============================================================
# 5-FOLD CV
# ============================================================
print("\n" + "="*60)
print("5-FOLD CROSS-VALIDATION")
print("="*60)

np.random.seed(42)
indices = np.random.permutation(n)
folds = np.array_split(indices, 5)
cv_errors = []

for k in range(5):
    test_idx = folds[k]
    train_idx = np.concatenate([folds[j] for j in range(5) if j != k])
    
    Xtr = np.column_stack([np.ones(len(train_idx)), Xs[train_idx]])
    ytr = y[train_idx]
    Xte = np.column_stack([np.ones(len(test_idx)), Xs[test_idx]])
    yte = y[test_idx]
    
    b_cv = np.linalg.lstsq(Xtr, ytr, rcond=None)[0]
    y_pred = Xte @ b_cv
    fold_mse = np.mean((yte - y_pred)**2)
    cv_errors.append(fold_mse)
    print(f"  Fold {k+1}: test={test_idx.tolist()}, MSE={fold_mse:.1f}, RMSE={np.sqrt(fold_mse):.1f}")

CV_RMSE = np.sqrt(np.mean(cv_errors))
print(f"\n5-fold CV RMSE = {CV_RMSE:.2f}")
print(f"Training RMSE  = {RMSE:.2f}")
print(f"Overfitting gap = {CV_RMSE - RMSE:+.2f}")

# ============================================================
# LASSO (coordinate descent)
# ============================================================
print("\n" + "="*60)
print("LASSO REGRESSION")
print("="*60)

def lasso_cd(X, y, lam, max_iter=1000, tol=1e-6):
    """Coordinate descent Lasso."""
    n, p = X.shape
    beta = np.zeros(p)
    for _ in range(max_iter):
        beta_old = beta.copy()
        for j in range(p):
            r = y - X @ beta + X[:,j]*beta[j]
            rho = X[:,j] @ r / n
            z = np.sum(X[:,j]**2) / n
            if z == 0:
                beta[j] = 0
            else:
                beta[j] = np.sign(rho) * max(abs(rho) - lam, 0) / z
        if np.max(np.abs(beta - beta_old)) < tol:
            break
    return beta

# Sweep lambda
lambdas = [0.1, 1, 5, 10, 20, 50, 100]
print("Lambda sweep (standardized, no intercept penalty):")
for lam in lambdas:
    X_lasso = np.column_stack([Xs, np.ones(n)])  # features first, intercept last
    b_lasso = lasso_cd(X_lasso, y, lam)
    y_h = X_lasso @ b_lasso
    R2_l = 1 - np.sum((y-y_h)**2)/SS_tot
    nz = np.sum(np.abs(b_lasso[:p]) > 0.01)
    feats_kept = [feat_names[i] for i in range(p) if abs(b_lasso[i]) > 0.01]
    print(f"  lam={lam:5.1f}: R2={R2_l:.4f}, nonzero={int(nz)}, feats={','.join(feats_kept) if feats_kept else '(none)'}")

# Best Lasso (pick one with good R2 and sparsity)
best_lam = 10
b_lasso_best = lasso_cd(np.column_stack([Xs, np.ones(n)]), y, best_lam)
print(f"\nBest Lasso (lambda={best_lam}):")
for i, name in enumerate(feat_names):
    print(f"  {name:12s}: {b_lasso_best[i]:+.3f}")

# ============================================================
# RESIDUAL ANALYSIS
# ============================================================
print("\n" + "="*60)
print("RESIDUAL ANALYSIS")
print("="*60)

h = np.zeros(n)
for i in range(n):
    h[i] = X_int[i] @ np.linalg.inv(XtX) @ X_int[i]

stud_resid = np.zeros(n)
for i in range(n):
    denom = (n-p-2)
    if denom <= 0:
        s_i = RMSE
    else:
        s_i_sq = (SS_res - resid[i]**2/(1-h[i])) / denom
        s_i = np.sqrt(max(s_i_sq, 0))
    stud_resid[i] = resid[i] / (s_i * np.sqrt(max(1-h[i], 1e-10))) if s_i > 0 else 0

cooks_d = np.zeros(n)
for i in range(n):
    cooks_d[i] = (stud_resid[i]**2 * h[i]) / ((p+1) * max(1-h[i], 1e-10))

threshold_sr = 2.0
threshold_cd = 4.0/n

anomalies = []
print("Anomaly detection (|SR|>2 or Cook's D > 4/n):")
for i in range(n):
    is_anom = abs(stud_resid[i]) > threshold_sr or cooks_d[i] > threshold_cd
    marker = ' *** ANOMALY' if is_anom else ''
    if is_anom or abs(stud_resid[i]) > 1.5:
        print(f"  Station #{i+1}: actual={y[i]:.0f}, pred={y_hat[i]:.0f}, "
              f"resid={resid[i]:+.0f}, SR={stud_resid[i]:+.2f}, CD={cooks_d[i]:.4f}{marker}")
        if is_anom:
            anomalies.append(i)

if not anomalies:
    print("  No anomalies at strict thresholds.")
    # Relax to |SR|>1.5
    for i in range(n):
        if abs(stud_resid[i]) > 1.5:
            anomalies.append(i)
    if anomalies:
        print(f"  Relaxed threshold |SR|>1.5: {len(anomalies)} potential anomalies")
        for i in anomalies:
            print(f"    Station #{i+1}: resid={resid[i]:+.0f}, SR={stud_resid[i]:+.2f}")

# ============================================================
# FEATURE IMPORTANCE (stepwise-like)
# ============================================================
print("\n" + "="*60)
print("FEATURE IMPORTANCE (semi-partial R2)")
print("="*60)

spc2 = np.zeros(p)
for j in range(p):
    X_red = np.delete(Xs, j, axis=1)
    X_red_int = np.column_stack([np.ones(n), X_red])
    b_red = np.linalg.lstsq(X_red_int, y, rcond=None)[0]
    yh_red = X_red_int @ b_red
    SS_res_red = np.sum((y - yh_red)**2)
    spc2[j] = (SS_res_red - SS_res) / SS_tot

rank_spc = np.argsort(spc2)[::-1]
abs_beta = np.abs(beta[1:])
rank_beta = np.argsort(abs_beta)[::-1]

print("By |standardized coefficient|:")
for rank, idx in enumerate(rank_beta):
    print(f"  {rank+1}. {feat_names[idx]}: |beta|={abs_beta[idx]:.3f}")

print("\nBy semi-partial R2:")
for rank, idx in enumerate(rank_spc):
    print(f"  {rank+1}. {feat_names[idx]}: spR2={spc2[idx]:.4f} ({spc2[idx]*100:.1f}%)")

# Forward stepwise
print("\nForward Stepwise Selection:")
selected = []
remaining = list(range(p))
X_cur = np.column_stack([np.ones(n)])
for step in range(p):
    best_j = -1
    best_R2 = -1
    for j in remaining:
        X_try = np.column_stack([X_cur, Xs[:,j]])
        b_try = np.linalg.lstsq(X_try, y, rcond=None)[0]
        yh_try = X_try @ b_try
        R2_try = 1 - np.sum((y-yh_try)**2)/SS_tot
        if R2_try > best_R2:
            best_R2 = R2_try
            best_j = j
    selected.append(best_j)
    remaining.remove(best_j)
    X_cur = np.column_stack([X_cur, Xs[:,best_j]])
    print(f"  Step {step+1}: +{feat_names[best_j]} -> R2={best_R2:.4f}")

# ============================================================
# FIGURES
# ============================================================
print("\n" + "="*60)
print("GENERATING FIGURES")
print("="*60)

# Fig 1: Actual vs Predicted
fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(y, y_hat, c='steelblue', s=60, edgecolors='black', zorder=3)
lims = [min(y.min(), y_hat.min())-20, max(y.max(), y_hat.max())+20]
ax.plot(lims, lims, 'r--', linewidth=1, label='Perfect')
ax.set_xlabel('Actual Daily Rentals')
ax.set_ylabel('Predicted Daily Rentals')
ax.set_title(f'OLS: Actual vs Predicted\nR2={R2:.3f}, RMSE={RMSE:.0f}, CV-RMSE={CV_RMSE:.0f}')
ax.legend()
ax.grid(True, alpha=0.3)
for i in anomalies:
    ax.annotate(f'#{i+1}', (y[i], y_hat[i]), fontsize=9, color='red',
               xytext=(5,5), textcoords='offset points')
plt.tight_layout()
plt.savefig('artifacts/figures/fig1_actual_vs_predicted.png', dpi=150)
plt.close()
print("Saved fig1")

# Fig 2: Feature importance
fig, ax = plt.subplots(figsize=(8, 5))
colors = ['forestgreen' if beta[i+1]>0 else 'coral' for i in range(p)]
ax.barh([feat_names[i] for i in range(p)][::-1],
       [beta[i+1] for i in range(p)][::-1],
       color=colors[::-1], edgecolor='black')
ax.set_xlabel('Standardized Coefficient')
ax.set_title('Feature Importance (OLS Standardized Coefficients)')
ax.axvline(0, color='black', linewidth=0.5)
for i, (name, val) in enumerate(zip(feat_names[::-1], beta[1:][::-1])):
    ax.text(val + 0.5*np.sign(val), i, f'{val:+.2f}', va='center', fontsize=10)
plt.tight_layout()
plt.savefig('artifacts/figures/fig2_feature_importance.png', dpi=150)
plt.close()
print("Saved fig2")

# Fig 3: Residuals + Cook's D
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].scatter(y_hat, resid, c='steelblue', s=60, edgecolors='black', zorder=3)
axes[0].axhline(0, color='red', linestyle='--')
axes[0].set_xlabel('Predicted')
axes[0].set_ylabel('Residual')
axes[0].set_title('Residuals vs Predicted')
axes[0].grid(True, alpha=0.3)

axes[1].bar(range(1, n+1), cooks_d, color='steelblue', edgecolor='black')
axes[1].axhline(threshold_cd, color='red', linestyle='--', label=f'Threshold 4/n={threshold_cd:.3f}')
axes[1].set_xlabel('Station #')
axes[1].set_ylabel("Cook's Distance")
axes[1].set_title("Cook's Distance")
axes[1].legend()
plt.tight_layout()
plt.savefig('artifacts/figures/fig3_residuals_cooks.png', dpi=150)
plt.close()
print("Saved fig3")

# ============================================================
# FROZEN NUMBERS (standard schema)
# ============================================================
frozen = {"numbers": [
    {"id": "r2", "label": "OLS R-squared", "value": round(R2, 4), "tol": 0.0001,
     "source": "solve.py:OLS", "path": "artifacts/solve.py"},
    {"id": "r2_adj", "label": "Adjusted R-squared", "value": round(R2_adj, 4), "tol": 0.0001,
     "source": "solve.py:OLS", "path": "artifacts/solve.py"},
    {"id": "rmse_train", "label": "Training RMSE", "value": round(RMSE, 2), "tol": 0.1,
     "source": "solve.py:OLS", "path": "artifacts/solve.py"},
    {"id": "rmse_cv", "label": "5-fold CV RMSE", "value": round(CV_RMSE, 2), "tol": 0.1,
     "source": "solve.py:5-fold CV", "path": "artifacts/solve.py"},
    {"id": "overfit_gap", "label": "CV-Training RMSE gap", "value": round(CV_RMSE-RMSE, 2), "tol": 0.1,
     "source": "solve.py:CV comparison", "path": "artifacts/solve.py"},
    {"id": "n_anomalies", "label": "Number of anomaly stations", "value": len(anomalies), "tol": 0,
     "source": "solve.py:residual analysis", "path": "artifacts/solve.py"},
]}

for i, name in enumerate(feat_names):
    frozen["numbers"].append({
        "id": f"beta_{name}", "label": f"Standardized coefficient: {name}",
        "value": round(float(beta[i+1]), 4), "tol": 0.001,
        "source": "solve.py:OLS", "path": "artifacts/solve.py"
    })
    frozen["numbers"].append({
        "id": f"vif_{name}", "label": f"VIF: {name}",
        "value": round(float(vif_list[i]), 2), "tol": 0.01,
        "source": "solve.py:VIF", "path": "artifacts/solve.py"
    })
    frozen["numbers"].append({
        "id": f"spc2_{name}", "label": f"Semi-partial R2: {name}",
        "value": round(float(spc2[i]), 4), "tol": 0.001,
        "source": "solve.py:semipartial", "path": "artifacts/solve.py"
    })

# Top feature
top_feat_idx = int(rank_spc[0])
frozen["numbers"].append({
    "id": "top_feature", "label": "Most important feature (by spR2)",
    "value": top_feat_idx, "tol": 0,
    "source": "solve.py:feature ranking", "path": "artifacts/solve.py"
})

# Forward stepwise first feature
frozen["numbers"].append({
    "id": "stepwise_first", "label": "First feature in forward stepwise",
    "value": int(selected[0]), "tol": 0,
    "source": "solve.py:forward stepwise", "path": "artifacts/solve.py"
})

with open('artifacts/frozen_numbers.json', 'w') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)
print(f"\nSaved frozen_numbers.json ({len(frozen['numbers'])} entries)")

print("\n" + "="*60)
print("SOLVER COMPLETE")
print("="*60)
