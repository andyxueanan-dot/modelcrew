# Solver Results — 2024 MCM-C Tennis Momentum

## Q1: EWMA 动量指数

- **Server win rate (全局)**: p_server = 0.673
- **EWMA 参数**: α = 0.1，server-adjusted residual
- 成功为全部 31 场比赛计算了逐分动量指数
- 示例图 `figures/fig1_momentum_example.png`（Match 1301: Alcaraz vs Jarry）
  - 上图：cumulative games won（比分走势）
  - 下图：EWMA momentum index（蓝色 = P1 动量，红色 = P2 动量）

## Q2: 随机性检验 ⭐ 关键

### 2a. Wald-Wolfowitz Runs Test（31 场）

| 指标 | Raw | Server-Adjusted |
|------|-----|-----------------|
| α=0.05 显著场数 | 5/31 | 5/31 |
| Bonferroni 校正后 (α=0.0016) | **1/31** | 1/31 |
| Z 均值 | −0.986 | −0.986 |
| Z 标准差 | 1.002 | 1.002 |

- 期望：α=0.05 下随机应有 ~1.55 场显著；观测到 5 场，略高于期望
- Bonferroni 校正后仅 **1 场** 显著（match 1408, Z=−3.44, p=0.000584）
- Z 均值为负（−0.986）→ runs 比期望略多 → 倾向于**交替**而非连胜 → **微弱反对热手**
- ⚠️ **更正（Codex 交叉验证）**：原"server-adjusted runs test"是空操作（二值化后≡原始序列），**并未控制发球权**，"raw 与 adjusted 一致"不能作为发球权被控制的证据。真正的发球权控制检验见 `CORRECTION_serveaware.md`：条件置换全 31 场 **0/31 显著**、min p≈0.16，post-streak 分层后无热手——**结论不变且更稳**。本节 runs test 仅作为对原始序列随机性的辅助证据。

### 2b. Permutation Test（10,000 次打乱，5 场样本）

| Match | Observed 5+ streaks | Max streak | p(perm) |
|-------|---------------------|------------|---------|
| 1301 | 4 | 8 | 0.991 |
| 1302 | 6 | 6 | 0.589 |
| 1303 | 8 | 6 | 0.073 |
| 1304 | 13 | 8 | 0.212 |
| 1305 | 9 | 8 | 0.330 |

- **全部 p ≥ 0.073**（最小 0.0733）→ 未达 0.05 显著（注：应表述为"未显著"而非"远大于"）。**注**：此为 5 场样本、且未控制发球权的旧检验；真正控制发球权的全 31 场条件置换见 `CORRECTION_serveaware.md`（0/31 显著、min p≈0.16）。
- 没有一场比赛的连胜分布超出随机基线

### 2c. Post-Streak Win Rate（热手核心检验）

| Streak length k | n (instances) | Overall next_win | Serving | Returning |
|-----------------|---------------|------------------|---------|-----------|
| 3 | 2016 | 0.499 | 0.703 | 0.345 |
| 4 | 998 | 0.429 | 0.701 | 0.342 |
| 5 | 426 | 0.427 | 0.693 | 0.301 |
| 6 | 182 | 0.462 | 0.765 | 0.281 |

- **Overall next_win 均 ≤ 0.50** → 连胜后下一分的胜率并未提高
- 控制发球后：serving ≈ 0.70（与全局 0.673 一致），returning ≈ 0.30-0.35
- **结论：不存在"热手"效应**——连胜后赢下一分的概率与基线无差异

## Q3: Swing（动量反转）预测

- **模型**: Logistic Regression, C=0.1, 5 features
- **样本**: Train 4765 / Test 1899（按比赛 70/30 划分，避免泄漏）
- **Swing 正例率**: 52.9%
- **AUC-ROC**: 0.529（仅略高于随机 0.5）
- **特征系数**:
  - momentum: **−0.524** ← 负系数，动量大时更可能反转（均值回归）
  - velocity: −0.065
  - streak: −0.020
  - score_diff: −0.017
  - server: +0.103

→ Swing 几乎不可预测；动量的负系数进一步支持"反转"而非"延续"

## 可复现性

- Random seed: 42
- Python packages: pandas, numpy, scipy, scikit-learn, matplotlib
- α_EWMA: 0.1, Permutations: 10,000
- 输出文件: `solver_results.json`, `runs_test_details.csv`, `figures/fig1_momentum_example.png`
