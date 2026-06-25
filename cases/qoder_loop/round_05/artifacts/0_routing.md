# Routing Decision — Round 05

## Problem Classification
**Type**: 机理ODE (Mechanism/ODE)  
**Subtype**: 传染病动力学 SIR-V 模型

## Method Selection

### Primary Methods
1. **scipy.integrate.odeint** — 求解 SIR-V ODE 系统
2. **相平面分析** — S vs I 相图，观察系统轨迹
3. **敏感性分析** — R₀ 和 v 对峰值感染的影响热力图

### Secondary Methods
- 峰值检测（argmax + 插值）
- 群体免疫阈值计算（R_eff < 1 的临界条件）
- 二分搜索求最低接种速率 v_min

## Pipeline

```
Router (本题) 
  → Analyst (ODE 建模 + 参数校准)
    → Modeler (SIR-V 方程 + 群体免疫阈值)
      → Solver (odeint + 可视化 + 敏感性)
        → Critic (审计报告)
          → Writer (论文)
            → Judge (盲评)
```

## Key Challenges

1. **疫苗接种项的建模**：v·e·S/N 假设优先接种易感者，且接种速率受易感者比例限制
2. **群体免疫阈值**：R_eff = R₀ · S/N < 1 的临界条件，涉及 S 的动态变化
3. **敏感性分析的维度**：R₀ ∈ [1.5, 5.0] × v ∈ [0, 20000] 的二维热力图

## Auto-Confirm Checkpoints

- CP1 (Routing): ✅ Auto-confirmed
- CP2 (Analysis): ✅ Auto-confirmed
- CP3 (Model): ✅ Auto-confirmed
- CP4 (Results): ✅ Auto-confirmed
