# 明天的待办（ModelCrew 收尾）

> 记于 2026-06-22 晚。今天的成果已全部 commit + push（见 `git log`，最新 `c0a3056`）。
> 仓库：https://github.com/andyxueanan-dot/modelcrew

---

## 🔧 任务 A（最重要）：把应急选址案例的最优值跑稳

**问题**：`cases/2024_logistics_siting/` 里现在报的 headline 最优 = **4,554,431**，
但它**不是全局最优**——终审 Critic 独立重跑，用 4 个种子(1/7/13/99) × 2500 起点都稳定得到 **4,418,714.9**（优 2.98%），
那个更优解在右上簇 [82,80] 放了一个站（约 `[79.65, 79.58]`），正是我方解缺的那个盆地。

**我昨晚测过的**（`solve.py` 的 k-means++ multistart）：
| 起点数 | seeds[42,1,7,99] min |
|---|---|
| 300 | 4,492,982 |
| 1000 | 4,483,644 |
| 2000 | 4,479,643 |

→ 加起点收敛很慢，还没到 4,418,715。说明**纯靠加起点不够**。

**明天怎么修（任选其一，按性价比）**：
1. **改进 multistart**：k-means++ 起点里**强制覆盖每个数据簇**（或对每个社区都试一次做种子），起点数提到 ~2000；
   目标是 seed=42 也能稳定 ≤ 4,418,715。
2. 或**直接采纳更优解**：把 Critic 找到的 4,418,715（含右上簇站点）作为 headline，并说明"经 Critic 独立全局搜索修正"。
3. 跑稳后**验证**：`cd cases/2024_logistics_siting && python artifacts/solve.py`，确认 `multistart_best.cost == sensitivity["4"]`。

**改完后必须同步更新这些**（否则数字打架）：
- `artifacts/frozen_numbers.json`（best_cost / sens_K4 / naive_gap / median_gap 等）；
- 跑 `python tools/check_frozen.py`（必须仍 24/24，或按新数更新冻结值）；
- `artifacts/4_results.md`、`artifacts/6_paper.md`、`artifacts/5_audit.md` 里的数字；
- **让 Critic 子代理用新数字复审一次**（读落盘文件，覆盖 5_audit.md）；
- README 里若引用了该案例数字也要同步。

> 注：即便不修，案例也是**自洽且诚实**的（results.json 报 best-found，5_audit 已用 C4 ❌ 透明说明"这不是全局、Critic 找到更优"）。
> 修它只是为了让 headline 直接是全局最优、叙事更干净；**不修也能交**。

---

## 🔴 任务 B：清理 git 历史里的旧泄露截图（放最后做）

旧的**未打码** `05_qoder_ui_overview.png`（含阿里云账号）仍在 git 历史里。
当前 HEAD 已是打码版，泄露已缓解；这步是彻底抹除历史。**等任务 A 数字定稿后再做**（一次 force-push 覆盖全部）。

参考命令（用 git filter-repo，需先 `pip install git-filter-repo`）：
```bash
cd /e/Code/qoder
# 方案：把该文件的所有历史版本替换为当前打码版（或彻底移除旧 blob）
git filter-repo --path cases/2024_mcm_c_tennis/artifacts/screenshots/05_qoder_ui_overview.png --invert-paths --force
# 然后把打码版重新 add 回来 commit，再 force-push
# （filter-repo 会移除 remote，需重新 git remote add origin <url> 再 push --force）
```
> ⚠️ force-push 会重写公开历史；本仓库是个人作品集、无协作者，安全。做之前先 `git clone` 一份备份到别处更稳。

---

## 🔴 任务 C（你本人做，我代替不了）：核实天池赛道八赛制

用浏览器打开 `tianchi.aliyun.com/forum/post/1053391`，从帖子顶部找**活动主帖**，确认：
- **截止时间 DDL**（别用 6/4 那个海信 CAD 赛的时间！那不是你的比赛）；
- **评分标准**、**是否强制要视频/Skill 包**。
确认后告诉我，我再按真实要求调整提交物。

---

## ✅ 今天已完成（已备份，无需重做）
- 截图05账号打码（隐私）
- frozen_numbers 数字可追溯 + check_frozen（24/24）
- 演示视频逐镜脚本 `submission/演示视频脚本.md`
- 第3个案例·应急选址（优化型）端到端跑通 + Critic 终审
- README 中英版 + 实践文档 → "三案例两题型"
- 7 角色移植成 Claude Code subagents 并验证（`.claude/agents/`）
