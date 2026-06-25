"""
practice_04_green_eval · Solver 求解脚本（确定性，无随机种子，字节级可复现）

承接 3_model.md：主方案 M1 = min-max + CRITIC 赋权 + 加权 TOPSIS。
对照：M0 等权+加权和 / M2 熵权+加权和 / M3 PCA / M5 CRITIC×政策先验。
口径敏感性：N1 min-max / N2 z-score / N3 向量归一（各跑 CRITIC+TOPSIS）。
数据扰动：加性高斯噪声蒙特卡洛 N(0, k·std)，k=5%/10%/20% 各 1000 次（固定随机种子，可复现）。
  —— 注：原"单列乘性 ±δ"扰动在 min-max 归一下是数学恒等式（min-max(a·x)=min-max(x)），
  名次恒不变，是失效实验；已替换为对真实测量误差更贴近的加性噪声。

输出：
  - results.json   全部数值结果（论文真值源的上游）
  - figures/*.png  关键可视化
运行：python artifacts/solve.py   （cwd 任意，全部用绝对/脚本相对路径）

设计约束（对应 Critic 待审计清单 C1/C10）：
  - 逆向 3 项 energy_intensity / carbon_intensity / pm25 统一在无量纲化同口径转向（max-x），杜绝两处各自为政。
  - 全流程确定性：无随机；PCA 主成分符号显式校准与综合方向同向；列顺序固定。
"""
import json
import os
import numpy as np
import pandas as pd
from itertools import combinations

HERE = os.path.dirname(os.path.abspath(__file__))
CASE = os.path.dirname(HERE)
DATA = os.path.join(CASE, "data", "indicators.csv")
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

REVERSE = ["energy_intensity", "carbon_intensity", "pm25"]  # 逆向（越小越好）
# 政策先验权重（M5 用，A7 张力对照）：碳/能耗政策上更重要，给簇内三项更高先验。
# 来源：双碳政策直觉，碳排+能耗为核心减排抓手；非数据导出，仅作敏感性对照（Critic C7：不可凑名次）。
POLICY_PRIOR = {
    "energy_intensity": 0.20, "renewable_share": 0.15, "forest_cover": 0.10,
    "carbon_intensity": 0.25, "solid_waste_util": 0.10, "park_green_percap": 0.05,
    "pm25": 0.15,
}

ROUND = 4  # 论文圆整口径


def load():
    df = pd.read_csv(DATA, index_col="region")
    # 固定列顺序（可复现）
    return df[["energy_intensity", "renewable_share", "forest_cover",
               "carbon_intensity", "solid_waste_util", "park_green_percap", "pm25"]].astype(float)


# ----------------------- 无量纲化（含同口径转向） -----------------------
def norm_minmax(df):
    """N1 min-max：逆向 (max-x)/(max-min)，正向 (x-min)/(max-min)。落 [0,1]。"""
    R = df.copy()
    for c in df.columns:
        lo, hi = df[c].min(), df[c].max()
        if c in REVERSE:
            R[c] = (hi - df[c]) / (hi - lo)
        else:
            R[c] = (df[c] - lo) / (hi - lo)
    return R


def norm_zscore(df):
    """N2 z-score：先把逆向列取负统一方向，再每列 (x-mean)/std。可出负值。"""
    R = df.copy()
    for c in df.columns:
        x = -df[c] if c in REVERSE else df[c]
        R[c] = (x - x.mean()) / x.std(ddof=1)
    return R


def norm_vector(df):
    """N3 向量归一：先逆向取负平移到正区间，再每列除以 sqrt(sum x^2)。"""
    R = df.copy()
    for c in df.columns:
        x = -df[c] if c in REVERSE else df[c]
        x = x - x.min() + 1e-9  # 平移到正，保留方向与相对间距
        R[c] = x / np.sqrt((x ** 2).sum())
    return R


# ----------------------- 赋权 -----------------------
def w_equal(R):
    return pd.Series(1.0 / R.shape[1], index=R.columns)


def w_critic(R):
    """CRITIC：w_j ∝ σ_j · Σ_k(1 - r_jk)。对比强度×冲突性，显式压低强相关簇（治 D1）。"""
    sd = R.std(ddof=1)
    corr = R.corr()
    conflict = (1 - corr).sum(axis=0)
    C = sd * conflict
    return C / C.sum()


def w_entropy(R):
    """熵权法：对 min-max [0,1] 列做行归一为概率，算信息熵，权重 ∝ (1-熵)冗余度。
    纯离散度驱动、不看相关性（D2 兑现、D1 不处理），作反面镜子。"""
    P = R / R.sum(axis=0)
    P = P.replace(0, np.nan)
    k = 1.0 / np.log(R.shape[0])
    e = -k * (P * np.log(P)).sum(axis=0)  # 信息熵
    d = 1 - e  # 冗余度（区分度）
    return d / d.sum()


def w_pca_loadings(R):
    """M3 PCA：用第一主成分（最大方差方向）的载荷绝对值构造权重。
    显式校准 PC1 符号使其与综合方向同向（与各指标正相关，因 R 已全部转为越大越好）。"""
    Z = (R - R.mean()) / R.std(ddof=1)  # 标准化进 PCA
    cov = np.cov(Z.values, rowvar=False)
    vals, vecs = np.linalg.eigh(cov)  # 升序
    pc1 = vecs[:, -1]  # 最大特征值对应
    # 符号校准：让 PC1 与"所有指标之和"方向一致（载荷和为正）
    if pc1.sum() < 0:
        pc1 = -pc1
    w = np.abs(pc1)
    w = w / w.sum()
    return pd.Series(w, index=R.columns)


def w_critic_policy(R, alpha=0.5):
    """M5 组合赋权：CRITIC 与政策先验几何融合 w ∝ w_critic^(1-a) · w_policy^a。
    a=0.5 等权融合客观/先验。仅作 A7 张力对照（Critic C7）。"""
    wc = w_critic(R)
    wp = pd.Series(POLICY_PRIOR)[R.columns]
    comb = (wc ** (1 - alpha)) * (wp ** alpha)
    return comb / comb.sum()


# ----------------------- 聚合 -----------------------
def aggregate_saw(R, w):
    """加权和 SAW。返回得分 Series。"""
    return (R * w).sum(axis=1)


def aggregate_topsis(R, w):
    """加权 TOPSIS，返回贴近度 C_i 及到正/负理想解距离（供 Q2 短板诊断）。"""
    V = R * w
    vp = V.max()
    vn = V.min()
    Dp = np.sqrt(((V - vp) ** 2).sum(axis=1))
    Dn = np.sqrt(((V - vn) ** 2).sum(axis=1))
    C = Dn / (Dp + Dn)
    return C, Dp, Dn, V, vp, vn


def aggregate_pca_score(R, w_unused=None):
    """M3：直接用 PC1 得分（标准化后投影），符号已校准同向。"""
    Z = (R - R.mean()) / R.std(ddof=1)
    cov = np.cov(Z.values, rowvar=False)
    vals, vecs = np.linalg.eigh(cov)
    pc1 = vecs[:, -1]
    if pc1.sum() < 0:
        pc1 = -pc1
    score = Z.values @ pc1
    var_explained = vals[-1] / vals.sum()
    return pd.Series(score, index=R.index), float(var_explained), pd.Series(pc1, index=R.columns)


def ranks_from_score(score):
    """得分降序 → 名次（1=最好）。method='min' 处理并列。"""
    return score.rank(ascending=False, method="min")


# ----------------------- 排名相关系数（手写，确定性） -----------------------
def spearman(s1, s2):
    """Spearman 秩相关：对名次（值）求 Pearson。s1,s2 为得分 Series（同 index）。"""
    r1 = s1.rank()
    r2 = s2.rank()
    return float(np.corrcoef(r1.values, r2.values)[0, 1])


def kendall_tau(s1, s2):
    """Kendall tau-b。"""
    x = s1.values
    y = s2.values
    n = len(x)
    conc = disc = 0
    for i, j in combinations(range(n), 2):
        a = np.sign(x[i] - x[j])
        b = np.sign(y[i] - y[j])
        if a * b > 0:
            conc += 1
        elif a * b < 0:
            disc += 1
    return float((conc - disc) / (0.5 * n * (n - 1)))


# ============================ 主流程 ============================
def main():
    df = load()
    regions = list(df.index)
    cols = list(df.columns)

    R = norm_minmax(df)  # 主口径

    # ---------- 各方案权重 ----------
    weights = {
        "M0_equal": w_equal(R),
        "M1_critic": w_critic(R),
        "M2_entropy": w_entropy(R),
        "M3_pca_loadings": w_pca_loadings(R),
        "M5_critic_policy": w_critic_policy(R, alpha=0.5),
    }
    # 单独标准差权重（仅供 D1 降权验证对照）
    w_std_only = R.std(ddof=1) / R.std(ddof=1).sum()

    # ---------- 各方案得分与排名 ----------
    # M1 主方案: CRITIC + TOPSIS
    C1, Dp1, Dn1, V1, vp1, vn1 = aggregate_topsis(R, weights["M1_critic"])
    rank1 = ranks_from_score(C1)

    # M0: 等权 + 加权和
    s0 = aggregate_saw(R, weights["M0_equal"])
    # M2: 熵权 + 加权和
    s2 = aggregate_saw(R, weights["M2_entropy"])
    # M3: PCA 主成分得分
    s3, pca_var, pca_load = aggregate_pca_score(R)
    # M5: CRITIC×政策先验 + TOPSIS（与主方案同聚合，仅换权重，纯看赋权张力）
    C5, _, _, _, _, _ = aggregate_topsis(R, weights["M5_critic_policy"])

    scores = {
        "M0_equal_saw": s0,
        "M1_critic_topsis": C1,
        "M2_entropy_saw": s2,
        "M3_pca_score": s3,
        "M5_policy_topsis": C5,
    }
    ranks = {k: ranks_from_score(v) for k, v in scores.items()}

    # ---------- Q3 稳健性：秩相关矩阵（以 M1 为基准） ----------
    base = scores["M1_critic_topsis"]
    rank_corr = {}
    for k, v in scores.items():
        rank_corr[k] = {
            "spearman_vs_M1": round(spearman(base, v), ROUND),
            "kendall_vs_M1": round(kendall_tau(base, v), ROUND),
        }

    # ---------- Q3 口径敏感性：N1/N2/N3 各跑 CRITIC+TOPSIS ----------
    norm_variants = {"N1_minmax": norm_minmax, "N2_zscore": norm_zscore, "N3_vector": norm_vector}
    norm_scores = {}
    norm_ranks = {}
    for nk, fn in norm_variants.items():
        Rn = fn(df)
        wn = w_critic(Rn)
        Cn, _, _, _, _, _ = aggregate_topsis(Rn, wn)
        norm_scores[nk] = Cn
        norm_ranks[nk] = ranks_from_score(Cn)
    norm_corr = {nk: {"spearman_vs_N1": round(spearman(norm_scores["N1_minmax"], v), ROUND),
                      "kendall_vs_N1": round(kendall_tau(norm_scores["N1_minmax"], v), ROUND)}
                 for nk, v in norm_scores.items()}

    # ---------- Q3 数据扰动：加性高斯噪声蒙特卡洛（固定种子，可复现） ----------
    # 诚实的数据扰动模型。原"单列乘性 ±δ"扰动在 min-max 下是恒等式
    #   min-max(a·x) = (a·x − a·lo)/(a·hi − a·lo) = (x − lo)/(hi − lo)
    # 乘性缩放被完全抵消 ⇒ R 矩阵逐位不变 ⇒ 权重/贴近度/名次恒不变（失效实验，测了个寂寞）。
    # 改用加性噪声 x' = x + N(0, k·std_j)（贴近真实测量误差），对每列按其原始标准差缩放噪声，
    # k ∈ {5%, 10%, 20%}，各 1000 次，固定随机种子保证字节级可复现。
    # 每次重算 M1（min-max+CRITIC+TOPSIS），统计：①整体名次向量改变比例；②各地区名次分布。
    MC_SEED = 20240625
    MC_N = 1000
    base_rank_vec = {r: int(rank1[r]) for r in regions}
    col_std = df.std(ddof=1)

    def run_mc(k, n=MC_N, seed=MC_SEED):
        rng = np.random.default_rng(seed)  # 每个 k 用同一固定种子，独立可复现
        changed = 0
        rank_samples = {r: [] for r in regions}
        scale = (k * col_std.values)  # 各列噪声标准差（按原始量纲）
        for _ in range(n):
            noise = rng.normal(0.0, 1.0, size=df.shape) * scale
            dfp = df + noise
            Rp = norm_minmax(dfp)
            wp = w_critic(Rp)
            Cp, _, _, _, _, _ = aggregate_topsis(Rp, wp)
            rp = ranks_from_score(Cp)
            rp_int = {r: int(rp[r]) for r in regions}
            if rp_int != base_rank_vec:
                changed += 1
            for r in regions:
                rank_samples[r].append(rp_int[r])
        per_region = {}
        for r in regions:
            arr = np.array(rank_samples[r])
            per_region[r] = {
                "base_rank": base_rank_vec[r],
                "mean_rank": round(float(arr.mean()), 4),
                "p05_rank": int(np.percentile(arr, 5)),
                "p95_rank": int(np.percentile(arr, 95)),
                "min_rank": int(arr.min()),
                "max_rank": int(arr.max()),
                "span": int(arr.max() - arr.min()),
                "pct_rank_changed": round(float((arr != base_rank_vec[r]).mean()), 4),
            }
        return {
            "noise_k": k,
            "n_runs": n,
            "seed": seed,
            "n_ranking_changed": int(changed),
            "frac_ranking_changed": round(changed / n, 4),
            "per_region": per_region,
        }

    mc_results = {f"k{int(k*100):02d}pct": run_mc(k) for k in (0.05, 0.10, 0.20)}

    # 加性噪声下"最不稳地区"：以 5% 档名次改变比例最大者（剔除恒不动的头尾）为准
    mc5 = mc_results["k05pct"]["per_region"]
    most_unstable = max(mc5.items(), key=lambda kv: (kv[1]["pct_rank_changed"], kv[1]["span"]))
    # 用于 Fig3 误差棒（5% 档 p05–p95 名次区间）
    pick = mc5

    # ---------- Q3 跨方案名次波动（M0/M1/M2/M3 四套主对照，含口径 N2/N3） ----------
    cross_rank_table = {}
    method_set = {
        "M0_equal_saw": ranks["M0_equal_saw"],
        "M1_critic_topsis": ranks["M1_critic_topsis"],
        "M2_entropy_saw": ranks["M2_entropy_saw"],
        "M3_pca_score": ranks["M3_pca_score"],
        "M5_policy_topsis": ranks["M5_policy_topsis"],
        "N2_zscore_critic_topsis": norm_ranks["N2_zscore"],
        "N3_vector_critic_topsis": norm_ranks["N3_vector"],
    }
    cross_rank_spread = {}
    for r in regions:
        rr = [int(method_set[m][r]) for m in method_set]
        cross_rank_table[r] = {m: int(method_set[m][r]) for m in method_set}
        cross_rank_spread[r] = {"min": min(rr), "max": max(rr), "span": max(rr) - min(rr)}
    most_unstable_cross = max(cross_rank_spread.items(), key=lambda kv: kv[1]["span"])

    # ---------- Q2 短板诊断：靠后地区（M1 名次后3）的指标贡献分解 ----------
    # 门槛：M1 名次后 3 名（出分后定）。短板归因双视角：
    #   (a) 加权和缺口分解 gap_j = w_j*(r*_j - r_ij)，r*_j = 该列理想(=1, min-max下)
    #   (b) TOPSIS 到负理想各维分量（离负理想越近=越短板）
    laggards = [r for r in regions if rank1[r] >= 8]  # 后3名
    w_m1 = weights["M1_critic"]
    shortboard = {}
    for r in laggards:
        # (a) SAW 缺口分解（用 M1 的 CRITIC 权重，理想 r*=1）
        gap = {c: round(float(w_m1[c] * (1.0 - R.loc[r, c])), ROUND) for c in cols}
        gap_sorted = sorted(gap.items(), key=lambda kv: kv[1], reverse=True)
        # (b) TOPSIS 各维到正理想距离平方分量（越大越短板）
        dist_p = {c: round(float((V1.loc[r, c] - vp1[c]) ** 2), 6) for c in cols}
        dist_sorted = sorted(dist_p.items(), key=lambda kv: kv[1], reverse=True)
        shortboard[r] = {
            "rank_M1": int(rank1[r]),
            "closeness_M1": round(float(C1[r]), ROUND),
            "saw_gap_contribution": gap,
            "top3_shortboard_by_gap": [g[0] for g in gap_sorted[:3]],
            "topsis_dist_to_ideal_sq": dist_p,
            "top3_shortboard_by_topsis": [d[0] for d in dist_sorted[:3]],
            "raw_values": {c: float(df.loc[r, c]) for c in cols},
        }

    # ---------- C2 受控隔离：固定聚合(TOPSIS)、只换赋权，量化"去冗余的单独效应" ----------
    # 原 M1 vs M2 同时换了赋权(CRITIC↔熵权)与聚合(TOPSIS↔SAW)，是混杂对比。
    # 这里固定 TOPSIS 聚合，仅替换权重为 熵权/等权/std-only，单独看"换赋权"对名次的影响。
    base_topsis_score = scores["M1_critic_topsis"]
    c2_isolation = {}
    for wname, wser in [("entropy", weights["M2_entropy"]),
                        ("equal", weights["M0_equal"]),
                        ("std_only", w_std_only)]:
        Cx, _, _, _, _, _ = aggregate_topsis(R, wser)
        c2_isolation[wname] = {
            "spearman_vs_critic": round(spearman(base_topsis_score, Cx), ROUND),
            "kendall_vs_critic": round(kendall_tau(base_topsis_score, Cx), ROUND),
            "ranks": {r: int(ranks_from_score(Cx)[r]) for r in regions},
        }

    # ---------- C4 受控归因：CRITIC 各指标权重相对等权(1/7)的增减 ----------
    # 论文原称"抬高 forest_cover 与 pm25 权重→H 反超 G"，实测核对：唯一被抬的是 forest_cover，
    # pm25 相对等权不升反微降。下表给出每项 CRITIC − 等权 的差值供如实归因。
    w_eq_val = 1.0 / len(cols)
    critic_vs_equal_delta = {c: round(float(weights["M1_critic"][c] - w_eq_val), ROUND) for c in cols}
    c4_attrib = {
        "critic_minus_equal": critic_vs_equal_delta,
        "raised_vs_equal": [c for c in cols if critic_vs_equal_delta[c] > 0],
        "lowered_vs_equal": [c for c in cols if critic_vs_equal_delta[c] < 0],
        "forest_cover_delta": critic_vs_equal_delta["forest_cover"],
        "pm25_delta": critic_vs_equal_delta["pm25"],
        "note": "相对等权仅 forest_cover 被抬(+%.4f)，pm25 不升反微降(%.4f)；H 反超 G 由 forest_cover 抬权驱动" % (
            critic_vs_equal_delta["forest_cover"], critic_vs_equal_delta["pm25"]),
    }

    # ---------- D1 降权验证（CRITIC vs std-only） ----------
    d1_check = {
        "critic_weights": {c: round(float(weights["M1_critic"][c]), ROUND) for c in cols},
        "std_only_weights": {c: round(float(w_std_only[c]), ROUND) for c in cols},
        "energy_carbon_critic_sum": round(float(weights["M1_critic"][["energy_intensity", "carbon_intensity"]].sum()), ROUND),
        "energy_carbon_std_only_sum": round(float(w_std_only[["energy_intensity", "carbon_intensity"]].sum()), ROUND),
        "d1_downweighted": bool(weights["M1_critic"][["energy_intensity", "carbon_intensity"]].sum()
                               < w_std_only[["energy_intensity", "carbon_intensity"]].sum()),
    }

    # ---------- 组装 results.json ----------
    def ser(d):
        return {k: round(float(v), ROUND) for k, v in d.items()}

    def serw(w):
        return {k: round(float(v), ROUND) for k, v in w.items()}

    # M1 主排名表（含距离，供论文表）
    m1_table = []
    for r in sorted(regions, key=lambda x: -C1[x]):
        m1_table.append({
            "region": r, "rank": int(rank1[r]),
            "closeness": round(float(C1[r]), ROUND),
            "D_plus": round(float(Dp1[r]), ROUND),
            "D_minus": round(float(Dn1[r]), ROUND),
        })

    results = {
        "meta": {
            "case": "practice_04_green_eval",
            "main_method": "M1 = min-max + CRITIC weighting + weighted TOPSIS",
            "deterministic": True, "random_seed": None, "round_digits": ROUND,
            "n_regions": len(regions), "n_indicators": len(cols),
            "reverse_indicators": REVERSE, "columns_order": cols,
        },
        "Q1": {
            "weights": {k: serw(v) for k, v in weights.items()},
            "M1_main_ranking": m1_table,
            "M1_top3": [m1_table[i]["region"] for i in range(3)],
            "M1_bottom3": [m1_table[-(i + 1)]["region"] for i in range(3)][::-1],
            "G_vs_H": {"G_rank": int(rank1["G"]), "H_rank": int(rank1["H"]),
                       "first_place": "H" if rank1["H"] < rank1["G"] else "G"},
            "all_method_scores": {k: ser(v) for k, v in scores.items()},
            "all_method_ranks": {k: {r: int(v[r]) for r in regions} for k, v in ranks.items()},
            "d1_downweight_check": d1_check,
            "c4_attribution_critic_vs_equal": c4_attrib,
            "pca_var_explained_pc1": round(pca_var, ROUND),
            "pca_pc1_loadings": serw(pca_load),
        },
        "Q2": {
            "laggard_threshold": "M1 rank >= 8 (bottom 3)",
            "laggards": laggards,
            "shortboard_diagnosis": shortboard,
        },
        "Q3": {
            "rank_correlation_vs_M1": rank_corr,
            "c2_dedup_isolation_fixed_topsis": c2_isolation,
            "norm_caliber_scores": {k: ser(v) for k, v in norm_scores.items()},
            "norm_caliber_ranks": {k: {r: int(v[r]) for r in regions} for k, v in norm_ranks.items()},
            "norm_caliber_corr_vs_N1": norm_corr,
            "data_perturbation_additive_gaussian_mc": {
                "noise_model": "x' = x + N(0, k*std_j) per column; min-max+CRITIC+TOPSIS recomputed each run",
                "note_multiplicative_invalid": "原乘性 ±δ 扰动在 min-max 下恒等(min-max(a·x)=min-max(x))，名次恒不变，已弃用",
                "seed": MC_SEED, "n_runs_each": MC_N,
                "k05pct": mc_results["k05pct"],
                "k10pct": mc_results["k10pct"],
                "k20pct": mc_results["k20pct"],
                "frac_ranking_changed_by_k": {
                    "k05pct": mc_results["k05pct"]["frac_ranking_changed"],
                    "k10pct": mc_results["k10pct"]["frac_ranking_changed"],
                    "k20pct": mc_results["k20pct"]["frac_ranking_changed"],
                },
            },
            "most_unstable_region_under_perturb": {"region": most_unstable[0], **most_unstable[1]},
            "cross_method_rank_table": cross_rank_table,
            "cross_method_rank_spread": cross_rank_spread,
            "most_unstable_region_cross_method": {"region": most_unstable_cross[0], **most_unstable_cross[1]},
        },
    }

    out = os.path.join(HERE, "results.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("written:", out)

    # ---------- 可视化 ----------
    make_figures(df, R, regions, cols, m1_table, C1, weights, scores, ranks,
                 method_set, pick, shortboard, w_std_only)

    # ---------- 控制台摘要 ----------
    print("\n=== M1 主排名 ===")
    for row in m1_table:
        print(f"  {row['rank']:>2}  {row['region']}  C={row['closeness']:.4f}")
    print("Top3:", results["Q1"]["M1_top3"], " Bottom3:", results["Q1"]["M1_bottom3"])
    print("G vs H 第一:", results["Q1"]["G_vs_H"]["first_place"],
          f"(G={rank1['G']:.0f}, H={rank1['H']:.0f})")
    print("D1 降权:", d1_check["d1_downweighted"],
          f"(energy+carbon CRITIC={d1_check['energy_carbon_critic_sum']} < std_only={d1_check['energy_carbon_std_only_sum']})")
    print(f"C4 CRITIC vs 等权: 被抬={c4_attrib['raised_vs_equal']} forest_cover_delta={c4_attrib['forest_cover_delta']:+}, "
          f"pm25_delta={c4_attrib['pm25_delta']:+} (pm25 不升反降)")
    print("C2 受控隔离(固定TOPSIS只换赋权) Spearman vs CRITIC:",
          {k: v["spearman_vs_critic"] for k, v in c2_isolation.items()})
    print("加性高斯噪声蒙特卡洛(seed=%d, n=%d) 名次改变比例:" % (MC_SEED, MC_N),
          {k: v["frac_ranking_changed"] for k, v in mc_results.items()})
    print(f"最不稳地区(加性5%噪声): {most_unstable[0]} 改名次比例={most_unstable[1]['pct_rank_changed']*100:.1f}% "
          f"p05-p95=[{most_unstable[1]['p05_rank']},{most_unstable[1]['p95_rank']}]")
    print("最不稳地区(跨方案):", most_unstable_cross[0], most_unstable_cross[1])
    print("\nSpearman vs M1:")
    for k, v in rank_corr.items():
        print(f"  {k}: spearman={v['spearman_vs_M1']}, kendall={v['kendall_vs_M1']}")
    return results


def make_figures(df, R, regions, cols, m1_table, C1, weights, scores, ranks,
                 method_set, perturb_rank_range, shortboard, w_std_only):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    # 中文字体（若无则用英文标签，不阻塞）
    plt.rcParams["axes.unicode_minus"] = False
    for f in ["Microsoft YaHei", "SimHei", "DejaVu Sans"]:
        try:
            font_manager.findfont(f, fallback_to_default=False)
            plt.rcParams["font.sans-serif"] = [f]
            break
        except Exception:
            continue

    # Fig1: M1 综合贴近度排序条形（带 D+/D-）
    fig, ax = plt.subplots(figsize=(8, 5))
    order = [row["region"] for row in m1_table]
    vals = [row["closeness"] for row in m1_table]
    colors = ["#2ca02c" if v >= 0.5 else ("#ff7f0e" if v >= 0.35 else "#d62728") for v in vals]
    bars = ax.bar(order, vals, color=colors, edgecolor="black", linewidth=0.5)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.01, f"{v:.3f}", ha="center", fontsize=8)
    ax.set_title("M1 (CRITIC + weighted TOPSIS) green-low-carbon closeness ranking", fontsize=11)
    ax.set_xlabel("Region (sorted by rank)")
    ax.set_ylabel("Closeness coefficient C_i  (dimensionless, 0-1)")
    ax.set_ylim(0, max(vals) * 1.18)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig1_M1_ranking_bar.png"), dpi=150)
    plt.close(fig)

    # Fig2: 跨方案名次热图
    methods = list(method_set.keys())
    mat = np.array([[int(method_set[m][r]) for m in methods] for r in regions])
    fig, ax = plt.subplots(figsize=(9, 5.5))
    im = ax.imshow(mat, cmap="RdYlGn_r", aspect="auto", vmin=1, vmax=10)
    ax.set_xticks(range(len(methods)))
    ax.set_xticklabels([m.replace("_", "\n") for m in methods], fontsize=7, rotation=0)
    ax.set_yticks(range(len(regions)))
    ax.set_yticklabels(regions)
    for i in range(len(regions)):
        for j in range(len(methods)):
            ax.text(j, i, mat[i, j], ha="center", va="center", fontsize=8, color="black")
    ax.set_title("Rank under different weighting / normalization schemes (1=best, 10=worst)", fontsize=10)
    ax.set_ylabel("Region")
    fig.colorbar(im, ax=ax, label="Rank")
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig2_cross_method_rank_heatmap.png"), dpi=150)
    plt.close(fig)

    # Fig3: 加性高斯噪声(5%·std) 蒙特卡洛下名次分布（误差棒=p05–p95 敏感区间）
    fig, ax = plt.subplots(figsize=(8.5, 5))
    order = [row["region"] for row in m1_table]
    base = [perturb_rank_range[r]["base_rank"] for r in order]
    lo = [perturb_rank_range[r]["p05_rank"] for r in order]
    hi = [perturb_rank_range[r]["p95_rank"] for r in order]
    pct = [perturb_rank_range[r]["pct_rank_changed"] for r in order]
    yerr = [[b - l for b, l in zip(base, lo)], [h - b for b, h in zip(base, hi)]]
    colors = ["#d62728" if p > 0.2 else ("#ff7f0e" if p > 0.0 else "#2ca02c") for p in pct]
    for i, r in enumerate(order):
        ax.errorbar([r], [base[i]], yerr=[[yerr[0][i]], [yerr[1][i]]], fmt="o",
                    color=colors[i], ecolor=colors[i], capsize=5, markersize=8, linewidth=2)
        ax.text(i, hi[i] + 0.15, f"{pct[i]*100:.0f}%", ha="center", va="top", fontsize=8)
    ax.set_title("M1 rank under additive Gaussian noise N(0, 5%·std), 1000 MC runs (seed=20240625)", fontsize=10)
    ax.set_xlabel("Region (sorted by M1 base rank).  Red=rank changed >20% of runs, green=frozen")
    ax.set_ylabel("Rank (1=best).  Bars = 5th-95th percentile;  label = % of runs rank changed")
    ax.invert_yaxis()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig3_perturbation_rank_interval.png"), dpi=150)
    plt.close(fig)

    # Fig4: CRITIC 权重 vs 单独标准差权重（D1 降权可视化）
    fig, ax = plt.subplots(figsize=(9, 5))
    x = np.arange(len(cols))
    wc = [weights["M1_critic"][c] for c in cols]
    ws = [w_std_only[c] for c in cols]
    ax.bar(x - 0.2, wc, 0.4, label="CRITIC (M1)", color="#2ca02c", edgecolor="black", linewidth=0.4)
    ax.bar(x + 0.2, ws, 0.4, label="Std-only (no conflict term)", color="#7f7f7f", edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace("_", "\n") for c in cols], fontsize=7)
    ax.set_title("CRITIC vs std-only weights: conflict term down-weights collinear D1 cluster", fontsize=10)
    ax.set_ylabel("Weight (sum=1)")
    ax.axhline(1 / 7, color="black", ls="--", lw=0.7, alpha=0.6, label="equal 1/7")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig4_critic_vs_std_weights.png"), dpi=150)
    plt.close(fig)

    # Fig5: 短板诊断堆叠（靠后地区各指标 SAW 缺口贡献）
    laggards = list(shortboard.keys())
    laggards = sorted(laggards, key=lambda r: shortboard[r]["rank_M1"])
    fig, ax = plt.subplots(figsize=(8, 5))
    bottom = np.zeros(len(laggards))
    cmap = plt.get_cmap("tab10")
    for ci, c in enumerate(cols):
        vals = [shortboard[r]["saw_gap_contribution"][c] for r in laggards]
        ax.bar(laggards, vals, bottom=bottom, label=c, color=cmap(ci))
        bottom += np.array(vals)
    ax.set_title("Q2 shortboard: per-indicator gap-to-ideal contribution (CRITIC-weighted)", fontsize=10)
    ax.set_xlabel("Laggard region (M1 bottom 3)")
    ax.set_ylabel("Gap contribution  w_j*(1 - r_ij)")
    ax.legend(fontsize=7, ncol=2, loc="upper right")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIGDIR, "fig5_shortboard_diagnosis.png"), dpi=150)
    plt.close(fig)

    print("figures written to:", FIGDIR)


if __name__ == "__main__":
    main()
