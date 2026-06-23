# 收尾清单（ModelCrew）

> 更新于 2026-06-23：昨日待办的 A、B 已完成，只剩需要你本人做的 C。

## ✅ 任务 A：应急选址案例的最优值跑稳（已完成）
- 根因：初版 k-means++ 随机多起点漏掉"放弃左下簇"的全局盆地。
- 修复：`solve.py` 新增**数据驱动结构化起点**，稳定找到并三重复核全局最优 **4,418,714.9**。
- `modelcrew-critic` 子代理终审：亲自尝试证伪未果，**C4 由 ❌ 翻为 ✅**（强经验全局，无形式化证书）。
- 自纠记录见 `cases/2024_logistics_siting/artifacts/CORRECTION_global.md`；frozen 24/24。

## ✅ 任务 B：清理 git 历史里的旧泄露截图（已完成）
- 用 `git filter-repo` 把旧·未打码的 `05_qoder_ui_overview.png`（含阿里云账号）替换为打码版。
- 旧泄露 blob `635c7d4…` 已从全库彻底清除（含删掉 Codex 检查点 ref），已 force-push。
- 本会话安全备份：`/tmp/qoder_backup.git`（确认无误后可删）。
- 提示：GitHub 端旧 commit 已不可达，旧 blob 会随 GitHub 自身 gc 清掉；若要立即彻底清除可联系 GitHub 支持（个人邮箱，风险低，通常不必）。

## 🔴 任务 C（你本人做，我代替不了）：核实天池赛道八赛制
用浏览器打开 `tianchi.aliyun.com/forum/post/1053391`，从帖子顶部找**活动主帖**，确认：
- **截止时间 DDL**（别用 6/4 那个海信 CAD 赛的时间！那不是你的比赛）；
- **评分标准**、**是否强制要视频/Skill 包**。
确认后告诉我，我再按真实要求调整提交物。

---

## ✅ 全部已完成（已备份到 GitHub）
- 三个案例（网球数据型 / 信用金融型 / 选址优化型），覆盖数据型+优化型两大题型
- 反幻觉 Critic 两次自纠闭环（网球 Codex / 选址全局最优）
- frozen_numbers 数字可追溯（24/24）+ 演示视频脚本
- 7 角色移植成 Claude Code subagents 并端到端验证
- 截图隐私打码 + git 历史清理
- README 中英双语（含切换按钮 / 复用说明 / 用什么软件跑）
