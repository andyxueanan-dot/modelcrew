# Routing Decision — Round 08

## Problem Classification
**Type**: 数据 (Data)  
**Subtype**: 多重共线性与主成分回归 (Multicollinearity + PCR)

## Method Selection

### Primary Methods
1. **OLS 回归** — 全模型拟合 + VIF 诊断
2. **PCA + PCR** — 主成分降维 + 主成分回归
3. **逐步回归** — 前向选择筛选特征

### Secondary Methods
- 相关矩阵热力图
- VIF 计算
- 5 折交叉验证
- 碎石图（PCA 方差解释比例）

## Pipeline

```
Router (本题) 
  → Analyst (共线性诊断 + 降维策略)
    → Modeler (OLS + PCA + PCR + 逐步回归)
      → Solver (数值计算 + 交叉验证 + 可视化)
        → Critic (审计报告)
          → Writer (论文)
            → Judge (盲评)
```

## Key Challenges

1. **共线性诊断**：VIF 是否超过 10？哪些特征是共线性源头？
2. **PCR 的组件选择**：保留多少主成分？90% 方差解释需要几个？
3. **模型对比**：OLS、PCR、逐步回归的预测精度（RMSE）谁最优？

## Auto-Confirm Checkpoints

- CP1 (Routing): ✅ Auto-confirmed
- CP2 (Analysis): ✅ Auto-confirmed
- CP3 (Model): ✅ Auto-confirmed
- CP4 (Results): ✅ Auto-confirmed
