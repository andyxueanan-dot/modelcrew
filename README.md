# ModelCrew 🧮🤖

> A **reusable** multi-agent crew that solves math-modeling-contest problems —
> reads any problem, **summons the right specialists**, and lets a skeptic agent **interrogate every conclusion.**

一支**可复用**的数学建模 AI 团队：`Router` 读懂任意赛题 → 自动召唤对应专家
（审题 / 数据 / 建模 / 求解）→ 由 ⭐`Critic` 反幻觉评审对抗式把关 → `Writer` 出报告。
以后打国赛/美赛，**换个题目直接复用**，团队定义不用改。

为 **QoderWork CN 大赛 · 赛道八「多 Agent 编排挑战」** 而作，
并以 **2024 MCM Problem C（网球动量）** 为样例验证端到端跑通。

## ✨ 亮点

- **可复用框架**：7 个 AI 角色打包成专家套件，换题即用、跨比赛复用。
- ⭐**反幻觉 Critic**：对每条结论做对抗式审计 + 三方辩论裁决——在网球 demo 中把"动量真实存在"判为 ❌（实为统计学经典的*热手谬误*）。
- **真验证 + 可复现**：348 行 Python、真实统计检验（Wald-Wolfowitz runs test / 条件置换 / 逻辑回归），`seed=42` 一键复现。
- **两轮交叉验证**：独立 AI + Codex 复审，发现并修正一处统计学漏洞（"server-adjusted" 空操作），用真正控制发球权的检验确认——结论不变且更稳。
- 🏦 **可复用性已实证（金融案例）**：同一支团队**零改动**换到**信用卡违约预测**（UCI 3 万条信用风险数据）——XGBoost AUC 0.782 / KS 0.422，Critic 以"银行模型上线评审"否决直接部署（公平合规风险），并发现**移除性别/年龄等敏感属性后 AUC 仅降 0.003**（合规成本≈0）。详见 `cases/credit_default_fintech/`。

## 目录结构

```
qoder/
├── PLAN.md                  # 主计划（框架 / 样例 / 时间线 / 提交清单）
├── agents/                  # ★ 7 角色团队源稿（0_router … 6_writer，题目无关）
├── skills/                  # 7 个 modelcrew-* 技能（Qoder SKILL.md 备份）
│   └── modelcrew-{router,analyst,scout,modeler,solver,critic,writer}/SKILL.md
├── references/              # 6 份借鉴资产（model_catalog/anti_patterns/rubrics/
│                            #   feedback_layers/writing_templates/related_work）
├── cases/
│   ├── 2024_mcm_c_tennis/      # demo①：网球动量（数学建模 / 体育）
│   └── credit_default_fintech/ # demo②：信用卡违约预测（金融风控，证明可复用）
└── submission/              # 实践文档.md + forum_post.md（天池作品 + 论坛帖）
```

## 核心思想

- **可复用**：智能体按"建模流程"而非"某道题"定义；换题只需新建一个 `cases/<题>/`。
- **自动召唤**：`Router` 按题型(连续/离散/数据/运筹/环境/政策)决定召唤哪些专家、什么顺序。
- ⭐**反幻觉闸门**：任何结论必须过 `Critic` 的对抗式审计（随机性 / 因果 / 过拟合 / 外推）才放行，
  被证伪则回退重做——这是把"作业"变成"真实 AI 工程"的那一步。
