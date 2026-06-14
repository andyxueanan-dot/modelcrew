# 工件 artifacts · 信用卡违约预测

ModelCrew 各角色跑完后把产出存到这里：

| 文件 | 来自 | 内容 |
|------|------|------|
| `0_routing.md` | Router | 判为数据型/分类 + 召唤策略 + 时序图 |
| `1_analysis.md` | Analyst | 子问题 Q1–Q4 / 假设 / 陷阱 |
| `2_data_brief.md` | Scout | 字段体检、类别不平衡、敏感属性陷阱 |
| `3_model.md` | Modeler | 模型定义（逻辑回归 baseline 等）+ 待审计结论 |
| `4_results.md` + `solve.py` + `results.json` + `figures/` | Solver | 训练评估（AUC/KS/PR/召回）+ 特征重要性 + 可复现 |
| `5_audit.md` | ⭐Critic | 准确率陷阱 / 数据泄漏 / 公平合规 / 阈值，三级裁决 |
| `6_paper.md` | Writer | 信用风险建模报告 + 局限性 |

`screenshots/` 放 Qoder 运行截图（Router 召唤、Critic 风控审计、最终指标）。

> 跑完后由人核验：本地重跑 `solve.py` 确认指标真实可复现，重点检查 Critic 是否真抓到不平衡/泄漏/公平问题。
