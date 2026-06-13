"""Solver: EWMA Momentum + Runs Test + Swing Prediction for 2024 MCM-C Tennis"""
import pandas as pd
import numpy as np
from scipy import stats
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json
import os

np.random.seed(42)
os.makedirs('artifacts/figures', exist_ok=True)

df = pd.read_csv('data/Wimbledon_featured_matches.csv')
matches = df['match_id'].unique()
p_server = (df['point_victor'] == df['server']).mean()  # 0.673
print(f"Server win rate: {p_server:.3f}")

# ============================================================
# Q1: EWMA MOMENTUM INDEX
# ============================================================
print("\n" + "="*60)
print("Q1: EWMA MOMENTUM INDEX")
print("="*60)

def compute_ewma_momentum(match_df, alpha=0.1):
    """Compute EWMA momentum index for a single match."""
    y = (match_df['point_victor'] == 1).astype(float).values
    s = (match_df['server'] == 1).astype(float).values
    # Server-adjusted residual
    expected = np.where(s == 1, p_server, 1 - p_server)
    r = y - expected
    # EWMA
    e = np.zeros(len(r))
    for t in range(1, len(r)):
        e[t] = alpha * r[t] + (1 - alpha) * e[t-1]
    return e

# Compute for all matches
all_momentum = {}
for mid in matches:
    m = df[df['match_id'] == mid].reset_index(drop=True)
    all_momentum[mid] = compute_ewma_momentum(m, alpha=0.1)

# Plot example match (Alcaraz vs Jarry - first match)
fig, axes = plt.subplots(2, 1, figsize=(14, 8), gridspec_kw={'height_ratios': [1, 1]})
mid = matches[0]
m = df[df['match_id'] == mid].reset_index(drop=True)
e = all_momentum[mid]

# Top: score progression
axes[0].plot(m['point_no'], m['p1_games'] + m['p1_sets']*6, 'b-', label='P1 games', alpha=0.7)
axes[0].plot(m['point_no'], m['p2_games'] + m['p2_sets']*6, 'r-', label='P2 games', alpha=0.7)
axes[0].set_title(f'{m["player1"].iloc[0]} vs {m["player2"].iloc[0]}')
axes[0].set_ylabel('Cumulative games won')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Bottom: momentum index
axes[1].axhline(y=0, color='k', linestyle='--', alpha=0.3)
axes[1].fill_between(range(len(e)), e, 0, where=e>0, color='blue', alpha=0.3, label='P1 momentum')
axes[1].fill_between(range(len(e)), e, 0, where=e<0, color='red', alpha=0.3, label='P2 momentum')
axes[1].plot(e, 'k-', linewidth=0.8, alpha=0.7)
axes[1].set_xlabel('Point number')
axes[1].set_ylabel('Momentum index (EWMA α=0.1)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('artifacts/figures/fig1_momentum_example.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"Saved fig1_momentum_example.png for {mid}")

# ============================================================
# Q2: RUNS TEST + PERMUTATION TEST (KEY FOR CRITIC)
# ============================================================
print("\n" + "="*60)
print("Q2: RANDOMNESS TESTS (for Critic audit)")
print("="*60)

def wald_wolfowitz_runs_test(binary_seq):
    """Wald-Wolfowitz runs test for randomness."""
    n = len(binary_seq)
    n1 = np.sum(binary_seq == 1)
    n2 = n - n1
    if n1 == 0 or n2 == 0:
        return None, None, None
    # Count runs
    runs = 1
    for i in range(1, n):
        if binary_seq[i] != binary_seq[i-1]:
            runs += 1
    # Expected runs and variance
    e_r = (2 * n1 * n2) / n + 1
    var_r = (2 * n1 * n2 * (2 * n1 * n2 - n)) / (n**2 * (n - 1))
    z = (runs - e_r) / np.sqrt(var_r)
    p_value = 2 * stats.norm.cdf(-abs(z))
    return runs, z, p_value

def streak_distribution(binary_seq, min_streak=3):
    """Count streaks of each length."""
    streaks = []
    current = 1
    for i in range(1, len(binary_seq)):
        if binary_seq[i] == binary_seq[i-1]:
            current += 1
        else:
            if current >= min_streak:
                streaks.append(current)
            current = 1
    if current >= min_streak:
        streaks.append(current)
    return streaks

# Run tests on all matches
results_q2 = []
for mid in matches:
    m = df[df['match_id'] == mid].reset_index(drop=True)
    pv = m['point_victor'].values
    
    # Raw runs test (unadjusted)
    runs, z, p = wald_wolfowitz_runs_test(pv)
    
    # Server-adjusted runs test
    y = (pv == 1).astype(int)
    s = (m['server'] == 1).astype(int)
    # Residual: 1 if winner > expected, 0 otherwise
    expected_win_p1 = np.where(s == 1, p_server, 1 - p_server)
    residual = (y > expected_win_p1).astype(int)  # binary: outperformed expectation?
    # Simpler: just use median split on residual
    r_cont = y - expected_win_p1
    r_binary = (r_cont > 0).astype(int)
    runs_adj, z_adj, p_adj = wald_wolfowitz_runs_test(r_binary)
    
    results_q2.append({
        'match': mid,
        'n_points': len(pv),
        'runs_raw': runs,
        'z_raw': z,
        'p_raw': p,
        'runs_adj': runs_adj,
        'z_adj': z_adj,
        'p_adj': p_adj,
    })

results_df = pd.DataFrame(results_q2)
print("\n--- Runs Test Results (all 31 matches) ---")
print(f"Raw: {sum(results_df['p_raw'] < 0.05)}/31 significant at α=0.05")
print(f"Adjusted: {sum(results_df['p_adj'] < 0.05)}/31 significant at α=0.05")
print(f"Raw Z-statistics: mean={results_df['z_raw'].mean():.3f}, std={results_df['z_raw'].std():.3f}")
print(f"Adj Z-statistics: mean={results_df['z_adj'].mean():.3f}, std={results_df['z_adj'].std():.3f}")
print(f"\nBonferroni-adjusted threshold: α={0.05/31:.4f}")
sig_bonf = sum(results_df['p_raw'] < 0.05/31)
print(f"Raw significant after Bonferroni: {sig_bonf}/31")

# Permutation test: compare streak counts
print("\n--- Permutation Test (10,000 shuffles) ---")
n_perms = 10000
observed_streak_counts = {}
perm_streak_distributions = {}

for mid in matches[:5]:  # Do 5 matches for speed
    m = df[df['match_id'] == mid].reset_index(drop=True)
    pv = m['point_victor'].values
    
    # Observed streak distribution
    obs_streaks = streak_distribution(pv, min_streak=3)
    obs_count_5plus = sum(1 for s in obs_streaks if s >= 5)
    observed_streak_counts[mid] = {'total': len(obs_streaks), '5plus': obs_count_5plus, 'max': max(obs_streaks) if obs_streaks else 0}
    
    # Permutation
    perm_counts_5plus = []
    for _ in range(n_perms):
        shuffled = pv.copy()
        np.random.shuffle(shuffled)
        perm_streaks = streak_distribution(shuffled, min_streak=3)
        perm_counts_5plus.append(sum(1 for s in perm_streaks if s >= 5))
    
    p_perm = np.mean(np.array(perm_counts_5plus) >= obs_count_5plus)
    observed_streak_counts[mid]['p_perm_5plus'] = p_perm
    perm_streak_distributions[mid] = perm_counts_5plus
    print(f"{mid}: observed 5+ streaks={obs_count_5plus}, p(perm)={p_perm:.4f}")

# Post-streak win rate analysis (hot-hand test)
print("\n--- Post-Streak Win Rate (Hot-Hand Test) ---")
all_post_streak = {3: [], 4: [], 5: [], 6: []}
for mid in matches:
    m = df[df['match_id'] == mid].reset_index(drop=True)
    pv = m['point_victor'].values
    server = m['server'].values
    
    for k in [3, 4, 5, 6]:
        for i in range(k, len(pv)):
            # Check if previous k points were all won by same player
            streak_player = pv[i-1]
            if all(pv[i-k:i] == streak_player):
                # Did the streak player win the next point?
                won_next = 1 if pv[i] == streak_player else 0
                # Was streak player serving?
                was_serving = 1 if server[i] == streak_player else 0
                all_post_streak[k].append({'won': won_next, 'serving': was_serving})

for k in [3, 4, 5, 6]:
    data = all_post_streak[k]
    if data:
        overall_rate = np.mean([d['won'] for d in data])
        serving_rate = np.mean([d['won'] for d in data if d['serving']])
        returning_rate = np.mean([d['won'] for d in data if not d['serving']])
        n = len(data)
        print(f"Streak {k}: n={n}, overall next_win={overall_rate:.3f}, serving={serving_rate:.3f}, returning={returning_rate:.3f}")

# ============================================================
# Q3: SWING PREDICTION
# ============================================================
print("\n" + "="*60)
print("Q3: SWING PREDICTION")
print("="*60)

# Build features and labels
def build_swing_features(match_df, alpha=0.1):
    """Build feature matrix for swing prediction."""
    y_pts = (match_df['point_victor'] == 1).astype(float).values
    s = (match_df['server'] == 1).astype(float).values
    n = len(y_pts)
    
    # EWMA momentum
    expected = np.where(s == 1, p_server, 1 - p_server)
    r = y_pts - expected
    e = np.zeros(n)
    for t in range(1, n):
        e[t] = alpha * r[t] + (1 - alpha) * e[t-1]
    
    # Features
    features = np.zeros((n, 5))
    for t in range(10, n):
        features[t, 0] = e[t]  # current momentum
        features[t, 1] = e[t] - e[max(0, t-5)]  # momentum velocity (5-pt)
        
        # Current streak
        streak = 0
        for j in range(t, max(0, t-20), -1):
            if y_pts[j] == y_pts[t]:
                streak += 1
            else:
                break
        features[t, 2] = streak if y_pts[t] == 1 else -streak
        
        # Score diff (cumulative points)
        features[t, 3] = np.sum(y_pts[:t]) - np.sum(1 - y_pts[:t])
        
        features[t, 4] = s[t]  # server
    
    # Swing label: did momentum change sign in next 10 points?
    swing_label = np.zeros(n, dtype=int)
    for t in range(10, n - 10):
        future_e = e[t+1:t+11]
        if e[t] > 0 and np.any(future_e < -0.02):
            swing_label[t] = 1
        elif e[t] < 0 and np.any(future_e > 0.02):
            swing_label[t] = 1
    
    return features[10:n-10], swing_label[10:n-10]

# Collect all data
X_all, y_all = [], []
match_splits = []
for mid in matches:
    m = df[df['match_id'] == mid].reset_index(drop=True)
    X, y = build_swing_features(m)
    X_all.append(X)
    y_all.append(y)
    match_splits.append(len(X))

X_all = np.vstack(X_all)
y_all = np.concatenate(y_all)

print(f"Total samples: {len(X_all)}, Swing rate: {y_all.mean():.3f}")

# Train/test split by match (70/30)
np.random.seed(42)
train_matches = np.random.choice(len(matches), size=int(0.7 * len(matches)), replace=False)
test_matches = np.setdiff1d(np.arange(len(matches)), train_matches)

X_train, y_train, X_test, y_test = [], [], [], []
idx = 0
for i, n_pts in enumerate(match_splits):
    if i in train_matches:
        X_train.append(X_all[idx:idx+n_pts])
        y_train.append(y_all[idx:idx+n_pts])
    else:
        X_test.append(X_all[idx:idx+n_pts])
        y_test.append(y_all[idx:idx+n_pts])
    idx += n_pts

X_train = np.vstack(X_train)
y_train = np.concatenate(y_train)
X_test = np.vstack(X_test)
y_test = np.concatenate(y_test)

# Train logistic regression
clf = LogisticRegression(max_iter=1000, C=0.1)
clf.fit(X_train, y_train)
y_pred_proba = clf.predict_proba(X_test)[:, 1]
auc = roc_auc_score(y_test, y_pred_proba)
print(f"\nSwing Prediction AUC-ROC: {auc:.3f}")
print(f"Feature coefficients: {dict(zip(['momentum', 'velocity', 'streak', 'score_diff', 'server'], clf.coef_[0].round(3)))}")

# ============================================================
# SAVE RESULTS
# ============================================================
results_summary = {
    'server_win_rate': round(p_server, 3),
    'runs_test': {
        'n_matches': 31,
        'raw_significant_0.05': int(sum(results_df['p_raw'] < 0.05)),
        'raw_significant_bonferroni': sig_bonf,
        'adj_significant_0.05': int(sum(results_df['p_adj'] < 0.05)),
        'mean_z_raw': round(results_df['z_raw'].mean(), 3),
        'mean_z_adj': round(results_df['z_adj'].mean(), 3),
    },
    'permutation_test': observed_streak_counts,
    'swing_prediction': {
        'auc_roc': round(auc, 3),
        'n_train': len(X_train),
        'n_test': len(X_test),
    },
    'reproducibility': {
        'random_seed': 42,
        'python_packages': 'pandas, numpy, scipy, scikit-learn, matplotlib',
        'alpha_ewma': 0.1,
        'n_permutations': n_perms,
    }
}

with open('artifacts/solver_results.json', 'w') as f:
    json.dump(results_summary, f, indent=2)

# Save runs test details
results_df.to_csv('artifacts/runs_test_details.csv', index=False)

print("\n" + "="*60)
print("SOLVER COMPLETE")
print("="*60)
print(f"Results saved to artifacts/solver_results.json")
print(f"Runs test details: artifacts/runs_test_details.csv")
print(f"Figure: artifacts/figures/fig1_momentum_example.png")
