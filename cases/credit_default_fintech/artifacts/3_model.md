# Model Definitions — 信用卡违约预测

## Method Selection Rationale

| Model | Why | Alternatives | Trade-off |
|-------|-----|-------------|-----------|
| **Logistic Regression (baseline)** | Interpretable coefficients; industry standard for credit scoring; regulatory-friendly | — | May underfit non-linear relationships |
| **XGBoost (primary)** | State-of-the-art tabular data; built-in feature importance; handles class imbalance via scale_pos_weight | Random Forest, LightGBM | Less interpretable than logistic regression; requires hyperparameter tuning |
| **Random Forest (comparison)** | Robust baseline; less sensitive to hyperparameters | — | Slower than XGBoost; less competitive on tabular data |

## Model 1: Logistic Regression (Baseline)

### Variables
| Symbol | Meaning | Type | Domain |
|--------|---------|------|--------|
| X | Feature vector (23 features after dropping ID) | Input | ℝ^d |
| y | Default indicator (0/1) | Target | {0, 1} |
| P(y=1|X) | Predicted default probability | Output | [0, 1] |

### Equation
```
P(y=1|X) = σ(w^T X + b)
```
where σ is the logistic sigmoid function.

### Handling Class Imbalance
- `class_weight='balanced'`: weights inversely proportional to class frequency
- Effective weight for class 1 (default): 30000 / (2 × 6636) ≈ 2.26
- Effective weight for class 0 (non-default): 30000 / (2 × 23364) ≈ 0.64

## Model 2: XGBoost (Primary)

### Key Hyperparameters
| Parameter | Value | Rationale |
|-----------|-------|-----------|
| n_estimators | 300 | Balance between performance and overfitting |
| max_depth | 5 | Moderate depth; credit data has moderate interactions |
| learning_rate | 0.1 | Standard; allows convergence |
| scale_pos_weight | 3.52 (= 23364/6636) | Handles class imbalance |
| eval_metric | 'auc' | Optimize for AUC directly |
| early_stopping_rounds | 50 | Prevent overfitting |

## Evaluation Metrics (银行级)

| Metric | Formula / Definition | Why This Metric |
|--------|---------------------|-----------------|
| **AUC-ROC** | Area under ROC curve | Discrimination ability; threshold-independent |
| **KS statistic** | max\|TPR − FPR\| across all thresholds | Standard credit scoring metric; max separation of good/bad |
| **Precision** | TP / (TP + FP) | Of predicted defaults, how many are real? (cost of false alarm) |
| **Recall (Sensitivity)** | TP / (TP + FN) | Of real defaults, how many did we catch? (risk coverage) |
| **F1-score** | 2 × P × R / (P + R) | Balance between precision and recall |
| **PR-AUC** | Area under precision-recall curve | Better than ROC-AUC for imbalanced data |
| **Confusion Matrix** | [TN, FP; FN, TP] | Full picture of prediction errors |

## Feature Importance Methods
1. **XGBoost built-in**: gain, weight, cover
2. **Permutation importance**: model-agnostic; shuffle each feature and measure AUC drop
3. **Logistic regression coefficients**: direct interpretation (sign = direction, magnitude = strength)

## Sensitive Attribute Audit Plan
For each protected attribute (SEX, AGE, EDUCATION, MARRIAGE):
1. Measure default rate by group (disparate impact analysis)
2. Measure model performance (AUC) by group
3. Train model WITHOUT sensitive attributes and compare performance
4. Report disparate impact ratio: P(default|protected) / P(default|reference)

## Conclusions Pending Audit

| # | Conclusion | Confidence | Depends On |
|---|-----------|-----------|-----------|
| C1 | XGBoost outperforms logistic regression on AUC | High | A2 (no data leakage), A6 (representative split) |
| C2 | PAY_0 is the single most important predictor | High | A2 (PAY_0 time anchor) |
| C3 | The model achieves AUC > 0.75, demonstrating meaningful predictive power | Medium–High | A2, A5, A6 |
| C4 | Credit utilization (BILL_AMT/LIMIT_BAL) and payment delay trend are important secondary predictors | Medium | A1, A2 |
| C5 | The model can be safely deployed for credit risk assessment | **Low** | A3 (sensitive attributes), A6 (no concept drift) — **Critic must audit fairness** |
| C6 | Removing sensitive attributes (SEX/AGE/EDUCATION) does not materially degrade model performance | Medium | To be tested empirically |
