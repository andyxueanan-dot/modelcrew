# ModelCrew 🧮🤖

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/语言-简体中文-d9241c?style=for-the-badge" alt="简体中文"></a>
  <a href="README_EN.md"><img src="https://img.shields.io/badge/Language-English-555?style=for-the-badge" alt="English"></a>
</p>

> 一支**可复用**的多 Agent 数学建模 AI 团队：`Router` 读懂任意赛题 → 自动召唤对应专家
> （审题 / 数据 / 建模 / 求解）→ 由 ⭐`Critic` 反幻觉评审对抗式把关 → `Writer` 出报告。
> **换个题目直接复用，团队定义一行不用改。**

为 **QoderWork CN 大赛 · 赛道八「多 Agent 编排挑战」** 而作，
先以 **2024 MCM Problem C（网球动量）** 验证端到端跑通，再**零改动**复用到**信用卡违约预测**（金融风控）证明可复用性。

---

## 🔁 核心：换题即用（这才是赛道八「编排」真正想考的）

ModelCrew 的智能体按**「建模流程」**而非**「某一道题」**定义，所以换题时框架完全不动：

```
                         ┌─────────────────────────────────────────┐
   新赛题 + 数据  ─────▶  │  @数学建模 ModelCrew（已安装的专家套件）  │ ─────▶  论文 + 反幻觉审计
                         │  Router→Analyst→Scout→Modeler→Solver     │
                         │         →⭐Critic→Writer（定义不变）      │
                         └─────────────────────────────────────────┘
```

**复用只要 3 步，全程不碰团队定义：**

| 步骤 | 做什么 | 改动量 |
|---|---|---|
| 1️⃣ 放题 | 新建 `cases/<新题>/`，丢进题面 + 数据 | 只加文件 |
| 2️⃣ 召唤 | 对 `@数学建模 ModelCrew` 说一句"按本题路由" | 一句话 |
| 3️⃣ 跑 | Router 自动判题型、召唤专家、Critic 把关、Writer 出稿 | **0 行代码** |

> **为什么能复用**：7 个角色是按"读题 / 数据体检 / 选模型 / 求解 / 反幻觉 / 写作"这些**通用建模动作**抽象的，
> 与具体赛题解耦。题目无关 ⟹ 即插即用。
>
> ⚠️ **诚实说明**：上图是 7 角色的**完整阵容**，但 Router 会**按题型裁剪实际派发**——并非每题都召满 7 个。
> 例如本仓库两个 demo 都是**数据型(C)**，召唤路径为 Analyst→Scout→Modeler→Solver→Critic→Writer；
> 连续型/优化型会换成另一条链路（详见 `agents/0_router.md` 的召唤策略）。

### ✅ 可复用性已被两个不同领域实证

| 案例 | 领域 | 数据 | 团队改动 | 结果亮点 |
|---|---|---|---|---|
| `cases/2024_mcm_c_tennis/` | 体育 / 统计 | 温网逐分 7284 分 | — | Critic 把"动量真实存在"判为 ❌（*热手谬误*） |
| `cases/credit_default_fintech/` | **金融风控** | UCI 信用卡 3 万条 | **0 行** | Critic 当"上线评审"否决直接部署（公平合规） |

> 同一支团队，从**网球**换到**银行信用风险**，**团队定义一行没改**——这就是"可复用"的硬证据。

---

## ✨ 亮点

- **可复用框架**：7 个 AI 角色打包成专家套件，换题即用、跨比赛复用（见上方 🔁）。
- ⭐**反幻觉 Critic**：对每条结论做对抗式审计 + 三方辩论裁决——在网球 demo 中把"动量真实存在"判为 ❌（实为统计学经典的*热手谬误*）。
- **真验证 + 可复现**：348 行 Python、真实统计检验（Wald-Wolfowitz runs test / 条件置换 / 逻辑回归），`seed=42` 一键复现。
- **两轮交叉验证**：独立 AI + Codex 复审，发现并修正一处统计学漏洞（"server-adjusted" 空操作），用真正控制发球权的检验确认——结论不变且更稳。
- 🏦 **金融案例（可复用性已实证）**：同一支团队**零改动**换到**信用卡违约预测**（UCI 3 万条信用风险数据）——XGBoost AUC 0.782 / KS 0.422，Critic 以"银行模型上线评审"否决直接部署（公平合规风险），并发现**移除性别/年龄等敏感属性后 AUC 仅降 0.003**（合规成本≈0）。详见 `cases/credit_default_fintech/`。

## ⚡ 快速复现（验证 demo 数字是真的）

```bash
git clone https://github.com/andyxueanan-dot/modelcrew.git && cd modelcrew
pip install -r requirements.txt
# 金融案例（信用卡违约）：输出 AUC/KS 落盘 artifacts/results.json
cd cases/credit_default_fintech && python artifacts/solve.py && cd ../..
# 网球案例（动量/热手）：输出 runs test / 置换检验 → solver_results.json
cd cases/2024_mcm_c_tennis   && python artifacts/solve.py
```

两个脚本都设了 `seed=42`，跑出的数字应与各 `artifacts/` 下的 JSON 和论文散文逐位一致——这正是本作品"反幻觉 / 可复现"主张的硬验证。

## 🛠 用什么软件跑？（环境 & 可移植性）

**本作品在 Qoder 上构建并提交**（赛道八要求）。但 ModelCrew 的"内核"是**纯 Markdown 的角色定义 + 参考资产**（`agents/` + `references/`），**与具体工具解耦**——所以它能移植到别的 agentic 工具，不是只能在 Qoder 上跑。

| 工具 | 能不能跑 | 怎么跑 |
|---|---|---|
| **Qoder**（原生，已实测） | ✅ 最省事 | 7 个 `SKILL.md` = 7 技能 → 打包成专家套件；`/` 调技能、`@` 召唤整队 |
| **Claude Code**（已移植+验证） | ✅ 已验证 | 7 个子代理见 [`.claude/agents/`](.claude/agents/)，端到端跑通（[验证记录](.claude/agents/VERIFICATION.md)） |
| **Codex CLI** | ⚠️ 可以，但更手动 | 无"命名子代理套件"机制；把角色写进 `AGENTS.md`，按 Router→…→Writer 顺序用提示词逐步驱动 |
| **任意 LLM 对话** | ⚠️ 最朴素 | 把每个 `agents/*.md` 当系统提示，逐角色手动接力 |

> 一句话：**比赛交的是 Qoder 版**；但内核就是"角色 + 流程 + Critic 闸门"的 Markdown，**已在 Claude Code 里复刻并验证**（见 [`.claude/agents/`](.claude/agents/)：7 个 subagent + 格式校验 + 端到端冒烟测试，Critic 在迷你赛题里成功把"存在热手"判为 ❌）。Qoder 的价值在于把"技能 / 套件 / 子代理"做成了一键安装、`@` 一下就召唤的产品化封装。

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

---

<sub>作者 Andy（厦门大学马来西亚校区 · 数据科学与大数据技术）· QoderWork CN 大赛赛道八参赛作品</sub>
