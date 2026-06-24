# ModelCrew · 可复用的多 Agent 数学建模框架 —— 主计划

> QoderWork CN 大赛 · **赛道八「多 Agent 编排挑战」** · 个人参赛
> 验证样例：**2024 MCM Problem C —— 网球的"动量"**
> 截止：**2026-06-30 23:59**

---

## 一句话目标

不做一次性分析，而是造一支 **8 角色、可复用的数学建模 AI 团队**：
**Router 读懂任意赛题 → 自动召唤对应专家 → Critic 闸门反幻觉把关 → 产出报告**。
用 2024 美赛 C 题验证它端到端跑通；以后打国赛/美赛**换个题目直接复用**。

## 为什么是"框架"而不是"一道题"

赛道八考的是"**设计一个 AI 团队来自动化解决复杂问题**"——重点是**系统**。
- 一次性分析 = 作业；
- 可复用框架 = 真工程 + 我自己以后真用得上的工具（国赛约 9 月、美赛明年 2 月）。
这是赛道八里的差异化打击，也是作品集里能讲半小时的料。

## 诚实的定位（不吹牛）

它是**建模副驾(copilot)/脚手架**，自动包办可复用的流程——审题、选方法、搭框架、查错、套 LaTeX 论文格式、模拟评委打分；
**硬核的建模灵感仍由人(我)来把舵**。这"把舵"不是口号：流程里设了 **4 个显式卡点**（审题后/选模型后/Critic 审出❌后/评委打分后，见 `references/human_checkpoints.md`）停下来请人拍板。
"通用"指流程通用，不是"全自动解出任何题"——可复用流程自动跑，**关键判断留给人**。

---

## 框架：8 角色 AI 团队（`agents/`，题目无关、可复用）

| # | Agent | 通用职责 |
|---|-------|---------|
| 0 | **Router 调度** | 读题 → 判题型(连续/离散/数据/运筹/环境/政策) → **召唤**对应专家 → 调度 + Critic 闸门 |
| 1 | **Analyst 审题** | 拆子问题、定义、假设、陷阱 |
| 2 | **Scout 数据** | 找/读数据、质量体检、清洗留痕 |
| 3 | **Modeler 建模** | 按题型选方法、建模、列待审计结论 |
| 4 | **Solver 求解** | 求解 + 敏感性分析 + 可视化 |
| 5 | ⭐**Critic 反幻觉评审** | 对抗式审计：随机性/因果/过拟合/外推（**框架签名招式**） |
| 6 | **Writer 写作** | 按竞赛口味写报告 + **LaTeX 投稿件**，如实写局限 |
| 7 | ⚖️**Judge 评委** | 模拟限时阅卷评委，按 rubrics 给整篇打分 + 预估奖级(非官方) + 只改一处建议（落地 L3 Panel）|

> Judge≠Critic：Critic 过程中管"对不对"（✅/⚠️/❌ 闸门）、Judge 终局管"能拿多少分"。
> 4 个人把舵卡点（CP1 审题 / CP2 选模型 / CP3 ❌处置 / CP4 评委复盘）见 `references/human_checkpoints.md`。

## 样例：`cases/2024_mcm_c_tennis/`

用网球动量题验证框架。选它因为 Q2"连胜是否随机"正中 **热手谬误**——Critic 的完美舞台。
Router 路由路线：Analyst → Scout(重) → Modeler(EWMA) → Solver → ⭐Critic → Writer(+LaTeX) → ⚖️Judge。
产出存 `cases/2024_mcm_c_tennis/artifacts/`。

## 目录结构

```
qoder/
├── PLAN.md / README.md
├── agents/                      # ★ 可复用的 8 角色团队源稿（0_router.md … 6_writer.md + 7_judge.md）
├── skills/                      # 8 个 modelcrew-* 技能（Qoder SKILL.md 备份）
├── templates/                   # LaTeX 论文模板（美赛 mcm_ / 国赛 cumcm_ + 占位符约定）
├── references/                  # 借鉴资产（模型目录/反模式/评分/四层反馈/写作模板/相关工作/人把舵卡点）
├── cases/
│   └── 2024_mcm_c_tennis/       # demo 样例（README.md + data/ + artifacts/ + screenshots/）
└── submission/                  # 实践文档.md + forum_post.md（天池作品 + 论坛帖）
```

## 时间线（零散投入版）

- **6/19 反腐 quiz、6/20 TOSPINE 决赛先扛**，之前只插"现在能做"的格子。
- **现在**：学生认证 → 拿 4000 Credits → 登录 Qoder 逛技能广场 → ⚠️**搞清楚多 Agent 怎么落地 + 能否存成可复用模板，回来同步**。
- **6/21 起主力**（约 9 天，每次 1-2h，做完即存档）：
  Router 路由 → Analyst → Scout → Modeler → Solver → ⭐Critic(高光) → Writer → 写论坛帖提交。

## 提交清单

- [ ] 天池报名（联系方式填对）
- [x] 学生认证通过，4000 Credits 到账
- [ ] 各 Agent 对话记录截图 + Markdown 工件打包上传天池
- [ ] 论坛帖：完整 Qoder 界面截图 + 对话结果，主线突出"可复用框架 + 反幻觉 Critic"
- [ ] 等赛后 3 个工作日验证通过

## 借鉴与致谢（论坛帖如实写明）

`references/` 下的 6 份资产（模型目录 / 反模式 / 评分维度 / 四层反馈 / 写作模板 / 相关工作）
在**方法论上参考了开源项目 [mathmodel-skill](https://github.com/handsomeZR-netizen/mathmodel-skill)（MIT）**，
以及学术系统 MM-Agent / ModelingAgent / Sci-Mind（详见 `references/related_work.md`），
但内容全部由我们自己重写，未搬运其原创蒸馏数据。四层反馈(L1–L4)与对抗辩论 Critic 即来自这些项目的设计思路。
其中 5 份挂载到 `modelcrew-router / modeler / scout / solver / critic / writer` 技能（运行时会查阅 `references/`），`related_work.md` 为引用资产。

## 进度

- [x] 7 个 `modelcrew-*` 技能创建（用户级，跨比赛复用）
- [x] 打包成专家套件「数学建模 ModelCrew」(enabled/installed)
- [x] 6 份 `references/` 借鉴资产（含 MM-Agent/ModelingAgent/Sci-Mind 借鉴），挂载到相关技能
- [x] 全部备份进仓库 `skills/` + `references/` 版本管理
- [x] **跑通网球 demo**（v1 单审 + v2 辩论 两版审计、348 行真代码、可复现）
- [x] 写实践文档 + 论坛帖（11 张截图已配齐）
- [ ] 打包上传天池作品 + 发布论坛帖（剩纯手动动作）

## ⚠️ 待确认（登录 Qoder 后回来同步）

1. Qoder 的"多 Agent 编排"怎么实现？多 skill 串联，还是单 skill 内角色切换？
2. **能否把这套编排存成可复用 skill 模板**？（决定"复用"是一键重跑还是拷脚本重喂）
3. 技能广场有无现成的数据分析/建模类 skill 可复用？
4. 对话记录怎么导出成 Markdown？
