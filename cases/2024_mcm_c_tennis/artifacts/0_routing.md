# Routing Plan — 2024 MCM Problem C: Momentum in Tennis

## Problem Classification

| Dimension | Classification | Evidence |
|-----------|---------------|----------|
| Primary type | **Data-driven (数据型)** | Problem provides a 7284-row CSV of point-by-point match data; all 4 sub-questions ask to model/predict from data |
| Paradigm | **Data-driven** | No physical mechanism; momentum must be inferred from statistical patterns in sequential point outcomes |
| Secondary type | Prediction / Time-series / Classification | Q1 = quantification (index construction), Q2 = hypothesis testing, Q3 = prediction (swing detection), Q4 = generalizability |
| Confidence | **High** | Classic MCM-C data problem, well-documented dataset |

## Summon Strategy

| Order | Agent | Why This Agent | Key Task |
|-------|-------|---------------|----------|
| 1 | Analyst | Problem decomposition | Parse Q1–Q4, define "momentum" and "swing", list assumptions, flag hot-hand controversy |
| 2 | **Scout (heavy)** | Data is the core asset | Field documentation, quality diagnostics, derived features (point sequences, streak indicators, server advantage) |
| 3 | Modeler (stats/ML) | Build quantitative models | EWMA momentum index, logistic regression / random forest for swing prediction, runs test framework |
| 4 | **Critic (randomness / hot-hand)** | **Key gate for Q2** | Runs test vs shuffled baseline, test for hot-hand fallacy, audit all conclusions for overfitting and extrapolation |
| 5 | Writer | Competition paper | Standard MCM paper structure, polished abstract, honest limitations section |

## Collaboration Sequence

```
Analyst ──→ Scout(heavy) ──→ Modeler ──→ Critic ──→ Writer
                                  ↑          │
                                  └──────────┘ (if ❌, max 2 rounds)
```

**Special note on Q2 (hot-hand fallacy):**
This is the framework's highlight moment. The Modeler will likely build a momentum model that "proves" momentum exists. The Critic must then adversarially test this claim using:
1. Wald-Wolfowitz runs test on point sequences
2. Shuffled/permutation baseline comparison
3. Streak-length distribution vs geometric (memoryless) expectation

If the Critic falsifies the momentum claim for Q2, the Modeler must revise (Round 1). After Round 2, unresolved conclusions get annotated as uncertain in the paper.

## Dispatch Log

| Event | Agent | Status | Notes |
|-------|-------|--------|-------|
| Problem received | Router | ✅ | MCM-C data-driven, confidence high |
| Routing plan generated | Router | ✅ | 5 agents summoned, Scout and Critic weighted heavy |
