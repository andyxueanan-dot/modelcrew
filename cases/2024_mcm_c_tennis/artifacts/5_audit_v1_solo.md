# Critic Audit Report — 2024 MCM-C Tennis Momentum

**Auditor**: Anti-Hallucination Critic (ModelCrew)
**Scope**: Full audit of 6 conclusions (C1–C6) from Modeler, verified against Solver numerical output
**Verdict system**: ✅ Stands | ⚠️ Questionable | ❌ Falsified
**Mode**: Solo single-critic audit (v1 baseline). A later run re-audits the same conclusions in adversarial-debate mode — see `5_audit_v2_debate.md`. Same verdicts, different process.

---

## Executive Summary

| # | Conclusion | Verdict | Key Reason |
|---|-----------|---------|------------|
| C1 | EWMA momentum tracks match dynamics | ⚠️ Questionable | Visualization is reasonable, but α=0.1 is arbitrary and no ground-truth validation |
| **C2** | **Point sequences deviate significantly from randomness (momentum is real)** | **❌ Falsified** | **5/31 significant at α=0.05 (expected ~1.55); after Bonferroni only 1/31; permutation tests all p ≥ 0.073** |
| C3 | Streaks ≥5 occur more often than i.i.d. null | ❌ Falsified | All 5 permutation test p-values ∈ [0.07, 0.99]; no evidence of excess streaks |
| C4 | Hot-hand effect negligible after server adjustment | ✅ Stands | Post-streak win rates (0.43–0.50) match base rate; serving/returning rates consistent |
| C5 | Swing prediction AUC > 0.65 | ❌ Falsified | Actual AUC = 0.529, barely above chance (0.5) |
| C6 | Generalizes to other sports | ❌ Falsified | Pure speculation; zero cross-tournament or cross-sport evidence |

**Overall**: 1 ✅ / 1 ⚠️ / 4 ❌ — The "momentum is real" narrative is not supported by this dataset. The coach's claim that streaks are random is largely vindicated.

---

## Detailed Audit

### C1: EWMA Momentum Index Tracks Match Dynamics → ⚠️ Questionable

**1. Randomness / Significance**
Not applicable (descriptive, not inferential). No statistical test claimed.

**2. Correlation ≠ Causation**
The EWMA index is a descriptive proxy, not a causal claim. However, the modeler implicitly equates "EWMA swings" with "real momentum shifts" — this is a definitional circularity. The index measures recent performance differential, which is tautologically correlated with score changes.

**3. Overfitting / Leakage**
No overfitting risk (no training involved). No leakage (purely forward-looking EWMA). ✅

**4. Dimensions / Boundaries**
- Units: dimensionless index (residual × decay). Acceptable.
- Boundary: when α → 0, momentum = 0 always; when α → 1, momentum = raw residual. Both degenerate. α=0.1 is reasonable but **not justified by sensitivity analysis**.
- The sweep range "0.05–0.3" was proposed but not executed. ⚠️

**5. Feasibility / Optimality**
Computationally trivial. No feasibility issue.

**6. Sample / Extrapolation**
Applied to all 31 matches. No extrapolation issue within sample.

**7. Assumption Fragility**
- Depends on A1 (momentum ≈ smoothed recent outcomes) and A4 (server adjustment). A1 is a modeling choice, not a fact — psychological momentum may exist but be unmeasurable by EWMA.
- A4 uses a global p_server=0.673 rather than per-player serve statistics. This is a blunt adjustment: a big server like Isner (p ≈ 0.80) and an average server are treated identically.

**Verdict rationale**: The EWMA index is a reasonable first approximation for descriptive visualization, but the lack of sensitivity analysis on α and the crude server adjustment prevent a "Stands" verdict. The claim that it "tracks match dynamics" is only validated by visual inspection of one match, not systematically.

---

### C2: Point Sequences Deviate from Randomness → ❌ Falsified ⭐ KEY (Q2)

This is the central claim of the entire analysis. The Modeler posited that momentum effects would produce statistically detectable non-randomness in point sequences. Three independent tests were conducted.

**1. Randomness / Significance**

**Test A: Wald-Wolfowitz Runs Test (31 matches)**
- At α=0.05 (uncorrected): 5/31 matches significant. Under the null (i.i.d.), we expect 31 × 0.05 = 1.55 false positives. Observing 5 is mildly elevated (one-sided exact binomial P(X≥5; n=31, p=0.05) = 0.0179; the 0.036 figure is the two-sided/doubled value).
- **Bonferroni correction (α = 0.05/31 = 0.0016)**: Only **1/31** significant (match 1408, Z=−3.44, p=0.000584). Under Bonferroni null, we expect ~0.05 false positives, so 1 is within noise.
- **Mean Z = −0.986** (negative = more runs than expected = MORE alternation, not more streaking). If hot-hand existed, Z should be **positive** (fewer runs = longer streaks). The sign of the effect is **opposite** to the hot-hand prediction.
- ⚠️ Correction: the "server-adjusted" runs test was later found to be a no-op (it reproduces the raw sequence), so "raw == adjusted" does NOT show the server confound was controlled. A genuine server-aware conditional permutation (all 31 matches) gives 0/31 significant, min p ≈ 0.16 — the outcome holds. See `CORRECTION_serveaware.md`.

**Test B: Permutation Baseline (10,000 shuffles, 5 matches)**
- p-values for "number of streaks ≥5": 0.991, 0.589, 0.073, 0.212, 0.330
- **All p ≥ 0.073** (none significant at 0.05). The observed streak distributions are consistent with random shuffling. (This 5-match test does not control for serving; the genuine server-aware test — all 31 matches, 0/31 significant — is in `CORRECTION_serveaware.md`.)
- Match 1303 (p=0.073) is the closest to significance, but still far from any reasonable threshold, and would not survive multiple comparison correction.

**Test C: Post-Streak Win Rate (Hot-Hand Core Test)**
- After streaks of k=3,4,5,6, the next-point win rate is 0.499, 0.429, 0.427, 0.462.
- **All below 0.50**. If hot-hand existed, these should be ABOVE base rate.
- Controlling for server: serving post-streak win rates (0.69–0.77) match the global server win rate (0.673). Returning rates (0.28–0.35) match the global return win rate (1−0.673 = 0.327).
- **No evidence of elevated post-streak performance**.

**2. Correlation ≠ Causation**
Even if we had detected non-randomness, attributing it to "momentum" rather than other factors (fatigue cycles, tactical adjustments, score-dependent play) would require additional evidence. This is moot since no non-randomness was detected.

**3. Overfitting / Leakage**
No overfitting (non-parametric tests). No leakage (tests are within-match, no cross-match contamination). ✅

**4. Dimensions / Boundaries**
- Runs test: well-defined for binary sequences. ✅
- Permutation test: preserves marginal frequencies, destroys temporal structure. ✅
- One concern: the permutation test shuffles ALL points in a match, which destroys the service game structure (a server serves 4 consecutive points, then switches). This means the null model doesn't preserve service game patterns. However, since the **server-adjusted runs test** (which controls for service structure) also shows no significant effect, this concern does not change the conclusion.

**5. Feasibility / Optimality**
Tests are standard and well-powered for the sample sizes involved (122–337 points per match).

**6. Sample / Extrapolation**
31 matches is a moderate sample. The multiple comparison correction is appropriately applied.

**7. Assumption Fragility**
- A2 (conditional independence) was tested and **not rejected** by the data. This is actually good news for A2 — the assumption holds.
- A6 (permutation preserves marginals) is valid.

**Verdict rationale**: Three independent tests converge on the same conclusion: point sequences in this dataset are **not distinguishable from random** after controlling for server advantage. The single Bonferroni-significant match (1408) is within the expected false positive rate. The mean negative Z-score is particularly damning — if anything, there is slight evidence for MORE alternation than random, the opposite of hot-hand. **C2 is falsified.**

---

### C3: Streaks ≥5 Exceed i.i.d. Null → ❌ Falsified

**1. Randomness / Significance**
Permutation test directly addresses this: observed streak counts vs. shuffled baseline. All 5 tested matches have p ∈ [0.073, 0.991]. No match shows excess streaks at any conventional significance level.

**2–3. Correlation / Overfitting**
Not applicable (descriptive comparison against null model).

**4. Dimensions / Boundaries**
The "min_streak=3" threshold and "5+ streak" metric are reasonable but arbitrary. However, since the test fails at every threshold, this is not a concern.

**5–7. Feasibility / Sample / Assumptions**
Same permutation test concerns as C2. A6 applies and is valid.

**Verdict rationale**: Direct empirical refutation. The observed frequency of long streaks is fully consistent with random chance. **C3 is falsified.**

---

### C4: Hot-Hand Negligible After Server Adjustment → ✅ Stands

**1. Randomness / Significance**
Post-streak win rates across k=3,4,5,6: overall 0.43–0.50, serving 0.69–0.77, returning 0.28–0.35. All within sampling noise of base rates (server: 0.673, returner: 0.327). The sample sizes are large (n=182–2016), so the estimates are precise.

**2. Correlation ≠ Causation**
This is a null finding (no effect detected), so causation is not at issue.

**3. Overfitting / Leakage**
No modeling involved; purely descriptive statistics. ✅

**4. Dimensions / Boundaries**
Win rates are probabilities ∈ [0,1]. Correctly computed. ✅

**5. Feasibility / Optimality**
Straightforward computation. No issue.

**6. Sample / Extrapolation**
Large n (2016 instances for k=3). Sufficient statistical power to detect even small effects. If a hot-hand effect exists, it is smaller than our detection threshold (~2-3 percentage points at k=3).

**7. Assumption Fragility**
Depends on A2 (independence) and A4 (server control). A2 is supported by C2's results. A4 is crudely satisfied (global server rate is a reasonable first-order control).

**Verdict rationale**: The null hypothesis (no hot-hand) is not rejected. Post-streak performance matches base rates across all streak lengths and after controlling for server. This is a well-supported negative finding. **C4 stands.**

---

### C5: Swing Prediction AUC > 0.65 → ❌ Falsified

**1. Randomness / Significance**
AUC = 0.529 on the test set (n=1899). The 95% CI for AUC under the null (random classifier) is approximately [0.49, 0.51]. Our AUC of 0.529 is marginally above chance but **far below the claimed 0.65 threshold**. The swing prediction model is essentially useless.

**2. Correlation ≠ Causation**
The model's momentum coefficient is −0.524 (negative), suggesting that high momentum predicts a swing AGAINST the current leader. This is consistent with mean-reversion (regression to the mean) rather than momentum continuation. However, the overall predictive power is negligible.

**3. Overfitting / Leakage**
- Match-level 70/30 split prevents within-match leakage. ✅
- C=0.1 regularization is appropriate. ✅
- No overfitting detected (train/test performance would need to be compared, but the low AUC suggests the model isn't even overfitting successfully).

**4. Dimensions / Boundaries**
AUC ∈ [0,1]. 0.5 = chance. 0.529 is within the "useless" range for practical prediction.

**5. Feasibility / Optimality**
Logistic regression is a reasonable baseline. However, the Modeler noted alternatives (random forest, gradient boosting) were not tried. Given the near-chance AUC, more complex models would likely also fail (the signal may simply not exist).

**6. Sample / Extrapolation**
n_test = 1899 is adequate for AUC estimation. Match-level split is correct.

**7. Assumption Fragility**
- A5 (swing definition via fixed threshold on momentum change) is a key fragility. The swing label depends on the EWMA index (which itself is ⚠️ Questionable per C1) and an arbitrary threshold (sign change + 0.02). Different definitions might yield different results, but given the fundamental weakness of the signal, this is unlikely to change the conclusion.

**Verdict rationale**: The claimed AUC > 0.65 is not achieved. The actual AUC of 0.529 is barely distinguishable from random guessing. The negative momentum coefficient is interesting (suggests mean-reversion) but does not rescue the predictive claim. **C5 is falsified.**

---

### C6: Generalizes to Other Tournaments/Sports → ❌ Falsified

**1–6. Not auditable**
No cross-tournament or cross-sport data was analyzed. The claim is purely speculative. Even within-tournament generalization is limited to 31 featured matches at a single Grand Slam event.

**7. Assumption Fragility**
A3 (featured matches are representative) is already questionable — featured matches are likely closer/more dramatic than average. A4 (server dominance) may vary across surfaces (clay vs. grass vs. hard court).

**Verdict rationale**: Zero empirical evidence. Any generalization claim would be fabricated. **C6 is falsified** (more precisely: unsubstantiated to the point of being unusable in a paper).

---

## Summary for Writer

### What can be written as findings (✅):
- **C4**: After controlling for server advantage, there is no detectable hot-hand effect in this dataset. Post-streak win rates match base rates. This supports the coach's claim that streaks appear random.

### What must be written with caveats (⚠️):
- **C1**: The EWMA momentum index provides a useful visualization tool, but its parameters are not optimized and its validity as a measure of "true" momentum is unverified.

### What CANNOT be written as findings (❌):
- **C2**: We cannot claim momentum is real. The statistical evidence does not support it.
- **C3**: Long streaks do not exceed random expectation.
- **C5**: Swing prediction is essentially at chance level.
- **C6**: No generalization evidence exists.

### Recommended paper narrative:
The paper should honestly report that the data does **not** support the existence of non-random momentum effects in tennis. The EWMA index is a useful descriptive tool, but statistical tests (runs test, permutation test, post-streak analysis) consistently fail to reject the null hypothesis of random point sequences. This aligns with the Gilovich et al. (1985) hot-hand fallacy literature, though we note Miller & Sanjurjo (2018) showed the original test was biased — our tests are not subject to that bias. The coach's skepticism is empirically justified.

### Rework needed?
**No rework needed.** The models are sound; the conclusions simply need to be honestly reported as largely null findings. The Critic does not recommend a rework round — the Solver output is valid and the negative results are scientifically meaningful.
