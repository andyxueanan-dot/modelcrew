# Model — 供应链网络图论模型

## 1. 网络表示

### 有向加权图 G = (V, E)
- **V** = {S1, S2, S3, M1, M2, M3, M4, D1, D2, D3, R1, R2}, |V| = 12
- **E** = 17 条有向边，每条边 e = (u, v) 有权重 w(e)（成本）和可靠性 r(e)
- **邻接矩阵** A: A[i][j] = w(i,j) if edge exists, else ∞

## 2. Dijkstra 最短路径

### 目标
min Σ w(e_i) for e_i in path(S1→R1)

### 算法
```
1. 初始化: dist[S1] = 0, dist[v] = ∞ for v ≠ S1
2. Priority queue Q = {S1}
3. While Q not empty:
   a. u = extract_min(Q)
   b. For each neighbor v of u:
      if dist[u] + w(u,v) < dist[v]:
         dist[v] = dist[u] + w(u,v)
         prev[v] = u
         Q.insert(v)
4. 回溯: R1 → prev[R1] → ... → S1
```

### 路径可靠性
R(path) = Π r(e_i) for e_i in path

## 3. 中心性指标

### 3.1 度中心性 (Degree Centrality)
对于有向图：
- 入度 (In-degree): C_in(v) = |{u : (u,v) ∈ E}|
- 出度 (Out-degree): C_out(v) = |{u : (v,u) ∈ E}|
- 总度: C_deg(v) = C_in(v) + C_out(v)

### 3.2 介数中心性 (Betweenness Centrality)
C_B(v) = Σ_{s≠v≠t} σ_st(v) / σ_st

其中：
- σ_st = s→t 的最短路径总数
- σ_st(v) = s→t 的最短路径中经过 v 的数量
- 归一化: C_B'(v) = C_B(v) / ((n-1)(n-2)/2)

### 3.3 接近中心性 (Closeness Centrality)
C_C(v) = (n-1) / Σ_{u≠v} d(v,u)

其中 d(v,u) 是 v→u 的最短路径长度。

## 4. 节点失效模拟

### 移除 M1
- 从 V 中移除 M1
- 从 E 中移除所有与 M1 相关的边: (S1,M1), (S2,M1), (M1,D1), (M1,D2)
- 得到新图 G' = (V', E')
- 在 G' 上重新运行 Dijkstra 求 S1→R1 的最短路径

### 网络连通性
- 计算 G' 的连通分量
- 检查是否有节点与 S1 或 R1 断连

## 5. 输出指标

| 指标 | 公式 | 含义 |
|------|------|------|
| 最短路径成本 | Σ w(e_i) | 总运输成本 |
| 路径可靠性 | Π r(e_i) | 路径正常运行的概率 |
| 度中心性 | C_deg(v) | 节点的直接连接数 |
| 介数中心性 | C_B(v) | 节点控制最短路径的能力 |
| 接近中心性 | C_C(v) | 节点到其他节点的平均距离 |
| 失效后成本 | Σ w'(e_i) | M1 失效后的新路径成本 |
| 成本变化率 | (新成本 - 原成本) / 原成本 | 失效的影响程度 |
