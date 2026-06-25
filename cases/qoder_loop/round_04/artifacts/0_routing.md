# Routing Decision — Round 04

## Problem Classification
**Type**: 图论网络 (Graph/Network)  
**Subtype**: 供应链网络韧性评估 (Supply Chain Network Resilience)

## Method Selection

### Primary Methods
1. **Dijkstra 最短路径算法** — 求解 S1→R1 的最短路径
2. **中心性分析** — 度中心性、介数中心性、接近中心性
3. **节点失效模拟** — 移除 M1 后重新计算最短路径

### Secondary Methods
- 网络可视化（邻接矩阵 + 节点中心性热力图）
- 路径可靠性计算（边可靠性乘积）
- 网络连通性分析（移除节点后的连通分量）

## Pipeline

```
Router (本题) 
  → Analyst (网络拓扑分析 + 关键节点识别)
    → Modeler (Dijkstra + 中心性 + 失效模拟)
      → Solver (数值计算 + 可视化)
        → Critic (审计报告)
          → Writer (论文)
            → Judge (盲评)
```

## Key Challenges

1. **M1 是瓶颈吗？** — M1 连接 S1/S2 到 D1/D2，可能是高介数节点
2. **冗余路径** — S1→R1 是否有多条替代路径？成本和可靠性如何权衡？
3. **可靠性 vs 成本** — 最短路径不一定是最可靠路径

## Auto-Confirm Checkpoints

- CP1 (Routing): ✅ Auto-confirmed
- CP2 (Analysis): ✅ Auto-confirmed
- CP3 (Model): ✅ Auto-confirmed
- CP4 (Results): ✅ Auto-confirmed
