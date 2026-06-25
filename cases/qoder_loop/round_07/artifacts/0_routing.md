# Routing Decision — Round 07

## Problem Classification
**Type**: 优化 (Optimization)  
**Subtype**: 带容量约束的设施选址问题 (Capacitated Facility Location Problem)

## Method Selection

### Primary Methods
1. **完全枚举** — 2^8 = 256 种开放组合
2. **运输问题** — 对每种开放组合求解最小运输成本
3. **可行性筛选** — 容量 + 预算 + 最少开放数

### Secondary Methods
- Pareto 前沿（总成本 vs 开放数）
- 敏感性分析（预算、运输单价）
- 影子价格（约束松紧度分析）

## Pipeline

```
Router (本题) 
  → Analyst (选址建模 + 约束设计)
    → Modeler (0-1 IP + 运输子问题)
      → Solver (枚举 + 运输求解 + 可视化)
        → Critic (审计报告)
          → Writer (论文)
            → Judge (盲评)
```

## Key Challenges

1. **运输子问题的求解**：给定开放设施集合，如何分配市场到设施？（贪心 vs LP）
2. **约束松紧度**：预算 3000 万是否紧致？容量是否接近瓶颈？
3. **Pareto 前沿**：开放更多设施 → 运输成本下降但建设成本上升

## Auto-Confirm Checkpoints

- CP1 (Routing): ✅ Auto-confirmed
- CP2 (Analysis): ✅ Auto-confirmed
- CP3 (Model): ✅ Auto-confirmed
- CP4 (Results): ✅ Auto-confirmed
