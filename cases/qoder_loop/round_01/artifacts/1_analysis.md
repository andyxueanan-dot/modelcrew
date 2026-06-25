# R1 Analysis — 研发项目组合优选

## Sub-Questions

| ID | Restatement | Type | Priority |
|----|-----------|------|----------|
| Q1 | 在 budget≤150 + staff≤40 + dependency(B→D) 下最大化总收益 | Required | ⭐⭐⭐ |
| Q2 | 最少预算使得 |selected|≥3 且 总收益≥350 | Required | ⭐⭐ |
| Q3 | C 收益 150→280 后最优组合是否改变 | Required | ⭐⭐ |

## Key Definitions

| Term | Definition |
|------|-----------|
| 0-1 变量 x_i | 1=立项, 0=不立项 |
| 依赖约束 | x_D ≤ x_B (选 D 则必须选 B) |
| 总收益 | Σ r_i · x_i |

## Assumptions

| # | Assumption | Fragility |
|---|-----------|-----------|
| A1 | 预期收益为确定性参数，无随机性 | 高——现实中收益是预期值 |
| A2 | 项目间除 B→D 外无其他依赖或互斥 | 中 |
| A3 | 预算和人力为硬约束，不可突破 | 低 |
| A4 | 项目收益可加（无协同/冲突） | 中——可能有 1+1>2 |

## Traps

1. **依赖关系遗漏**：D 的前置是 B，如果忘了 x_D ≤ x_B 会得出非法解
2. **双约束**：预算和人力同时约束，不能只看一个
3. **Q2 是 min-cost 而非 max-profit**：目标函数方向不同
