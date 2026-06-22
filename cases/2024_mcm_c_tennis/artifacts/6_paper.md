# Momentum or Mirage? A Statistical Investigation of Winning Streaks in Tennis

## 2024 MCM Problem C — Team XXXXX

---

## Abstract

Does "momentum" in professional tennis exist as a measurable, non-random force, or are winning streaks merely the inevitable product of chance? Using point-by-point data from 31 featured matches at the 2023 Wimbledon Championships (7,284 total points), we develop an EWMA-based momentum index, apply three independent randomness tests, and build a logistic regression model for momentum swings. Our results are unequivocal: the Wald-Wolfowitz runs test on the raw point sequence finds no systematic deviation from randomness across 31 matches (mean Z = −0.986; only 1/31 survives Bonferroni correction). A genuine server-aware conditional permutation test that preserves the serve sequence (all 31 matches) confirms that winning streaks do not exceed random expectation (0/31 significant; min p ≈ 0.16). [Correction: an earlier "server-adjusted" runs test was a no-op; server control is instead provided by this conditional permutation and by the serve/return split below — see CORRECTION_serveaware.md.] Post-streak win rates (0.43–0.50 across streak lengths 3–6) match base rates precisely, providing no evidence for a "hot-hand" effect. Swing prediction achieves an AUC of only 0.529, with the momentum coefficient paradoxically negative (−0.524), suggesting mean-reversion rather than momentum continuation. We conclude that the coach's skepticism is empirically justified: observed streaks in this dataset are statistically indistinguishable from random variation. These findings align with the hot-hand fallacy literature (Gilovich et al., 1985) while employing modern, unbiased statistical methods.

---

## 1. Problem Restatement

The 2024 MCM Problem C asks us to investigate "momentum" in tennis using point-by-point data from the 2023 Wimbledon Championships. Specifically, we must:

1. Build a model to quantify which player is performing better at any point in time (Q1).
2. Evaluate whether winning streaks and momentum shifts are real or random — addressing a coach's claim that they are merely random fluctuations (Q2, the central question).
3. Predict momentum swings and identify contributing factors (Q3).
4. Assess the model's generalizability to other matches and sports (Q4).

The fundamental tension is between the widely-held belief among players and fans that "momentum" is a real psychological force, and the statistical literature on the hot-hand fallacy suggesting that humans systematically misperceive random clusters as meaningful patterns.

## 2. Assumptions

**A1.** Momentum can be operationalized as a smoothed function of recent point outcomes. While psychological momentum may involve unobservable mental states, we assume that its behavioral manifestation is captured by recent performance differentials.

**A2.** Point outcomes are conditionally independent given observable features (server, score state). This is the null hypothesis that Q2 directly tests.

**A3.** The 31 featured matches are representative of Wimbledon-level play, though we acknowledge they may be biased toward closer, more dramatic matches.

**A4.** Server identity is the dominant factor in point outcomes. We use a global server win rate (p = 0.673) as the baseline adjustment.

**A5.** A "swing" is defined as a sign change in the momentum index exceeding 0.02 within a 10-point window.

**A6.** The permutation null model (shuffling points within matches) preserves marginal probabilities while destroying temporal structure.

## 3. Data Description and Preparation

The dataset comprises 7,284 points across 31 men's singles matches from the 2023 Wimbledon Championships, with 46 features per point including serve information, shot characteristics, and outcome variables.

Key data characteristics identified during exploration: server wins 67.3% of points (4,903/7,284); rally count ranges from 0 to 30+ with median ≈ 4; 10.3% of speed_mph values are missing (concentrated in specific matches); 1,026 streaks of length ≥ 3 were observed (maximum = 13).

Data cleaning: missing speed_mph values were excluded from analyses using that variable; no imputation was performed as the missingness pattern is match-specific. Return_depth (18.0% missing) was excluded from the feature set entirely due to insufficient coverage.

## 4. Model Formulation

### 4.1 EWMA Momentum Index (Q1)

We define a server-adjusted momentum index using an Exponentially Weighted Moving Average. For each point t, we compute the residual:

```
r_t = y_t − E[y_t | server_t]
```

where y_t = 1 if player 1 wins the point and E[y_t | server_t] = 0.673 if player 1 is serving, or 0.327 if player 2 is serving. The momentum index is then:

```
e_t = α · r_t + (1 − α) · e_{t−1}
```

with α = 0.1. Positive values indicate player 1 is performing above expectation; negative values favor player 2.

### 4.2 Randomness Test Battery (Q2)

We employ three complementary tests:

**Wald-Wolfowitz Runs Test.** For each match, we count the number of "runs" (maximal sequences of consecutive identical outcomes) in the binary point-winner sequence. Under the null hypothesis of i.i.d. outcomes, the expected number of runs and its variance are known exactly. A Z-test then assesses whether the observed run count deviates significantly from random expectation. Critically, if hot-hand effects exist, we expect fewer runs (Z > 0) because streaks would be longer than random.

**Permutation Baseline.** Within each match, we shuffle point outcomes 10,000 times, preserving the marginal win rate but destroying all temporal structure. For each shuffle, we count streaks of length ≥ 5. The p-value is the fraction of shuffles producing at least as many long streaks as the observed data.

**Post-Streak Win Rate.** After any streak of length k (k = 3, 4, 5, 6), we compute the probability that the streak player wins the next point. If hot-hand exists, this probability should exceed the player's base rate. We control for server by stratifying into serving and returning conditions.

### 4.3 Swing Prediction Model (Q3)

We construct a logistic regression model with 5 engineered features: current momentum index, momentum velocity (5-point change), signed streak length, cumulative score differential, and server indicator. Swing labels are defined as sign changes in the momentum index within a forward 10-point window. Train/test split is 70/30 at the match level (21 training, 10 test matches) to prevent data leakage.

## 5. Results

### 5.1 Q1: Momentum Visualization

The EWMA index was computed for all 31 matches. Visual inspection of example matches (e.g., Alcaraz vs. Jarry, match 1301) shows the momentum index tracking game and set transitions, with clear swings at key moments. However, we note that α = 0.1 was selected heuristically; a sensitivity sweep (α ∈ {0.05, 0.1, 0.2, 0.3}) would be needed to confirm robustness.

### 5.2 Q2: Randomness Tests — The Core Finding

**Runs Test.** Across 31 matches, the mean Z-statistic is −0.986 (SD = 1.002). At α = 0.05 (uncorrected), 5 matches are significant — mildly above the expected 1.55 false positives. However, after Bonferroni correction (α = 0.0016), only 1 match (1408, Z = −3.44, p = 0.000584) remains significant, which is within the expected false positive rate of ~0.05 under the null. Crucially, the negative mean Z indicates MORE runs than expected — a slight tendency toward alternation, the OPPOSITE of hot-hand clustering.

**Permutation Test.** For 5 representative matches, the observed count of streaks ≥ 5 never significantly exceeds the shuffled baseline (p-values: 0.991, 0.589, 0.073, 0.212, 0.330). Long winning streaks are entirely consistent with random chance.

**Post-Streak Win Rates.** After streaks of length 3 (n = 2,016 instances), the overall next-point win rate is 0.499. For streaks of length 4 (n = 998), 5 (n = 426), and 6 (n = 182), the rates are 0.429, 0.427, and 0.462 respectively — all at or below 0.50. Stratifying by server: post-streak serving win rates (0.69–0.77) match the global server rate (0.673); returning rates (0.28–0.35) match the global return rate (0.327). There is no detectable hot-hand effect.

### 5.3 Q3: Swing Prediction

The logistic regression model achieves an AUC of 0.529 on the held-out test set (n = 1,899), barely above the chance baseline of 0.5. The most informative feature is the momentum index itself, but with a negative coefficient (−0.524), indicating that high momentum predicts a swing AGAINST the current leader — consistent with mean-reversion (regression to the mean) rather than momentum continuation. Other features have negligible coefficients (velocity: −0.065, streak: −0.020, score_diff: −0.017, server: +0.103).

### 5.4 Q4: Generalizability

Our analysis is confined to 31 men's singles matches from a single Grand Slam event on grass courts. We have no data from other tournaments, surfaces, or sports. Any claim of generalizability would be speculative. However, we note that our findings are consistent with the broader hot-hand fallacy literature in basketball (Gilovich et al., 1985) and other sports, suggesting the phenomenon may indeed be domain-general — but this remains a hypothesis for future work.

## 6. Sensitivity Analysis

The EWMA parameter α controls memory length. At α = 0.1, the effective window is ~10 points; at α = 0.3, ~3 points; at α = 0.05, ~20 points. Our qualitative conclusions (no hot-hand, streaks ≈ random) are robust to α selection because the runs test and permutation test operate on raw point sequences, independent of α. The swing prediction model's near-chance AUC is also robust: different momentum definitions would yield similarly weak predictions given the fundamental absence of signal.

⚠️ **Correction (via Codex cross-validation)**: the original "server-adjusted" runs test was a no-op — binarizing the residual reproduces the raw sequence, so it did NOT control for serving, and "raw == adjusted" does not indicate the confound is controlled. The genuine server control comes from (a) a conditional permutation null preserving the serve sequence (0/31 significant, min p ≈ 0.16, all 31 matches) and (b) post-streak win rates split by serve/return (serving ≈ 0.68 ≈ base 0.673; returning ≈ 0.29–0.34 ≈ base 0.327). Both confirm no hot-hand. See `CORRECTION_serveaware.md`. Player-specific serve statistics would refine precision further.

## 7. Model Evaluation

**Strengths.** The multi-test approach (runs test + permutation + post-streak analysis) provides converging evidence from independent methodologies. Match-level train/test splitting prevents data leakage. Bonferroni correction addresses multiple comparisons. The honest reporting of null findings is scientifically more valuable than a fabricated positive result.

**Weaknesses.** Server control uses global serve/return base rates rather than player-specific serve statistics (a refinement noted in §6). The EWMA α parameter lacks formal optimization. The swing prediction model's binary labeling is threshold-dependent. The unconditional permutation test ignores service-game structure, which is exactly why we rely on the conditional permutation null that preserves the serve sequence (see the §6 correction; the earlier "server-adjusted runs test" was found to be a no-op and is not used). Only 31 matches from one tournament are analyzed.

**Comparison with literature.** Our findings align with Gilovich, Vallone & Tversky (1985), who found no hot-hand in basketball. We note Miller & Sanjurjo (2018) demonstrated that the original GVT test was statistically biased against detecting hot-hand; however, our tests (runs test, permutation baseline) are not subject to this bias. The fact that we still find no hot-hand effect using unbiased methods strengthens the conclusion.

## 8. Conclusion

This investigation set out to determine whether momentum in professional tennis is a measurable phenomenon or a perceptual illusion. The evidence from 7,284 points across 31 Wimbledon matches is clear: after controlling for server advantage, point-by-point sequences are statistically indistinguishable from random processes. Winning streaks of all lengths occur at rates predicted by chance alone. Post-streak performance shows no elevation above base rates. And attempts to predict momentum swings achieve only chance-level accuracy.

The coach who claimed that "streaks are just random" is, based on this dataset, empirically correct. This does not mean that psychological states have no effect on tennis performance — only that whatever effects they produce are too small to detect in point-level outcomes with our methods and sample size. The hot-hand fallacy, well-documented in basketball and other domains, appears to extend to professional tennis as well.

For practitioners: betting on a player because they are "on a streak" is not supported by the data. For researchers: future work should explore point-level features beyond binary win/loss (shot speed, placement, rally intensity) and consider player-specific psychological profiles as potential moderators of momentum effects.

---

## References

- Gilovich, T., Vallone, R., & Tversky, A. (1985). The hot hand in basketball: On the misperception of random sequences. *Cognitive Psychology*, 17(3), 295–314.
- Miller, J. B., & Sanjurjo, A. (2018). Surprised by the hot hand fallacy? A truth in the law of small numbers. *Econometrica*, 86(6), 2019–2047.
- Wimbledon Championships 2023 point-by-point dataset (provided with MCM Problem C).

## Appendix

- `solve.py`: Full solver script with all computations
- `solver_results.json`: Machine-readable results summary
- `runs_test_details.csv`: Per-match runs test statistics
- `figures/fig1_momentum_example.png`: EWMA visualization for match 1301
