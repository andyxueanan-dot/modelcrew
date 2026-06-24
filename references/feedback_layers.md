# 四层反馈机制 feedback_layers

> 供 `modelcrew-router` 编排时调用。把单一的"Critic 闸门"升级为**四层递进反馈**——
> 这是 ModelCrew 从"顺流水线"进化为"自我纠错的工程系统"的关键，也是赛道八里最能体现"编排"深度的部分。
> （方法论参考了开源项目 mathmodel-skill 的多层反馈设计，本文为我们自己的多 Agent 适配版。）

## L1 · 阶段级 Critic（即时闸门）
- **触发**：每个 Agent 产出后立即。
- **动作**：`modelcrew-critic` 按 `rubrics.md` 对该产出打分 → verdict。
  - pass → 进下一 Agent
  - refine → 让该 Agent **只改问题处（diff-only）**，最多 3 次
  - block → 停下报告用户
- 这是我们已有的核心闸门。
- **对抗辩论增强（借鉴 Sci-Mind）**：对"效果是真是假"这类高风险结论，L1 不出独裁裁决，而是先让
  "理论家(主张成立)"与"怀疑者(主张是随机/混杂/过拟合)"各陈证据，Critic 当裁判再裁决。详见 `modelcrew-critic`。

## L2 · 跨阶段一致性回检
- **触发**：在 Modeler、Solver、Writer 阶段末尾。
- **动作**：回读全链路工件，检测**早期假设/选型/符号是否被后续事实推翻**。
  - 例：Analyst 假设"数据平稳"，但 Scout 体检发现明显趋势 → 冲突。
  - 例：Modeler 用 $x_i$，Writer 写成 $a_i$ → 符号漂移。
- **冲突处理**：**定向回滚**到出问题的那一步重做，而不是整段重来。

## L3 · 终局多视角 Panel —— ✅ 已由「评委 Judge」落地
- **触发**：Writer 出定稿后，调用 `modelcrew-judge` 一次。
- **动作**：用 **5 个独立视角**评审最终成果，每维 1–10 + 证据：
  1. 题目契合（有没有答非所问）
  2. 数学严谨（推导/假设）
  3. 结果可信（灵敏度/可复现）
  4. 写作呈现（图表/摘要/逻辑）
  5. 创新性（变体/组合）
- 聚合成 **0–100 总分 + 预估奖级（非官方）+「只改一处」建议**，落盘 `cases/<题>/artifacts/7_review.md`；
  在卡点 **CP4** 由人决定是否**定向重跑最弱一环一次**，把"局部最优"推向"全局最优"。
- **L3≠Critic 闸门**：L1 的 Critic 管"对不对"（✅/⚠️/❌）、是过程闸门；L3 的 Judge 管"能拿多少分"、是终局评分。
  实证产物见 `cases/2024_mcm_c_tennis/artifacts/7_review.md`。

## L4 · 反 gaming 校准（可选，高强度模式）
- **触发**：迭代多轮后抽查。
- **动作**：对某个维度**换一套 prompt 框架重新打分**，若两次分差 >2，说明该维度被"刷分"了 → 重置重评。
- 防止 Agent 学会糊弄 rubric。

---
## Router 编排伪代码
```
for agent in summon_strategy:
    artifact = agent.run(context)
    v = L1_critic(artifact)            # 即时闸门
    while v == refine and iter < 3:
        artifact = agent.refine(artifact, v.fixes)
        v = L1_critic(artifact)
    if v == block: halt_and_report()
    if agent in [modeler, solver, writer]:
        L2_consistency_check(decision_log)   # 跨阶段回检
final = L3_panel_review(all_artifacts)        # 终局 5 视角
if championship_mode: L4_calibration()
```
