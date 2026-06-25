# R1 Model — 农业种植方案优化

## 候选方法
| # | 方法 | 优点 | 缺点 |
|---|------|------|------|
| M1 | 完全枚举 (4^3=64) | 保证全局最优, 透明可验证 | 仅适合小规模 |
| M2 | 整数规划 (scipy/PuLP) | 通用求解器 | 需要额外依赖 |
| M3 | 遗传算法/启发式 | 可扩展 | 不保证全局最优 |

## 选型: M1 完全枚举

理由: 3地块×4作物=64种分配, 枚举保证全局最优且便于Q2/Q3敏感性分析。

## 数学模型

**决策变量**: x_{ij} ∈ {0,1}, i=地块, j=作物. 每地块 Σ_j x_{ij} = 1.

**目标函数**: max Σ_i Σ_j x_{ij} · Area_i · Profit_j
其中 Profit_j = Yield_j × Price_j - SeedCost_j

**约束**:
- Σ_i Σ_j x_{ij} · Area_i · WaterAdj_i · Water_j ≤ 100000 (用水)
- Σ_i Σ_j x_{ij} · Area_i · Fert_j ≤ 12000 (化肥)
- Σ_i Σ_j x_{ij} · Area_i · Yield_j · IsGrain_j ≥ 80000 (粮食)
- 土壤适配: x_{ij}=0 if SoilQuality_i < MinSoil_j

## 待审计结论
| # | 结论 | Confidence |
|---|------|-----------|
| C1 | Q1最优方案及净利润 | High (exact) |
| C2 | Q2用水影子价格 | High (exact) |
| C3 | Q3方案是否改变 | High (exact) |
| C4 | 约束紧致性分析 | High |
| C5 | 各作物单位面积利润排名 | High |
