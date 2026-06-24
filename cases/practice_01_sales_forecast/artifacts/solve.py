# -*- coding: utf-8 -*-
"""
solve.py · ModelCrew Solver — 练习01 月度销量预测（时间序列）
数据自生成(seed=42, 确定性) → 留出验证选模型 → 全量重拟合 → 12 步预测+PI → 诚实误差。
落盘: data/sales.csv + results.json + frozen_numbers.json + figures/
"""
import os, json, hashlib, platform
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.stats.diagnostic import acorr_ljungbox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
matplotlib.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei",
    "Noto Sans CJK SC", "WenQuanYi Zen Hei", "DejaVu Sans"]
matplotlib.rcParams["axes.unicode_minus"] = False

SEED = 42
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(FIGDIR, exist_ok=True)
DATA = os.path.join(DATA_DIR, "sales.csv")
N, H, M = 48, 12, 12          # 总月数 / 预测步数 / 季节周期
TEST = 12                      # 留出最后 12 个月做验证


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(8192), b""):
            h.update(c)
    return h.hexdigest()


def gen_data():
    """确定性生成: 趋势 + 年度季节 + 噪声 (加法)。"""
    rng = np.random.default_rng(SEED)
    t = np.arange(1, N + 1)
    trend = 100 + 1.6 * t
    season = 18 * np.sin(2 * np.pi * (t - 1) / M) + 7 * np.cos(2 * np.pi * (t - 1) / M)
    noise = rng.normal(0, 7, N)
    sales = np.round(trend + season + noise, 1)
    df = pd.DataFrame({"month": t, "sales": sales})
    df.to_csv(DATA, index=False)
    return df


def mape(a, f):
    a, f = np.asarray(a, float), np.asarray(f, float)
    return float(np.mean(np.abs((a - f) / a)) * 100)


def rmse(a, f):
    return float(np.sqrt(np.mean((np.asarray(a, float) - np.asarray(f, float)) ** 2)))


def seasonal_naive(train, steps, m=M):
    """基线: y_t = y_{t-m}。"""
    last = train[-m:]
    return np.array([last[i % m] for i in range(steps)])


def ols_trend_season(train, steps, m=M):
    """趋势 + 季节哑变量 OLS, 带预测区间。"""
    n = len(train)
    tt = np.arange(1, n + 1)
    seas = (tt - 1) % m
    X = np.column_stack([np.ones(n), tt, *[(seas == k).astype(float) for k in range(1, m)]])
    model = sm.OLS(train, X).fit()
    tf = np.arange(n + 1, n + steps + 1)
    sf = (tf - 1) % m
    Xf = np.column_stack([np.ones(steps), tf, *[(sf == k).astype(float) for k in range(1, m)]])
    pred = model.get_prediction(Xf).summary_frame(alpha=0.05)
    return model, pred["mean"].to_numpy(), pred["obs_ci_lower"].to_numpy(), pred["obs_ci_upper"].to_numpy()


def hw(train, steps, damped):
    """Holt-Winters 加法趋势+加法季节(可阻尼)。"""
    fit = ExponentialSmoothing(train, trend="add", damped_trend=damped,
                               seasonal="add", seasonal_periods=M,
                               initialization_method="estimated").fit()
    fc = fit.forecast(steps)
    resid = train - fit.fittedvalues
    se = np.std(resid, ddof=1)
    z = stats.norm.ppf(0.975)
    # 朴素递增区间(随步数放大): se*sqrt(h)
    half = z * se * np.sqrt(np.arange(1, steps + 1))
    return fit, np.asarray(fc), np.asarray(fc) - half, np.asarray(fc) + half


def main():
    df = gen_data()
    y = df.sales.to_numpy()
    train, test = y[:-TEST], y[-TEST:]

    # ---- 留出验证: 各模型在最后 TEST 个月的 MAPE/RMSE ----
    val = {}
    _, f_sn, *_ = (None,) + (seasonal_naive(train, TEST),) + (None, None)
    f_sn = seasonal_naive(train, TEST)
    val["seasonal_naive"] = dict(mape=mape(test, f_sn), rmse=rmse(test, f_sn))
    _, f_ols, lo_ols, hi_ols = ols_trend_season(train, TEST)
    val["ols_trend_season"] = dict(mape=mape(test, f_ols), rmse=rmse(test, f_ols))
    for damped in (False, True):
        _, f_hw, *_ = hw(train, TEST, damped)
        val[f"holt_winters{'_damped' if damped else ''}"] = dict(mape=mape(test, f_hw), rmse=rmse(test, f_hw))

    # ---- 选模型: 验证 MAPE 最小 ----
    best = min(val, key=lambda k: val[k]["mape"])

    # ---- 全量重拟合 best, 预测 H 步 + 95% PI ----
    if best == "seasonal_naive":
        fc = seasonal_naive(y, H); lo = hi = None; resid = y[M:] - y[:-M]
        ljung_p = float(acorr_ljungbox(resid, lags=[M], return_df=True)["lb_pvalue"].iloc[0])
    elif best == "ols_trend_season":
        mdl, fc, lo, hi = ols_trend_season(y, H)
        resid = mdl.resid
        ljung_p = float(acorr_ljungbox(resid, lags=[M], return_df=True)["lb_pvalue"].iloc[0])
    else:
        damped = best.endswith("damped")
        fit, fc, lo, hi = hw(y, H, damped)
        resid = y - fit.fittedvalues
        ljung_p = float(acorr_ljungbox(resid, lags=[M], return_df=True)["lb_pvalue"].iloc[0])

    # ---- 敏感性: 季节周期误设 (m=6) 对 best(若 HW) 的验证 MAPE ----
    sens = {}
    try:
        fit6 = ExponentialSmoothing(train, trend="add", seasonal="add",
                                    seasonal_periods=6, initialization_method="estimated").fit()
        sens["wrong_period_m6_val_mape"] = mape(test, np.asarray(fit6.forecast(TEST)))
    except Exception as e:
        sens["wrong_period_m6_val_mape"] = None

    results = dict(
        meta=dict(case="practice_01_sales_forecast", data_md5=md5_of(DATA), seed=SEED,
                  n_months=N, horizon=H, test_window=TEST, season_period=M,
                  python=platform.python_version(), numpy=np.__version__,
                  pandas=pd.__version__, statsmodels=__import__("statsmodels").__version__),
        validation=val,
        best_model=best,
        best_val_mape=val[best]["mape"],
        baseline_val_mape=val["seasonal_naive"]["mape"],
        improvement_vs_baseline_pp=val["seasonal_naive"]["mape"] - val[best]["mape"],
        forecast=dict(
            months=list(range(N + 1, N + H + 1)),
            point=[round(float(v), 1) for v in fc],
            lower95=None if lo is None else [round(float(v), 1) for v in lo],
            upper95=None if hi is None else [round(float(v), 1) for v in hi],
        ),
        residual_ljungbox_p=ljung_p,
        residual_white=bool(ljung_p > 0.05),
        sensitivity=sens,
    )
    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # ---- 图1: 历史 + 各模型留出预测 ----
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(df.month, y, "k-o", ms=3, label="实际销量")
    ax.axvline(N - TEST + 0.5, ls="--", color="grey")
    tm = np.arange(N - TEST + 1, N + 1)
    ax.plot(tm, f_sn, "--", label=f"季节朴素(MAPE {val['seasonal_naive']['mape']:.1f}%)")
    ax.plot(tm, f_ols, "--", label=f"趋势+季节OLS(MAPE {val['ols_trend_season']['mape']:.1f}%)")
    _, f_hwd, *_ = hw(train, TEST, True)
    ax.plot(tm, f_hwd, "--", label=f"阻尼HW(MAPE {val['holt_winters_damped']['mape']:.1f}%)")
    ax.set_title("留出验证：最后 12 个月各模型预测 vs 实际（虚线左为训练）")
    ax.set_xlabel("月"); ax.set_ylabel("销量"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIGDIR, "fig1_validation.png"), dpi=140); plt.close(fig)

    # ---- 图2: 全量拟合 + 未来 12 月预测 + PI ----
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.plot(df.month, y, "k-o", ms=3, label="历史实际")
    fm = list(range(N + 1, N + H + 1))
    ax.plot(fm, fc, "b-s", ms=3, label=f"预测({best})")
    if lo is not None:
        ax.fill_between(fm, lo, hi, color="b", alpha=0.15, label="95% 预测区间")
    ax.set_title(f"全量重拟合 {best} → 未来 12 个月预测（带 95% PI）")
    ax.set_xlabel("月"); ax.set_ylabel("销量"); ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(FIGDIR, "fig2_forecast.png"), dpi=140); plt.close(fig)

    # ---- frozen_numbers (check_frozen 策展 schema) ----
    rel = "artifacts/results.json"
    def f4(p, nd=2):
        v = results
        for s in p.split("."):
            v = v[int(s)] if isinstance(v, list) else v[s]
        return round(float(v), nd)
    frozen = [
        dict(id="best_model_val_mape", label="选用模型留出 MAPE(%)", value=f4("best_val_mape"),
             tol=0.05, source=rel, path="best_val_mape", cited_in="6_paper.md"),
        dict(id="baseline_val_mape", label="季节朴素基线留出 MAPE(%)", value=f4("baseline_val_mape"),
             tol=0.05, source=rel, path="baseline_val_mape", cited_in="6_paper.md"),
        dict(id="improvement_pp", label="较基线降低 MAPE(百分点)", value=f4("improvement_vs_baseline_pp"),
             tol=0.05, source=rel, path="improvement_vs_baseline_pp", cited_in="6_paper.md"),
        dict(id="ljungbox_p", label="残差 Ljung-Box p 值", value=f4("residual_ljungbox_p", 3),
             tol=0.005, source=rel, path="residual_ljungbox_p", cited_in="6_paper.md"),
    ]
    with open(os.path.join(HERE, "frozen_numbers.json"), "w", encoding="utf-8") as f:
        json.dump(dict(case="practice_01_sales_forecast", note="论文数字唯一真相源",
                       inputs=["artifacts/solve.py"], numbers=frozen), f, ensure_ascii=False, indent=2)

    print("BEST:", best, "| val MAPE %.2f%%" % val[best]["mape"],
          "| baseline %.2f%%" % val["seasonal_naive"]["mape"],
          "| Ljung-Box p=%.3f" % ljung_p)
    for k, v in val.items():
        print(f"  {k:22s} MAPE={v['mape']:.2f}%  RMSE={v['rmse']:.2f}")
    print("forecast[0:3]:", results["forecast"]["point"][:3])


if __name__ == "__main__":
    main()
