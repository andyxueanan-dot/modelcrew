"""
Solver R1: Farm Crop Planting Optimization
3 plots x 4 crops, enumeration with constraints
Q1: Max net profit, Q2: Water shadow price, Q3: Cotton price sensitivity
"""
import itertools
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import json, os

np.random.seed(42)
os.makedirs('artifacts/figures', exist_ok=True)

# ============================================================
# DATA
# ============================================================
plots = {
    1: {'area': 200, 'soil': 0.85, 'irrig': 'drip'},
    2: {'area': 150, 'soil': 0.70, 'irrig': 'flood'},
    3: {'area': 100, 'soil': 0.60, 'irrig': 'rain'},
}

crops = {
    'wheat':  {'seed': 120, 'water': 300, 'fert': 25, 'yield_kg': 450, 'price': 2.8,  'min_soil': 0.55, 'grain': True},
    'corn':   {'seed': 90,  'water': 250, 'fert': 30, 'yield_kg': 600, 'price': 2.2,  'min_soil': 0.50, 'grain': True},
    'soybean':{'seed': 80,  'water': 180, 'fert': 15, 'yield_kg': 200, 'price': 5.5,  'min_soil': 0.45, 'grain': True},
    'cotton': {'seed': 150, 'water': 350, 'fert': 35, 'yield_kg': 120, 'price': 15.0, 'min_soil': 0.65, 'grain': False},
}

crop_names = list(crops.keys())
plot_ids = list(plots.keys())

WATER_LIMIT = 100000  # m3
FERT_LIMIT = 12000    # kg
GRAIN_MIN = 80000     # kg

# Water adjustment by irrigation type
def water_adj(irrig):
    if irrig == 'drip':  return 1.0
    if irrig == 'flood': return 1.0 / 0.8  # = 1.25
    if irrig == 'rain':  return 0.4
    return 1.0

# Profit per mu (revenue - seed cost)
for c in crop_names:
    d = crops[c]
    d['profit_per_mu'] = d['yield_kg'] * d['price'] - d['seed']
    print(f"{c:8s}: profit/mu = {d['yield_kg']}*{d['price']} - {d['seed']} = {d['profit_per_mu']:.0f} yuan")

# ============================================================
# ENUMERATION
# ============================================================
print("\n" + "="*60)
print("ENUMERATING ALL ASSIGNMENTS")
print("="*60)

def evaluate(assignment, cotton_price_override=None):
    """assignment: dict {plot_id: crop_name}"""
    total_water = 0
    total_fert = 0
    total_grain = 0
    total_profit = 0
    details = {}

    for pid in plot_ids:
        p = plots[pid]
        cn = assignment[pid]
        c = crops[cn].copy()
        if cotton_price_override and cn == 'cotton':
            c['price'] = cotton_price_override
            c['profit_per_mu'] = c['yield_kg'] * c['price'] - c['seed']

        # Soil check
        if p['soil'] < c['min_soil']:
            return None  # infeasible

        wa = water_adj(p['irrig'])
        plot_water = p['area'] * c['water'] * wa
        plot_fert = p['area'] * c['fert']
        plot_yield = p['area'] * c['yield_kg']
        plot_profit = p['area'] * c['profit_per_mu']

        total_water += plot_water
        total_fert += plot_fert
        if c['grain']:
            total_grain += plot_yield
        total_profit += plot_profit

        details[pid] = {
            'crop': cn, 'area': p['area'],
            'water': round(plot_water, 1), 'fert': plot_fert,
            'yield_kg': plot_yield, 'profit': round(plot_profit, 1)
        }

    return {
        'assignment': assignment,
        'details': details,
        'total_water': round(total_water, 1),
        'total_fert': total_fert,
        'total_grain': total_grain,
        'total_profit': round(total_profit, 1),
        'feasible': (total_water <= WATER_LIMIT and total_fert <= FERT_LIMIT and total_grain >= GRAIN_MIN),
    }

# Enumerate all 4^3 = 64 assignments
all_results = []
for combo in itertools.product(crop_names, repeat=3):
    assign = {plot_ids[i]: combo[i] for i in range(3)}
    r = evaluate(assign)
    if r is not None:  # soil-feasible
        all_results.append(r)

soil_feasible = [r for r in all_results]
fully_feasible = [r for r in all_results if r['feasible']]

print(f"Total assignments: {len(list(itertools.product(crop_names, repeat=3)))}")
print(f"Soil-feasible: {len(soil_feasible)}")
print(f"Fully feasible (water+fert+grain): {len(fully_feasible)}")

# ============================================================
# Q1: MAXIMIZE PROFIT
# ============================================================
print("\n" + "="*60)
print("Q1: MAXIMIZE NET PROFIT")
print("="*60)

fully_feasible.sort(key=lambda x: x['total_profit'], reverse=True)

print("\nTop 5 feasible plans:")
for i, r in enumerate(fully_feasible[:5]):
    a = r['assignment']
    print(f"  #{i+1}: Plot1={a[1]}, Plot2={a[2]}, Plot3={a[3]} | "
          f"profit={r['total_profit']:.0f}, water={r['total_water']:.0f}, "
          f"fert={r['total_fert']}, grain={r['total_grain']}")

q1_best = fully_feasible[0]
print(f"\n*** Q1 OPTIMAL:")
for pid in plot_ids:
    d = q1_best['details'][pid]
    print(f"  Plot {pid} ({plots[pid]['area']}mu, {plots[pid]['irrig']}): {d['crop']} | "
          f"water={d['water']}m3, fert={d['fert']}kg, yield={d['yield_kg']}kg, profit={d['profit']}yuan")
print(f"  TOTAL: profit={q1_best['total_profit']:.0f} yuan, "
      f"water={q1_best['total_water']:.0f}/{WATER_LIMIT}m3, "
      f"fert={q1_best['total_fert']}/{FERT_LIMIT}kg, "
      f"grain={q1_best['total_grain']}/{GRAIN_MIN}kg")

# ============================================================
# Q2: WATER SHADOW PRICE
# ============================================================
print("\n" + "="*60)
print("Q2: WATER SHADOW PRICE (profit +10%)")
print("="*60)

target_profit = q1_best['total_profit'] * 1.10
print(f"Current profit: {q1_best['total_profit']:.0f} yuan")
print(f"Target (+10%): {target_profit:.0f} yuan")

# Sweep water limits
water_sweep = []
for extra in range(0, 80001, 1000):
    wl = WATER_LIMIT + extra
    results_wl = []
    for combo in itertools.product(crop_names, repeat=3):
        assign = {plot_ids[i]: combo[i] for i in range(3)}
        r = evaluate(assign)
        if r is not None:
            tw = r['total_water']
            tf = r['total_fert']
            tg = r['total_grain']
            if tw <= wl and tf <= FERT_LIMIT and tg >= GRAIN_MIN:
                results_wl.append(r)
    if results_wl:
        best = max(results_wl, key=lambda x: x['total_profit'])
        water_sweep.append({'extra_water': extra, 'max_profit': best['total_profit'],
                           'assignment': best['assignment']})

# Find minimum extra water for target profit
min_extra = None
for ws in water_sweep:
    if ws['max_profit'] >= target_profit:
        min_extra = ws['extra_water']
        break

if min_extra is not None:
    print(f"*** Q2: Need at least {min_extra} m3 extra water to achieve +10% profit")
    print(f"  At +{min_extra} m3: max profit = {next(w['max_profit'] for w in water_sweep if w['extra_water']==min_extra):.0f}")
else:
    print("*** Q2: Even +80000 m3 extra water cannot achieve +10% profit")
    # Check what's the max possible profit
    max_possible = max(water_sweep, key=lambda x: x['max_profit'])
    print(f"  Max possible with +80000m3: {max_possible['max_profit']:.0f}")
    min_extra = -1  # flag

# ============================================================
# Q3: COTTON PRICE SENSITIVITY
# ============================================================
print("\n" + "="*60)
print("Q3: COTTON PRICE DROP 15->10 yuan/kg")
print("="*60)

q3_results = []
for combo in itertools.product(crop_names, repeat=3):
    assign = {plot_ids[i]: combo[i] for i in range(3)}
    r = evaluate(assign, cotton_price_override=10.0)
    if r is not None and r['feasible']:
        q3_results.append(r)

q3_results.sort(key=lambda x: x['total_profit'], reverse=True)

print("\nTop 3 (cotton=10):")
for i, r in enumerate(q3_results[:3]):
    a = r['assignment']
    print(f"  #{i+1}: Plot1={a[1]}, Plot2={a[2]}, Plot3={a[3]} | profit={r['total_profit']:.0f}")

q3_best = q3_results[0] if q3_results else None
if q3_best:
    q1_assign_str = ','.join(f"P{k}={v}" for k,v in sorted(q1_best['assignment'].items()))
    q3_assign_str = ','.join(f"P{k}={v}" for k,v in sorted(q3_best['assignment'].items()))
    changed = (q1_assign_str != q3_assign_str)
    print(f"\n*** Q3 OPTIMAL: {q3_assign_str} | profit={q3_best['total_profit']:.0f}")
    print(f"  Changed vs Q1? {changed}")
    print(f"  Q1 profit: {q1_best['total_profit']:.0f} -> Q3 profit: {q3_best['total_profit']:.0f} "
          f"(diff: {q3_best['total_profit'] - q1_best['total_profit']:+.0f})")

# ============================================================
# CONSTRAINT TIGHTNESS
# ============================================================
print("\n" + "="*60)
print("CONSTRAINT TIGHTNESS (Q1 optimal)")
print("="*60)
print(f"Water: {q1_best['total_water']:.0f}/{WATER_LIMIT} "
      f"(slack={WATER_LIMIT - q1_best['total_water']:.0f}, "
      f"{'TIGHT' if abs(WATER_LIMIT - q1_best['total_water']) < 1 else 'slack'})")
print(f"Fert:  {q1_best['total_fert']}/{FERT_LIMIT} "
      f"(slack={FERT_LIMIT - q1_best['total_fert']}, "
      f"{'TIGHT' if q1_best['total_fert'] == FERT_LIMIT else 'slack'})")
print(f"Grain: {q1_best['total_grain']}/{GRAIN_MIN} "
      f"(surplus={q1_best['total_grain'] - GRAIN_MIN}, "
      f"{'TIGHT' if q1_best['total_grain'] == GRAIN_MIN else 'slack'})")

# ============================================================
# FIGURES
# ============================================================
print("\n" + "="*60)
print("GENERATING FIGURES")
print("="*60)

# Fig 1: Profit distribution of feasible plans
profits = [r['total_profit'] for r in fully_feasible]
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(profits, bins=15, color='steelblue', edgecolor='black', alpha=0.7)
ax.axvline(q1_best['total_profit'], color='red', linewidth=2, linestyle='--',
          label=f'Optimal: {q1_best["total_profit"]:.0f}')
ax.set_xlabel('Net Profit (yuan)')
ax.set_ylabel('Count of feasible plans')
ax.set_title('Distribution of Net Profit across Feasible Planting Plans')
ax.legend()
plt.tight_layout()
plt.savefig('artifacts/figures/fig1_profit_distribution.png', dpi=150)
plt.close()
print("Saved fig1")

# Fig 2: Water shadow price curve
if water_sweep:
    fig, ax = plt.subplots(figsize=(10, 5))
    extras = [w['extra_water'] for w in water_sweep]
    profs = [w['max_profit'] for w in water_sweep]
    ax.plot(extras, profs, 'b-o', markersize=4, linewidth=1.5)
    if min_extra and min_extra > 0:
        target_p = next(w['max_profit'] for w in water_sweep if w['extra_water']==min_extra)
        ax.axvline(min_extra, color='red', linestyle='--', label=f'Min extra: {min_extra} m3')
        ax.axhline(target_profit, color='green', linestyle=':', label=f'Target: {target_profit:.0f}')
        ax.plot(min_extra, target_p, 'r*', markersize=15)
    ax.set_xlabel('Extra Water Quota (m3)')
    ax.set_ylabel('Max Achievable Profit (yuan)')
    ax.set_title('Q2: Water Shadow Price - Profit vs Extra Water')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('artifacts/figures/fig2_water_shadow_price.png', dpi=150)
    plt.close()
    print("Saved fig2")

# Fig 3: Q1 vs Q3 comparison
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax_idx, (title, best_r, cprice) in enumerate([
    ('Q1: cotton=15 yuan/kg', q1_best, 15.0),
    ('Q3: cotton=10 yuan/kg', q3_best, 10.0),
]):
    ax = axes[ax_idx]
    pids = list(best_r['details'].keys())
    crop_labels = [f"P{p}\n{best_r['details'][p]['crop']}" for p in pids]
    plot_profits = [best_r['details'][p]['profit'] for p in pids]
    colors_map = {'wheat': '#DAA520', 'corn': '#228B22', 'soybean': '#8B4513', 'cotton': '#FFB6C1'}
    bar_colors = [colors_map.get(best_r['details'][p]['crop'], 'gray') for p in pids]
    bars = ax.bar(crop_labels, plot_profits, color=bar_colors, edgecolor='black')
    ax.set_ylabel('Profit (yuan)')
    ax.set_title(f'{title}\nTotal: {best_r["total_profit"]:.0f}')
    for bar, val in zip(bars, plot_profits):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+100, f'{val:.0f}',
               ha='center', fontsize=10)
plt.tight_layout()
plt.savefig('artifacts/figures/fig3_q1_vs_q3.png', dpi=150)
plt.close()
print("Saved fig3")

# ============================================================
# FROZEN NUMBERS (standard schema)
# ============================================================
frozen = {
    "numbers": [
        {"id": "q1_profit", "label": "Q1 optimal net profit (yuan)",
         "value": q1_best['total_profit'], "tol": 0.1,
         "source": "solve.py:Q1 enumeration", "path": "artifacts/solve.py"},
        {"id": "q1_water", "label": "Q1 total water used (m3)",
         "value": q1_best['total_water'], "tol": 0.1,
         "source": "solve.py:Q1 enumeration", "path": "artifacts/solve.py"},
        {"id": "q1_fert", "label": "Q1 total fertilizer (kg)",
         "value": q1_best['total_fert'], "tol": 1,
         "source": "solve.py:Q1 enumeration", "path": "artifacts/solve.py"},
        {"id": "q1_grain", "label": "Q1 total grain output (kg)",
         "value": q1_best['total_grain'], "tol": 1,
         "source": "solve.py:Q1 enumeration", "path": "artifacts/solve.py"},
        {"id": "q1_n_feasible", "label": "Number of fully feasible plans",
         "value": len(fully_feasible), "tol": 0,
         "source": "solve.py:enumeration", "path": "artifacts/solve.py"},
        {"id": "q2_min_extra_water", "label": "Q2 min extra water for +10% profit (m3)",
         "value": min_extra if min_extra else -1, "tol": 1000,
         "source": "solve.py:Q2 water sweep", "path": "artifacts/solve.py"},
        {"id": "q3_profit", "label": "Q3 optimal profit with cotton=10 (yuan)",
         "value": q3_best['total_profit'] if q3_best else 0, "tol": 0.1,
         "source": "solve.py:Q3 cotton price sensitivity", "path": "artifacts/solve.py"},
        {"id": "q3_changed", "label": "Q3 optimal plan changed vs Q1 (1=yes, 0=no)",
         "value": 1 if (q3_best and changed) else 0, "tol": 0,
         "source": "solve.py:Q3 comparison", "path": "artifacts/solve.py"},
    ]
}

# Add per-plot details
for pid in plot_ids:
    d = q1_best['details'][pid]
    frozen["numbers"].append({
        "id": f"q1_plot{pid}_crop", "label": f"Q1 Plot {pid} crop",
        "value": crop_names.index(d['crop']), "tol": 0,
        "source": "solve.py:Q1", "path": "artifacts/solve.py"
    })
    frozen["numbers"].append({
        "id": f"q1_plot{pid}_profit", "label": f"Q1 Plot {pid} profit (yuan)",
        "value": d['profit'], "tol": 0.1,
        "source": "solve.py:Q1", "path": "artifacts/solve.py"
    })

with open('artifacts/frozen_numbers.json', 'w') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)
print(f"\nSaved frozen_numbers.json ({len(frozen['numbers'])} entries)")

print("\n" + "="*60)
print("SOLVER COMPLETE")
print("="*60)
