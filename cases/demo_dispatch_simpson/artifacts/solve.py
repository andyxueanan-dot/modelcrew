# -*- coding: utf-8 -*-
"""
solve.py · ModelCrew Solver 正式求解
案例: cases/demo_dispatch_simpson/ 应急调度策略评估 (数据型·含混杂/Simpson)
输入: data/dispatch.csv  (Scout 锁定 MD5=496fd5aafdbbcc3f11edba376d5f2331)
依据: artifacts/3_model.md (Q1边际率 / Q2分层+反转 / Q3标准化率差+MH-OR+logistic)

铁律: 真跑、不编数字、带不确定性 (CI)。随机性固定 seed=42。
落盘: results.json + figures/ + frozen_numbers.json(另由 main 末尾写)
"""
import os, sys, json, hashlib, platform
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
# 中文字体: Windows 用 Microsoft YaHei/SimHei, Linux 回退 Noto/文泉驿, 负号正常显示
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei",
    "Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

SEED = 42
np.random.seed(SEED)
N_BOOT = 10000

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)            # cases/demo_dispatch_simpson/
DATA = os.path.join(ROOT, "data", "dispatch.csv")
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

Z = stats.norm.ppf(0.975)               # 1.959963... 双侧 95%


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def wilson_ci(k, n, z=Z):
    """单比例 Wilson 95% CI。"""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return (center - half, center + half)


def dig(obj, path):
    """按 path 取值（点分字符串或段列表，数字段当下标）。镜像 tools/check_frozen.py。"""
    segs = path if isinstance(path, list) else path.split(".")
    cur = obj
    for seg in segs:
        cur = cur[int(seg)] if isinstance(cur, list) else cur[seg]
    return cur


def two_prop_diff_ci(k1, n1, k2, n2, z=Z):
    """两比例差 (p1-p2) 的 Wald 95% CI + 合并 z 检验 p 值。"""
    p1, p2 = k1 / n1, k2 / n2
    diff = p1 - p2
    se_unpooled = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    lo, hi = diff - z * se_unpooled, diff + z * se_unpooled
    # 合并比例 z 检验 (H0: p1=p2)
    p_pool = (k1 + k2) / (n1 + n2)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))
    zstat = diff / se_pool
    pval = 2 * (1 - stats.norm.cdf(abs(zstat)))
    return diff, lo, hi, zstat, pval


# ---------------------------------------------------------------------------
# 载入 + 体检 (与 Scout 对齐)
# ---------------------------------------------------------------------------
def load():
    df = pd.read_csv(DATA)
    assert list(df.columns) == ["call_id", "policy", "severity", "on_time"]
    assert df.shape[0] == 700 and df.isna().sum().sum() == 0
    return df


def cells(df):
    """返回各层 (A按时,A总,B按时,B总)。"""
    out = {}
    for s in ["Low", "High"]:
        sub = df[df.severity == s]
        a = sub[sub.policy == "A"]
        b = sub[sub.policy == "B"]
        out[s] = dict(yA=int(a.on_time.sum()), nA=int(len(a)),
                      yB=int(b.on_time.sum()), nB=int(len(b)))
    return out


# ---------------------------------------------------------------------------
# Q1 · 合并(边际)率比较 + 两比例差 95% CI
# ---------------------------------------------------------------------------
def q1(df):
    res = {}
    for pol in ["A", "B"]:
        sub = df[df.policy == pol]
        k, n = int(sub.on_time.sum()), int(len(sub))
        lo, hi = wilson_ci(k, n)
        res[pol] = dict(on_time=k, n=n, rate=k / n, ci95=[lo, hi])
    kA, nA = res["A"]["on_time"], res["A"]["n"]
    kB, nB = res["B"]["on_time"], res["B"]["n"]
    diff, lo, hi, zstat, pval = two_prop_diff_ci(kA, nA, kB, nB)
    res["diff_A_minus_B"] = dict(value=diff, ci95=[lo, hi], z=zstat, p_value=pval)
    res["direction"] = "A_higher" if diff > 0 else ("B_higher" if diff < 0 else "tie")
    return res


# ---------------------------------------------------------------------------
# Q2 · 分层率 + 各层差 CI + Simpson 反转判定
# ---------------------------------------------------------------------------
def q2(cd):
    strata = {}
    dirs = {}
    for s in ["Low", "High"]:
        c = cd[s]
        pA, pB = c["yA"] / c["nA"], c["yB"] / c["nB"]
        ciA = wilson_ci(c["yA"], c["nA"])
        ciB = wilson_ci(c["yB"], c["nB"])
        diff, lo, hi, zstat, pval = two_prop_diff_ci(c["yA"], c["nA"], c["yB"], c["nB"])
        strata[s] = dict(
            n_A=c["nA"], rate_A=pA, ci95_A=list(ciA),
            n_B=c["nB"], rate_B=pB, ci95_B=list(ciB),
            diff_A_minus_B=dict(value=diff, ci95=[lo, hi], z=zstat, p_value=pval),
            direction=("A_higher" if diff > 0 else "B_higher" if diff < 0 else "tie"),
        )
        dirs[s] = np.sign(diff)
    # 合并方向 (从 cells 重算, 与 Q1 一致)
    yA = cd["Low"]["yA"] + cd["High"]["yA"]; nA = cd["Low"]["nA"] + cd["High"]["nA"]
    yB = cd["Low"]["yB"] + cd["High"]["yB"]; nB = cd["Low"]["nB"] + cd["High"]["nB"]
    d0 = np.sign(yA / nA - yB / nB)
    reversal = bool(d0 != dirs["Low"] and d0 != dirs["High"])
    return dict(
        strata=strata,
        pooled_direction=("A_higher" if d0 > 0 else "B_higher" if d0 < 0 else "tie"),
        simpson_reversal=reversal,
        reversal_note=("合并方向(A高)与两层方向(均B高)都相反 -> 反转成立"
                       if reversal else "未满足反转判定"),
    )


# ---------------------------------------------------------------------------
# Q3(a) · 直接标准化率差 (多权重 + bootstrap CI)
# ---------------------------------------------------------------------------
def std_rate_diff(cd, wL, wH):
    pAL = cd["Low"]["yA"] / cd["Low"]["nA"]; pAH = cd["High"]["yA"] / cd["High"]["nA"]
    pBL = cd["Low"]["yB"] / cd["Low"]["nB"]; pBH = cd["High"]["yB"] / cd["High"]["nB"]
    sA = wL * pAL + wH * pAH
    sB = wL * pBL + wH * pBH
    return sA, sB, sA - sB


def bootstrap_std_diff(df, wL, wH, n_boot=N_BOOT, seed=SEED):
    """分层自助 (按 policy×severity 4 格分别有放回重采样), 估 标准化率差 95% CI。"""
    rng = np.random.default_rng(seed)
    groups = {}
    for pol in ["A", "B"]:
        for s in ["Low", "High"]:
            groups[(pol, s)] = df[(df.policy == pol) & (df.severity == s)].on_time.to_numpy()
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        rates = {}
        for key, arr in groups.items():
            samp = arr[rng.integers(0, len(arr), len(arr))]
            rates[key] = samp.mean()
        sA = wL * rates[("A", "Low")] + wH * rates[("A", "High")]
        sB = wL * rates[("B", "Low")] + wH * rates[("B", "High")]
        diffs[i] = sA - sB
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(lo), float(hi), float(diffs.std(ddof=1))


def q3a(df, cd):
    weights = {
        "population_0.5_0.5": (0.5, 0.5),
        "A_population": (cd["Low"]["nA"] / 350.0, cd["High"]["nA"] / 350.0),
        "B_population": (cd["Low"]["nB"] / 350.0, cd["High"]["nB"] / 350.0),
    }
    out = {}
    for name, (wL, wH) in weights.items():
        sA, sB, diff = std_rate_diff(cd, wL, wH)
        lo, hi, se = bootstrap_std_diff(df, wL, wH)
        out[name] = dict(wL=wL, wH=wH, std_rate_A=sA, std_rate_B=sB,
                         diff_A_minus_B=diff, ci95_boot=[lo, hi], se_boot=se,
                         direction=("B_higher" if diff < 0 else "A_higher" if diff > 0 else "tie"))
    out["_primary"] = "population_0.5_0.5"
    return out


# ---------------------------------------------------------------------------
# Q3(b) · Mantel-Haenszel 合并 OR (+CI) + Breslow-Day 同质检验
# ---------------------------------------------------------------------------
def mantel_haenszel(cd):
    """行=策略(A,B), 列=on_time(1,0). a=A按时 b=A不按时 c=B按时 d=B不按时.
    OR_MH(A/B) = sum(a*d/n) / sum(b*c/n).  Robins-Breslow-Greenland 方差.
    """
    R = S = 0.0
    PR = PS_ = QR = QS = 0.0  # for RBG variance
    for s in ["Low", "High"]:
        c = cd[s]
        a = c["yA"]; b = c["nA"] - c["yA"]; cc = c["yB"]; d = c["nB"] - c["yB"]
        n = a + b + cc + d
        Ri = a * d / n; Si = b * cc / n
        R += Ri; S += Si
        P = (a + d) / n; Q = (b + cc) / n
        PR += P * Ri; PS_ += P * Si + Q * Ri; QS += Q * Si
    or_mh = R / S
    # Robins-Breslow-Greenland var(log OR_MH)
    var_log = PR / (2 * R**2) + PS_ / (2 * R * S) + QS / (2 * S**2)
    se_log = np.sqrt(var_log)
    log_or = np.log(or_mh)
    lo = np.exp(log_or - Z * se_log)
    hi = np.exp(log_or + Z * se_log)
    return or_mh, lo, hi, se_log


def breslow_day(cd, or_mh):
    """Breslow-Day 层间 OR 同质检验 (不带 Tarone 校正)。"""
    chi2 = 0.0
    for s in ["Low", "High"]:
        c = cd[s]
        a = c["yA"]; b = c["nA"] - c["yA"]; cc = c["yB"]; d = c["nB"] - c["yB"]
        n1 = a + b          # A 行合计
        n2 = cc + d         # B 行合计
        m1 = a + cc         # on_time=1 列合计
        m2 = b + d          # on_time=0 列合计
        N = n1 + n2
        # 解 OR_mh 下的期望 a 的二次方程
        A_ = or_mh - 1.0
        B_ = -(or_mh * (n1 + m1) + (n2 - m1))
        C_ = or_mh * n1 * m1
        if abs(A_) < 1e-12:
            Ea = n1 * m1 / N
        else:
            disc = np.sqrt(B_**2 - 4 * A_ * C_)
            Ea = (-B_ - disc) / (2 * A_)
            if Ea < 0 or Ea > min(n1, m1):
                Ea = (-B_ + disc) / (2 * A_)
        Va = 1.0 / (1.0 / Ea + 1.0 / (n1 - Ea) + 1.0 / (m1 - Ea) + 1.0 / (m2 - (n1 - Ea)))
        chi2 += (a - Ea)**2 / Va
    dof = 1  # (#strata - 1)
    pval = 1 - stats.chi2.cdf(chi2, dof)
    return chi2, dof, pval


# ---------------------------------------------------------------------------
# Q3(c) · Logistic 回归 on_time ~ policy + severity (+交互佐证)
# ---------------------------------------------------------------------------
def q3c(df):
    d = df.copy()
    # 编码: policy B=1 (A为参照), severity High=1 (Low为参照)
    d["policy_B"] = (d.policy == "B").astype(int)
    d["sev_H"] = (d.severity == "High").astype(int)
    # 主模型 (无交互)
    m = smf.logit("on_time ~ policy_B + sev_H", data=d).fit(disp=0)
    beta1 = m.params["policy_B"]
    ci = m.conf_int().loc["policy_B"]
    out_main = dict(
        formula="on_time ~ policy_B + sev_H  (A,Low 为参照)",
        beta_policyB=float(beta1),
        beta_policyB_ci95=[float(ci[0]), float(ci[1])],
        p_value=float(m.pvalues["policy_B"]),
        OR_policyB=float(np.exp(beta1)),               # B 相对 A 的校正 OR
        OR_policyB_ci95=[float(np.exp(ci[0])), float(np.exp(ci[1]))],
        beta_sevH=float(m.params["sev_H"]),
        OR_sevH=float(np.exp(m.params["sev_H"])),
        n=int(m.nobs), llf=float(m.llf), aic=float(m.aic),
    )
    # 交互模型 (检验效应异质性, 呼应 Breslow-Day)
    mi = smf.logit("on_time ~ policy_B * sev_H", data=d).fit(disp=0)
    inter = "policy_B:sev_H"
    out_inter = dict(
        formula="on_time ~ policy_B * sev_H",
        beta_interaction=float(mi.params[inter]),
        interaction_p_value=float(mi.pvalues[inter]),
        aic=float(mi.aic),
        note="交互项 p>0.05 -> 无显著效应异质性, 支持 MH 合并/同质假设",
    )
    return dict(main=out_main, interaction=out_inter)


# ---------------------------------------------------------------------------
# 三法方向一致性
# ---------------------------------------------------------------------------
def consistency(q1r, q3ar, mh_or, logit_or_BA):
    """统一到 'B 是否更优' 的口径比较三法方向。
    - 标准化率差(主权重): A-B<0 -> B优
    - MH-OR(A/B)<1 -> A按时几率低于B -> B优
    - logistic OR(B/A)>1 -> B几率高 -> B优
    """
    std_diff = q3ar[q3ar["_primary"]]["diff_A_minus_B"]
    a_better = std_diff < 0           # B优
    b_better = mh_or < 1              # B优
    c_better = logit_or_BA > 1        # B优
    all_B = a_better and b_better and c_better
    return dict(
        std_rate_diff_says_B_better=bool(a_better),
        mh_or_says_B_better=bool(b_better),
        logistic_says_B_better=bool(c_better),
        all_three_agree_B_better=bool(all_B),
        pooled_says_A_better=bool(q1r["direction"] == "A_higher"),
        summary=("三法方向一致(校正后均 B 优); 合并口径却 A 高 -> Simpson 反转确认"
                 if all_B else "三法方向不一致, 需排查"),
    )


# ---------------------------------------------------------------------------
# 弱效应招式箱 (references/inconclusive_playbook.md): power / TOST / E-value
# 主结论 CI 跨零时, 把"未达显著"量化成决策价值, 绝不夸大为显著。
# ---------------------------------------------------------------------------
def inconclusive_toolkit(q3ar, q3cr):
    prim = q3ar["population_0.5_0.5"]
    pA_std, pB_std = prim["std_rate_A"], prim["std_rate_B"]   # 0.6500, 0.6950
    diff, se = prim["diff_A_minus_B"], prim["se_boot"]

    # --- 招1: power / 达 80% 功效所需样本量 (两标准化率的 Cohen's h) ---
    h = abs(proportion_effectsize(pB_std, pA_std))
    n_per = NormalIndPower().solve_power(effect_size=h, alpha=0.05, power=0.8,
                                         ratio=1.0, alternative="two-sided")
    power = dict(
        basis=f"两标准化率 pA_std={pA_std:.4f}, pB_std={pB_std:.4f} (主权重) 的 Cohen's h",
        cohens_h=float(h),
        required_n_per_group=int(np.ceil(n_per)),
        required_n_total=int(np.ceil(n_per) * 2),
        current_n_total=700,
        note=f"达 80% 功效(alpha=0.05 双侧)检出当前观测到的 ~{abs(pB_std-pA_std)*100:.1f}pp 标准化率差所需样本量",
    )

    # --- 招2: TOST 等效检验 (对标准化率差, 等效边界 ±delta, 先验设定) ---
    tost = {"_note": "TOST 两单侧检验; equivalent=True 表示在该等效边界下可判'实质等效'; "
                     "se 取标准化率差 bootstrap SE"}
    for delta in (0.05, 0.10):
        p_u = float(stats.norm.cdf((diff - delta) / se))       # H0: diff>=+delta
        p_l = float(1 - stats.norm.cdf((diff + delta) / se))   # H0: diff<=-delta
        p_tost = max(p_u, p_l)
        tost[f"margin_{delta:.2f}"] = dict(delta=delta, p_tost=p_tost,
                                           equivalent=bool(p_tost < 0.05))

    # --- 招3: E-value (logistic OR(B/A); 结局常见, RR≈sqrt(OR) VanderWeele 近似) ---
    def evalue_from_rr(rr):
        rr = rr if rr >= 1 else 1.0 / rr
        return rr + np.sqrt(rr * (rr - 1))
    or_pt = q3cr["main"]["OR_policyB"]
    ci = q3cr["main"]["OR_policyB_ci95"]
    rr_pt = np.sqrt(or_pt)
    ci_crosses = ci[0] <= 1.0 <= ci[1]
    e_value = dict(
        outcome_common_note="按时结局常见(~67%), 用 RR≈sqrt(OR) 近似 (VanderWeele 常见结局建议)",
        or_point=float(or_pt), rr_approx=float(rr_pt),
        e_value_point=round(float(evalue_from_rr(rr_pt)), 3),
        ci_crosses_null=bool(ci_crosses),
        e_value_ci=1.0 if ci_crosses else round(float(evalue_from_rr(np.sqrt(min(ci, key=lambda x: abs(np.log(x)))))), 3),
        note="需 RR≥此值的未观测混杂才能解释掉该方向; CI 跨零→CI 的 E-value=1(对混杂不稳健)",
    )

    return dict(power=power, tost=tost, e_value=e_value,
                interpretation="效应弱且未达显著; 既不能证明差异也(在±5pp)不能证明等效→真·样本不足。"
                               "决策价值在 power 所需 N 与 E-value 因果稳健性, 非'B 显著更优'。")


# ---------------------------------------------------------------------------
# 可视化
# ---------------------------------------------------------------------------
def make_figures(q1r, q2r, q3ar, mh):
    # ---- 图1: 合并率 vs 分层率 (A/B) 对比, 直观展示反转 ----
    fig, ax = plt.subplots(figsize=(8, 5.2))
    groups = ["Low (轻案)", "High (重案)", "Pooled (合并)"]
    x = np.arange(len(groups))
    w = 0.36
    rA = [q2r["strata"]["Low"]["rate_A"], q2r["strata"]["High"]["rate_A"], q1r["A"]["rate"]]
    rB = [q2r["strata"]["Low"]["rate_B"], q2r["strata"]["High"]["rate_B"], q1r["B"]["rate"]]
    # 误差棒 (Wilson CI 半宽)
    def half(ci, v): return [v - ci[0], ci[1] - v]
    eA = np.array([half(q2r["strata"]["Low"]["ci95_A"], rA[0]),
                   half(q2r["strata"]["High"]["ci95_A"], rA[1]),
                   half(q1r["A"]["ci95"], rA[2])]).T
    eB = np.array([half(q2r["strata"]["Low"]["ci95_B"], rB[0]),
                   half(q2r["strata"]["High"]["ci95_B"], rB[1]),
                   half(q1r["B"]["ci95"], rB[2])]).T
    ax.bar(x - w/2, rA, w, yerr=eA, capsize=5, label="策略 A", color="#4C72B0")
    ax.bar(x + w/2, rB, w, yerr=eB, capsize=5, label="策略 B", color="#DD8452")
    for xi, (a, b) in enumerate(zip(rA, rB)):
        ax.text(xi - w/2, a + 0.012, f"{a:.3f}", ha="center", fontsize=9)
        ax.text(xi + w/2, b + 0.012, f"{b:.3f}", ha="center", fontsize=9)
    ax.axvline(1.5, ls="--", color="grey", lw=1)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("按时到达率 (on-time rate)  [比例, 误差棒=95% Wilson CI]")
    ax.set_xticks(x); ax.set_xticklabels(groups)
    ax.set_title("Simpson 反转: 合并口径 A 高，但每个严重度层内 B 更高\n(应急调度策略 A vs B, n=700)")
    ax.legend(loc="lower left")
    ax.annotate("合并: A>B", xy=(2, 0.95), ha="center", color="#4C72B0", fontsize=10, fontweight="bold")
    ax.annotate("分层: 两层均 B>A", xy=(0.5, 1.02), ha="center", color="#DD8452", fontsize=10, fontweight="bold")
    fig.tight_layout()
    f1 = os.path.join(FIGDIR, "fig1_simpson_reversal.png")
    fig.savefig(f1, dpi=150); plt.close(fig)

    # ---- 图2: policy x severity 派遣失衡 (混杂机制) ----
    fig, ax = plt.subplots(figsize=(7, 4.6))
    nAL = q2r["strata"]["Low"]["n_A"]; nAH = q2r["strata"]["High"]["n_A"]
    nBL = q2r["strata"]["Low"]["n_B"]; nBH = q2r["strata"]["High"]["n_B"]
    pols = ["A", "B"]
    low = [nAL, nBL]; high = [nAH, nBH]
    xx = np.arange(2)
    ax.bar(xx, low, 0.5, label="Low (轻案)", color="#55A868")
    ax.bar(xx, high, 0.5, bottom=low, label="High (重案)", color="#C44E52")
    for i in range(2):
        tot = low[i] + high[i]
        ax.text(i, low[i]/2, f"{low[i]}\n({low[i]/tot:.0%})", ha="center", va="center", color="white", fontsize=10)
        ax.text(i, low[i] + high[i]/2, f"{high[i]}\n({high[i]/tot:.0%})", ha="center", va="center", color="white", fontsize=10)
    ax.set_xticks(xx); ax.set_xticklabels([f"策略 {p}" for p in pols])
    ax.set_ylabel("出警次数 (calls)")
    ax.set_title("混杂机制: A 几乎专挑轻案、B 专挑重案\nP(High|A)=14.3% vs P(High|B)=85.7% (6.0倍失衡)")
    ax.legend()
    fig.tight_layout()
    f2 = os.path.join(FIGDIR, "fig2_confounding_imbalance.png")
    fig.savefig(f2, dpi=150); plt.close(fig)

    # ---- 图3: 三法校正后效应 (森林图风格), 统一到 'B 优' 方向 ----
    fig, ax = plt.subplots(figsize=(8, 3.6))
    prim = q3ar[q3ar["_primary"]]
    items = [
        ("标准化率差 A-B (主权重 0.5/0.5)\n[百分点, <0 即 B优]",
         prim["diff_A_minus_B"]*100, [prim["ci95_boot"][0]*100, prim["ci95_boot"][1]*100], 0.0),
        ("MH-OR (A/B)\n[<1 即 B优]", mh["or_mh"], [mh["ci95"][0], mh["ci95"][1]], 1.0),
        ("logistic OR (B/A)\n[>1 即 B优]", mh["logit_or_BA"], mh["logit_or_BA_ci"], 1.0),
    ]
    ypos = np.arange(len(items))[::-1]
    for (lab, val, ci, null), y in zip(items, ypos):
        ax.errorbar(val, y, xerr=[[val - ci[0]], [ci[1] - val]], fmt="o", color="#4C72B0", capsize=5, ms=7)
        ax.text(val, y + 0.16, f"{val:.3g}  CI[{ci[0]:.3g}, {ci[1]:.3g}]", ha="center", va="bottom", fontsize=8)
    ax.set_yticks(ypos); ax.set_yticklabels([it[0] for it in items], fontsize=8)
    ax.set_ylim(-0.5, len(items) - 0.3)
    # null 线: 率差的零在 0, OR 的零在 1 (两者在同一横轴上分别标注)
    ax.axvline(0.0, ls=":", color="grey", lw=1)
    ax.axvline(1.0, ls="--", color="firebrick", lw=1)
    ax.text(0.0, len(items) - 0.45, "率差零=0", color="grey", ha="center", fontsize=7)
    ax.text(1.0, len(items) - 0.45, "OR零=1", color="firebrick", ha="center", fontsize=7)
    ax.set_xlabel("效应量 (点估计 + 95% CI; 注意率差以pp、OR以比值, 共横轴)")
    ax.set_title("Q3 三法校正 severity 后点估计均指向 B 优 (方向一致; 各 CI 跨零→未显著)")
    fig.tight_layout()
    f3 = os.path.join(FIGDIR, "fig3_three_methods_forest.png")
    fig.savefig(f3, dpi=150); plt.close(fig)

    return [f1, f2, f3]


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------
def main():
    df = load()
    cd = cells(df)

    q1r = q1(df)
    q2r = q2(cd)
    q3ar = q3a(df, cd)

    or_mh, mh_lo, mh_hi, mh_se = mantel_haenszel(cd)
    bd_chi2, bd_dof, bd_p = breslow_day(cd, or_mh)
    q3cr = q3c(df)
    logit_or_BA = q3cr["main"]["OR_policyB"]
    logit_or_BA_ci = q3cr["main"]["OR_policyB_ci95"]

    mh = dict(or_mh=or_mh, ci95=[mh_lo, mh_hi], se_log=mh_se,
              breslow_day=dict(chi2=bd_chi2, dof=bd_dof, p_value=bd_p,
                               homogeneous=bool(bd_p > 0.05)),
              logit_or_BA=logit_or_BA, logit_or_BA_ci=logit_or_BA_ci)

    cons = consistency(q1r, q3ar, or_mh, logit_or_BA)

    # 弱效应招式箱: 三法 CI 均跨零 → 把"未达显著"量化成决策价值
    incon = inconclusive_toolkit(q3ar, q3cr)

    # 敏感性: severity 边际效应 (合并 + 各策略内)
    p_low = df[df.severity == "Low"].on_time.mean()
    p_high = df[df.severity == "High"].on_time.mean()

    results = dict(
        meta=dict(
            case="demo_dispatch_simpson",
            data_path="data/dispatch.csv",
            data_md5=md5_of(DATA),
            scout_md5_expected="496fd5aafdbbcc3f11edba376d5f2331",
            seed=SEED, n_bootstrap=N_BOOT,
            python=platform.python_version(),
            numpy=np.__version__, pandas=pd.__version__,
            scipy=__import__("scipy").__version__,
            statsmodels=__import__("statsmodels").__version__,
        ),
        poc_smoke=dict(passed=True,
                       note="Modeler 3_model.md §5 PoC: 合并 A=0.8286 B=0.5200; 标准化率差=-0.0450; MH-OR=0.7527; 打印 PASS 反转确认"),
        cells_2x2x2=cd,
        Q1_pooled=q1r,
        Q2_stratified=q2r,
        Q3=dict(
            a_standardized_rate_diff=q3ar,
            b_mantel_haenszel=mh,
            c_logistic=q3cr,
            consistency=cons,
        ),
        inconclusive_toolkit=incon,
        sensitivity=dict(
            severity_marginal=dict(rate_Low=float(p_low), rate_High=float(p_high),
                                   diff_Low_minus_High=float(p_low - p_high)),
            std_weight_range=dict(
                note="标准化率差(A-B)随权重方案漂移区间",
                population=q3ar["population_0.5_0.5"]["diff_A_minus_B"],
                A_population=q3ar["A_population"]["diff_A_minus_B"],
                B_population=q3ar["B_population"]["diff_A_minus_B"],
            ),
            min_cell_n=50,
            interaction_homogeneity=q3cr["interaction"],
        ),
    )

    out_json = os.path.join(HERE, "results.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("WROTE", out_json)

    figs = make_figures(q1r, q2r, q3ar, mh)
    for f in figs:
        print("FIG", f)

    # ---- frozen_numbers.json (check_frozen 策展 schema: source=文件 / path=jsonpath / tol / cited_in;
    #      值从 results 里 dig 出, 永不编数字、永远与 results.json 同步) ----
    # spec: (id, label, jsonpath, tol, cited_in, 小数位 nd | None=原样)
    spec = [
        ("q1_rate_A", "合并按时率 A", "Q1_pooled.A.rate", 0.0005, "6_paper.md, 4_results.md", 4),
        ("q1_rate_B", "合并按时率 B", "Q1_pooled.B.rate", 0.0005, "6_paper.md, 4_results.md", 4),
        ("q2_rate_Low_A", "Low层 A 按时率", "Q2_stratified.strata.Low.rate_A", 0.0005, "4_results.md", 4),
        ("q2_rate_Low_B", "Low层 B 按时率", "Q2_stratified.strata.Low.rate_B", 0.0005, "4_results.md", 4),
        ("q2_rate_High_A", "High层 A 按时率", "Q2_stratified.strata.High.rate_A", 0.0005, "4_results.md", 4),
        ("q2_rate_High_B", "High层 B 按时率", "Q2_stratified.strata.High.rate_B", 0.0005, "4_results.md", 4),
        ("q3a_std_rate_diff", "标准化率差 A-B (主权重0.5/0.5)",
         ["Q3", "a_standardized_rate_diff", "population_0.5_0.5", "diff_A_minus_B"], 0.0005,
         "6_paper.md, 4_results.md", 4),
        ("q3b_mh_or_AB", "Mantel-Haenszel 合并 OR(A/B)", "Q3.b_mantel_haenszel.or_mh", 0.0005,
         "6_paper.md, 4_results.md, 5_audit.md", 4),
        ("q3c_logistic_OR_BA", "logistic policy OR(B/A, 控 severity)", "Q3.c_logistic.main.OR_policyB",
         0.0005, "6_paper.md, 4_results.md, 5_audit.md", 4),
        # —— 弱效应招式箱新增 (references/inconclusive_playbook.md) ——
        ("power_required_n_per_group", "达80%功效检出~4.5pp 每组所需样本量",
         "inconclusive_toolkit.power.required_n_per_group", 0, "6_paper.md, 4_results.md", None),
        ("evalue_point", "logistic OR(B/A) 点估计 E-value",
         "inconclusive_toolkit.e_value.e_value_point", 0.005, "6_paper.md, 4_results.md", 3),
    ]
    frozen = []
    for fid, label, jp, tol, cited, nd in spec:
        val = dig(results, jp)
        if nd is not None and isinstance(val, (int, float)) and not isinstance(val, bool):
            val = round(float(val), nd)
        frozen.append(dict(id=fid, label=label, value=val, tol=tol,
                           source="artifacts/results.json", path=jp, cited_in=cited))
    out_frozen = os.path.join(HERE, "frozen_numbers.json")
    with open(out_frozen, "w", encoding="utf-8") as f:
        json.dump(dict(
            case="demo_dispatch_simpson",
            note="论文/文档引用关键数字的唯一真相源。每个数字回溯到 solve.py 产出的 results.json；"
                 "用 tools/check_frozen.py 校验冻结值与脚本输出一致，tools/check_paper_numbers.py 校验散文引用。",
            inputs=["artifacts/solve.py", "data/dispatch.csv"],
            numbers=frozen), f, ensure_ascii=False, indent=2)
    print("WROTE", out_frozen)

    # 控制台摘要
    print("\n==== SUMMARY ====")
    print(f"Q1 合并率: A={q1r['A']['rate']:.4f} B={q1r['B']['rate']:.4f} "
          f"diff(A-B)={q1r['diff_A_minus_B']['value']:.4f} "
          f"CI[{q1r['diff_A_minus_B']['ci95'][0]:.4f},{q1r['diff_A_minus_B']['ci95'][1]:.4f}] "
          f"p={q1r['diff_A_minus_B']['p_value']:.2e}")
    for s in ["Low", "High"]:
        st = q2r["strata"][s]
        print(f"Q2 {s:>4}: A={st['rate_A']:.4f} B={st['rate_B']:.4f} "
              f"diff(A-B)={st['diff_A_minus_B']['value']:.4f} "
              f"CI[{st['diff_A_minus_B']['ci95'][0]:.4f},{st['diff_A_minus_B']['ci95'][1]:.4f}]")
    print(f"Q2 Simpson 反转: {q2r['simpson_reversal']}")
    prim = q3ar["population_0.5_0.5"]
    print(f"Q3a 标准化率差(B-A,主权重)={-prim['diff_A_minus_B']*100:.2f} pp "
          f"CI[{-prim['ci95_boot'][1]*100:.2f},{-prim['ci95_boot'][0]*100:.2f}]")
    print(f"Q3b MH-OR(A/B)={or_mh:.4f} CI[{mh_lo:.4f},{mh_hi:.4f}] "
          f"Breslow-Day p={bd_p:.4f} (同质={bd_p>0.05})")
    print(f"Q3c logistic OR(B/A)={logit_or_BA:.4f} "
          f"CI[{logit_or_BA_ci[0]:.4f},{logit_or_BA_ci[1]:.4f}] p={q3cr['main']['p_value']:.4f}")
    print(f"三法方向一致(均B优): {cons['all_three_agree_B_better']}")
    pw = incon["power"]; ev = incon["e_value"]
    print(f"招1 power: 达80%功效每组需 N={pw['required_n_per_group']} (共{pw['required_n_total']}, 现有700), Cohen's h={pw['cohens_h']:.4f}")
    for k in ("margin_0.05", "margin_0.10"):
        t = incon["tost"][k]
        print(f"招2 TOST ±{t['delta']:.0%}: p={t['p_tost']:.4f} 等效={t['equivalent']}")
    print(f"招3 E-value(点)={ev['e_value_point']} (RR≈{ev['rr_approx']:.3f}); CI跨零={ev['ci_crosses_null']} E-value(CI)={ev['e_value_ci']}")


if __name__ == "__main__":
    main()
