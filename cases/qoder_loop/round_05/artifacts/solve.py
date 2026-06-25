"""
Round 05: SIR-V Epidemic Model with Vaccination
Methods: ODE integration (scipy.integrate.odeint), sensitivity analysis, phase plane
"""

import os
import json
import numpy as np
from scipy.integrate import odeint
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# PARAMETERS
# ============================================================

N = 1_000_000          # Total population
I0 = 100               # Initial infected
R0_init = 0            # Initial recovered
S0 = N - I0 - R0_init  # Initial susceptible

beta = 0.3             # Transmission rate (per person per day)
gamma = 0.1            # Recovery rate (per person per day)
R0 = beta / gamma      # Basic reproduction number = 3.0

e = 0.85               # Vaccine efficacy (85%)

# Time span
t_max = 365            # 1 year
t = np.linspace(0, t_max, 1000)

# ============================================================
# SIR-V MODEL
# ============================================================

def sir_v(y, t, beta, gamma, N, v, e):
    """SIR-V ODE system"""
    S, I, R = y
    dSdt = -beta * S * I / N - v * e * S / N
    dIdt = beta * S * I / N - gamma * I
    dRdt = gamma * I + v * e * S / N
    return [dSdt, dIdt, dRdt]

# ============================================================
# STEP 1: BASELINE (v=0)
# ============================================================
print("=" * 60)
print("STEP 1: BASELINE (v=0, no vaccination)")
print("=" * 60)

y0 = [S0, I0, R0_init]
sol_base = odeint(sir_v, y0, t, args=(beta, gamma, N, 0, e))
S_base, I_base, R_base = sol_base.T

I_max_base = np.max(I_base)
t_peak_base = t[np.argmax(I_base)]
attack_rate_base = R_base[-1] / N
duration_base = t[np.where(I_base > 1)[0][-1]] if np.any(I_base > 1) else 0

print(f"Peak infected: {int(I_max_base):,}")
print(f"Peak time: {t_peak_base:.1f} days")
print(f"Attack rate: {attack_rate_base:.1%}")
print(f"Duration (I>1): {duration_base:.0f} days")
print()

# ============================================================
# STEP 2: VACCINATION (v=5000)
# ============================================================
print("=" * 60)
print("STEP 2: VACCINATION (v=5000 people/day)")
print("=" * 60)

v = 5000
sol_vac = odeint(sir_v, y0, t, args=(beta, gamma, N, v, e))
S_vac, I_vac, R_vac = sol_vac.T

I_max_vac = np.max(I_vac)
t_peak_vac = t[np.argmax(I_vac)]
attack_rate_vac = R_vac[-1] / N
duration_vac = t[np.where(I_vac > 1)[0][-1]] if np.any(I_vac > 1) else 0

print(f"Peak infected: {int(I_max_vac):,}")
print(f"Peak time: {t_peak_vac:.1f} days")
print(f"Attack rate: {attack_rate_vac:.1%}")
print(f"Duration (I>1): {duration_vac:.0f} days")

peak_reduction = (I_max_base - I_max_vac) / I_max_base * 100
duration_reduction = duration_base - duration_vac

print(f"\nPeak reduction: {peak_reduction:.1f}%")
print(f"Duration reduction: {duration_reduction:.0f} days")
print()

# ============================================================
# STEP 3: HERD IMMUNITY THRESHOLD
# ============================================================
print("=" * 60)
print("STEP 3: HERD IMMUNITY THRESHOLD")
print("=" * 60)

S_critical = N / R0
herd_immunity_pct = (1 - 1/R0) * 100

print(f"Critical susceptible: {int(S_critical):,} ({S_critical/N:.1%} of population)")
print(f"Herd immunity threshold: {herd_immunity_pct:.1f}% immune")
print(f"Need to immunize: {int(N * (1 - 1/R0)):,} people")

# Find minimum vaccination rate for herd immunity in 60 days
def simulate_vaccination(v_test, days=60):
    """Simulate vaccination for given days, return final S"""
    t_short = np.linspace(0, days, 200)
    sol = odeint(sir_v, y0, t_short, args=(beta, gamma, N, v_test, e))
    S_final = sol[-1, 0]
    return S_final

# Binary search for v_min
v_low, v_high = 0, 50000
for _ in range(20):
    v_mid = (v_low + v_high) / 2
    S_final = simulate_vaccination(v_mid, days=60)
    if S_final < S_critical:
        v_high = v_mid
    else:
        v_low = v_mid

v_min = (v_low + v_high) / 2
S_final_vmin = simulate_vaccination(v_min, days=60)

print(f"\nMinimum vaccination rate for herd immunity in 60 days: {int(v_min):,} people/day")
print(f"Final susceptible at v_min: {int(S_final_vmin):,} (threshold: {int(S_critical):,})")
print()

# ============================================================
# STEP 4: SENSITIVITY ANALYSIS
# ============================================================
print("=" * 60)
print("STEP 4: SENSITIVITY ANALYSIS (R0 vs v)")
print("=" * 60)

R0_values = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0]
v_values = [0, 2000, 5000, 10000, 15000, 20000]

I_max_grid = np.zeros((len(R0_values), len(v_values)))
t_peak_grid = np.zeros((len(R0_values), len(v_values)))

for i, R0_test in enumerate(R0_values):
    beta_test = R0_test * gamma
    for j, v_test in enumerate(v_values):
        sol = odeint(sir_v, y0, t, args=(beta_test, gamma, N, v_test, e))
        I_test = sol[:, 1]
        I_max_grid[i, j] = np.max(I_test) / N * 100  # percentage
        t_peak_grid[i, j] = t[np.argmax(I_test)]

print("\nPeak infected (% of population):")
print("R0\\v     ", "   ".join([f"{v:>6}" for v in v_values]))
for i, R0_test in enumerate(R0_values):
    row = f"R0={R0_test:.1f}  "
    for j in range(len(v_values)):
        row += f"{I_max_grid[i, j]:>6.1f}  "
    print(row)

print("\n" + "=" * 60)
print("GENERATING FIGURES")
print("=" * 60)

# Fig 1: SIR curves (baseline vs vaccination)
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Baseline
axes[0].plot(t, S_base/N, 'b-', label='Susceptible (S)', linewidth=2)
axes[0].plot(t, I_base/N, 'r-', label='Infected (I)', linewidth=2)
axes[0].plot(t, R_base/N, 'g-', label='Recovered (R)', linewidth=2)
axes[0].set_xlabel('Time (days)')
axes[0].set_ylabel('Proportion of population')
axes[0].set_title('Baseline (v=0)')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Vaccination
axes[1].plot(t, S_vac/N, 'b-', label='Susceptible (S)', linewidth=2)
axes[1].plot(t, I_vac/N, 'r-', label='Infected (I)', linewidth=2)
axes[1].plot(t, R_vac/N, 'g-', label='Recovered (R)', linewidth=2)
axes[1].set_xlabel('Time (days)')
axes[1].set_ylabel('Proportion of population')
axes[1].set_title(f'Vaccination (v={v:,}/day)')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/fig1_sir_curves.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1")

# Fig 2: Phase plane (S vs I)
fig, ax = plt.subplots(figsize=(10, 8))

ax.plot(S_base/N, I_base/N, 'r-', label='Baseline (v=0)', linewidth=2)
ax.plot(S_vac/N, I_vac/N, 'b-', label=f'Vaccination (v={v:,})', linewidth=2)
ax.axvline(x=1/R0, color='green', linestyle='--', label=f'Herd immunity threshold (S/N={1/R0:.2f})', linewidth=2)

# Mark start and peak
ax.plot(S_base[0]/N, I_base[0]/N, 'ro', markersize=10, label='Start')
ax.plot(S_base[np.argmax(I_base)]/N, I_max_base/N, 'r*', markersize=15, label='Peak (baseline)')
ax.plot(S_vac[np.argmax(I_vac)]/N, I_max_vac/N, 'b*', markersize=15, label='Peak (vaccination)')

ax.set_xlabel('Susceptible (S/N)')
ax.set_ylabel('Infected (I/N)')
ax.set_title('Phase Plane: S vs I')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/fig2_phase_plane.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2")

# Fig 3: Sensitivity heatmap
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Peak infected heatmap
im1 = axes[0].imshow(I_max_grid, cmap='YlOrRd', aspect='auto')
axes[0].set_xticks(range(len(v_values)))
axes[0].set_xticklabels([f'{v:,}' for v in v_values])
axes[0].set_yticks(range(len(R0_values)))
axes[0].set_yticklabels([f'{R0:.1f}' for R0 in R0_values])
axes[0].set_xlabel('Vaccination rate v (people/day)')
axes[0].set_ylabel('Basic reproduction number R0')
axes[0].set_title('Peak infected (% of population)')

# Add text annotations
for i in range(len(R0_values)):
    for j in range(len(v_values)):
        axes[0].text(j, i, f'{I_max_grid[i, j]:.1f}%',
                     ha='center', va='center', color='black', fontsize=9)

plt.colorbar(im1, ax=axes[0], label='Peak infected (%)')

# Peak time heatmap
im2 = axes[1].imshow(t_peak_grid, cmap='viridis', aspect='auto')
axes[1].set_xticks(range(len(v_values)))
axes[1].set_xticklabels([f'{v:,}' for v in v_values])
axes[1].set_yticks(range(len(R0_values)))
axes[1].set_yticklabels([f'{R0:.1f}' for R0 in R0_values])
axes[1].set_xlabel('Vaccination rate v (people/day)')
axes[1].set_ylabel('Basic reproduction number R0')
axes[1].set_title('Peak time (days)')

for i in range(len(R0_values)):
    for j in range(len(v_values)):
        axes[1].text(j, i, f'{t_peak_grid[i, j]:.0f}',
                     ha='center', va='center', color='white', fontsize=9)

plt.colorbar(im2, ax=axes[1], label='Peak time (days)')

plt.tight_layout()
plt.savefig('figures/fig3_sensitivity.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3")

# ============================================================
# SAVE FROZEN NUMBERS
# ============================================================

frozen = {
    "numbers": [
        # Parameters
        {"id": "N", "label": "Total population", "value": int(N), "tol": 0, "source": "input", "path": "params"},
        {"id": "beta", "label": "Transmission rate", "value": beta, "tol": 0, "source": "input", "path": "params"},
        {"id": "gamma", "label": "Recovery rate", "value": gamma, "tol": 0, "source": "input", "path": "params"},
        {"id": "R0", "label": "Basic reproduction number", "value": R0, "tol": 0, "source": "calculated", "path": "params"},
        {"id": "e", "label": "Vaccine efficacy", "value": e, "tol": 0, "source": "input", "path": "params"},
        
        # Q1: Baseline
        {"id": "I_max_base", "label": "Peak infected (baseline)", "value": int(I_max_base), "tol": 100, "source": "odeint", "path": "q1"},
        {"id": "t_peak_base", "label": "Peak time (baseline, days)", "value": round(t_peak_base, 1), "tol": 0.5, "source": "odeint", "path": "q1"},
        {"id": "attack_rate_base", "label": "Attack rate (baseline)", "value": round(attack_rate_base, 4), "tol": 0.001, "source": "odeint", "path": "q1"},
        {"id": "duration_base", "label": "Duration (baseline, days)", "value": int(duration_base), "tol": 5, "source": "odeint", "path": "q1"},
        
        # Q2: Vaccination
        {"id": "v", "label": "Vaccination rate", "value": int(v), "tol": 0, "source": "input", "path": "q2"},
        {"id": "I_max_vac", "label": "Peak infected (vaccination)", "value": int(I_max_vac), "tol": 100, "source": "odeint", "path": "q2"},
        {"id": "t_peak_vac", "label": "Peak time (vaccination, days)", "value": round(t_peak_vac, 1), "tol": 0.5, "source": "odeint", "path": "q2"},
        {"id": "attack_rate_vac", "label": "Attack rate (vaccination)", "value": round(attack_rate_vac, 4), "tol": 0.001, "source": "odeint", "path": "q2"},
        {"id": "duration_vac", "label": "Duration (vaccination, days)", "value": int(duration_vac), "tol": 5, "source": "odeint", "path": "q2"},
        {"id": "peak_reduction_pct", "label": "Peak reduction (%)", "value": round(peak_reduction, 1), "tol": 0.5, "source": "calculated", "path": "q2"},
        {"id": "duration_reduction", "label": "Duration reduction (days)", "value": int(duration_reduction), "tol": 2, "source": "calculated", "path": "q2"},
        
        # Q3: Herd immunity
        {"id": "S_critical", "label": "Critical susceptible", "value": int(S_critical), "tol": 100, "source": "calculated", "path": "q3"},
        {"id": "herd_immunity_pct", "label": "Herd immunity threshold (%)", "value": round(herd_immunity_pct, 1), "tol": 0.1, "source": "calculated", "path": "q3"},
        {"id": "v_min", "label": "Min vaccination rate for herd immunity in 60 days", "value": int(v_min), "tol": 100, "source": "binary_search", "path": "q3"},
    ]
}

# Add sensitivity grid
for i, R0_test in enumerate(R0_values):
    for j, v_test in enumerate(v_values):
        frozen["numbers"].append({
            "id": f"I_max_R0{R0_test}_v{v_test}",
            "label": f"Peak infected % (R0={R0_test}, v={v_test})",
            "value": round(I_max_grid[i, j], 2),
            "tol": 0.1,
            "source": "sensitivity",
            "path": "q4.grid"
        })

with open('frozen_numbers.json', 'w', encoding='utf-8') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)

print(f"\nSaved frozen_numbers.json ({len(frozen['numbers'])} entries)")

print("\n" + "=" * 60)
print("SOLVER COMPLETE")
print("=" * 60)
