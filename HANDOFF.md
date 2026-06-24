# HANDOFF · ModelCrew 刷题循环交接

> 给在**电脑上接棒**的你（或下一个 Claude Code 会话）。网页版会话的对话记录不能直接搬到本地，但**所有成果都在 git**。本文件 = 完整状态 + 一段可直接粘贴的接棒 prompt。
> 最后更新：2026-06-24。分支 `claude/progress-check-j7c4jc`，最新 commit 见 `git log -1`。

## 0. 怎么接棒（电脑上三步）

```bash
git fetch origin
git checkout claude/progress-check-j7c4jc      # 或 git pull origin claude/progress-check-j7c4jc
# 然后在仓库根目录开 claude，把下面第 6 节的「接棒 prompt」粘进去
```

## 1. 这个项目是什么

ModelCrew = 一套**数学建模竞赛（美赛/国赛）的多角色 AI 流水线**。8 个角色子代理：
Router→Analyst→Scout→Modeler→Solver→Critic→Writer→Judge（定义在 `agents/*.md`，发布版镜像在 `skills/modelcrew-*/SKILL.md`，**两者必须双同步**）。
- `references/`：可复用知识库（得奖论文范式、反模式、方法箱、弱效应招式、创新增压、评分量表…）。
- `tools/`：`check_frozen.py`（论文数字 vs 脚本输出一致性）、`check_paper_numbers.py`（散文数字 vs 冻结值）。**已改为自动发现 `cases/*/artifacts/frozen_numbers.json`，加新案例无需改工具**。
- `cases/`：每道题一个目录，`artifacts/` 下放 solve.py / results.json / frozen_numbers.json / 6_paper.md / 5_audit.md / 7_review.md / figures。

## 2. 这个会话做了什么

1. **框架升级（早期，已并入 commit `5b00df7`）**：弱效应招式箱 `inconclusive_playbook.md`、散文数字校验工具 `check_paper_numbers.py`、创新增压 `innovation_boost.md`，并接进相关角色。
2. **/loop 刷题**：不断喂新题→跑→Critic/Judge 打分→把扣分点沉淀进框架→蒸馏获奖做法。设的**停止阈值 = 一道全新题 Judge ≥ 90 且 Critic 无 ❌**。
3. **🔑 最重要的纠偏（基准诚信）**：用户指出基准要有效，**解题与评分都必须 clean-context**，否则量的是"带全上下文的编排者"而非框架。据此：
   - 立了 **`cases/practice_log.md` 纯净基准协议（5 条）**：解题/题面/评分三处无菌 + 污染隔离 + 编排者只传工件不注入内容。
   - 给 Judge 加 **盲评铁律 + 评委必须 Read 打开 figures/*.png 看图**（`agents/7_judge.md` + skill 双同步）。
   - **作废了 iter1/iter2 旧解**（编排者亲手写=污染），把 iter2 按协议**全无菌重跑**。

## 3. 当前诚实战绩

| 案例 | 解题方式 | 评分方式 | 分数 | 说明 |
|---|---|---|---|---|
| demo_dispatch_simpson | 8角色自跑(净) | 带上下文 | 87 | 可能略虚高(未盲评) |
| practice_01 销量预测 | 编排者亲写 ⚠️污染 | — | ~~86~~ | 作废，不算数 |
| practice_02 旧 | 编排者亲写 ⚠️污染 | 盲评 86.3 / 带上下文 89 | ~~86.3~~ | 作废；量出"带上下文评分"虚高~3分 |
| **practice_02′（净）** | **角色agent自解(净)** | **盲评+看图** | **84** | ✅ **当前唯一全无菌真分** |

**结论**：框架自己跑、盲评，机理题落在 **84/100**（国二偏上/国一边缘）。距阈值 90 还差，差在**创新性 + 写作呈现**两个天花板维（跨案例一致的系统短板）。"编排者亲手调"约值 +2.3 分水分，"带上下文评分"约值 +3 分水分——都已剔除。

## 4. 已沉淀的可复用经验（compounding，对以后任何题生效）

- `references/anti_patterns.md`：C4b 平局宣布赢家、C4c 阈值外推到未冻结圆整数。
- `references/winning_paper_patterns.md`：§3C 预测/时序得奖细则、§3D 机理/ODE 得奖细则（解析互验/独立积分器交叉验证/结构主张找反例/命名+操作化稳健指标）。
- `references/innovation_boost.md`：创新维系统性最弱，最省力补法=命名整套流程+把稳健性发现操作化成可报告指标。
- `cases/practice_log.md`：纯净基准协议 + 记分板（刷题控制中枢，先读它）。
- **新发现待办**：图内标注的数字要与 frozen 同口径圆整（practice_02′ fig1 "300k/36.8" vs 300466/36.85 被盲评抓到）——可考虑给 `check_paper_numbers.py` 加"扫描图注/或要求图用全精度"的规则。

## 5. 没做完 / 下一步候选

- **阈值 90 未达**：清洁框架当前 ~84。要冲 90 需真升「创新性 + 写作呈现」——靠 §3D/innovation_boost 的积累让**下一道新题从建模阶段就强**，而非事后调（事后调=污染）。
- iter1（销量预测）也该按纯净协议重跑一遍，拿它的真分。
- 可选：把"评委看图""图注口径"做成工具化检查。

## 6. 接棒 prompt（直接粘贴给本地 claude）

```
先 git pull origin claude/progress-check-j7c4jc 拉到最新（确保拿到全部已推送成果），再读 cases/practice_log.md（尤其「纯净基准协议」5 条）和 HANDOFF.md 了解现状。继续 ModelCrew /loop 刷题：停止阈值 = 一道全新题盲评 Judge ≥ 90 且 Critic 无 ❌。

铁律（务必遵守，否则基准作废）：
1. 解题全程用全新的 modelcrew 角色子代理（analyst→modeler→solver→critic→writer），各自 clean context；你只在角色间传工件，绝不亲手写 solve.py/论文，绝不注入解法/数字/命名/踩坑经验。
2. 题面 README 只写情景+参数+问题，不预埋方法或创新点。
3. 评分用全新 Judge + 中立 prompt（不透露目标分/历史分/作者意图），且 Judge 必须 Read 打开 figures/*.png 真看图；禁止续跑同一评委重评提分。
4. 每轮：刷一道新题型（优化/图论/评价/真实赛题皆可）→记分到 practice_log→把扣分点沉淀进 references→蒸馏≥1 条获奖做法→commit 推送。
5. 数字唯一真值源 frozen_numbers.json；跑 tools/check_frozen.py + check_paper_numbers.py 必须全过。

先确认你已读懂纯净协议，再开第一道新题（建议换"优化型"以补方法箱覆盖）。
```

## 7. 提醒

- 网页版云端的这个 `/loop` 会话独立运行，切到电脑不影响它；人在电脑上 `git pull` 看结果即可。
- 改任何角色指令都要 `agents/` + `skills/` **双同步**。
- 提交信息不要写模型标识符。
