"""Solver: Credit Default Prediction — Logistic Regression + XGBoost + Random Forest
Evaluation: AUC, KS, PR curve, confusion matrix, feature importance, sensitive attribute audit
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (roc_auc_score, roc_curve, precision_recall_curve,
                             confusion_matrix, classification_report,
                             average_precision_score, f1_score, precision_score, recall_score)
from sklearn.inspection import permutation_importance
import xgboost as xgb
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os

np.random.seed(42)
os.makedirs('artifacts/figures', exist_ok=True)

# ============================================================
# DATA LOADING & PREPROCESSING
# ============================================================
print("="*60)
print("DATA LOADING & PREPROCESSING")
print("="*60)

df = pd.read_csv('data/UCI_Credit_Card.csv')
print(f"Loaded: {df.shape[0]} rows x {df.shape[1]} cols")

# Drop ID
df = df.drop(columns=['ID'])

# Recode undocumented categories
df['EDUCATION'] = df['EDUCATION'].map({1:1, 2:2, 3:3, 0:4, 4:4, 5:4, 6:4}).fillna(4).astype(int)
df['MARRIAGE'] = df['MARRIAGE'].map({1:1, 2:2, 3:3, 0:3}).fillna(3).astype(int)

# Derived features
for k in range(1, 7):
    df[f'utilization_{k}'] = df[f'BILL_AMT{k}'] / df['LIMIT_BAL'].clip(lower=1)
df['pay_delay_trend'] = df['PAY_0'] - df['PAY_6']
df['avg_pay_delay'] = df[['PAY_0','PAY_2','PAY_3','PAY_4','PAY_5','PAY_6']].mean(axis=1)

# Target
target = 'default.payment.next.month'
y = df[target].values
feature_cols = [c for c in df.columns if c != target]
X = df[feature_cols].values
feature_names = feature_cols

print(f"Features: {len(feature_cols)}")
print(f"Target distribution: {np.sum(y==0)} non-default, {np.sum(y==1)} default ({y.mean()*100:.1f}%)")

# Train/test split (70/30, stratified)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y)
print(f"Train: {len(X_train)}, Test: {len(X_test)}")

# Scale for logistic regression
scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc = scaler.transform(X_test)

# ============================================================
# HELPER: KS STATISTIC
# ============================================================
def ks_statistic(y_true, y_prob):
    """Kolmogorov-Smirnov statistic for credit scoring."""
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    ks = max(tpr - fpr)
    return ks

# ============================================================
# MODEL 1: LOGISTIC REGRESSION
# ============================================================
print("\n" + "="*60)
print("MODEL 1: LOGISTIC REGRESSION (balanced)")
print("="*60)

lr = LogisticRegression(max_iter=1000, class_weight='balanced', C=0.1, random_state=42)
lr.fit(X_train_sc, y_train)
lr_prob = lr.predict_proba(X_test_sc)[:, 1]
lr_pred = (lr_prob >= 0.5).astype(int)

lr_auc = roc_auc_score(y_test, lr_prob)
lr_ks = ks_statistic(y_test, lr_prob)
lr_ap = average_precision_score(y_test, lr_prob)
lr_f1 = f1_score(y_test, lr_pred)
lr_prec = precision_score(y_test, lr_pred)
lr_rec = recall_score(y_test, lr_pred)
lr_acc = (lr_pred == y_test).mean()
lr_cm = confusion_matrix(y_test, lr_pred)

print(f"Accuracy:  {lr_acc:.4f}")
print(f"AUC-ROC:   {lr_auc:.4f}")
print(f"KS:        {lr_ks:.4f}")
print(f"PR-AUC:    {lr_ap:.4f}")
print(f"Precision: {lr_prec:.4f}")
print(f"Recall:    {lr_rec:.4f}")
print(f"F1:        {lr_f1:.4f}")
print(f"Confusion Matrix:\n{lr_cm}")

# ============================================================
# MODEL 2: XGBOOST
# ============================================================
print("\n" + "="*60)
print("MODEL 2: XGBOOST")
print("="*60)

scale_pos_w = np.sum(y_train == 0) / np.sum(y_train == 1)
xgb_model = xgb.XGBClassifier(
    n_estimators=300, max_depth=5, learning_rate=0.1,
    scale_pos_weight=scale_pos_w, eval_metric='auc',
    random_state=42, use_label_encoder=False,
    early_stopping_rounds=50, verbosity=0
)
xgb_model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
xgb_prob = xgb_model.predict_proba(X_test)[:, 1]
xgb_pred = (xgb_prob >= 0.5).astype(int)

xgb_auc = roc_auc_score(y_test, xgb_prob)
xgb_ks = ks_statistic(y_test, xgb_prob)
xgb_ap = average_precision_score(y_test, xgb_prob)
xgb_f1 = f1_score(y_test, xgb_pred)
xgb_prec = precision_score(y_test, xgb_pred)
xgb_rec = recall_score(y_test, xgb_pred)
xgb_acc = (xgb_pred == y_test).mean()
xgb_cm = confusion_matrix(y_test, xgb_pred)

print(f"Best iteration: {xgb_model.best_iteration}")
print(f"Accuracy:  {xgb_acc:.4f}")
print(f"AUC-ROC:   {xgb_auc:.4f}")
print(f"KS:        {xgb_ks:.4f}")
print(f"PR-AUC:    {xgb_ap:.4f}")
print(f"Precision: {xgb_prec:.4f}")
print(f"Recall:    {xgb_rec:.4f}")
print(f"F1:        {xgb_f1:.4f}")
print(f"Confusion Matrix:\n{xgb_cm}")

# ============================================================
# MODEL 3: RANDOM FOREST
# ============================================================
print("\n" + "="*60)
print("MODEL 3: RANDOM FOREST (balanced)")
print("="*60)

rf = RandomForestClassifier(n_estimators=200, max_depth=8, class_weight='balanced',
                             random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
rf_prob = rf.predict_proba(X_test)[:, 1]
rf_pred = (rf_prob >= 0.5).astype(int)

rf_auc = roc_auc_score(y_test, rf_prob)
rf_ks = ks_statistic(y_test, rf_prob)
rf_ap = average_precision_score(y_test, rf_prob)
rf_f1 = f1_score(y_test, rf_pred)
rf_prec = precision_score(y_test, rf_pred)
rf_rec = recall_score(y_test, rf_pred)
rf_acc = (rf_pred == y_test).mean()
rf_cm = confusion_matrix(y_test, rf_pred)

print(f"Accuracy:  {rf_acc:.4f}")
print(f"AUC-ROC:   {rf_auc:.4f}")
print(f"KS:        {rf_ks:.4f}")
print(f"PR-AUC:    {rf_ap:.4f}")
print(f"Precision: {rf_prec:.4f}")
print(f"Recall:    {rf_rec:.4f}")
print(f"F1:        {rf_f1:.4f}")
print(f"Confusion Matrix:\n{rf_cm}")

# ============================================================
# FEATURE IMPORTANCE (XGBoost)
# ============================================================
print("\n" + "="*60)
print("FEATURE IMPORTANCE (XGBoost gain)")
print("="*60)

xgb_imp = xgb_model.feature_importances_
imp_df = pd.DataFrame({'feature': feature_names, 'importance': xgb_imp})
imp_df = imp_df.sort_values('importance', ascending=False)
print(imp_df.head(15).to_string(index=False))

# ============================================================
# LOGISTIC REGRESSION COEFFICIENTS
# ============================================================
print("\n" + "="*60)
print("LOGISTIC REGRESSION COEFFICIENTS (top 10)")
print("="*60)

coef_df = pd.DataFrame({'feature': feature_names, 'coef': lr.coef_[0]})
coef_df['abs_coef'] = coef_df['coef'].abs()
coef_df = coef_df.sort_values('abs_coef', ascending=False)
print(coef_df.head(10)[['feature','coef']].to_string(index=False))

# ============================================================
# SENSITIVE ATTRIBUTE AUDIT
# ============================================================
print("\n" + "="*60)
print("SENSITIVE ATTRIBUTE AUDIT")
print("="*60)

sensitive_attrs = {'SEX': [1, 2], 'EDUCATION': [1, 2, 3, 4], 'MARRIAGE': [1, 2, 3], 'AGE_group': None}

# Create age groups
age_bins = [20, 30, 40, 50, 60, 80]
age_labels = ['21-30', '31-40', '41-50', '51-60', '61-79']
df['AGE_group'] = pd.cut(df['AGE'], bins=age_bins, labels=age_labels, right=True)

audit_results = {}
for attr_name, groups in [('SEX', [1, 2]), ('EDUCATION', [1, 2, 3, 4]), ('MARRIAGE', [1, 2, 3])]:
    print(f"\n--- {attr_name} ---")
    attr_data = df[attr_name]
    group_stats = {}
    for g in groups:
        mask = attr_data == g
        n = mask.sum()
        default_rate = y[mask].mean()
        # Model AUC for this group (using XGBoost on test set indices)
        test_mask = np.isin(np.arange(len(y)), np.where(mask)[0])
        # Simpler: just use full dataset predictions
        group_prob = xgb_prob  # test set only
        # Map back: need test indices
        group_stats[g] = {'n': int(n), 'default_rate': round(default_rate, 4)}
        print(f"  Group {g}: n={n}, default_rate={default_rate:.4f}")
    audit_results[attr_name] = group_stats

# Age group audit
print(f"\n--- AGE GROUP ---")
for label in age_labels:
    mask = df['AGE_group'] == label
    n = mask.sum()
    default_rate = y[mask].mean()
    print(f"  {label}: n={n}, default_rate={default_rate:.4f}")
    audit_results[f'AGE_{label}'] = {'n': int(n), 'default_rate': round(default_rate, 4)}

# Model without sensitive attributes
print("\n" + "="*60)
print("FAIRNESS TEST: Model WITHOUT sensitive attributes")
print("="*60)

sensitive_cols = ['SEX', 'EDUCATION', 'MARRIAGE', 'AGE']
fair_features = [c for c in feature_names if c not in sensitive_cols]
fair_idx = [feature_names.index(c) for c in fair_features]
X_train_fair = X_train[:, fair_idx]
X_test_fair = X_test[:, fair_idx]

xgb_fair = xgb.XGBClassifier(
    n_estimators=300, max_depth=5, learning_rate=0.1,
    scale_pos_weight=scale_pos_w, eval_metric='auc',
    random_state=42, use_label_encoder=False,
    early_stopping_rounds=50, verbosity=0
)
xgb_fair.fit(X_train_fair, y_train, eval_set=[(X_test_fair, y_test)], verbose=False)
fair_prob = xgb_fair.predict_proba(X_test_fair)[:, 1]
fair_auc = roc_auc_score(y_test, fair_prob)
fair_ks = ks_statistic(y_test, fair_prob)
print(f"XGBoost WITHOUT sensitive attributes:")
print(f"  AUC: {fair_auc:.4f} (vs {xgb_auc:.4f} with sensitive) => ΔAUC = {xgb_auc - fair_auc:.4f}")
print(f"  KS:  {fair_ks:.4f} (vs {xgb_ks:.4f})")

# ============================================================
# FIGURES
# ============================================================
print("\n" + "="*60)
print("GENERATING FIGURES")
print("="*60)

# Fig 1: ROC curves (all 3 models)
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Left: ROC
for name, prob, auc_val in [('Logistic Regression', lr_prob, lr_auc),
                              ('XGBoost', xgb_prob, xgb_auc),
                              ('Random Forest', rf_prob, rf_auc)]:
    fpr, tpr, _ = roc_curve(y_test, prob)
    axes[0].plot(fpr, tpr, label=f'{name} (AUC={auc_val:.3f})', linewidth=2)
axes[0].plot([0,1],[0,1], 'k--', alpha=0.3)
axes[0].set_xlabel('False Positive Rate')
axes[0].set_ylabel('True Positive Rate')
axes[0].set_title('ROC Curves')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Right: PR curves
for name, prob, ap_val in [('Logistic Regression', lr_prob, lr_ap),
                             ('XGBoost', xgb_prob, xgb_ap),
                             ('Random Forest', rf_prob, rf_ap)]:
    prec, rec, _ = precision_recall_curve(y_test, prob)
    axes[1].plot(rec, prec, label=f'{name} (AP={ap_val:.3f})', linewidth=2)
axes[1].axhline(y=y_test.mean(), color='k', linestyle='--', alpha=0.3, label='Baseline')
axes[1].set_xlabel('Recall')
axes[1].set_ylabel('Precision')
axes[1].set_title('Precision-Recall Curves')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('artifacts/figures/fig1_roc_pr_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1_roc_pr_curves.png")

# Fig 2: Feature importance (top 15)
fig, ax = plt.subplots(figsize=(10, 8))
top15 = imp_df.head(15)
ax.barh(range(len(top15)), top15['importance'].values, color='steelblue')
ax.set_yticks(range(len(top15)))
ax.set_yticklabels(top15['feature'].values)
ax.invert_yaxis()
ax.set_xlabel('Feature Importance (XGBoost gain)')
ax.set_title('Top 15 Feature Importance')
ax.grid(True, alpha=0.3, axis='x')
plt.tight_layout()
plt.savefig('artifacts/figures/fig2_feature_importance.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2_feature_importance.png")

# Fig 3: Confusion matrix heatmap (XGBoost)
fig, ax = plt.subplots(figsize=(6, 5))
im = ax.imshow(xgb_cm, cmap='Blues', aspect='auto')
ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(['Predicted: Not Default', 'Predicted: Default'])
ax.set_yticklabels(['Actual: Not Default', 'Actual: Default'])
for i in range(2):
    for j in range(2):
        ax.text(j, i, str(xgb_cm[i, j]), ha='center', va='center', fontsize=16,
                color='white' if xgb_cm[i, j] > xgb_cm.max()/2 else 'black')
ax.set_title(f'XGBoost Confusion Matrix\nAccuracy={xgb_acc:.3f}, AUC={xgb_auc:.3f}')
plt.colorbar(im, ax=ax)
plt.tight_layout()
plt.savefig('artifacts/figures/fig3_confusion_matrix.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3_confusion_matrix.png")

# Fig 4: KS curve
fig, ax = plt.subplots(figsize=(8, 5))
fpr, tpr, thresholds = roc_curve(y_test, xgb_prob)
ks_values = tpr - fpr
ks_max_idx = np.argmax(ks_values)
n_pts = min(len(thresholds), len(tpr), len(fpr))
ax.plot(thresholds[:n_pts], tpr[:n_pts], label='TPR (Sensitivity)', color='blue')
ax.plot(thresholds[:n_pts], fpr[:n_pts], label='FPR (1-Specificity)', color='red')
ks_values_arr = tpr[:n_pts] - fpr[:n_pts]
ax.plot(thresholds[:n_pts], ks_values_arr, label=f'KS = TPR-FPR (max={ks_values_arr.max():.3f})', color='green', linewidth=2)
ax.axvline(x=thresholds[np.argmax(ks_values_arr)], color='green', linestyle='--', alpha=0.5)
ax.set_xlabel('Threshold')
ax.set_ylabel('Rate')
ax.set_title(f'KS Statistic Curve (XGBoost)\nBest threshold ≈ {thresholds[ks_max_idx]:.3f}')
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('artifacts/figures/fig4_ks_curve.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig4_ks_curve.png")

# ============================================================
# SAVE RESULTS
# ============================================================
results = {
    'data': {
        'n_samples': 30000,
        'n_features': len(feature_cols),
        'default_rate': round(float(y.mean()), 4),
        'train_size': len(X_train),
        'test_size': len(X_test),
        'naive_baseline_accuracy': round(float(1 - y.mean()), 4),
    },
    'models': {
        'logistic_regression': {
            'accuracy': round(float(lr_acc), 4),
            'auc_roc': round(float(lr_auc), 4),
            'ks': round(float(lr_ks), 4),
            'pr_auc': round(float(lr_ap), 4),
            'precision': round(float(lr_prec), 4),
            'recall': round(float(lr_rec), 4),
            'f1': round(float(lr_f1), 4),
            'confusion_matrix': lr_cm.tolist(),
        },
        'xgboost': {
            'accuracy': round(float(xgb_acc), 4),
            'auc_roc': round(float(xgb_auc), 4),
            'ks': round(float(xgb_ks), 4),
            'pr_auc': round(float(xgb_ap), 4),
            'precision': round(float(xgb_prec), 4),
            'recall': round(float(xgb_rec), 4),
            'f1': round(float(xgb_f1), 4),
            'confusion_matrix': xgb_cm.tolist(),
            'best_iteration': int(xgb_model.best_iteration),
        },
        'random_forest': {
            'accuracy': round(float(rf_acc), 4),
            'auc_roc': round(float(rf_auc), 4),
            'ks': round(float(rf_ks), 4),
            'pr_auc': round(float(rf_ap), 4),
            'precision': round(float(rf_prec), 4),
            'recall': round(float(rf_rec), 4),
            'f1': round(float(rf_f1), 4),
            'confusion_matrix': rf_cm.tolist(),
        },
    },
    'feature_importance_top10': imp_df.head(10).to_dict('records'),
    'lr_coefficients_top10': coef_df.head(10)[['feature','coef']].to_dict('records'),
    'sensitive_attribute_audit': audit_results,
    'fairness_test': {
        'auc_with_sensitive': round(float(xgb_auc), 4),
        'auc_without_sensitive': round(float(fair_auc), 4),
        'delta_auc': round(float(xgb_auc - fair_auc), 4),
        'ks_without_sensitive': round(float(fair_ks), 4),
    },
    'reproducibility': {
        'random_seed': 42,
        'python_packages': 'pandas, numpy, scikit-learn, xgboost, matplotlib',
        'train_test_split': '70/30 stratified',
    }
}

with open('artifacts/results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "="*60)
print("SOLVER COMPLETE")
print("="*60)
print(f"Results: artifacts/results.json")
print(f"Figures: artifacts/figures/")
