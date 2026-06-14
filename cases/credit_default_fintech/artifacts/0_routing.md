# Routing Plan — 信用卡违约预测（信用风险评分）

## Problem Classification

| Dimension | Classification | Evidence |
|-----------|---------------|----------|
| Primary type | **Data-driven / Classification (数据型·二分类)** | 30,000 条结构化客户数据，标签 `default.payment.next.month` (0/1)，预测下月是否违约 |
| Paradigm | **Data-driven** | 无物理机制；违约概率必须从历史还款行为 + 人口属性中统计推断 |
| Secondary type | Risk scoring / Binary classification / Feature importance | Q1 = 预测建模，Q2 = 特征归因，Q3 = 不平衡评估，Q4 = 合规审计 |
| Confidence | **High** | UCI 经典数据集，学术界广泛使用，题型明确 |

## Summon Strategy

| Order | Agent | Why This Agent | Key Task |
|-------|-------|---------------|----------|
| 1 | Analyst | 问题拆解 | 拆 Q1–Q4，定义"违约"和"信用评分"，列出假设，标记准确率陷阱和合规风险 |
| 2 | **Scout (heavy)** | 数据质量 + 合规敏感属性 | 字段文档，PAY_0..6 编码含义，类别不平衡诊断，**敏感属性 (SEX/AGE/EDUCATION) 标记** |
| 3 | Modeler (stats/ML) | 分类模型 | Logistic Regression baseline → XGBoost/RF 对比，特征重要性，类别不平衡处理 (SMOTE/class_weight) |
| 4 | Solver (heavy) | 银行级评估指标 | **AUC、KS statistic、Precision-Recall 曲线、混淆矩阵、召回率、精确率、特征重要性**；不只看准确率 |
| 5 | **Critic (上线评审)** | ⭐ 银行模型治理 | **准确率陷阱 + 数据泄漏 + 公平合规 + 过拟合/阈值/校准** |
| 6 | Writer | 风控建模报告 | 标准结构，强调合规局限性和模型治理建议 |

## Collaboration Sequence

```
Analyst → Scout(heavy) → Modeler → Solver(heavy) → ⭐Critic(上线评审) → Writer
                                      ↑                    │
                                      └────────────────────┘ (if ❌, max 2 rounds)
```

**Special note on Critic (银行模型上线评审)**:
Critic 必须重点审计四个银行风控核心问题：
1. **准确率陷阱**：违约率 22%，全预测"不违约"也有 77.9% 准确率 → 必须用 AUC/KS/F1 评估
2. **数据泄漏**：PAY_0 等字段是否包含了未来信息（还款状态是当期还是前期的？）
3. **公平与合规**：SEX/AGE/EDUCATION 作为特征 → 真实银行场景涉嫌歧视
4. **过拟合/阈值/校准**：风控关心高风险客户的召回率和概率校准

## Dispatch Log

| Event | Agent | Status | Notes |
|-------|-------|--------|-------|
| Problem received | Router | ✅ | 数据型·二分类，confidence high |
| Routing plan generated | Router | ✅ | 6 agents summoned，Scout/Solver/Critic weighted heavy |
