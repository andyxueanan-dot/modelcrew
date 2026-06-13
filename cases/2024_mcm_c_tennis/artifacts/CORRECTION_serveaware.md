# 更正说明 · 发球权控制检验（Codex 交叉验证触发）

> 这份更正本身就是作品价值的一部分：**ModelCrew 的 Critic 漏掉了一个 bug，外部交叉验证(Codex)抓到了，我重做了真正的检验——结论不仅成立，还更稳。** 这正是"反幻觉 + 交叉验证"的意义。

## 发现的 bug（🔴）
原始 `solve.py` 的"server-adjusted runs test"是**空操作**：
```python
expected = np.where(s == 1, p_server, 1 - p_server)   # ∈ (0,1)
r_binary = (y - expected > 0)                          # y=1→True, y=0→False  ⟹  r_binary ≡ y
```
本地验证：`r_binary == y` 为 **True，diffs=0**。所以它**根本没有控制发球权**。
原 `4_results.md` / `6_paper.md` 中"Raw 与 Server-Adjusted 一致 ⟹ 发球权已充分控制"的解释是**错的**——一致只是因为二者是同一个计算。

## 真正控制发球权的检验（`solve_v2_serveaware.py` → `serveaware_results.json`）

**① 条件置换 null（保留发球序列，按发球/接发分层打乱，全 31 场，B=5000）**
- 显著场数 **0 / 31**（α=0.05）；min p ≈ **0.16**，中位 p ≈ **0.90**
- 比原来那个被混淆的 5 场置换(min p=0.073)**更干净、更强地支持"无超额连胜"**

**② 连胜后胜率按发球/接发分层**（真正的发球权控制）
| k | 发球方下一分胜率 | 接发方下一分胜率 |
|---|---|---|
| 3 | 0.681 (n=1017) | 0.330 (n=999) |
| 4 | 0.676 (n=503) | 0.339 (n=495) |
| 5 | 0.683 (n=205) | 0.290 (n=221) |
| 6 | 0.727 (n=88) | 0.255 (n=94) |
- 发球方 ≈ 0.68 ≈ 全局发球胜率 0.673；接发方 ≈ 0.29–0.34 ≈ 全局接发胜率 0.327
- 连胜后表现与基线无异 → **无热手效应**

## 对原结论的影响
- ❌ 作废："runs test 的 server-adjusted 与 raw 一致证明发球权被控制"（解释错误）。
- ✅ 不变且更稳："网球动量是热手谬误"的总结论——现在由**真正控制发球权**的条件置换 + 分层 post-streak 支撑。
- runs test (mean Z=−0.986) 仍是对**原始逐分序列**随机性的有效检验，但它**不控制发球权**，仅作为辅助证据；发球权控制以本文件的检验为准。

## 复现
```
cd cases/2024_mcm_c_tennis
python artifacts/solve_v2_serveaware.py   # 写出 serveaware_results.json
```
（原 `solve.py` 同样从 case 根目录运行：`python artifacts/solve.py`）
