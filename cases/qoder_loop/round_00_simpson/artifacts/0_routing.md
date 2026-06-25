# Routing Plan — 派单策略 A/B 评估（辛普森悖论）

## Problem Classification

| Dimension | Classification | Evidence |
|-----------|---------------|----------|
| Primary type | **Discrete / Statistical (离散型·统计推断)** | 二项分布比例比较（按时送达率），分层分析，因果推断 |
| Paradigm | **Hypothesis testing + Causal inference** | 需要从汇总数据 vs 分层数据的矛盾中识别辛普森悖论，做出因果解释 |
| Secondary type | Proportion comparison / Stratified analysis / Decision analysis | Q1 = 统计检验 + 因果论证，Q2 = 决策建议，Q3 = 敏感性分析 |
| Confidence | **High** | 经典辛普森悖论结构，2×2×2 列联表，方法论成熟 |

## Summon Strategy

| Order | Agent | Why This Agent | Key Task |
|-------|-------|---------------|----------|
| 1 | Analyst | 问题拆解 | 识别辛普森悖论陷阱，拆 Q1/Q2/Q3，定义"更优"的操作化标准 |
| 2 | Modeler | 方法选择 | 2-3 候选方法（比例 z 检验 / Mantel-Haenszel / Bayesian），选型 |
| 3 | Solver | 真算 | 汇总 vs 分层比例检验，置信区间，效应量，可视化，frozen_numbers |
| 4 | **Critic** | ⭐ 核心关卡 | 拦截"A 更优"的直觉结论；审计因果推断的逻辑链；检验分层口径敏感性 |
| 5 | Writer | 论文 | 清晰呈现悖论结构，诚实报告分层 vs 汇总的矛盾 |
| 6 | **Judge** | 🏆 模拟评委 | 盲评审打分，预估奖级 |

## Collaboration Sequence

```
Analyst ──[CP1 确认]──→ Modeler ──[CP2 确认]──→ Solver ──→ ⭐Critic ──→ Writer ──→ ⚖️Judge
```

## Dispatch Log

| Event | Agent | Status | Notes |
|-------|-------|--------|-------|
| Problem received | Router | ✅ | 离散型·统计推断，辛普森悖论，confidence high |
| Routing plan generated | Router | ✅ | 6 agents summoned, CP1+CP2 两道确认门 |
