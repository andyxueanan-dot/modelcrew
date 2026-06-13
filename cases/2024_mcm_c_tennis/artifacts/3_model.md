# Model Definitions — 2024 MCM Problem C

## Method Selection Rationale

| Sub-Question | Method | Why This Method | Alternatives Considered | Trade-off |
|-------------|--------|----------------|------------------------|-----------|
| Q1 | EWMA momentum index | Interpretable, computationally simple, captures recency decay naturally | Hidden Markov Model (HMM), Kalman filter | HMM captures latent states but is complex and harder to interpret; EWMA is transparent for judges |
| Q2 | Wald-Wolfowitz runs test + permutation test | Classical nonparametric test for randomness; permutation test provides robust baseline | Chi-squared test on streak counts, logistic regression on lag features | Runs test directly addresses "is the sequence random?"; permutation test avoids parametric assumptions |
| Q3 | Logistic regression with engineered features | Interpretable feature importance; good baseline | Random forest, gradient boosting | Tree models may overfit on 31 matches; logistic regression gives clear coefficient interpretation |

## Model for Q1: EWMA Momentum Index

### Variables
| Symbol | Meaning | Type | Domain |
|--------|---------|------|--------|
| y_t | Point outcome at time t (1 if P1 wins, 0 if P2 wins) | State | {0, 1} |
| s_t | Server indicator (1 if P1 serves, 0 if P2 serves) | Parameter | {0, 1} |
| p_server | Base probability of server winning a point | Parameter | ≈ 0.67 |
| e_t | EWMA momentum at time t | State | ℝ |
| α | Smoothing parameter | Parameter | [0.01, 0.5] |

### Equations

**Step 1: Adjust for server advantage**
```
r_t = y_t - E[y_t | s_t] = y_t - (p_server if s_t=1 else (1 - p_server))
```

**Step 2: EWMA smoothing**
```
e_t = α · r_t + (1 - α) · e_{t-1}
```

The momentum index `e_t` is positive when P1 is performing above expectation and negative when P2 is.

### Parameters
| Symbol | Value / Source | Sensitivity |
|--------|---------------|-------------|
| α | 0.1 (baseline; sweep 0.05–0.3) | **high** — controls how quickly past points are forgotten |
| p_server | 0.673 (estimated from data: 4903/7284) | medium — varies by player |

## Model for Q2: Randomness Tests

### Test 1: Wald-Wolfowitz Runs Test
- **Null hypothesis**: The sequence of point winners is i.i.d. (no momentum)
- **Test statistic**: Number of runs R in the binary sequence {y_t}
- **Expected runs under H0**: E[R] = (2n₁n₂)/(n₁+n₂) + 1
- **Variance**: Var[R] = (2n₁n₂)(2n₁n₂ - n₁ - n₂) / ((n₁+n₂)²(n₁+n₂-1))
- **Z-statistic**: Z = (R - E[R]) / √Var[R]
- **Decision**: If |Z| > 1.96, reject H0 at α=0.05 (two-tailed)

### Test 2: Permutation Baseline
- Shuffle point outcomes within each match 10,000 times
- Compute streak distribution for each shuffle
- Compare observed streak counts to shuffled distribution
- p-value = fraction of shuffles with ≥ observed streaks

### Test 3: Post-streak Win Rate
- After a streak of k points by player X, what is X's probability of winning the next point?
- Compare to base rate (controlling for server)
- If hot-hand exists, post-streak win rate > base rate

## Model for Q3: Swing Prediction

### Variables
| Symbol | Meaning | Type | Domain |
|--------|---------|------|--------|
| X_t | Feature vector at time t | Input | ℝ^d |
| y_swing | Binary: did momentum swing in next k points? | Target | {0, 1} |

### Features
1. Current momentum index e_t
2. Momentum velocity (Δe_t over last 5 points)
3. Current streak length and direction
4. Score differential (games, sets)
5. Server indicator
6. Rally count (recent average)
7. Unforced error rate (recent 10 points)

### Model
Logistic regression: P(swing | X_t) = σ(w^T X_t + b)
- Train/test: 70/30 match-level split (21 train, 10 test matches)
- Evaluation: AUC-ROC, precision-recall

## Conclusions Pending Audit

| # | Conclusion | Confidence | Depends On |
|---|-----------|-----------|-----------|
| C1 | The EWMA momentum index successfully tracks match dynamics, with visible swings correlating to game/set changes | High | A1, A4 |
| C2 | Point sequences in tennis matches show statistically significant deviations from randomness (i.e., momentum is real) | **Medium** | A2 — **THIS IS THE KEY CLAIM FOR Q2, MUST BE AUDITED BY CRITIC** |
| C3 | Streaks of length ≥ 5 occur more frequently than expected under i.i.d. null model | Medium | A2, A6 |
| C4 | After adjusting for server advantage, the hot-hand effect is negligible (post-streak win rate ≈ base rate) | Medium | A2, A4 |
| C5 | Momentum swings can be predicted with AUC > 0.65 using engineered features | Low–Medium | A1, A5 |
| C6 | The model generalizes to other tennis tournaments but generalization to other sports is speculative | Low | A3, A4 |
