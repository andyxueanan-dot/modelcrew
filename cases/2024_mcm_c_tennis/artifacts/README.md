# 工件 artifacts

各 Agent 运行后把产出存到这里（文件名与 `agents/` 编号对应）：

| 文件 | 来自 Agent | 内容 |
|------|-----------|------|
| `0_routing.md` | Router | 题型判断 + 召唤策略 + 调度日志 |
| `1_analysis.md` | Analyst | 子问题 / 假设 / 陷阱 |
| `2_data_brief.md` | Scout | 字段说明 / 数据体检 / 清洗日志 |
| `3_model.md` | Modeler | 动量模型(EWMA) + 反转预测 + 待审计结论 |
| `4_results.md` | Solver | 求解结果 / 敏感性 / 图表 |
| `5_audit.md` | ⭐Critic | 随机性检验、热手谬误审计、裁决表（= 辩论版，与 v2 同） |
| `6_paper.md` | Writer | 最终报告草稿 |

### Critic 两版审计（同一结论，不同过程）
| 文件 | 模式 | 说明 |
|------|------|------|
| `5_audit_v1_solo.md` | 单审基线 | 单个 Critic 逐条审计 C1–C6，1✅/1⚠️/4❌ |
| `5_audit_v2_debate.md` | 对抗辩论 | 理论家 vs 怀疑者 vs 裁判，四轮辩论 + 终局裁决（裁决结论与 v1 一致，证明结论稳健） |

### Solver 真实代码与数据
`solve.py`(348 行) · `solver_results.json`(统计量) · `runs_test_details.csv`(逐场 runs test) · `figures/`(动量可视化)
运行方式（脚本中路径相对 case 根目录）：`cd cases/2024_mcm_c_tennis && python artifacts/solve.py`

### ⚠️ 更正补充（Codex 交叉验证）
`CORRECTION_serveaware.md` + `solve_v2_serveaware.py` + `serveaware_results.json`：原 `solve.py` 的 "server-adjusted runs test" 是空操作（未真正控制发球权）；此处用条件置换重做了**真正的发球权控制检验**（全 31 场 0/31 显著、min p≈0.16），核心结论不变且更稳。

### 截图
`screenshots/` 共 11 张（01 建技能 → 11 真代码），供天池作品与论坛帖使用。

> 工作方式：在 Qoder 里跑一个 Agent → 把对话存成对应的 Markdown → 放进本目录 → 截图留档。
