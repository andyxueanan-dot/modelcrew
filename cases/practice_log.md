# 刷题记录 practice_log（ModelCrew 自练 scoreboard）

> 由 `/loop` 自动驱动：不断喂**全新题目**→ 8 角色跑 → Judge 打分 → 吸取经验写进 `references/` → 蒸馏获奖论文做法。
>
> **停止阈值（本轮 /loop 设定）**：当一道**全新题目**（非已有案例）经 **Judge ≥ 90/100** 且 **Critic 无 ❌**（无红线违反）即停——视为"框架已能稳定产出国一/O 奖级作品"。
>
> 每轮产物：新 `cases/practice_NN_*/` 工件 + 本表加一行 + `references/` 至少一处"吸取经验" + `winning_paper_patterns.md` 至少一条新蒸馏。

## 记分板

| # | 题目 | 题型 / 方法箱 | Judge | Critic | 吸取的教训（写进哪） | 蒸馏 |
|---|---|---|---|---|---|---|
| — | （基线）demo_dispatch_simpson | 数据型·因果/Simpson | 87 | 无❌ | 弱效应招式箱已沉淀 | — |
| 01 | 月度销量预测 | 预测型·时序(HW/OLS/季节朴素) | **86** | 无❌(2⚠️, 5视角8.6) | C4b「平局上宣布赢家」→`anti_patterns`；创新系统性最弱→强化`innovation_boost` | `winning_paper_patterns §3C` 预测/时序得奖细则 |

## 进度备注
- **阈值 90 未达（86）→ 继续。**
- 🔑 **跨案例 meta-教训**：创新性是系统性最弱维（demo_dispatch 7 / practice_01 7），其余四维已国一水准。框架"严谨/诚实/可复现"过硬，但"创新落点+命名"反复差一口。**已据此强化 `innovation_boost.md`：每题建模阶段就把一个稳健性/等价发现操作化成「可报告指标 + 可引用命名」**，下一题从一开始按此做，目标冲 90。
- 工具升级：`check_frozen.py`/`check_paper_numbers.py` 改为**自动发现案例**，刷新题无需改工具。
