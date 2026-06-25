# -*- coding: utf-8 -*-
"""练习题03「穿越沙漠」关键结果可视化。读 results.json，出图到 figures/。确定性，无随机。"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
os.makedirs(FIG, exist_ok=True)

# 中文字体（尽量找系统中文字体；找不到则回退英文标签）
ZH = None
for cand in ["Microsoft YaHei", "SimHei", "SimSun", "DengXian"]:
    try:
        font_manager.findfont(cand, fallback_to_default=False)
        ZH = cand; break
    except Exception:
        continue
if ZH:
    plt.rcParams["font.sans-serif"] = [ZH]
    plt.rcParams["axes.unicode_minus"] = False
def L(zh, en): return zh if ZH else en

with open(os.path.join(HERE, "results.json"), encoding="utf-8") as f:
    R = json.load(f)

# ---------- 图1：Q1 最优方案逐日水/食/现金 ----------
rows = R["Q1"]["daily_table"]
days = [r["day"] for r in rows]
water = [r["water"] for r in rows]
food = [r["food"] for r in rows]
cash = [r["cash"] for r in rows]
load = [r["load"] for r in rows]

fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(days, water, "o-", color="#1f77b4", label=L("剩余水(箱)", "Water (boxes)"))
ax1.plot(days, food, "s-", color="#2ca02c", label=L("剩余食物(箱)", "Food (boxes)"))
ax1.set_xlabel(L("天 t", "Day t"))
ax1.set_ylabel(L("资源剩余(箱)", "Resource (boxes)"))
ax1.set_xticks(days)
ax2 = ax1.twinx()
ax2.plot(days, cash, "^--", color="#d62728", label=L("现金(元)", "Cash (yuan)"))
ax2.set_ylabel(L("现金(元)", "Cash (yuan)"), color="#d62728")
ax2.tick_params(axis="y", labelcolor="#d62728")
lines1, lab1 = ax1.get_legend_handles_labels()
lines2, lab2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, lab1 + lab2, loc="center right")
route = R["Q1"]["route"]
ax1.set_title(L(f"Q1 最优方案逐日资源/现金（路线 {('→'.join(map(str,route)))}，最优财富 {R['Q1']['optimal_wealth']:.0f} 元）",
                f"Q1 Optimal daily resources/cash (route {('-'.join(map(str,route)))}, wealth {R['Q1']['optimal_wealth']:.0f})"))
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig1_q1_daily_plan.png"), dpi=140)
plt.close(fig)

# ---------- 图2：Q3 矿山收益 M 敏感性 + 临界点 ----------
mr = R["Q3"]["mine_revenue_M"]
Ms = [d["value"] for d in mr]
Ws = [d["optimal_wealth"] for d in mr]
mining = [d.get("mining_is_optimal") for d in mr]
Mthr = R["Q3"]["critical_points"]["mine_revenue_threshold_for_mining"]
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(Ms, Ws, "o-", color="#1f77b4")
# 标注挖矿划算区
for x, y, m in zip(Ms, Ws, mining):
    ax.plot(x, y, "o", color=("#d62728" if m else "#1f77b4"))
if Mthr is not None:
    ax.axvline(Mthr, color="#ff7f0e", ls="--", label=L(f"挖矿划算临界 M*={Mthr}", f"Mining threshold M*={Mthr}"))
ax.axhline(R["Q1"]["optimal_wealth"], color="gray", ls=":", label=L("基线(直达)9410", "Baseline (direct) 9410"))
ax.set_xlabel(L("矿山收益 M (元/天)", "Mine revenue M (yuan/day)"))
ax.set_ylabel(L("最优最终财富 (元)", "Optimal final wealth (yuan)"))
ax.set_title(L("Q3 矿山收益敏感性：红点=挖矿划算，蓝点=直达更优",
               "Q3 Mine-revenue sensitivity: red=mining optimal, blue=direct optimal"))
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig2_q3_mine_revenue.png"), dpi=140)
plt.close(fig)

# ---------- 图3：Q2 安全垫 → 财富/稳健性权衡 ----------
bufs = sorted(int(k.split("_")[1]) for k in R["Q2"] if k.startswith("buffer_"))
wealths = [R["Q2"][f"buffer_{b}"]["final_wealth"] for b in bufs]
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(bufs, wealths, "o-", color="#2ca02c", label=L("真实序列下在线财富", "Online wealth (true seq)"))
ax.axhline(R["Q1"]["optimal_wealth"], color="gray", ls=":", label=L("Q1上帝视角最优 9410", "Q1 offline optimal 9410"))
# 标注对抗序列最小可幸存 buffer（取最大者作为稳健下限）
adv = R["Q2"]["adversarial"]
min_safe = [d["min_survivable_buffer"] for d in adv.values() if d["min_survivable_buffer"] is not None]
if min_safe:
    rb = max(min_safe)
    ax.axvline(rb, color="#d62728", ls="--",
               label=L(f"对抗序列稳健所需 buffer≥{rb}", f"Robust buffer≥{rb} (adversarial)"))
ax.set_xlabel(L("安全垫 buffer (沙暴当量天数)", "Safety buffer (storm-equiv days)"))
ax.set_ylabel(L("在线策略最终财富 (元)", "Online final wealth (yuan)"))
ax.set_title(L("Q2 安全垫 vs 财富/稳健性权衡（buffer 越大越稳健但财富越低）",
               "Q2 Safety buffer vs wealth/robustness trade-off"))
ax.legend()
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig3_q2_buffer_tradeoff.png"), dpi=140)
plt.close(fig)

# ---------- 图4：Q3 负重上限 + 消耗缩放 双子图 ----------
lm = R["Q3"]["load_max"]; Wx = [d["value"] for d in lm]; Wy = [d["optimal_wealth"] for d in lm]
Wmin = [d.get("mining_is_optimal") for d in lm]
Wthr = R["Q3"]["critical_points"]["load_threshold_for_mining"]
cs = R["Q3"]["consume_scale"]; Sx = [d["value"] for d in cs]; Sy = [d["optimal_wealth"] for d in cs]
fig, (axa, axb) = plt.subplots(1, 2, figsize=(12, 5))
axa.plot(Wx, Wy, "o-", color="#1f77b4")
for x, y, m in zip(Wx, Wy, Wmin):
    axa.plot(x, y, "o", color=("#d62728" if m else "#1f77b4"))
if Wthr is not None:
    axa.axvline(Wthr, color="#ff7f0e", ls="--", label=L(f"挖矿可行临界 W*={Wthr}kg", f"Mining feasible W*={Wthr}kg"))
axa.axvline(1200, color="gray", ls=":", label=L("题面负重 1200kg", "Given load 1200kg"))
axa.set_xlabel(L("负重上限 (kg)", "Load limit (kg)")); axa.set_ylabel(L("最优财富 (元)", "Optimal wealth (yuan)"))
axa.set_title(L("负重上限敏感性", "Load-limit sensitivity")); axa.legend()
axb.plot(Sx, Sy, "s-", color="#9467bd")
axb.set_xlabel(L("消耗缩放系数", "Consumption scale")); axb.set_ylabel(L("最优财富 (元)", "Optimal wealth (yuan)"))
axb.set_title(L("天气消耗量敏感性", "Consumption sensitivity"))
fig.suptitle(L("Q3 关键参数敏感性（红点=该参数下挖矿变为最优）",
               "Q3 Key-parameter sensitivity (red=mining becomes optimal)"))
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig4_q3_load_consume.png"), dpi=140)
plt.close(fig)

print("figures written to", FIG)
for fn in sorted(os.listdir(FIG)):
    print("  ", fn)
