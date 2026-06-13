# Problem Analysis — 2024 MCM Problem C

## Sub-Questions

| ID | Restatement | Type | Depends On | Evaluation Hint |
|----|-----------|------|-----------|----------------|
| Q1 | Build a quantitative model to measure which player is performing better at any point in time, and by how much. | Required | — | Continuous index/score; visualization of momentum swings over a match |
| **Q2** | **Evaluate whether "winning streaks" and momentum shifts are real or just random fluctuations. A coach claims streaks are random — test this claim rigorously.** | **Required (KEY)** | Q1 | **Hypothesis test with statistical evidence; runs test; comparison against null model** |
| Q3 | Can we predict momentum swings (turning points) in a match? Which factors contribute most? | Required | Q1, Q2 | Predictive model; feature importance ranking; validation on held-out matches |
| Q4 | Does the momentum model generalize to other matches, other tournaments, or other sports? | Bonus | Q1–Q3 | Discussion + evidence from cross-match validation; limitations clearly stated |

## Key Definitions

| Term | Definition | Source |
|------|-----------|--------|
| **Momentum** | A time-varying latent variable reflecting which player has a recent performance advantage, operationalized as an EWMA of point-level performance indicators (wins, aces, winners, forced errors by opponent). Ranges from -1 (P2 dominant) to +1 (P1 dominant). | Our assumption |
| **Swing** | A rapid reversal in the momentum index — specifically, a sign change in the momentum derivative exceeding a threshold Δ within a window of k consecutive points. | Our assumption |
| **Streak** | A sequence of consecutive points won by the same player. Length ≥ 3 is considered a "notable streak" for analysis. | Problem-original |
| **Hot-hand** | The belief that a player who has just won several consecutive points has an elevated probability of winning the next point (beyond their base rate). | Academic literature |
| **Point winner** | Binary: 1 if player 1 won the point, 2 if player 2 won. The fundamental unit of analysis. | Problem-original |

## Assumptions

| # | Assumption | Why | Fragility |
|---|-----------|-----|-----------|
| A1 | Momentum can be captured by a smoothed function of recent point outcomes | Standard approach in time-series; EWMA is interpretable and computationally simple | If momentum is a truly latent state that depends on unobservable psychological factors, our proxy may miss real dynamics |
| A2 | Point outcomes within a match are conditionally independent given observable features (server, score state, recent performance) | Required for standard statistical tests; simplifies modeling | If there is genuine psychological momentum (hot-hand effect), this assumption is violated — **this is exactly what Q2 tests** |
| A3 | The 31 featured matches are representative of typical Wimbledon play | Dataset is given; we use it as-is | Selection bias: featured matches may be closer/more dramatic than average, inflating apparent momentum swings |
| A4 | Server identity is a dominant factor in point outcomes | Well-established in tennis analytics; our models control for it | If server advantage varies significantly across players (e.g., weak servers), a uniform server effect is inaccurate |
| A5 | "Swing" can be defined by a fixed threshold on momentum change rate | Needed for operationalization | The optimal threshold is arbitrary; different thresholds may yield different conclusions about which factors matter |
| A6 | The shuffled/permutation baseline preserves marginal point probabilities but destroys temporal structure | Standard null model for randomness tests | If point probabilities themselves are non-stationary within a match, the shuffled baseline may not be a fair comparison |

## Traps & Warnings

1. **Hot-hand fallacy controversy**: The academic literature is split. Gilovich, Vallone & Tversky (1985) found no evidence for hot-hand in basketball. Later work (Miller & Sanjurjo 2018) showed the original statistical test was biased. Our Critic must be aware of this debate and use appropriate tests.

2. **Server confound**: Server wins ~65% of points in men's tennis. A "streak" might just be a service game — not momentum. Models MUST control for server.

3. **Non-stationarity**: Player performance changes over a 5-set match (fatigue, tactical adjustment). A momentum model that assumes stationarity will misattribute fatigue effects to momentum.

4. **Multiple comparisons**: Testing 31 matches × multiple hypotheses inflates false positive rate. Must apply correction (e.g., Bonferroni or FDR).

5. **Q4 generalizability**: Only Wimbledon data is provided. Claims about "other sports" are speculative — the paper must acknowledge this explicitly.
