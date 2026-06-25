# 相关工作与设计对标 related_work

> 供 `实践文档.md` / 论坛帖引用。说明 ModelCrew 的设计与学术界/开源界主流多 Agent 建模系统的关系——
> 既证明我们方向正确（被验证），也说明我们借鉴了哪些经验、做了哪些原生适配。

## 对标系统

| 系统 | 来源 | 核心设计 | 我们借鉴了什么 |
|---|---|---|---|
| **MM-Agent** | NeurIPS 2025 ([repo](https://github.com/usail-hkust/LLM-MM-Agent)) | 4 阶段(分析→建模→求解→报告) + Actor-Critic + **分层模型库 HMML(98 方法, 按问题检索)** + MLE-Solver 迭代求解。**助本科队获 MCM/ICM 2025 Finalist Award（top 2.0%）** | ① 选型做成 Actor-Critic（建模手提案、Critic 先质疑再定）② 模型目录分层可检索 ③ 求解迭代自改 |
| **ModelingAgent** | [arXiv 2505.15068](https://arxiv.org/abs/2505.15068) | 4 agent(Idea Proposer / Data Searcher / Model Implementor / Report Writer) + 中央 critic + 迭代自完善；评估用 **ModelingJudge（多专家视角打分）** | ① 给 Scout 增加"数据搜索"能力(无数据时主动找) ② L3 终局 5 视角 panel |
| **Sci-Mind** | [arXiv 2603.27584](https://arxiv.org/abs/2603.27584) | **对抗认知辩证法**：理论家 vs 实用主义者辩论，剪掉"优雅但不可行"的模型；经验记忆回收 + 自验证执行(形式化断言) | ① Critic 升级为**对抗辩论模式** ② Solver 加**自验证断言** ③ `references/` 即我们的"经验记忆" |
| **MathModelAgent** ⭐产品化最强对标 | [repo](https://github.com/jihe520/MathModelAgent)（~2.4k★）| 建模手/代码手/论文手三智能体 + Vue/FastAPI **Web UI** + 云代码沙箱(E2B) + ChromaDB **RAG 方法库** + Tavily **联网取真数据** + Typst 17 模板 + HITL | ① 联网搜真实数据/参数(Scout 升级) ② Word/DOCX 等多格式输出 ③（重型）Web UI / RAG 方法库 / 云沙箱 |
| **math-modeling-skills** ⭐机制最像我们 | [repo](https://github.com/xuec699-sudo/math-modeling-skills) | 三角色 + **G1–G6 六道硬闸门**：候选模型先跑 ≤30 行 **PoC 才准用** / frozen numbers + **staleness 失效检测** / 5 人评审团 / 学术诚信 7 类阻断；模型依赖 DAG；DOCX 输出 | ① **选模型前 PoC 冒烟闸**（已采纳，见 Modeler/Solver）② 学术诚信阻断闸 ③ Word/DOCX 输出 |
| **mathmodel-skill** ⭐经验蒸馏最扎实 | [repo](https://github.com/handsomeZR-netizen/mathmodel-skill) | 从 **91 篇真获奖论文(2023-25, A-F全)** 蒸馏 `empirical.json`**实测分位**(篇幅/图/表/公式/摘要/引用) + 命名变体库 + 段落句式库 + anti_patterns 30+ + `score_artifact.py` 按分位注入 evidence | ① **§2E 论文体量实测分位**(图p50=8/公式p50=24/摘要p50=992，含 A-F 分题型) ② 命名变体库→`innovation_boost` ③ 段落句式库→`writing_templates`（iter3 吸收，均注明来源）|
| business-science/ai-data-science-team | [repo](https://github.com/business-science/ai-data-science-team) | 数据科学 agent 团队 + 可视化可复现流水线 | 强调可复现流水线 |
| rjmurillo/ai-agents | [repo](https://github.com/rjmurillo/ai-agents) | 7-agent 软件流水线 + **每阶段质量闸门** | 验证我们的 L1 逐阶段 Critic 闸门 |

## 我们的定位

- **共识**：ModelCrew 的"角色分工 + Critic 闸门 + 多层反馈"与上述获奖/学术系统不谋而合——**说明设计方向经过验证**。
- **护城河（两大中文竞品都没我们深）**：
  1. **对抗式反幻觉 Critic**（三方辩论 + ✅⚠️❌ + 主动查相关≠因果/过拟合/数据泄漏/外推）——MathModelAgent 只做"9 步格式/数值校验"、math-modeling-skills 的"5 人评审团"偏一致性/完整性，**都不是主动证伪**；学术上最近的 Sci-Mind 只是论文，我们是落地实现。
  2. **模拟评委 Judge**（按 rubric 给整篇打分 + 预估奖级 + 只改一处）——两家都没有这一终局评分角色。
  3. **Critic / Judge 职责分离**（过程逐条证伪 vs 终局整篇评分），正对齐 2025–26 LLM-as-judge 的"per-criterion 二元裁决 + holistic 评分"分层最佳实践。
- **差异（原创实现点）**：原生 Qoder Skill/套件 + Claude Code subagents 双实现，一键安装、题目无关即插即用，比"Vue+FastAPI 全栈"分发更轻。

## 未来工作（诚实列出，显示调研深度）
- **已采纳（2026-06 这轮补的）**：选模型前 **PoC 冒烟闸**（借鉴 math-modeling-skills G2）；Judge **双序打分 + 偏置自检**（缓解 LLM 评委位置/自偏好偏置，arXiv 2506.22316 / 2604.06996）；Critic **防"一个 token 廉价过闸"**（arXiv 2507.08794）；Scout **联网取真数据**（搜到的数进 frozen + 附 URL）；Writer **可选 DOCX 输出**。
- **待办**：把 `model_catalog` 扩成 MM-Agent 式可检索知识库（98+ 方法）；引入 **MM-Bench（111 题）/ EngiBench** 做可量化回归测试；学术诚信硬闸（抄袭/编数据/缺引用）；图表 VLM-critic 闭环（借鉴 PaperBanana）。
