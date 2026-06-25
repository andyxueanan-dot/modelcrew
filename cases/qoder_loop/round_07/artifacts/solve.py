"""
Round 07: Capacitated Facility Location Problem
Methods: Complete enumeration, greedy assignment, sensitivity analysis
"""

import os
import json
import numpy as np
from itertools import combinations
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# DATA
# ============================================================

# Facilities: [F1 Beijing, F2 Shanghai, F3 Guangzhou, F4 Chengdu, F5 Xi'an, F6 Wuhan, F7 Shenyang, F8 Kunming]
facilities = ['F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8']
f_cost = np.array([800, 900, 750, 650, 600, 700, 550, 600])  # 万元
f_cap = np.array([500, 600, 550, 450, 400, 500, 350, 350])    # 吨/日
f_coord = np.array([
    [116.4, 39.9], [121.5, 31.2], [113.3, 23.1], [104.1, 30.6],
    [108.9, 34.3], [114.3, 30.6], [123.4, 41.8], [102.7, 25.0]
])

# Markets: [M1-M12]
markets = ['M1', 'M2', 'M3', 'M4', 'M5', 'M6', 'M7', 'M8', 'M9', 'M10', 'M11', 'M12']
m_demand = np.array([180, 220, 200, 150, 100, 170, 130, 90, 110, 160, 140, 120])  # 吨/日
m_coord = np.array([
    [116.0, 40.0], [121.0, 31.5], [113.0, 23.0], [104.0, 30.5],
    [108.5, 34.5], [114.0, 30.5], [123.5, 42.0], [102.5, 25.0],
    [118.0, 24.5], [120.0, 30.0], [104.5, 30.0], [110.0, 22.0]
])

# Parameters
alpha = 2  # 元/吨·公里
km_per_deg = 111  # km per degree (simplified)
budget = 3000  # 万元
k_min = 3  # minimum facilities

# ============================================================
# DISTANCE MATRIX
# ============================================================

def compute_distance(c1, c2):
    """Euclidean distance * 111 km/deg"""
    return np.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2) * km_per_deg

dist = np.zeros((len(markets), len(facilities)))
for i in range(len(markets)):
    for j in range(len(facilities)):
        dist[i, j] = compute_distance(m_coord[i], f_coord[j])

# Transport cost matrix (元/吨)
transport_cost = alpha * dist

# ============================================================
# GREEDY ASSIGNMENT
# ============================================================

def greedy_assign(open_facilities, dist, m_demand, f_cap):
    """
    Greedy assignment: assign each market to nearest open facility with capacity.
    Returns: assignment array, transport cost, feasible flag
    """
    n_markets = len(m_demand)
    assignment = np.full(n_markets, -1, dtype=int)
    remaining_cap = {j: f_cap[j] for j in open_facilities}
    total_transport = 0
    
    # Sort markets by demand (largest first - harder to place)
    market_order = np.argsort(-m_demand)
    
    for i in market_order:
        # Find nearest open facility with capacity
        candidates = [(dist[i, j], j) for j in open_facilities if remaining_cap[j] >= m_demand[i]]
        if not candidates:
            return None, float('inf'), False  # infeasible
        
        candidates.sort()
        _, j = candidates[0]
        assignment[i] = j
        remaining_cap[j] -= m_demand[i]
        total_transport += transport_cost[i, j] * m_demand[i]
    
    return assignment, total_transport, True

# ============================================================
# STEP 1: COMPLETE ENUMERATION
# ============================================================
print("=" * 60)
print("STEP 1: COMPLETE ENUMERATION (budget=3000)")
print("=" * 60)

feasible_solutions = []

# Enumerate all subsets of size >= k_min
for k in range(k_min, len(facilities) + 1):
    for combo in combinations(range(len(facilities)), k):
        # Check budget
        build_cost = sum(f_cost[j] for j in combo)
        if build_cost > budget:
            continue
        
        # Check total capacity
        total_cap = sum(f_cap[j] for j in combo)
        if total_cap < sum(m_demand):
            continue
        
        # Try greedy assignment
        assignment, transport, feasible = greedy_assign(list(combo), dist, m_demand, f_cap)
        
        if feasible:
            total_cost = build_cost * 10000 + transport  # 万元 -> 元
            feasible_solutions.append({
                'combo': combo,
                'k': k,
                'build_cost': build_cost,
                'transport': transport / 10000,  # 元 -> 万元
                'total_cost': total_cost / 10000,  # 万元
                'assignment': assignment
            })

print(f"\nTotal feasible solutions: {len(feasible_solutions)}")

# Sort by total cost
feasible_solutions.sort(key=lambda x: x['total_cost'])

# Top 5 solutions
print("\nTop 5 solutions:")
print(f"{'Rank':<6} {'Facilities':<20} {'Build':>8} {'Transport':>10} {'Total':>10}")
print("-" * 60)
for i, sol in enumerate(feasible_solutions[:5]):
    facs = ' '.join([facilities[j] for j in sol['combo']])
    print(f"{i+1:<6} {facs:<20} {sol['build_cost']:>8.0f} {sol['transport']:>10.2f} {sol['total_cost']:>10.2f}")

best = feasible_solutions[0]
print(f"\nOptimal solution:")
print(f"  Facilities: {' '.join([facilities[j] for j in best['combo']])}")
print(f"  Build cost: {best['build_cost']:.0f} 万元")
print(f"  Transport cost: {best['transport']:.2f} 万元/日")
print(f"  Total cost: {best['total_cost']:.2f} 万元 (build) + transport")

# Assignment details
print(f"\nMarket assignment:")
for i in range(len(markets)):
    j = best['assignment'][i]
    d = dist[i, j]
    print(f"  {markets[i]} -> {facilities[j]} (dist={d:.0f}km, cost={transport_cost[i,j]*m_demand[i]/10000:.2f}万元/日)")

# ============================================================
# STEP 2: BUDGET SENSITIVITY (2500)
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: BUDGET SENSITIVITY (budget=2500)")
print("=" * 60)

budget2 = 2500
feasible_b2 = [s for s in feasible_solutions if s['build_cost'] <= budget2]

if feasible_b2:
    feasible_b2.sort(key=lambda x: x['total_cost'])
    best_b2 = feasible_b2[0]
    print(f"\nOptimal with budget={budget2}:")
    print(f"  Facilities: {' '.join([facilities[j] for j in best_b2['combo']])}")
    print(f"  Build cost: {best_b2['build_cost']:.0f} 万元")
    print(f"  Transport cost: {best_b2['transport']:.2f} 万元/日")
    print(f"  Total cost: {best_b2['total_cost']:.2f} 万元")
    cost_increase = best_b2['total_cost'] - best['total_cost']
    print(f"  Cost increase: {cost_increase:.2f} 万元 ({cost_increase/best['total_cost']*100:.1f}%)")
else:
    print(f"\nNo feasible solution with budget={budget2}")
    best_b2 = None

# ============================================================
# STEP 3: FACILITY REMOVAL (F1 cannot be built)
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: FACILITY REMOVAL (F1 excluded)")
print("=" * 60)

feasible_no_f1 = [s for s in feasible_solutions if 0 not in s['combo']]

if feasible_no_f1:
    feasible_no_f1.sort(key=lambda x: x['total_cost'])
    best_no_f1 = feasible_no_f1[0]
    print(f"\nOptimal without F1:")
    print(f"  Facilities: {' '.join([facilities[j] for j in best_no_f1['combo']])}")
    print(f"  Build cost: {best_no_f1['build_cost']:.0f} 万元")
    print(f"  Transport cost: {best_no_f1['transport']:.2f} 万元/日")
    print(f"  Total cost: {best_no_f1['total_cost']:.2f} 万元")
    cost_increase = best_no_f1['total_cost'] - best['total_cost']
    print(f"  Cost increase: {cost_increase:.2f} 万元 ({cost_increase/best['total_cost']*100:.1f}%)")
else:
    print(f"\nNo feasible solution without F1")
    best_no_f1 = None

# ============================================================
# STEP 4: PARETO FRONTIER
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: PARETO FRONTIER (cost vs number of facilities)")
print("=" * 60)

pareto = {}
for sol in feasible_solutions:
    k = sol['k']
    if k not in pareto or sol['total_cost'] < pareto[k]['total_cost']:
        pareto[k] = sol

print(f"\n{'k':>3} {'Build':>8} {'Transport':>10} {'Total':>10}")
print("-" * 35)
for k in sorted(pareto.keys()):
    s = pareto[k]
    print(f"{k:>3} {s['build_cost']:>8.0f} {s['transport']:>10.2f} {s['total_cost']:>10.2f}")

# ============================================================
# GENERATE FIGURES
# ============================================================
print("\n" + "=" * 60)
print("GENERATING FIGURES")
print("=" * 60)

# Fig 1: Geographic map with optimal solution
fig, ax = plt.subplots(figsize=(12, 8))

# Plot facilities
for j in range(len(facilities)):
    color = 'red' if j in best['combo'] else 'gray'
    size = 200 if j in best['combo'] else 100
    ax.scatter(f_coord[j, 0], f_coord[j, 1], s=size, c=color, marker='s', 
               label=facilities[j] if j == 0 else '', zorder=5)
    ax.annotate(facilities[j], (f_coord[j, 0], f_coord[j, 1]), 
                textcoords="offset points", xytext=(5, 5), fontsize=9)

# Plot markets
for i in range(len(markets)):
    ax.scatter(m_coord[i, 0], m_coord[i, 1], s=100, c='blue', marker='o', 
               label=markets[i] if i == 0 else '', zorder=5)
    ax.annotate(markets[i], (m_coord[i, 0], m_coord[i, 1]), 
                textcoords="offset points", xytext=(5, -10), fontsize=8)

# Draw assignments
for i in range(len(markets)):
    j = best['assignment'][i]
    ax.plot([m_coord[i, 0], f_coord[j, 0]], [m_coord[i, 1], f_coord[j, 1]], 
            'k-', alpha=0.3, linewidth=1)

ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_title('Optimal Facility Location (red=open, gray=closed)')
ax.legend(loc='upper right')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/fig1_map.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1")

# Fig 2: Cost breakdown by solution
fig, ax = plt.subplots(figsize=(10, 6))

top_n = min(10, len(feasible_solutions))
x = range(top_n)
build = [feasible_solutions[i]['build_cost'] for i in x]
transport = [feasible_solutions[i]['transport'] for i in x]

ax.bar(x, build, label='Build cost', color='steelblue')
ax.bar(x, transport, bottom=build, label='Transport cost', color='coral')

ax.set_xlabel('Solution rank')
ax.set_ylabel('Cost (万元)')
ax.set_title('Top 10 Solutions: Cost Breakdown')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('figures/fig2_cost_breakdown.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2")

# Fig 3: Pareto frontier
fig, ax = plt.subplots(figsize=(10, 6))

k_vals = sorted(pareto.keys())
build_vals = [pareto[k]['build_cost'] for k in k_vals]
transport_vals = [pareto[k]['transport'] for k in k_vals]
total_vals = [pareto[k]['total_cost'] for k in k_vals]

ax.plot(k_vals, total_vals, 'bo-', linewidth=2, markersize=10, label='Total cost')
ax.plot(k_vals, build_vals, 'rs--', linewidth=1.5, markersize=8, label='Build cost')
ax.plot(k_vals, transport_vals, 'g^-', linewidth=1.5, markersize=8, label='Transport cost')

ax.set_xlabel('Number of open facilities')
ax.set_ylabel('Cost (万元)')
ax.set_title('Pareto Frontier: Cost vs Number of Facilities')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/fig3_pareto.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3")

# ============================================================
# SAVE FROZEN NUMBERS
# ============================================================

frozen = {
    "numbers": [
        # Parameters
        {"id": "n_facilities", "label": "Number of candidate facilities", "value": 8, "tol": 0, "source": "input", "path": "params"},
        {"id": "n_markets", "label": "Number of markets", "value": 12, "tol": 0, "source": "input", "path": "params"},
        {"id": "total_demand", "label": "Total demand", "value": int(sum(m_demand)), "tol": 0, "source": "input", "path": "params"},
        {"id": "budget", "label": "Budget", "value": int(budget), "tol": 0, "source": "input", "path": "params"},
        
        # Q1: Optimal solution
        {"id": "opt_k", "label": "Optimal number of facilities", "value": int(best['k']), "tol": 0, "source": "enumeration", "path": "q1"},
        {"id": "opt_build_cost", "label": "Optimal build cost", "value": float(round(best['build_cost'], 2)), "tol": 1, "source": "enumeration", "path": "q1"},
        {"id": "opt_transport", "label": "Optimal transport cost", "value": float(round(best['transport'], 2)), "tol": 0.1, "source": "enumeration", "path": "q1"},
        {"id": "opt_total_cost", "label": "Optimal total cost", "value": float(round(best['total_cost'], 2)), "tol": 0.1, "source": "enumeration", "path": "q1"},
        {"id": "n_feasible", "label": "Number of feasible solutions", "value": int(len(feasible_solutions)), "tol": 0, "source": "enumeration", "path": "q1"},
        
        # Q2: Budget 2500
        {"id": "budget2", "label": "Budget (Q2)", "value": 2500, "tol": 0, "source": "input", "path": "q2"},
    ]
}

if best_b2:
    frozen["numbers"].append({"id": "opt_b2_total", "label": "Optimal cost (budget=2500)", "value": float(round(best_b2['total_cost'], 2)), "tol": 0.1, "source": "enumeration", "path": "q2"})
    frozen["numbers"].append({"id": "cost_increase_b2", "label": "Cost increase (budget=2500)", "value": float(round(best_b2['total_cost'] - best['total_cost'], 2)), "tol": 0.1, "source": "calculated", "path": "q2"})

# Q3: No F1
if best_no_f1:
    frozen["numbers"].append({"id": "opt_no_f1_total", "label": "Optimal cost (no F1)", "value": float(round(best_no_f1['total_cost'], 2)), "tol": 0.1, "source": "enumeration", "path": "q3"})
    frozen["numbers"].append({"id": "cost_increase_no_f1", "label": "Cost increase (no F1)", "value": float(round(best_no_f1['total_cost'] - best['total_cost'], 2)), "tol": 0.1, "source": "calculated", "path": "q3"})

# Add top 5 solutions
for i, sol in enumerate(feasible_solutions[:5]):
    frozen["numbers"].append({
        "id": f"rank{i+1}_total_cost",
        "label": f"Rank {i+1} total cost",
        "value": float(round(sol['total_cost'], 2)),
        "tol": 0.1,
        "source": "enumeration",
        "path": "ranking"
    })

with open('frozen_numbers.json', 'w', encoding='utf-8') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)

print(f"\nSaved frozen_numbers.json ({len(frozen['numbers'])} entries)")

print("\n" + "=" * 60)
print("SOLVER COMPLETE")
print("=" * 60)
