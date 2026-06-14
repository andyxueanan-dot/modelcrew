# Solver Results — 信用卡违约预测

## 数据概况
- 样本量：30,000（Train 21,000 / Test 9,000，70/30 分层划分）
- 特征数：31（原始 24 + 派生 7：utilization_1..6, avg_pay_delay, pay_delay_trend）
- 违约率：22.1%（6,636/30,000）
- Naive baseline（全预测"不违约"）：accuracy = 77.9%

## 模型对比

| 指标 | Logistic Regression | XGBoost | Random Forest |
|------|-------------------|---------|---------------|
| **Accuracy** | 0.6942 | 0.7603 | **0.7824** |
| **AUC-ROC** | 0.7169 | **0.7815** | 0.7792 |
| **KS** | 0.3677 | 0.4223 | **0.4257** |
| **PR-AUC** | 0.4953 | **0.5540** | 0.5519 |
| **Precision** | 0.3814 | 0.4683 | **0.5072** |
| **Recall** | 0.6148 | **0.6163** | 0.5841 |
| **F1** | 0.4708 | 0.5322 | **0.5430** |

### 关键发现
- **所有模型的 accuracy 均低于 naive baseline (77.9%)**，但 AUC 和 KS 才是真正有意义的指标
- XGBoost 在 AUC（0.782）上最优，KS = 0.422（银行模型一般要求 KS > 0.30，达标）
- Random Forest 在 F1（0.543）和 Precision（0.507）上最优
- **Recall 均在 0.58–0.62 范围**：约 40% 的违约客户被漏检——风控角度看这是核心风险

## 混淆矩阵（XGBoost，threshold=0.5）

| | Predicted: Not Default | Predicted: Default |
|--|----------------------|-------------------|
| **Actual: Not Default** | 5,616 (TN) | 1,393 (FP) |
| **Actual: Default** | 764 (FN) | 1,227 (TP) |

- 1,393 位好客户被误判为违约（假阳性）→ 可能错失优质客户
- 764 位违约客户被漏判（假阴性）→ 信用风险敞口

## 特征重要性（XGBoost Gain Top 10）

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | **PAY_0** | 0.371 |
| 2 | avg_pay_delay | 0.130 |
| 3 | PAY_2 | 0.034 |
| 4 | PAY_AMT2 | 0.032 |
| 5 | PAY_3 | 0.030 |
| 6 | PAY_AMT3 | 0.026 |
| 7 | BILL_AMT1 | 0.022 |
| 8 | utilization_2 | 0.021 |
| 9 | LIMIT_BAL | 0.021 |
| 10 | PAY_AMT1 | 0.020 |

→ **PAY_0 单独贡献了 37% 的预测力**，加上 avg_pay_delay（13%），还款历史特征占比超过 50%。

## Logistic Regression 系数（Top 5）

| Feature | Coefficient | Interpretation |
|---------|------------|----------------|
| PAY_0 | +0.369 | 逾期月数每增 1，违约 odds 增 45% |
| utilization_1 | −0.241 | 高额度利用率反而降低违约概率（可能混淆了高消费=高收入） |
| PAY_AMT2 | −0.225 | 上月还款金额越高，违约风险越低 |
| pay_delay_trend | +0.197 | 还款延迟恶化趋势增加违约风险 |
| LIMIT_BAL | −0.185 | 额度越高（收入越高），违约越低 |

## 敏感属性审计

| 属性 | 组别 | n | 违约率 | 差异 |
|------|------|---|--------|------|
| **SEX** | Male (1) | 11,888 | **24.2%** | +3.4pp vs Female |
| | Female (2) | 18,112 | 20.8% | |
| **EDUCATION** | Graduate (1) | 10,585 | 19.2% | — |
| | University (2) | 14,030 | 23.7% | — |
| | High School (3) | 4,917 | **25.2%** | 最高风险 |
| | Other (4) | 468 | 7.1% | 样本小 |
| **MARRIAGE** | Married (1) | 13,659 | 23.5% | — |
| | Single (2) | 15,964 | 20.9% | — |
| | Other (3) | 377 | 23.6% | — |
| **AGE** | 21–30 | 11,013 | 22.4% | — |
| | 31–40 | 10,713 | 20.4% | 最低风险 |
| | 41–50 | 6,005 | 23.3% | — |
| | 51–60 | 1,997 | **25.2%** | — |
| | 61–79 | 272 | **26.8%** | 最高风险（样本小） |

### Fairness Test: 移除敏感属性后的模型

| 指标 | 含敏感属性 | 不含敏感属性 | Δ |
|------|-----------|------------|---|
| AUC | 0.7815 | 0.7789 | **−0.003** |
| KS | 0.4223 | 0.4234 | +0.001 |

→ **移除 SEX/AGE/EDUCATION/MARRIAGE 后 AUC 仅下降 0.003**——这些属性对模型预测力几乎没有贡献。这意味着可以安全地移除它们以满足合规要求，而不牺牲模型性能。

## 可复现性

- Random seed: 42
- Python packages: pandas, numpy, scikit-learn, xgboost, matplotlib
- Train/test split: 70/30 stratified
- XGBoost early stopping: 50 rounds (best iteration = 43)
- Output: `results.json`, `figures/fig1_roc_pr_curves.png`, `fig2_feature_importance.png`, `fig3_confusion_matrix.png`, `fig4_ks_curve.png`
