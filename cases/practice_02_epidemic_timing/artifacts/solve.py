#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Solver for practice_02_epidemic_timing.

Faithfully implements the deterministic SIR-ODE + step intervention model
defined in 3_model.md. Deterministic / byte-reproducible: no randomness, fixed
solver settings. Produces results.json, frozen_numbers.json (number-source of
truth), and figures/.

Symbol disambiguation (per Modeler T1):
  Rrepro = basic reproduction number (= 3.0). NEVER call it R0.
  Rmv    = removed compartment state.

Run: python solve.py
"""
import json
import os
import platform
import sys

import numpy as np
import scipy
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

# ----------------------------------------------------------------------------
# Fixed solver settings (reproducibility, per 3_model.md §4)
# ----------------------------------------------------------------------------
METHOD = "LSODA"
RTOL = 1e-9
ATOL = 1e-9
MAX_STEP = 0.5  # cap step so peak is resolved; LSODA is stiff-aware
T_END = 600.0   # long enough for full epidemic to burn out at all c scanned

# ----------------------------------------------------------------------------
# Baseline parameters (3_model.md §1.2)
# ----------------------------------------------------------------------------
N = 1_000_000.0
I0 = 10.0
GAMMA = 1.0 / 6.0           # recovery rate /day (6-day infectious period)
RREPRO = 3.0                # basic reproduction number
BETA0 = RREPRO * GAMMA      # 0.5 /day
H_FRAC = 0.08               # capacity fraction
H = H_FRAC * N              # 80,000 simultaneously-in-treatment


# ----------------------------------------------------------------------------
# Core ODE with step intervention: beta drops to beta0*(1-c) at t=tau
# ----------------------------------------------------------------------------
def make_rhs(beta0, gamma, n, tau, c):
    def rhs(t, y):
        S, I, Rmv = y
        beta = beta0 if t < tau else beta0 * (1.0 - c)
        infection = beta * S * I / n
        return [-infection, infection - gamma * I, gamma * I]

    return rhs


def integrate(beta0, gamma, n, i0, tau, c, t_end=T_END):
    """Integrate SIR with step intervention. Returns scipy solution object.

    tau is added as an explicit breakpoint so LSODA does not step over the
    discontinuity in beta.
    """
    y0 = [n - i0, i0, 0.0]
    rhs = make_rhs(beta0, gamma, n, tau, c)
    if 0.0 < tau < t_end:
        # split integration at tau to handle the beta discontinuity cleanly
        sol1 = solve_ivp(rhs, [0.0, tau], y0, method=METHOD, rtol=RTOL,
                         atol=ATOL, dense_output=True, max_step=MAX_STEP)
        y_tau = sol1.y[:, -1]
        sol2 = solve_ivp(rhs, [tau, t_end], y_tau, method=METHOD, rtol=RTOL,
                         atol=ATOL, dense_output=True, max_step=MAX_STEP)
        return _Stitched(sol1, sol2, tau, t_end)
    sol = solve_ivp(rhs, [0.0, t_end], y0, method=METHOD, rtol=RTOL,
                    atol=ATOL, dense_output=True, max_step=MAX_STEP)
    return sol


class _Stitched:
    """Glue two dense_output solutions at tau so .sol() works seamlessly."""

    def __init__(self, s1, s2, tau, t_end):
        self.s1, self.s2, self.tau, self.t_end = s1, s2, tau, t_end
        self.y = np.hstack([s1.y, s2.y])
        self.t = np.hstack([s1.t, s2.t])

    def sol(self, ts):
        ts = np.asarray(ts, dtype=float)
        out = np.empty((3, ts.size))
        m = ts <= self.tau
        if m.any():
            out[:, m] = self.s1.sol(ts[m])
        if (~m).any():
            out[:, ~m] = self.s2.sol(ts[~m])
        return out


def peak_I(beta0, gamma, n, i0, tau, c, t_end=T_END, ngrid=240001):
    """Return (Imax, t_peak) via dense grid + parabolic refine.

    Grid is fine (dt ~ t_end/ngrid) so the peak is located accurately;
    parabolic interpolation around the max sharpens t_peak.
    """
    sol = integrate(beta0, gamma, n, i0, tau, c, t_end)
    ts = np.linspace(0.0, t_end, ngrid)
    I = sol.sol(ts)[1]
    ip = int(np.argmax(I))
    Imax = float(I[ip])
    t_peak = float(ts[ip])
    # parabolic refinement
    if 0 < ip < len(ts) - 1:
        y0_, y1_, y2_ = I[ip - 1], I[ip], I[ip + 1]
        denom = (y0_ - 2 * y1_ + y2_)
        if denom != 0:
            delta = 0.5 * (y0_ - y2_) / denom
            dt = ts[1] - ts[0]
            t_peak = float(ts[ip] + delta * dt)
            Imax = float(y1_ - 0.25 * (y0_ - y2_) * delta)
    return Imax, t_peak, sol


# ----------------------------------------------------------------------------
# Q1: no-intervention characterization
# ----------------------------------------------------------------------------
def solve_Q1():
    # no intervention: c=0 (tau irrelevant)
    Imax, t_peak, sol = peak_I(BETA0, GAMMA, N, I0, tau=0.0, c=0.0)
    # final size via long integration
    ts = np.linspace(0.0, T_END, 240001)
    y = sol.sol(ts)
    z_num = 1.0 - y[0, -1] / N
    I_end = y[1, -1]
    # conservation check
    cons = np.abs(y.sum(axis=0) - N).max()
    # final-size equation root
    z_eqn = brentq(lambda z: z - (1.0 - np.exp(-RREPRO * z)), 1e-9, 1 - 1e-12,
                   xtol=1e-12, rtol=1e-14)
    # analytic peak fraction (Modeler eq)
    analytic_peak_frac = 1.0 - 1.0 / RREPRO - np.log(RREPRO) / RREPRO
    # analytic reproduction number check: linearized growth rate r = beta-gamma
    r_growth = BETA0 - GAMMA
    Rrepro_check = BETA0 / GAMMA
    # peak analytic anchor: S = N/Rrepro at peak
    S_at_peak = sol.sol([t_peak])[0, 0]
    S_anchor = N / RREPRO
    return {
        "Rrepro": RREPRO,
        "Rrepro_check_beta_over_gamma": float(Rrepro_check),
        "beta0": float(BETA0),
        "gamma": float(GAMMA),
        "linear_growth_rate_per_day": float(r_growth),
        "Imax": float(Imax),
        "Imax_frac": float(Imax / N),
        "Imax_analytic_frac": float(analytic_peak_frac),
        "Imax_analytic": float(analytic_peak_frac * N),
        "t_peak_days": float(t_peak),
        "S_at_peak": float(S_at_peak),
        "S_anchor_N_over_Rrepro": float(S_anchor),
        "S_at_peak_rel_err": float(abs(S_at_peak - S_anchor) / S_anchor),
        "final_size_z_numeric": float(z_num),
        "final_size_z_equation": float(z_eqn),
        "final_size_abs_diff": float(abs(z_num - z_eqn)),
        "I_at_t_end": float(I_end),
        "conservation_max_abs_err": float(cons),
        "h_capacity_abs": float(H),
        "Imax_over_h": float(Imax / H),
    }


# ----------------------------------------------------------------------------
# Q2: intervention. Peak functional P(tau,c) and critical tau*(c)
# ----------------------------------------------------------------------------
def g_func(tau, c, beta0=BETA0, threshold=H):
    """g(tau,c) = P(tau,c) - threshold. <=0 means capacity respected."""
    Imax, _, _ = peak_I(beta0, GAMMA, N, I0, tau, c)
    return Imax - threshold


def find_tau_star(c, beta0=BETA0, threshold=H, tau_hi=None):
    """Largest tau with P(tau,c) <= threshold (latest feasible day).

    Relies on monotonicity of P in tau (verified separately, C7). Returns
    (tau_star, status). status in {'feasible_interval','infeasible_at_0',
    'always_feasible'}.
    """
    if tau_hi is None:
        # no-intervention peak time gives a natural upper bracket
        _, tpk, _ = peak_I(beta0, GAMMA, N, I0, 0.0, 0.0)
        tau_hi = tpk + 60.0
    g0 = g_func(0.0, c, beta0, threshold)
    if g0 > 0:
        return None, "infeasible_at_0"
    ghi = g_func(tau_hi, c, beta0, threshold)
    if ghi <= 0:
        return float(tau_hi), "always_feasible_within_bracket"
    tau_star = brentq(lambda t: g_func(t, c, beta0, threshold), 0.0, tau_hi,
                      xtol=1e-4, rtol=1e-8)
    return float(tau_star), "feasible_interval"


def solve_Q2():
    c_star = 1.0 - 1.0 / RREPRO  # 0.6667 threshold strength
    c_baseline = 0.6
    out = {
        "c_star_threshold": float(c_star),
        "c_baseline": c_baseline,
        "h_capacity_abs": float(H),
    }

    # C5: verify R_e and immediate-decline behavior across c
    Re = {f"{c:.2f}": float(RREPRO * (1 - c)) for c in [0.4, 0.5, 0.6, 0.7]}
    out["R_e_after_intervention"] = Re

    # tau* for a sweep of c (full feasible domain, Modeler §2.3)
    tau_star_by_c = {}
    for c in [0.4, 0.5, 0.6, 0.7]:
        ts_, status = find_tau_star(c)
        tau_star_by_c[f"{c:.2f}"] = {
            "tau_star": ts_, "status": status,
            "R_e": float(RREPRO * (1 - c)),
        }
    out["tau_star_by_c"] = tau_star_by_c

    # baseline headline: tau*(0.6)
    out["tau_star_baseline_c0.6"] = tau_star_by_c["0.60"]["tau_star"]

    # 20% margin operational version (P <= 0.8h)
    ts_margin, st_margin = find_tau_star(c_baseline, threshold=0.8 * H)
    out["tau_star_baseline_c0.6_20pct_margin"] = ts_margin
    out["tau_star_baseline_margin_status"] = st_margin

    # C7: monotonicity check of P(tau, c=0.6) over a tau grid
    taus = np.linspace(0.0, 60.0, 61)
    Ps = np.array([peak_I(BETA0, GAMMA, N, I0, t, c_baseline)[0] for t in taus])
    diffs = np.diff(Ps)
    out["monotonicity_P_vs_tau_c0.6"] = {
        "min_diff": float(diffs.min()),
        "is_monotone_nondecreasing": bool((diffs >= -1.0).all()),  # 1-person tol
        "P_at_tau0": float(Ps[0]),
        "P_at_tau60": float(Ps[-1]),
    }

    # C8: find a c so small that P(0,c) > h (infeasible even at day 0)
    infeasible_cs = []
    for c in [0.1, 0.2, 0.3, 0.35, 0.4]:
        g0 = g_func(0.0, c)
        if g0 > 0:
            infeasible_cs.append({"c": c, "P0_minus_h": float(g0),
                                   "P0": float(g0 + H)})
    out["infeasible_at_day0_examples"] = infeasible_cs

    return out, taus.tolist(), Ps.tolist()


# ----------------------------------------------------------------------------
# Q2-c / Q3: robustness (worst-case box) + sensitivity
# ----------------------------------------------------------------------------
def find_tau_star_param(c, Rrepro, gamma, threshold=H):
    """tau*(c) for arbitrary (Rrepro, gamma). Returns (tau_star, status)."""
    beta0 = Rrepro * gamma

    def gp(tau):
        Imax, _, _ = peak_I(beta0, gamma, N, I0, tau, c)
        return Imax - threshold

    # bracket from this parameterization's no-intervention peak
    _, tpk, _ = peak_I(beta0, gamma, N, I0, 0.0, 0.0)
    tau_hi = tpk + 60.0
    if gp(0.0) > 0:
        return None, "infeasible_at_0"
    if gp(tau_hi) <= 0:
        return float(tau_hi), "always_feasible_within_bracket"
    return float(brentq(gp, 0.0, tau_hi, xtol=1e-4, rtol=1e-8)), "feasible_interval"


def solve_Q3(taus_grid, Ps_grid):
    c_baseline = 0.6
    out = {}

    # nominal tau*
    tau_nom, _ = find_tau_star_param(c_baseline, RREPRO, GAMMA)
    out["tau_star_nominal_c0.6"] = tau_nom

    # ---- single-parameter sweeps ----
    # Rrepro sweep
    Rsweep = [2.5, 2.75, 3.0, 3.25, 3.5]
    tau_vs_R = {}
    for Rr in Rsweep:
        ts_, st = find_tau_star_param(c_baseline, Rr, GAMMA)
        tau_vs_R[f"{Rr:.2f}"] = {"tau_star": ts_, "status": st}
    out["tau_star_vs_Rrepro_c0.6"] = tau_vs_R

    # gamma sweep (infectious period 5-7 days)
    periods = [5, 5.5, 6, 6.5, 7]
    tau_vs_gamma = {}
    for d in periods:
        g_ = 1.0 / d
        ts_, st = find_tau_star_param(c_baseline, RREPRO, g_)
        tau_vs_gamma[f"period_{d}d"] = {"gamma": float(g_), "tau_star": ts_,
                                         "status": st}
    out["tau_star_vs_infectious_period_c0.6"] = tau_vs_gamma

    # h sweep (6%-10% N)
    h_vs = {}
    for hf in [0.06, 0.07, 0.08, 0.09, 0.10]:
        ts_, st = find_tau_star_param(c_baseline, RREPRO, GAMMA,
                                      threshold=hf * N)
        h_vs[f"{hf:.2f}"] = {"h_abs": float(hf * N), "tau_star": ts_,
                             "status": st}
    out["tau_star_vs_h_c0.6"] = h_vs

    # c sweep already partly in Q2; add elasticity-relevant fine points
    tau_vs_c = {}
    for c in [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]:
        ts_, st = find_tau_star_param(c, RREPRO, GAMMA)
        tau_vs_c[f"{c:.2f}"] = {"tau_star": ts_, "status": st}
    out["tau_star_vs_c"] = tau_vs_c

    # ---- local elasticities at nominal point: (p/tau*) dtau*/dp ----
    def elasticity(param):
        h_rel = 0.02  # 2% perturbation
        if param == "Rrepro":
            pm, pp = RREPRO * (1 - h_rel), RREPRO * (1 + h_rel)
            tm, _ = find_tau_star_param(c_baseline, pm, GAMMA)
            tp, _ = find_tau_star_param(c_baseline, pp, GAMMA)
            p0 = RREPRO
        elif param == "gamma":
            pm, pp = GAMMA * (1 - h_rel), GAMMA * (1 + h_rel)
            tm, _ = find_tau_star_param(c_baseline, RREPRO, pm)
            tp, _ = find_tau_star_param(c_baseline, RREPRO, pp)
            p0 = GAMMA
        elif param == "c":
            pm, pp = c_baseline * (1 - h_rel), c_baseline * (1 + h_rel)
            tm, _ = find_tau_star_param(pm, RREPRO, GAMMA)
            tp, _ = find_tau_star_param(pp, RREPRO, GAMMA)
            p0 = c_baseline
        elif param == "h":
            pm, pp = H * (1 - h_rel), H * (1 + h_rel)
            tm, _ = find_tau_star_param(c_baseline, RREPRO, GAMMA, threshold=pm)
            tp, _ = find_tau_star_param(c_baseline, RREPRO, GAMMA, threshold=pp)
            p0 = H
        if tm is None or tp is None or tau_nom is None or tau_nom == 0:
            return None
        dtau_dp = (tp - tm) / (pp - pm)
        return float((p0 / tau_nom) * dtau_dp)

    out["elasticity_tau_star"] = {
        "Rrepro": elasticity("Rrepro"),
        "c": elasticity("c"),
        "h": elasticity("h"),
        "gamma": elasticity("gamma"),
    }

    # ---- robust worst-case box (Modeler §3.2) ----
    # Worst case (max peak): Rrepro high, gamma -> we evaluate both ends, c
    # effective discounted to 0.7c (adherence). Box corners scanned exhaustively.
    Rbox = [2.5, 3.5]
    gbox = [1.0 / 7.0, 1.0 / 5.0]
    c_eff_box = [0.7 * c_baseline, c_baseline]  # adherence discount
    # robust tau* = largest tau s.t. ALL corners satisfy P<=h
    # i.e. min over corners of tau*(corner). Worst corner drives it.
    corner_taus = []
    for Rr in Rbox:
        for g_ in gbox:
            for ce in c_eff_box:
                ts_, st = find_tau_star_param(ce, Rr, g_)
                corner_taus.append({"Rrepro": Rr, "gamma": float(g_),
                                    "c_eff": ce, "tau_star": ts_, "status": st})
    out["robust_corners"] = corner_taus
    valid = [d["tau_star"] for d in corner_taus
             if d["tau_star"] is not None]
    infeasible_corner = any(d["tau_star"] is None for d in corner_taus)
    if infeasible_corner:
        out["tau_star_robust_c0.6"] = None
        out["robust_status"] = "infeasible_corner_exists"
        out["safety_lead_time_days"] = None
    else:
        tau_robust = float(min(valid))
        out["tau_star_robust_c0.6"] = tau_robust
        out["robust_status"] = "feasible_all_corners"
        out["safety_lead_time_days"] = (
            float(tau_nom - tau_robust) if tau_nom is not None else None
        )

    return out


# ----------------------------------------------------------------------------
# Figures
# ----------------------------------------------------------------------------
def fig_Q1(q1):
    sol = integrate(BETA0, GAMMA, N, I0, 0.0, 0.0)
    ts = np.linspace(0, 200, 4000)
    y = sol.sol(ts)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ts, y[0] / 1e3, label="S (susceptible)", color="tab:blue")
    ax.plot(ts, y[1] / 1e3, label="I (in treatment / prevalence)",
            color="tab:red", lw=2)
    ax.plot(ts, y[2] / 1e3, label="R (removed)", color="tab:green")
    ax.axhline(H / 1e3, ls="--", color="black",
               label=f"capacity h = {H/1e3:.0f}k (8% N)")
    ax.axvline(q1["t_peak_days"], ls=":", color="tab:red", alpha=0.6)
    ax.annotate(f"peak I = {q1['Imax']/1e3:.0f}k\n@ day {q1['t_peak_days']:.1f}",
                xy=(q1["t_peak_days"], q1["Imax"] / 1e3),
                xytext=(q1["t_peak_days"] + 20, q1["Imax"] / 1e3),
                fontsize=9)
    ax.set_xlabel("time (days)")
    ax.set_ylabel("population (thousands)")
    ax.set_title("Q1: No-intervention SIR epidemic (R0=3.0, N=1e6)")
    ax.legend(loc="center right", fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig1_Q1_baseline.png"), dpi=130)
    plt.close(fig)


def fig_Q2_curves(taus, Ps):
    fig, ax = plt.subplots(figsize=(8, 5))
    taus = np.array(taus)
    Ps = np.array(Ps)
    ax.plot(taus, Ps / 1e3, "o-", color="tab:purple", ms=3,
            label="P(τ, c=0.6) peak I")
    ax.axhline(H / 1e3, ls="--", color="black", label="capacity h = 80k")
    ax.axhline(0.8 * H / 1e3, ls=":", color="gray", label="0.8h (20% margin)")
    ax.set_xlabel("intervention start day τ")
    ax.set_ylabel("peak in-treatment I (thousands)")
    ax.set_title("Q2: Peak prevalence vs intervention timing (c=0.6)")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig2_Q2_peak_vs_tau.png"), dpi=130)
    plt.close(fig)


def fig_phase_diagram():
    """Intervention phase diagram: g(tau,c)=0 contour in (tau,c) plane."""
    taus = np.linspace(0, 50, 60)
    cs = np.linspace(0.3, 0.8, 50)
    Pgrid = np.empty((cs.size, taus.size))
    for i, c in enumerate(cs):
        for j, t in enumerate(taus):
            Pgrid[i, j] = peak_I(BETA0, GAMMA, N, I0, t, c)[0]
    fig, ax = plt.subplots(figsize=(8, 6))
    cf = ax.contourf(taus, cs, Pgrid / 1e3, levels=20, cmap="RdYlGn_r")
    cbar = fig.colorbar(cf, ax=ax)
    cbar.set_label("peak in-treatment I (thousands)")
    cs_line = ax.contour(taus, cs, Pgrid, levels=[H], colors="black",
                         linewidths=2)
    ax.clabel(cs_line, fmt="g=0 (h=80k)", fontsize=9)
    c_star = 1 - 1 / RREPRO
    ax.axhline(c_star, ls="--", color="blue",
               label=f"c* = 1-1/R0 = {c_star:.3f}")
    ax.set_xlabel("intervention start day τ")
    ax.set_ylabel("intervention strength c")
    ax.set_title("Intervention phase diagram: feasible (green) vs overload (red)")
    ax.legend(loc="upper right", fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig3_phase_diagram.png"), dpi=130)
    plt.close(fig)


def fig_sensitivity(q3):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.2))
    # Rrepro
    d = q3["tau_star_vs_Rrepro_c0.6"]
    xs = [float(k) for k in d]
    ys = [d[k]["tau_star"] for k in d]
    axes[0].plot(xs, ys, "o-", color="tab:red")
    axes[0].set_xlabel("R0 (basic reproduction number)")
    axes[0].set_ylabel("latest feasible τ* (days)")
    axes[0].set_title("τ* vs R0  (c=0.6)")
    axes[0].grid(alpha=0.3)
    # c
    d = q3["tau_star_vs_c"]
    xs = [float(k) for k in d]
    ys = [d[k]["tau_star"] if d[k]["tau_star"] is not None else np.nan
          for k in d]
    axes[1].plot(xs, ys, "o-", color="tab:purple")
    axes[1].axvline(1 - 1 / RREPRO, ls="--", color="blue", label="c*")
    axes[1].set_xlabel("intervention strength c")
    axes[1].set_ylabel("latest feasible τ* (days)")
    axes[1].set_title("τ* vs c")
    axes[1].legend(fontsize=8)
    axes[1].grid(alpha=0.3)
    # h
    d = q3["tau_star_vs_h_c0.6"]
    xs = [float(k) * 100 for k in d]
    ys = [d[k]["tau_star"] for k in d]
    axes[2].plot(xs, ys, "o-", color="tab:green")
    axes[2].set_xlabel("capacity h (% of N)")
    axes[2].set_ylabel("latest feasible τ* (days)")
    axes[2].set_title("τ* vs h  (c=0.6)")
    axes[2].grid(alpha=0.3)
    fig.suptitle("Q3: Sensitivity of latest feasible intervention day τ*")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig4_sensitivity.png"), dpi=130)
    plt.close(fig)


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def main():
    print("Solving Q1 (no-intervention baseline)...")
    q1 = solve_Q1()
    print(f"  Imax={q1['Imax']:.1f} ({q1['Imax_frac']:.4f}N) "
          f"t_peak={q1['t_peak_days']:.3f}d  z={q1['final_size_z_numeric']:.5f}")
    print(f"  conservation err={q1['conservation_max_abs_err']:.2e}  "
          f"final-size num-vs-eqn diff={q1['final_size_abs_diff']:.2e}")
    print(f"  S_at_peak rel-err vs N/R0={q1['S_at_peak_rel_err']:.2e}")

    print("Solving Q2 (intervention timing)...")
    q2, taus_grid, Ps_grid = solve_Q2()
    print(f"  tau*(c=0.6)={q2['tau_star_baseline_c0.6']}  "
          f"c*={q2['c_star_threshold']:.4f}")
    print(f"  monotone P(tau): {q2['monotonicity_P_vs_tau_c0.6']['is_monotone_nondecreasing']}")
    print(f"  infeasible-at-0 c examples: "
          f"{[d['c'] for d in q2['infeasible_at_day0_examples']]}")

    print("Solving Q3 (sensitivity + robustness)...")
    q3 = solve_Q3(taus_grid, Ps_grid)
    print(f"  tau*_nominal={q3['tau_star_nominal_c0.6']}  "
          f"tau*_robust={q3['tau_star_robust_c0.6']}  "
          f"lead-time Δτ={q3['safety_lead_time_days']}")
    print(f"  elasticities: {q3['elasticity_tau_star']}")

    print("Rendering figures...")
    fig_Q1(q1)
    fig_Q2_curves(taus_grid, Ps_grid)
    fig_phase_diagram()
    fig_sensitivity(q3)

    results = {
        "meta": {
            "case": "practice_02_epidemic_timing",
            "model": "deterministic SIR-ODE + step intervention (3_model.md)",
            "solver": {
                "method": METHOD, "rtol": RTOL, "atol": ATOL,
                "max_step": MAX_STEP, "t_end": T_END,
                "tau_breakpoint_split": True,
                "peak_locate": "fine grid 240001 + parabolic refine",
                "final_size": "long integration vs brentq final-size eqn",
                "tau_star": "brentq root of g(tau,c)=0 (monotone in tau)",
            },
            "params": {
                "N": N, "I0": I0, "gamma": GAMMA, "Rrepro": RREPRO,
                "beta0": BETA0, "h_frac": H_FRAC, "h_abs": H,
            },
            "randomness": "none (fully deterministic)",
            "versions": {
                "python": platform.python_version(),
                "numpy": np.__version__,
                "scipy": scipy.__version__,
                "matplotlib": matplotlib.__version__,
                "platform": platform.platform(),
            },
        },
        "Q1": q1,
        "Q2": q2,
        "Q3": q3,
        "Q2_curves": {"taus": taus_grid, "peak_I": Ps_grid},
    }

    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Wrote results.json")

    write_frozen(q1, q2, q3)
    print("Wrote frozen_numbers.json")
    print("DONE.")


def write_frozen(q1, q2, q3):
    numbers = [
        {"id": "Q1_Rrepro", "label": "基本再生数 R0",
         "value": round(q1["Rrepro"], 4), "tol": 1e-6,
         "source": "artifacts/results.json", "path": "Q1.Rrepro",
         "cited_in": "6_paper.md"},
        {"id": "Q1_beta0", "label": "传播率 β0 (/天)",
         "value": round(q1["beta0"], 6), "tol": 1e-6,
         "source": "artifacts/results.json", "path": "Q1.beta0",
         "cited_in": "6_paper.md"},
        {"id": "Q1_Imax", "label": "无干预峰值在治 I_max (人)",
         "value": round(q1["Imax"], 0), "tol": 50.0,
         "source": "artifacts/results.json", "path": "Q1.Imax",
         "cited_in": "6_paper.md"},
        {"id": "Q1_Imax_frac", "label": "无干预峰值占 N 比例",
         "value": round(q1["Imax_frac"], 4), "tol": 1e-3,
         "source": "artifacts/results.json", "path": "Q1.Imax_frac",
         "cited_in": "6_paper.md"},
        {"id": "Q1_t_peak", "label": "无干预峰值出现日 (天)",
         "value": round(q1["t_peak_days"], 2), "tol": 0.05,
         "source": "artifacts/results.json", "path": "Q1.t_peak_days",
         "cited_in": "6_paper.md"},
        {"id": "Q1_final_size_z", "label": "无干预最终累计感染比例 z",
         "value": round(q1["final_size_z_numeric"], 4), "tol": 1e-3,
         "source": "artifacts/results.json", "path": "Q1.final_size_z_numeric",
         "cited_in": "6_paper.md"},
        {"id": "Q2_c_star", "label": "力度阈值 c* = 1-1/R0",
         "value": round(q2["c_star_threshold"], 4), "tol": 1e-3,
         "source": "artifacts/results.json", "path": "Q2.c_star_threshold",
         "cited_in": "6_paper.md"},
        {"id": "Q2_tau_star_c06", "label": "最迟可行干预日 τ*(c=0.6) (天)",
         "value": round(q2["tau_star_baseline_c0.6"], 2), "tol": 0.1,
         "source": "artifacts/results.json", "path": "Q2.tau_star_baseline_c0.6",
         "cited_in": "6_paper.md"},
        {"id": "Q2_tau_star_c06_margin",
         "label": "τ*(c=0.6, 20%余量) (天)",
         "value": round(q2["tau_star_baseline_c0.6_20pct_margin"], 2),
         "tol": 0.1, "source": "artifacts/results.json",
         "path": "Q2.tau_star_baseline_c0.6_20pct_margin",
         "cited_in": "6_paper.md"},
        {"id": "Q3_tau_robust", "label": "稳健最迟干预日 τ*_robust(c=0.6) (天)",
         "value": round(q3["tau_star_robust_c0.6"], 2)
         if q3["tau_star_robust_c0.6"] is not None else -1,
         "tol": 0.1, "source": "artifacts/results.json",
         "path": "Q3.tau_star_robust_c0.6", "cited_in": "6_paper.md"},
        {"id": "Q3_lead_time", "label": "安全提前量 Δτ (天)",
         "value": round(q3["safety_lead_time_days"], 2)
         if q3["safety_lead_time_days"] is not None else -1,
         "tol": 0.15, "source": "artifacts/results.json",
         "path": "Q3.safety_lead_time_days", "cited_in": "6_paper.md"},
        {"id": "Q3_elasticity_Rrepro", "label": "τ* 对 R0 的弹性",
         "value": round(q3["elasticity_tau_star"]["Rrepro"], 3), "tol": 0.05,
         "source": "artifacts/results.json",
         "path": "Q3.elasticity_tau_star.Rrepro", "cited_in": "6_paper.md"},
    ]
    frozen = {
        "case": "practice_02_epidemic_timing",
        "note": "论文数字唯一真值源；由 solve.py 生成 results.json 后冻结。"
                "SIR-ODE + 阶跃干预，确定性可复现。",
        "inputs": ["artifacts/solve.py"],
        "numbers": numbers,
    }
    with open(os.path.join(HERE, "frozen_numbers.json"), "w",
              encoding="utf-8") as f:
        json.dump(frozen, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
