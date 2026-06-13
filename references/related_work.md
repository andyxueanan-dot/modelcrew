# 相关工作与设计对标 related_work

> 供 `实践文档.md` / 论坛帖引用。说明 ModelCrew 的设计与学术界/开源界主流多 Agent 建模系统的关系——
> 既证明我们方向正确（被验证），也说明我们借鉴了哪些经验、做了哪些原生适配。

## 对标系统

| 系统 | 来源 | 核心设计 | 我们借鉴了什么 |
|---|---|---|---|
| **MM-Agent** | NeurIPS 2025 ([repo](https://github.com/usail-hkust/LLM-MM-Agent)) | 4 阶段(分析→建模→求解→报告) + Actor-Critic + **分层模型库 HMML(98 方法, 按问题检索)** + MLE-Solver 迭代求解。**助本科队获 MCM/ICM 2025 Finalist Award（top 2.0%）** | ① 选型做成 Actor-Critic（建模手提案、Critic 先质疑再定）② 模型目录分层可检索 ③ 求解迭代自改 |
| **ModelingAgent** | [arXiv 2505.15068](https://arxiv.org/abs/2505.15068) | 4 agent(Idea Proposer / Data Searcher / Model Implementor / Report Writer) + 中央 critic + 迭代自完善；评估用 **ModelingJudge（多专家视角打分）** | ① 给 Scout 增加"数据搜索"能力(无数据时主动找) ② L3 终局 5 视角 panel |
| **Sci-Mind** | [arXiv 2603.27584](https://arxiv.org/abs/2603.27584) | **对抗认知辩证法**：理论家 vs 实用主义者辩论，剪掉"优雅但不可行"的模型；经验记忆回收 + 自验证执行(形式化断言) | ① Critic 升级为**对抗辩论模式** ② Solver 加**自验证断言** ③ `references/` 即我们的"经验记忆" |
| business-science/ai-data-science-team | [repo](https://github.com/business-science/ai-data-science-team) | 数据科学 agent 团队 + 可视化可复现流水线 | 强调可复现流水线 |
| rjmurillo/ai-agents | [repo](https://github.com/rjmurillo/ai-agents) | 7-agent 软件流水线 + **每阶段质量闸门** | 验证我们的 L1 逐阶段 Critic 闸门 |

## 我们的定位

- **共识**：ModelCrew 的"角色分工 + Critic 闸门 + 多层反馈"与上述获奖/学术系统不谋而合——**说明设计方向经过验证**。
- **差异（我们的原创点）**：
  1. **原生 Qoder 实现**——用 Skill + 专家套件落地，可一键安装、跨比赛复用，而非论文里的独立代码框架；
  2. **反幻觉 Critic 为中心**——把"对抗式证伪"放在团队核心，并升级为辩论模式；
  3. **题目无关、即插即用**——换题只换 `cases/`，团队定义不动。

## 未来工作（诚实列出，显示调研深度）
- 把 `model_catalog` 扩成 MM-Agent 式的完整可检索知识库（98+ 方法节点）；
- 给 Scout 接入真实数据源 API（当前为人工提供候选源）；
- 引入 ModelingBench / EngiBench 这类基准做客观自评。
