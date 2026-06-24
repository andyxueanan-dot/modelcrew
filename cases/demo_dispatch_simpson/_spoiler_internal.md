# 内部埋点说明（仅供复核，**Agent 不应读此文件**）

数据内置 **辛普森悖论(Simpson's paradox)**：
- 按 `policy` 汇总：A 290/350 = **82.9%** ≫ B 182/350 = **52.0%** → naive 误判"A 更优"。
- 按 `severity` 分层：Low 层 B 94.0% > A 90.0%；High 层 B 45.0% > A 40.0% → **B 在两层都更好（翻盘）**。
- 混杂变量 = `severity`：A 主接 Low（容易）呼叫(300/350)、B 主接 High（困难）呼叫(300/350)。

预期闭环：Solver 对 Q1 报汇总率（A 更优）→ Critic 分层证伪"A 更优"(❌，相关≠因果/混杂)→ 触发自纠：
改用分层 / Mantel–Haenszel 合并 OR / 加 severity 控制的 logistic → 结论翻为"B 不劣于甚至更优"。
