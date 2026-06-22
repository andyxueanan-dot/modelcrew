# 工件 artifacts · 应急服务站选址（优化型）

ModelCrew 各角色（Claude Code subagents 版）跑完后把产出存到这里：

| 文件 | 来自 | 内容 |
|------|------|------|
| `0_routing.md` | Router | 判为优化型 + 召唤策略 + 时序图 |
| `1_analysis.md` | Analyst | 子问题 Q1–Q4 / 假设 / 陷阱 |
| `3_model.md` | Modeler | p-中位模型定义 + 方法选择（Weiszfeld+多起点）+ 待审计结论 |
| `4_results.md` + `solve.py` + `results.json` + `figures/` | Solver | 求解 + 局部最优陷阱诊断 + K 敏感性 + 可复现 |
| `5_audit.md` | ⭐Critic | 可行性 / **局部vs全局最优** / K 选择 / 落地风险，三级裁决 |
| `6_paper.md` | Writer | 选址优化报告 + 局限性 |

> 复现：`cd cases/2024_logistics_siting && python artifacts/solve.py`（seed 固定）。
> 数字可追溯：`frozen_numbers.json` + 仓库根 `python tools/check_frozen.py`。
