# ModelCrew 🧮🤖

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/语言-简体中文-d9241c?style=for-the-badge" alt="简体中文"></a>
  <a href="README_EN.md"><img src="https://img.shields.io/badge/Language-English-555?style=for-the-badge" alt="English"></a>
</p>

> 一支**可复用**的多 Agent 数学建模 AI 团队 / 完整建模副驾：`Router` 读懂任意赛题 → 自动召唤对应专家
> （审题 / 数据 / 建模 / 求解）→ 由 ⭐`Critic` 反幻觉评审对抗式把关 → `Writer` 出报告（**含 LaTeX 投稿件**）
> → `Judge` **充当评委给整篇打分**；全程在 **4 个关键处停下让人拍板**。
> **换个题目直接复用，团队定义一行不用改。**

为 **QoderWork CN 大赛 · 赛道八「多 Agent 编排挑战」** 而作，
先以 **2024 MCM Problem C（网球动量）** 验证端到端跑通，再**零改动**复用到**信用卡违约预测**（金融风控）证明可复用性。

---

## 🔁 核心：换题即用（这才是赛道八「编排」真正想考的）

ModelCrew 的智能体按**「建模流程」**而非**「某一道题」**定义，所以换题时框架完全不动：

```
                         ┌──────────────────────────────────────────────┐
   新赛题 + 数据  ─────▶  │  @数学建模 ModelCrew（已安装的专家套件）       │ ─────▶  LaTeX 论文 + 反幻觉审计 + 评委评分
                         │  Router→Analyst→Scout→Modeler→Solver          │
                         │     →⭐Critic→Writer(含LaTeX)→评委Judge（定义不变）│
                         │     ↑ 全程 4 个 🛑 卡点让人拍板                  │
                         └──────────────────────────────────────────────┘
```

**复用只要 3 步，全程不碰团队定义：**

| 步骤 | 做什么 | 改动量 |
|---|---|---|
| 1️⃣ 放题 | 新建 `cases/<新题>/`，丢进题面 + 数据 | 只加文件 |
| 2️⃣ 召唤 | 对 `@数学建模 ModelCrew` 说一句"按本题路由" | 一句话 |
| 3️⃣ 跑 | Router 自动判题型、召唤专家、Critic 把关、Writer 出稿 | **0 行代码** |

> **为什么能复用**：8 个角色是按"读题 / 数据体检 / 选模型 / 求解 / 反幻觉 / 写作 / 评分"这些**通用建模动作**抽象的，
> 与具体赛题解耦。题目无关 ⟹ 即插即用。
>
> ⚠️ **诚实说明**：上图是 8 角色的**完整阵容**，但 Router 会**按题型裁剪实际派发**——并非每题都召满。
> 数据型(C) 走 Analyst→Scout→Modeler→Solver→Critic→Writer→Judge；**优化型(B) 自动改走** Analyst→Modeler→Solver→Critic→Writer→Judge（无重型 Scout）。
> 这套"按题型换链路"已在下方**数据型 + 优化型两类题**上各跑通一次（详见 `agents/0_router.md`）。

### ✅ 可复用性已被三个案例、两大题型实证

| 案例 | 题型 / 领域 | 数据 | 团队改动 | 结果亮点 |
|---|---|---|---|---|
| `cases/2024_mcm_c_tennis/` | 数据型 · 体育/统计 | 温网逐分 7284 分 | — | Critic 把"动量真实存在"判为 ❌（*热手谬误*） |
| `cases/credit_default_fintech/` | 数据型 · **金融风控** | UCI 信用卡 3 万条 | **0 行** | Critic 当"上线评审"否决直接部署（公平合规） |
| `cases/2024_logistics_siting/` | **优化型** · 运筹/选址 | 64 社区应急选址 | **0 行** | Critic 把"单次搜索即最优"判为 ❌（局部最优陷阱）|

> 同一支团队，从**网球**→**银行信用风险**→**应急选址优化**，**跨数据型与优化型两大题型、定义一行没改**——这才是"换题即用"的硬证据。

---

## 🚀 从"出一篇报告"到"完整建模副驾"

ModelCrew 现在覆盖**拿到题 → 上手 → 建模求解 → LaTeX 论文 → 评委打分**的全流程，中间留 **4 个让人拍板的卡点**：

| 新增能力 | 是什么 | 落地实证 |
|---|---|---|
| 📝 **LaTeX 投稿件** | Writer 新增 LaTeX 模式，`6_paper.md`(内容真相源) → 填模板 → `6_paper.tex`；美赛/国赛两套模板 | 网球案例 `6_paper.tex` **已用 MiKTeX 真编译出 6 页 PDF**（`cases/2024_mcm_c_tennis/artifacts/6_paper.pdf`） |
| ⚖️ **评委 Judge（第 8 角色）** | 模拟限时阅卷评委，按 `rubrics.md` 给整篇打分 + 预估奖级(非官方) + "只改一处"建议；落地此前空悬的 L3 五视角 Panel | 网球 `7_review.md`：总分 ≈75/100、预估 H～M、最弱维度=创新性 |
| 🛑 **4 个人把舵卡点** | 审题后/选模型后/Critic 审出❌后/评委打分后各停一次，请人确认或补判断（可切 `/grill-me` 式逼问） | 协议 `references/human_checkpoints.md`；样例 `cases/.../checkpoints_log.md` |
| 🧰 **弱效应决策招式箱** | 主结论 CI 跨零时不停在"做不出结论"：功效/样本量反算 + TOST 等效检验 + E-value 因果稳健性 + 决策导向收口，把"未达显著"转成决策价值（**不夸大为显著**） | `references/inconclusive_playbook.md`；调度案例落地后 Judge **83→87**（见下） |
| 🔢 **散文数字自动校验** | 把"Critic 手写脚本抓散文残留旧值"沉淀成常驻工具：按 `frozen_numbers.json` 的 `cited_in` 核对论文正文每个引用，舍入感知、零误报 | `tools/check_paper_numbers.py`，全库 **68/68** 一致；已抓出并修正 siting 案例一处可追溯缺口 |
| 💡 **创新增压清单** | Modeler 选完 baseline 强制过一遍"能否升一档"（变体/组合/问题操作化 + 可引用命名）；Judge 据此评创新有锚点 | `references/innovation_boost.md`；调度案例创新维 7→8.3 |

> **Judge ≠ Critic**：Critic 在过程中管"对不对"（✅/⚠️/❌ 硬闸门），Judge 在终局管"能拿多少分"（评分+奖级）。
> 卡点体现定位——ModelCrew 是**建模副驾**：可复用流程自动跑，**关键判断留给人**。

> 🧪 **端到端自跑实证**：`cases/demo_dispatch_simpson/`（调度策略评估，埋了辛普森混杂）是用升级后的 **8 角色子代理自己从头跑完**的——Router→Analyst→Scout→Modeler→Solver→Critic→Writer→Judge 全链路真跑：Solver 先跑 **PoC 冒烟闸**(PASS) 再三法求解；⭐**Critic 独立从原始 CSV 复算、抓出散文里 3 处旧数字并触发修正**（`CORRECTION_audit.md`）、并把"方向≠显著"措辞红线立好；国赛 `6_paper.tex` 用 **xelatex 真编译出 PDF**；Judge 给 **83/100**（预估国二偏上，非官方）。
>
> 🔁 **再用它做框架优化的回归验证**：针对 Judge 指出的最弱点（"未达显著→决断力不足"+创新偏弱），把短板沉淀成框架能力（弱效应招式箱 / 散文数字校验工具 / 创新增压清单），再用本题回归——Solver 重跑加 **功效反算(达80%功效需 N=3412，现700) + TOST + E-value(1.566)**、Writer 在 §8 补**三段式决策收口**（全程不越"未达显著"红线，经 `5_audit.md §0.2` 独立复算确认），PDF 重编为 **14 页**，Judge 重打分 **83 → 87**（国一下沿/强国二上沿，非官方）。`check_frozen` 35/35 + `check_paper_numbers` 68/68 全绿。这既证明"框架升级真能提分"，也证明"它自己跑、自己纠错、自己提分"。

---

## ✨ 亮点

- **可复用框架**：8 个 AI 角色（含⚖️评委）打包成专家套件，换题即用、跨比赛复用（见上方 🔁）。
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

```bash
# 数字可追溯校验：论文引用的每个数字都回溯到脚本输出，源比结果新会报 STALE
python tools/check_frozen.py        # 冻结值==脚本输出，当前 35/35 一致
python tools/check_paper_numbers.py # 论文正文每个引用==冻结值，当前 68/68 一致
```
> 每个案例 `artifacts/frozen_numbers.json` 是论文数字的**唯一真相源**：`check_frozen.py` 核对"冻结值 == 脚本输出"并在 `solve.py`/数据被改动后提示重跑；`check_paper_numbers.py` 进一步核对"论文/文档正文里手写的每个引用 == 冻结值"（舍入感知、零误报）——把"反幻觉"从人工 Critic 延伸成**两道可自动跑的门禁**（借鉴 `math-modeling-skills`）。

## 🛠 用什么软件跑？（环境 & 可移植性）

**本作品在 Qoder 上构建并提交**（赛道八要求）。但 ModelCrew 的"内核"是**纯 Markdown 的角色定义 + 参考资产**（`agents/` + `references/`），**与具体工具解耦**——所以它能移植到别的 agentic 工具，不是只能在 Qoder 上跑。

| 工具 | 能不能跑 | 怎么跑 |
|---|---|---|
| **Qoder**（原生，已实测） | ✅ 最省事 | 8 个 `SKILL.md` = 8 技能 → 打包成专家套件；`/` 调技能、`@` 召唤整队 |
| **Claude Code**（已移植+验证） | ✅ 已验证 | 8 个子代理见 [`.claude/agents/`](.claude/agents/)，端到端跑通（[验证记录](.claude/agents/VERIFICATION.md)） |
| **Codex CLI** | ⚠️ 可以，但更手动 | 无"命名子代理套件"机制；把角色写进 `AGENTS.md`，按 Router→…→Writer 顺序用提示词逐步驱动 |
| **任意 LLM 对话** | ⚠️ 最朴素 | 把每个 `agents/*.md` 当系统提示，逐角色手动接力 |

> 一句话：**比赛交的是 Qoder 版**；但内核就是"角色 + 流程 + Critic 闸门"的 Markdown，**已在 Claude Code 里复刻并验证**（见 [`.claude/agents/`](.claude/agents/)：8 个 subagent + 格式校验 + 端到端冒烟测试，Critic 在迷你赛题里成功把"存在热手"判为 ❌）。Qoder 的价值在于把"技能 / 套件 / 子代理"做成了一键安装、`@` 一下就召唤的产品化封装。

## 目录结构

```
qoder/
├── PLAN.md                  # 主计划（框架 / 样例 / 时间线 / 提交清单）
├── agents/                  # ★ 8 角色团队源稿（0_router … 6_writer + 7_judge，题目无关）
├── skills/                  # 8 个 modelcrew-* 技能（Qoder SKILL.md 备份）
│   └── modelcrew-{router,analyst,scout,modeler,solver,critic,writer,judge}/SKILL.md
├── templates/               # ★ LaTeX 论文模板（美赛 mcm_ / 国赛 cumcm_ + 占位符约定）
├── references/              # 借鉴资产（model_catalog/anti_patterns/rubrics/feedback_layers/
│                            #   writing_templates/related_work/human_checkpoints/
│                            #   inconclusive_playbook ★弱效应招式箱/innovation_boost ★创新增压）
├── cases/
│   ├── 2024_mcm_c_tennis/      # demo①：网球动量（数据型 / 体育）★含 6_paper.tex/.pdf + 7_review.md
│   ├── credit_default_fintech/ # demo②：信用卡违约预测（数据型 / 金融风控）
│   ├── 2024_logistics_siting/  # demo③：应急服务站选址（优化型 / 运筹，证明换题型即用）
│   └── demo_dispatch_simpson/  # demo④：调度策略评估（数据型 / 辛普森混杂）——8 角色自跑+自纠，弱效应招式箱回归后 Judge 83→87，.tex 真编译 14 页
├── tools/check_frozen.py        # 数字可追溯校验（冻结值↔脚本输出，35/35）
├── tools/check_paper_numbers.py # 散文数字校验（论文正文引用↔冻结值，68/68）
├── .claude/agents/          # 8 角色的 Claude Code subagents 移植版（已端到端验证）
└── submission/              # 实践文档.md + forum_post.md + 演示视频脚本.md
```

## 核心思想

- **可复用**：智能体按"建模流程"而非"某道题"定义；换题只需新建一个 `cases/<题>/`。
- **自动召唤**：`Router` 按题型(连续/离散/数据/运筹/环境/政策)决定召唤哪些专家、什么顺序。
- ⭐**反幻觉闸门**：任何结论必须过 `Critic` 的对抗式审计（随机性 / 因果 / 过拟合 / 外推）才放行，
  被证伪则回退重做——这是把"作业"变成"真实 AI 工程"的那一步。

---

<sub>作者 Andy（厦门大学马来西亚校区 · 数据科学与大数据技术）· QoderWork CN 大赛赛道八参赛作品</sub>
