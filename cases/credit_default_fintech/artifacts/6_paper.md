# 信用风险评分模型的构建、评估与治理审计

## 基于 UCI 信用卡违约数据的预测建模与合规分析

---

## Abstract

Can a bank reliably predict which credit card customers will default next month? Using the UCI "default of credit card clients" dataset (30,000 Taiwanese credit card customers, 2005), we build and rigorously evaluate binary classification models for next-month default prediction. With a default rate of 22.1%, the naive baseline of "predict no default for everyone" achieves 77.9% accuracy — a vivid illustration of the accuracy trap in imbalanced classification. Our XGBoost model achieves an AUC-ROC of 0.782 and a KS statistic of 0.422, well above the industry threshold of 0.30, with the most recent payment status (PAY_0) contributing 37% of predictive power. However, our adversarial model governance audit reveals four deployment-blocking issues: (1) accuracy is a misleading metric under class imbalance (two of three models score below the naive baseline); (2) PAY_0's outsized importance raises potential data leakage concerns requiring sensitivity analysis; (3) the use of protected attributes (SEX, AGE, EDUCATION, MARRIAGE) violates fair lending regulations, though their removal costs only 0.003 AUC; and (4) predicted probabilities require calibration before use in risk-based pricing. We conclude that while the model demonstrates meaningful discriminatory power, it is not deployment-ready without addressing compliance, calibration, and concept drift — lessons that extend to any real-world credit scoring application.

---

## 1. Problem Restatement

Banks and credit card issuers need to assess the probability that a customer will default on their next payment. Accurate prediction enables proactive risk management: adjusting credit limits, flagging high-risk accounts, and allocating collection resources. The task is a binary classification problem — given 24 features describing a customer's credit profile, demographics, and recent payment history, predict whether they will default next month (1) or not (0).

The challenge extends beyond prediction accuracy. In real-world deployment, credit scoring models must satisfy regulatory requirements (fair lending laws, model validation standards) in addition to statistical performance. A model that discriminates based on gender or age, or that produces poorly calibrated probabilities, cannot be deployed regardless of its AUC.

## 2. Assumptions

**A1.** The dataset represents real credit card customers from a Taiwanese bank during April–September 2005. We assume the data accurately reflects customer behavior during this period.

**A2.** PAY_0 (most recent payment status) encodes information available at prediction time — specifically, the customer's payment behavior in the month prior to the prediction target. If PAY_0 overlaps temporally with the target period, it could constitute data leakage.

**A3.** All 24 features are assumed available at prediction time in a real deployment scenario.

**A4.** The binary default label accurately reflects bank records.

**A5.** Records are independent and identically distributed (i.i.d.).

**A6.** A random 70/30 train/test split adequately represents the distribution the model would encounter in deployment.

## 3. Data Description and Preparation

The UCI "default of credit card clients" dataset contains 30,000 records with 24 features and one binary target (`default.payment.next.month`). The default rate is 22.1% (6,636 / 30,000), creating a 3.5:1 class imbalance.

**Key feature groups:**
- Credit limit: LIMIT_BAL (10,000–1,000,000 TWD, mean 167,484)
- Demographics: SEX, EDUCATION, MARRIAGE, AGE (⚠️ protected attributes)
- Payment history: PAY_0 through PAY_6 (−2 to 8, encoding payment delay in months)
- Bill amounts: BILL_AMT1 through BILL_AMT6 (current and past 5 months)
- Payment amounts: PAY_AMT1 through PAY_AMT6

**Data quality:** Zero missing values across all columns. EDUCATION codes 0, 4, 5, 6 (468 records) and MARRIAGE code 0 (54 records) are undocumented and were recoded to "Other." No outliers were removed.

**Derived features:** We constructed credit utilization ratios (BILL_AMT_k / LIMIT_BAL), payment delay trend (PAY_0 − PAY_6), and average payment delay across 6 months.

**Critical data characteristic:** The naive baseline (predict all 0) achieves 77.9% accuracy. This means any evaluation relying solely on accuracy will be deeply misleading.

## 4. Model Formulation

### 4.1 Logistic Regression (Baseline)
Standard logistic regression with `class_weight='balanced'` to address class imbalance. Features are standardized via StandardScaler. Regularization: C=0.1.

### 4.2 XGBoost (Primary Model)
Gradient boosted trees with `scale_pos_weight = 3.52` (ratio of non-default to default). Hyperparameters: 300 max estimators, max_depth=5, learning_rate=0.1, early stopping at 50 rounds. Evaluation metric: AUC.

### 4.3 Random Forest (Comparison)
200 trees, max_depth=8, `class_weight='balanced'`. Provides a robust ensemble baseline.

### 4.4 Evaluation Framework

We evaluate using bank-standard metrics, explicitly **not** relying on accuracy:

- **AUC-ROC**: Threshold-independent discrimination ability
- **KS statistic**: Maximum separation between cumulative distributions of good and bad customers; industry threshold ≥ 0.30
- **Precision-Recall AUC**: More informative than ROC-AUC under class imbalance
- **Recall**: Of actual defaulters, what fraction does the model catch? (Risk coverage)
- **Precision**: Of predicted defaulters, what fraction actually default? (False alarm cost)
- **F1-score**: Harmonic mean of precision and recall
- **Confusion matrix**: Full error decomposition

## 5. Results

### 5.1 Model Comparison

| Metric | Naive Baseline | Logistic Reg. | XGBoost | Random Forest |
|--------|---------------|---------------|---------|---------------|
| Accuracy | 0.779 | 0.694 | 0.760 | 0.782 |
| **AUC-ROC** | 0.500 | 0.717 | **0.782** | 0.779 |
| **KS** | 0.000 | 0.368 | 0.422 | **0.426** |
| **PR-AUC** | 0.221 | 0.495 | **0.554** | 0.552 |
| Precision | — | 0.381 | 0.468 | **0.507** |
| Recall | 0.000 | 0.615 | **0.616** | 0.584 |
| F1 | 0.000 | 0.471 | 0.532 | **0.543** |

**Critical observation:** Two of three models (LR and XGBoost) have accuracy *below* the naive baseline of 77.9%. This is the accuracy trap in action — a model that correctly identifies 62% of defaulters (XGBoost) must flag many non-defaulters as risky, lowering accuracy. But its AUC of 0.782 and KS of 0.422 demonstrate genuine discriminatory power.

### 5.2 Feature Importance (XGBoost)

PAY_0 (most recent payment status) dominates with 37.1% of total feature importance, followed by average payment delay (13.0%). Payment history features collectively account for over 50% of predictive power. LIMIT_BAL (credit limit, a proxy for income) contributes 2.1%.

Logistic regression coefficients confirm: PAY_0 (coef = +0.369) increases default odds by 45% per unit; payment delay trend (+0.197) and LIMIT_BAL (−0.185) are the next strongest predictors.

### 5.3 Sensitive Attribute Audit

| Attribute | Group | Default Rate | Difference |
|-----------|-------|-------------|------------|
| SEX | Male | 24.2% | +3.4pp |
| | Female | 20.8% | |
| AGE | 61–79 | 26.8% | +6.4pp vs 31–40 |
| | 31–40 | 20.4% | |
| EDUCATION | High School | 25.2% | +6.0pp vs Graduate |
| | Graduate | 19.2% | |

**Fairness test:** Removing all four protected attributes (SEX, AGE, EDUCATION, MARRIAGE) from the model reduces AUC by only 0.003 (0.782 → 0.779). The cost of compliance is negligible. **Recommendation: remove these features before any deployment.**

## 6. Model Governance Audit

### 6.1 The Accuracy Trap
With 22.1% default rate, the naive baseline achieves 77.9% accuracy. Reporting accuracy without this baseline is misleading. All evaluation must prioritize AUC, KS, and F1.

### 6.2 PAY_0 Leakage Risk
PAY_0 accounts for 37% of predictive power — an unusually high concentration. If PAY_0 encodes information temporally overlapping with the target, it constitutes leakage. The UCI documentation does not precisely define the time anchor. A sensitivity analysis (model without PAY_0) is recommended.

### 6.3 Fairness and Compliance
Using SEX, AGE, EDUCATION, and MARRIAGE as features violates the US Equal Credit Opportunity Act (ECOA) and equivalent regulations in other jurisdictions. Since removing these features costs only 0.003 AUC, they should be excluded from any production model.

### 6.4 Calibration and Threshold Selection
XGBoost optimizes for AUC discrimination, not probability calibration. Predicted probabilities (e.g., P(default) = 0.70) may not correspond to actual 70% default rates. Platt scaling or isotonic regression calibration is needed before use in risk-based pricing. Additionally, the default threshold of 0.5 may not be optimal; banks should select thresholds based on their loss cost matrices.

### 6.5 Concept Drift
The data is from 2005 Taiwan. Economic conditions, regulations, and customer behavior have changed significantly. Any deployment would require retraining on recent data and ongoing performance monitoring.

## 7. Model Evaluation

**Strengths:**
- AUC of 0.782 and KS of 0.422 demonstrate meaningful predictive power, exceeding industry thresholds
- XGBoost outperforms logistic regression by a significant margin (ΔAUC = 0.065)
- Feature importance is interpretable and aligns with credit risk domain knowledge
- Class imbalance is properly addressed via balanced weights / scale_pos_weight
- Sensitive attribute removal costs near-zero AUC loss

**Weaknesses:**
- Recall of 0.616 means 38% of defaulters are missed — significant risk exposure
- PAY_0 dominance (37%) raises leakage concerns
- Probability calibration is absent
- Single-bank, single-country, 19-year-old data limits generalizability
- No cross-validation reported (single train/test split)

## 8. Conclusion

This work demonstrates that credit card default can be predicted with meaningful accuracy (AUC = 0.782, KS = 0.422) using payment history and credit limit features. The most recent payment status (PAY_0) is by far the strongest predictor, contributing 37% of model power.

However, our model governance audit — the kind of review that would precede actual deployment in a bank — identifies four blocking issues: protected attribute usage violates fair lending laws, PAY_0 may encode temporal leakage, predicted probabilities lack calibration, and the 2005 data is too old for 2024 deployment without retraining.

The most actionable finding is the sensitive attribute audit: removing SEX, AGE, EDUCATION, and MARRIAGE reduces AUC by only 0.003, making the compliance cost negligible. This should be standard practice in any credit scoring model.

The accuracy trap deserves special emphasis: in a 22% default rate setting, two of our three models scored below the naive baseline on accuracy while achieving strong AUC. Evaluating imbalanced classification models on accuracy alone is not just suboptimal — it is actively deceptive.

---

## References

- Yeh, I. C., & Lien, C. H. (2009). The comparisons of data mining techniques for the predictive accuracy of probability of default estimation by credit card users. *Expert Systems with Applications*, 36(2), 243–250.
- UCI Machine Learning Repository: Default of Credit Card Clients Data Set.
- US Equal Credit Opportunity Act (ECOA), 15 U.S.C. § 1691.
- Lundberg, S. M., & Lee, S. I. (2017). A unified approach to interpreting model predictions (SHAP). *NeurIPS*.

## Appendix

- `solve.py`: Full solver script with all computations
- `results.json`: Machine-readable results
- `figures/fig1_roc_pr_curves.png`: ROC and Precision-Recall curves
- `figures/fig2_feature_importance.png`: Top 15 feature importance
- `figures/fig3_confusion_matrix.png`: XGBoost confusion matrix
- `figures/fig4_ks_curve.png`: KS statistic curve with optimal threshold
