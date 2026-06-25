# Model — 应急疏散网络图论分析

## 1. Dijkstra 最短路径
dist[v] = min(dist[u] + w(u,v)) for all edges (u,v)
时间复杂度 O((V+E)log V)

## 2. Yen's K-最短路径
对 k=1,...,K:
  对前一路径的每个节点 i 做 spur:
    1. 移除与已知路径共享前缀的边
    2. 移除根路径节点(除 spur 节点)
    3. Dijkstra 从 spur 节点到目标
    4. 拼接根路径 + spur 路径
  选择候选中代价最小的加入 A

## 3. Edmonds-Karp 最大流
Ford-Fulkerson 的 BFS 变体:
1. BFS 在残差网络中找增广路径
2. 沿路径推流(瓶颈容量)
3. 更新残差网络
4. 重复直到无增广路径
时间复杂度 O(VE²)

## 4. 连通度
- 顶点连通度 κ: 最小的节点移除数使某 S→T 对断开
- 边连通度 λ: 最小割(将容量设为1的最大流)

## 5. 节点失效模拟
对每个 hub h ∈ {M1,M2,M3,M4}:
  移除 h 及其所有关联边
  重新计算 Dijkstra 和可达性
  记录断开对数和延误
