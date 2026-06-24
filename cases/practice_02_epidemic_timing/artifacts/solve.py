# -*- coding: utf-8 -*-
"""
solve.py · ModelCrew Solver — 练习02 传染病干预时机（SIR + 干预，连续/ODE）
确定性数值积分 → R0/峰值/最终规模 → 扫 τ 求最晚安全干预日 τ_max → 稳健半径 IWRR → 敏感性。
落盘: results.json + frozen_numbers.json + figures/
"""
import os, json, platform
import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei",
    "Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

# ---- 确定性参数 ----
N = 1_000_000          # 总人口
I0 = 10.0              # 初始感染
GAMMA = 1.0 / 6.0      # 恢复率(平均传染期 6 天)
R0 = 3.0               # 基本再生数
BETA = R0 * GAMMA      # 传播率
H_FRAC = 0.08          # 医疗容量占比
H = H_FRAC * N         # 容量(同时在治上限)
C = 0.6                # 干预把接触率降低 60%（保证坏情形下仍有有限干预窗口，稳健半径才有定义）
T = 300.0              # 模拟天数
DRIFT = 0.20           # 稳健半径用的坏情形: β 上浮 20%


def sir_rhs(t, y, beta):
    S, I, R = y
    inf = beta * S * I / N
    return [-inf, inf - GAMMA * I, GAMMA * I]


def simulate(beta_base, c, tau, T=T):
    """两段积分: [0,tau] 用 beta_base; [tau,T] 用 (1-c)*beta_base。返回 (t, I)。"""
    teval_fine = 0.1
    grid = lambda a, b: np.clip(np.arange(a, b + teval_fine, teval_fine), a, b)
    if tau <= 0:
        ts = grid(0, T)
        sol = solve_ivp(sir_rhs, (0, T), [N - I0, I0, 0.0], args=((1 - c) * beta_base,),
                        t_eval=ts, rtol=1e-8, atol=1e-6, method="RK45")
        return sol.t, sol.y[1]
    # phase 1
    ts1 = grid(0, tau)
    s1 = solve_ivp(sir_rhs, (0, tau), [N - I0, I0, 0.0], args=(beta_base,),
                   t_eval=ts1, rtol=1e-8, atol=1e-6, method="RK45")
    y_tau = s1.y[:, -1]
    # phase 2
    ts2 = grid(tau, T)
    s2 = solve_ivp(sir_rhs, (tau, T), y_tau, args=((1 - c) * beta_base,),
                   t_eval=ts2, rtol=1e-8, atol=1e-6, method="RK45")
    t = np.concatenate([s1.t[:-1], s2.t])
    I = np.concatenate([s1.y[1][:-1], s2.y[1]])
    return t, I


def peak_of(beta_base, c, tau):
    t, I = simulate(beta_base, c, tau)
    k = int(np.argmax(I))
    return I[k], t[k]


def final_size(r0):
    """最终规模方程 1 - z = exp(-R0 z) 的非平凡根。"""
    return brentq(lambda z: 1 - z - np.exp(-r0 * z), 1e-9, 1 - 1e-9)


def latest_safe_tau(beta_base, c, H, tau_grid):
    """峰值随 τ 单调增 → 最大的、峰值≤H 的整数 τ。无解返回 None。"""
    last = None
    for tau in tau_grid:
        pk, _ = peak_of(beta_base, c, tau)
        if pk <= H:
            last = tau
        else:
            break
    return last


def main():
    tau_grid = list(range(0, 121))   # 扫 0..120 天

    # ---- Q1 无干预基线 ----
    t0, I0_traj = simulate(BETA, 0.0, -1)   # c=0 即无干预
    base_peak = float(np.max(I0_traj)); base_peak_day = float(t0[int(np.argmax(I0_traj))])
    base_peak_frac = base_peak / N
    fsize = final_size(R0)                   # 最终累计感染比例
    s_at_peak = 1.0 / R0                     # 峰值时 S/N 理论值

    # ---- Q2 干预: 最晚安全起始日 ----
    tau_max = latest_safe_tau(BETA, C, H, tau_grid)
    # 坏情形 β 上浮 DRIFT
    tau_max_drift = latest_safe_tau(BETA * (1 + DRIFT), C, H, tau_grid)
    iwrr = None if (tau_max is None or tau_max_drift is None) else (tau_max - tau_max_drift)
    # 推荐稳健起始日 = 坏情形下仍安全的最晚日
    tau_safe = tau_max_drift

    # 干预后峰值(在 τ_max 与 τ_safe 起干预)
    pk_at_taumax, _ = peak_of(BETA, C, tau_max)
    pk_at_tausafe, _ = peak_of(BETA, C, tau_safe)

    # ---- Q3 敏感性: c 与 H 变动下的 τ_max ----
    sens = {}
    for c in (0.3, 0.4, 0.6):
        sens[f"tau_max_c{int(c*100)}"] = latest_safe_tau(BETA, c, H, tau_grid)
    for hf in (0.05, 0.10):
        sens[f"tau_max_H{int(hf*100)}"] = latest_safe_tau(BETA, C, hf * N, tau_grid)
    # 稳健半径关于漂移幅度
    for d in (0.10, 0.30):
        tm = latest_safe_tau(BETA * (1 + d), C, H, tau_grid)
        sens[f"iwrr_drift{int(d*100)}"] = None if (tau_max is None or tm is None) else tau_max - tm

    results = dict(
        meta=dict(case="practice_02_epidemic_timing",
                  N=N, I0=I0, gamma=round(GAMMA, 6), R0=R0, beta=round(BETA, 6),
                  capacity_frac=H_FRAC, intervention_c=C, drift=DRIFT, T_days=T,
                  python=platform.python_version(), numpy=np.__version__,
                  scipy=__import__("scipy").__version__, method="solve_ivp/RK45 two-phase"),
        q1=dict(R0=R0, baseline_peak=round(base_peak, 1),
                baseline_peak_frac=round(base_peak_frac, 4),
                baseline_peak_day=round(base_peak_day, 1),
                susceptible_frac_at_peak=round(s_at_peak, 4),
                final_size_frac=round(fsize, 4)),
        q2=dict(capacity=H, capacity_frac=H_FRAC,
                tau_max_days=tau_max, peak_at_tau_max=round(pk_at_taumax, 1),
                tau_max_drift20_days=tau_max_drift,
                robustness_radius_days=iwrr,
                tau_safe_recommended=tau_safe, peak_at_tau_safe=round(pk_at_tausafe, 1)),
        q3_sensitivity=sens,
    )
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ---- 图1: I(t) 无干预 vs τ_max vs τ_safe ----
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(t0, I0_traj / N * 100, "k-", lw=2, label=f"无干预(峰值 {base_peak_frac*100:.1f}%)")
    for tau, lab, col in [(tau_max, f"τ_max={tau_max}天起干预", "tab:orange"),
                          (tau_safe, f"稳健建议 τ={tau_safe}天起干预", "tab:green")]:
        t, I = simulate(BETA, C, tau)
        ax.plot(t, I / N * 100, "-", color=col, lw=1.8, label=lab)
    ax.axhline(H_FRAC * 100, ls="--", color="red", label=f"医疗容量 {H_FRAC*100:.0f}%")
    ax.set_title("同时在治感染比例：无干预 vs 不同起始日干预")
    ax.set_xlabel("天"); ax.set_ylabel("同时在治感染 (%人口)"); ax.legend(fontsize=8); ax.set_xlim(0, 200)
    fig.tight_layout(); fig.savefig(os.path.join(FIGDIR, "fig1_curves.png"), dpi=140); plt.close(fig)

    # ---- 图2: 峰值 vs 干预起始日 τ, 标 H 线与 τ_max/τ_safe ----
    taus = np.arange(0, 91)
    peaks = np.array([peak_of(BETA, C, int(tt))[0] for tt in taus]) / N * 100
    peaks_d = np.array([peak_of(BETA * (1 + DRIFT), C, int(tt))[0] for tt in taus]) / N * 100
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(taus, peaks, "b-o", ms=2.5, label="名义 R0=3.0")
    ax.plot(taus, peaks_d, "m--", lw=1.5, label="坏情形 β+20% (R0=3.6)")
    ax.axhline(H_FRAC * 100, ls="--", color="red", label=f"容量 {H_FRAC*100:.0f}%")
    ax.axvline(tau_max, color="tab:orange", ls=":", label=f"τ_max={tau_max}")
    ax.axvline(tau_safe, color="tab:green", ls=":", label=f"τ_safe={tau_safe}")
    ax.annotate("", xy=(tau_max, 2), xytext=(tau_safe, 2),
                arrowprops=dict(arrowstyle="<->", color="purple"))
    ax.text((tau_max + tau_safe) / 2, 3, f"IWRR={iwrr}天", color="purple", ha="center", fontsize=9)
    ax.set_title("干预后峰值随起始日 τ 变化（稳健半径 = 名义与坏情形 τ_max 之差）")
    ax.set_xlabel("干预起始日 τ (天)"); ax.set_ylabel("峰值同时在治 (%人口)"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIGDIR, "fig2_window.png"), dpi=140); plt.close(fig)

    # ---- frozen_numbers (策展 schema) ----
    rel = "artifacts/results.json"
    def f(path, nd):
        v = results
        for s in path.split("."):
            v = v[s]
        return round(float(v), nd)
    frozen = [
        dict(id="R0", label="基本再生数 R₀", value=f("q1.R0", 2), tol=0.005, source=rel, path="q1.R0", cited_in="6_paper.md"),
        dict(id="baseline_peak_frac", label="无干预峰值同时感染占比", value=f("q1.baseline_peak_frac", 4), tol=0.005, source=rel, path="q1.baseline_peak_frac", cited_in="6_paper.md"),
        dict(id="baseline_peak_day", label="无干预峰值时点(天)", value=f("q1.baseline_peak_day", 1), tol=0.5, source=rel, path="q1.baseline_peak_day", cited_in="6_paper.md"),
        dict(id="final_size_frac", label="最终累计感染比例", value=f("q1.final_size_frac", 4), tol=0.005, source=rel, path="q1.final_size_frac", cited_in="6_paper.md"),
        dict(id="tau_max_days", label="名义最晚安全干预日(天)", value=f("q2.tau_max_days", 1), tol=0.5, source=rel, path="q2.tau_max_days", cited_in="6_paper.md"),
        dict(id="tau_safe", label="稳健建议干预起始日(天)", value=f("q2.tau_safe_recommended", 1), tol=0.5, source=rel, path="q2.tau_safe_recommended", cited_in="6_paper.md"),
        dict(id="iwrr_days", label="干预窗口稳健半径 IWRR(天)", value=f("q2.robustness_radius_days", 1), tol=0.5, source=rel, path="q2.robustness_radius_days", cited_in="6_paper.md"),
    ]
    with open(os.path.join(HERE, "frozen_numbers.json"), "w", encoding="utf-8") as fh:
        json.dump(dict(case="practice_02_epidemic_timing", note="论文数字唯一真相源",
                       inputs=["artifacts/solve.py"], numbers=frozen), fh, ensure_ascii=False, indent=2)

    print(f"R0={R0} | baseline peak {base_peak_frac*100:.1f}% @ day {base_peak_day:.1f} | final size {fsize*100:.1f}%")
    print(f"capacity H={H_FRAC*100:.0f}% | tau_max(nominal)={tau_max} | tau_max(+20%)={tau_max_drift} | IWRR={iwrr} days | tau_safe={tau_safe}")
    print("sensitivity:", {k: v for k, v in sens.items()})


if __name__ == "__main__":
    main()
