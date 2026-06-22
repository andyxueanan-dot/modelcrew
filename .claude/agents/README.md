# ModelCrew · Claude Code subagents 移植版

把 ModelCrew 的 7 个角色（原为 Qoder 技能 / 专家套件）移植成 **Claude Code 原生子代理(subagents)**，证明本框架"内核与工具解耦、可移植"。

## 文件
| 子代理 | name | 对应 Qoder 角色 |
|---|---|---|
| `modelcrew-router.md` | `modelcrew-router` | Router 调度中枢（入口） |
| `modelcrew-analyst.md` | `modelcrew-analyst` | Analyst 审题 |
| `modelcrew-scout.md` | `modelcrew-scout` | Scout 数据侦察 |
| `modelcrew-modeler.md` | `modelcrew-modeler` | Modeler 建模 |
| `modelcrew-solver.md` | `modelcrew-solver` | Solver 求解 |
| `modelcrew-critic.md` | `modelcrew-critic` | ⭐Critic 反幻觉评审（硬闸门） |
| `modelcrew-writer.md` | `modelcrew-writer` | Writer 写作 |

## 怎么用（在 Claude Code 里）
1. 这些文件位于项目级 `.claude/agents/`，**Claude Code 启动时自动注册**为可用子代理类型。
2. 新建 `cases/<新题>/` 放题面 + 数据。
3. 让 Claude Code：「用 `modelcrew-router` 给 `cases/<新题>/` 路由」→ 它判型并给出召唤顺序；
   再按顺序调用 `modelcrew-analyst` → `modelcrew-scout` → `modelcrew-modeler` → `modelcrew-solver` → `modelcrew-critic` → `modelcrew-writer`。
4. 每个子代理把工件写进 `cases/<新题>/artifacts/`，与 Qoder 版完全一致。

> 与 Qoder 版的对应：Qoder「技能 SKILL.md」↔ Claude Code「subagent（带 frontmatter 的 .md）」；
> Qoder「`@` 召唤专家套件」↔ Claude Code「按 name 调用子代理」。角色内容是同一份 Markdown 内核。

## 移植/验证说明
- 这些 subagent 的正文内容与 `agents/0_router…6_writer.md` 源稿一致，仅补了 Claude Code 所需的 `name`/`description`/`tools` frontmatter，并把工件路径明确为 `cases/<题>/artifacts/`。
- 格式校验脚本见 `.claude/agents/_validate.py`（校验 frontmatter 合法、name 合规、字段齐全）。
