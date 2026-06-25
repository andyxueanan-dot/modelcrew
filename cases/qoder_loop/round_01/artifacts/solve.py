"""
Solver: R1 - R&D Project Portfolio Optimization (0-1 IP, enumeration)
Q1: Max total profit under budget + staff + dependency constraints
Q2: Min budget for |selected|>=3 and total_profit>=350
Q3: Sensitivity — if C profit 150->280, does optimum change?
"""
import itertools
import json, os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

np.random.seed(42)
os.makedirs('artifacts/figures', exist_ok=True)

# ============================================================
# DATA
# ============================================================
projects = {
    'A': {'cost': 30, 'staff': 8,  'profit': 180, 'risk': 'Low',  'prereq': None},
    'B': {'cost': 55, 'staff': 12, 'profit': 250, 'risk': 'Med',  'prereq': None},
    'C': {'cost': 20, 'staff': 6,  'profit': 150, 'risk': 'Low',  'prereq': None},
    'D': {'cost': 70, 'staff': 15, 'profit': 300, 'risk': 'High', 'prereq': 'B'},
    'E': {'cost': 45, 'staff': 10, 'profit': 220, 'risk': 'Med',  'prereq': None},
    'F': {'cost': 25, 'staff': 7,  'profit': 160, 'risk': 'Low',  'prereq': None},
}
names = list(projects.keys())
BUDGET = 150
STAFF  = 40

def evaluate(combo, profit_override=None):
    """Evaluate a binary combination. Returns dict or None if infeasible."""
    x = {names[i]: combo[i] for i in range(6)}
    # Dependency: x_D <= x_B
    if x['D'] == 1 and x['B'] == 0:
        return None
    total_cost  = sum(projects[n]['cost']  * x[n] for n in names)
    total_staff = sum(projects[n]['staff'] * x[n] for n in names)
    profits = {n: projects[n]['profit'] for n in names}
    if profit_override:
        profits.update(profit_override)
    total_profit = sum(profits[n] * x[n] for n in names)
    n_selected = sum(x[n] for n in names)
    return {
        'combo': combo,
        'x': x,
        'selected': [n for n in names if x[n]==1],
        'n_selected': n_selected,
        'cost': total_cost,
        'staff': total_staff,
        'profit': total_profit,
    }

# ============================================================
# Q1: Maximize profit under budget+staff+dependency
# ============================================================
print("="*60)
print("Q1: MAXIMIZE TOTAL PROFIT")
print("="*60)

all_combos = list(itertools.product([0,1], repeat=6))
feasible = []
for c in all_combos:
    r = evaluate(c)
    if r and r['cost'] <= BUDGET and r['staff'] <= STAFF:
        feasible.append(r)

feasible.sort(key=lambda x: x['profit'], reverse=True)

print(f"Total combinations: {len(all_combos)}")
print(f"Feasible (budget<=150, staff<=40, dependency): {len(feasible)}")
print()

# Top 5
print("Top 5 feasible combinations:")
for i, r in enumerate(feasible[:5]):
    sel = ','.join(r['selected']) if r['selected'] else '(none)'
    print(f"  #{i+1}: [{sel}] cost={r['cost']}, staff={r['staff']}, profit={r['profit']}")

q1_best = feasible[0]
print(f"\n*** Q1 OPTIMAL: {','.join(q1_best['selected'])} | profit={q1_best['profit']} cost={q1_best['cost']} staff={q1_best['staff']}")

# ============================================================
# Q2: Min budget for n_selected>=3 and profit>=350
# ============================================================
print("\n" + "="*60)
print("Q2: MIN BUDGET (|selected|>=3, profit>=350)")
print("="*60)

# Enumerate all combos with dependency, check profit>=350 and n>=3
q2_candidates = []
for c in all_combos:
    r = evaluate(c)
    if r and r['n_selected'] >= 3 and r['profit'] >= 350 and r['staff'] <= STAFF:
        q2_candidates.append(r)

q2_candidates.sort(key=lambda x: x['cost'])

print(f"Feasible combos (n>=3, profit>=350, staff<=40): {len(q2_candidates)}")
if q2_candidates:
    for i, r in enumerate(q2_candidates[:5]):
        sel = ','.join(r['selected'])
        print(f"  #{i+1}: [{sel}] cost={r['cost']}, staff={r['staff']}, profit={r['profit']}")
    q2_best = q2_candidates[0]
    print(f"\n*** Q2 MIN BUDGET: {q2_best['cost']} wan | combo=[{','.join(q2_best['selected'])}] profit={q2_best['profit']} staff={q2_best['staff']}")
else:
    print("No feasible combination found!")
    q2_best = None

# ============================================================
# Q3: Sensitivity — C profit 150 -> 280
# ============================================================
print("\n" + "="*60)
print("Q3: SENSITIVITY — C profit -> 280")
print("="*60)

feasible_q3 = []
for c in all_combos:
    r = evaluate(c, profit_override={'C': 280})
    if r and r['cost'] <= BUDGET and r['staff'] <= STAFF:
        feasible_q3.append(r)

feasible_q3.sort(key=lambda x: x['profit'], reverse=True)

print("Top 5 (with C=280):")
for i, r in enumerate(feasible_q3[:5]):
    sel = ','.join(r['selected'])
    print(f"  #{i+1}: [{sel}] cost={r['cost']}, staff={r['staff']}, profit={r['profit']}")

q3_best = feasible_q3[0]
print(f"\n*** Q3 OPTIMAL: {','.join(q3_best['selected'])} | profit={q3_best['profit']} cost={q3_best['cost']} staff={q3_best['staff']}")

changed = (sorted(q3_best['selected']) != sorted(q1_best['selected']))
print(f"*** Q3 combo changed vs Q1? {changed}")

# ============================================================
# Constraint tightness / shadow analysis
# ============================================================
print("\n" + "="*60)
print("CONSTRAINT ANALYSIS (Q1 optimal)")
print("="*60)
print(f"Budget used: {q1_best['cost']}/{BUDGET} (slack={BUDGET - q1_best['cost']})")
print(f"Staff  used: {q1_best['staff']}/{STAFF} (slack={STAFF - q1_best['staff']})")

# What if budget relaxed by 5?
feasible_relax_b = []
for c in all_combos:
    r = evaluate(c)
    if r and r['cost'] <= (BUDGET+5) and r['staff'] <= STAFF:
        feasible_relax_b.append(r)
feasible_relax_b.sort(key=lambda x: x['profit'], reverse=True)
print(f"If budget +5 (155): best profit = {feasible_relax_b[0]['profit']} (was {q1_best['profit']})")

# What if staff relaxed by 5?
feasible_relax_s = []
for c in all_combos:
    r = evaluate(c)
    if r and r['cost'] <= BUDGET and r['staff'] <= (STAFF+5):
        feasible_relax_s.append(r)
feasible_relax_s.sort(key=lambda x: x['profit'], reverse=True)
print(f"If staff  +5 (45):  best profit = {feasible_relax_s[0]['profit']} (was {q1_best['profit']})")

# ============================================================
# FIGURES
# ============================================================
print("\n" + "="*60)
print("GENERATING FIGURES")
print("="*60)

# Fig 1: Profit distribution of all feasible combinations
profits_all = [r['profit'] for r in feasible]
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(profits_all, bins=20, color='steelblue', edgecolor='black', alpha=0.7)
ax.axvline(q1_best['profit'], color='red', linewidth=2, linestyle='--', label=f'Optimal: {q1_best["profit"]}')
ax.set_xlabel('Total Profit (wan yuan)')
ax.set_ylabel('Count of feasible combinations')
ax.set_title('Distribution of Total Profit across Feasible Portfolios')
ax.legend()
plt.tight_layout()
plt.savefig('artifacts/figures/fig1_profit_distribution.png', dpi=150)
plt.close()
print("Saved fig1_profit_distribution.png")

# Fig 2: Top 5 combinations comparison
fig, ax = plt.subplots(figsize=(10, 5))
top5 = feasible[:5]
labels = [','.join(r['selected']) or '(none)' for r in top5]
profits = [r['profit'] for r in top5]
costs = [r['cost'] for r in top5]
x_pos = np.arange(len(labels))
w = 0.35
bars1 = ax.bar(x_pos - w/2, profits, w, label='Profit', color='forestgreen', edgecolor='black')
bars2 = ax.bar(x_pos + w/2, costs, w, label='Cost', color='coral', edgecolor='black')
ax.set_ylabel('Value (wan yuan)')
ax.set_title('Q1: Top 5 Feasible Portfolios')
ax.set_xticks(x_pos)
ax.set_xticklabels(labels, fontsize=9)
ax.legend()
for bar, val in zip(bars1, profits):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5, str(val), ha='center', fontsize=9)
for bar, val in zip(bars2, costs):
    ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5, str(val), ha='center', fontsize=9)
plt.tight_layout()
plt.savefig('artifacts/figures/fig2_top5_comparison.png', dpi=150)
plt.close()
print("Saved fig2_top5_comparison.png")

# Fig 3: Q1 vs Q3 comparison (sensitivity)
fig, ax = plt.subplots(figsize=(8, 5))
q1_sel = q1_best['selected']
q3_sel = q3_best['selected']
all_proj = names
q1_vals = [projects[p]['profit'] if p in q1_sel else 0 for p in all_proj]
q3_vals = [(280 if p=='C' else projects[p]['profit']) if p in q3_sel else 0 for p in all_proj]
x_pos = np.arange(len(all_proj))
w = 0.35
ax.bar(x_pos - w/2, q1_vals, w, label='Q1 (C=150)', color='steelblue', edgecolor='black')
ax.bar(x_pos + w/2, q3_vals, w, label='Q3 (C=280)', color='gold', edgecolor='black')
ax.set_xticks(x_pos)
ax.set_xticklabels(all_proj)
ax.set_ylabel('Contribution to Profit (wan yuan)')
ax.set_title(f'Q1 vs Q3: Portfolio Composition\nQ1=[{",".join(q1_sel)}] P={q1_best["profit"]} | Q3=[{",".join(q3_sel)}] P={q3_best["profit"]}')
ax.legend()
plt.tight_layout()
plt.savefig('artifacts/figures/fig3_sensitivity_q1_vs_q3.png', dpi=150)
plt.close()
print("Saved fig3_sensitivity_q1_vs_q3.png")

# ============================================================
# SAVE FROZEN NUMBERS
# ============================================================
frozen = {
    'seed': 42,
    'problem': 'R1_portfolio_optimization',
    'data': {n: projects[n] for n in names},
    'constraints': {'budget': BUDGET, 'staff': STAFF, 'dependency': 'D requires B'},
    'enumeration': {
        'total_combinations': len(all_combos),
        'feasible_count': len(feasible),
    },
    'q1': {
        'optimal_combo': q1_best['selected'],
        'total_profit': q1_best['profit'],
        'total_cost': q1_best['cost'],
        'total_staff': q1_best['staff'],
        'budget_slack': BUDGET - q1_best['cost'],
        'staff_slack': STAFF - q1_best['staff'],
    },
    'q1_top5': [{'combo': r['selected'], 'profit': r['profit'], 'cost': r['cost'], 'staff': r['staff']} for r in feasible[:5]],
    'q2': {
        'min_budget': q2_best['cost'] if q2_best else None,
        'combo': q2_best['selected'] if q2_best else None,
        'profit': q2_best['profit'] if q2_best else None,
        'staff': q2_best['staff'] if q2_best else None,
        'n_feasible': len(q2_candidates),
    },
    'q3': {
        'optimal_combo': q3_best['selected'],
        'total_profit': q3_best['profit'],
        'total_cost': q3_best['cost'],
        'total_staff': q3_best['staff'],
        'combo_changed': changed,
    },
    'constraint_analysis': {
        'budget_relax_5_profit': feasible_relax_b[0]['profit'],
        'staff_relax_5_profit': feasible_relax_s[0]['profit'],
    },
}

with open('artifacts/frozen_numbers.json', 'w') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)
print(f"\nSaved frozen_numbers.json")

print("\n" + "="*60)
print("SOLVER COMPLETE")
print("="*60)
