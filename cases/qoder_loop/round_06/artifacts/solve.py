"""
Round 06: Carbon Tax Policy Multi-Objective Analysis
Methods: Scenario analysis, binary search, Pareto frontier
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Change to script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# PARAMETERS
# ============================================================

# Industries: [Power, Manufacturing, Transport, Agriculture]
industries = ['Power', 'Manufacturing', 'Transport', 'Agriculture']

GDP = np.array([1.2, 2.8, 1.0, 0.8])  # trillion yuan
E = np.array([2.5, 1.5, 0.6, 0.4])    # billion tons CO2
Job = np.array([200, 1200, 800, 1800]) # 10,000 people
epsilon = np.array([0.15, 0.08, 0.05, 0.03])  # reduction elasticity

GDP_total = GDP.sum() + 2.2  # +2.2 for services
E_total = E.sum()
Job_total = Job.sum()

alpha = 0.3  # GDP loss coefficient (30% of tax cost)
beta = 500   # green jobs per 100 million yuan

# ============================================================
# MODEL FUNCTIONS
# ============================================================

def emission_reduction(tau, E_i, eps_i):
    """Emission reduction for industry i"""
    return E_i * (1 - np.exp(-eps_i * tau / 100))

def remaining_emission(tau, E_i, eps_i):
    """Remaining emission after reduction"""
    return E_i * np.exp(-eps_i * tau / 100)

def tax_cost(tau, E_i, eps_i):
    """Carbon tax cost (billion yuan). tau in yuan/ton, E_i in billion tons."""
    return tau * remaining_emission(tau, E_i, eps_i)

def gdp_loss(tau, E_i, eps_i):
    """GDP loss (trillion yuan). tax_cost in billion yuan, 1 trillion = 1000 billion."""
    return alpha * tax_cost(tau, E_i, eps_i) / 1000

def job_loss(tau, GDP_i, E_i, Job_i, eps_i):
    """Job loss (10,000 people)"""
    P_i = GDP_i / Job_i  # labor productivity (trillion yuan per 10,000 people)
    return gdp_loss(tau, E_i, eps_i) / P_i

def green_jobs(tau):
    """Green jobs created (10,000 people). Revenue in billion yuan, 1 billion = 10 x 100M."""
    revenue = sum(tax_cost(tau, E[i], epsilon[i]) for i in range(4))  # billion yuan
    return revenue * 10 * beta / 10000  # revenue*10 = 亿元, *beta = jobs, /10000 = 万人

def net_jobs(tau):
    """Net employment effect (10,000 people)"""
    job_losses = sum(job_loss(tau, GDP[i], E[i], Job[i], epsilon[i]) for i in range(4))
    return green_jobs(tau) - job_losses

def total_emission(tau):
    """Total remaining emission (billion tons)"""
    return sum(remaining_emission(tau, E[i], epsilon[i]) for i in range(4))

# ============================================================
# STEP 1: SCENARIO ANALYSIS (tau=200)
# ============================================================
print("=" * 60)
print("STEP 1: SCENARIO ANALYSIS (tau=200 yuan/ton)")
print("=" * 60)

tau = 200
print(f"\nCarbon tax: {tau} yuan/ton CO2\n")

print(f"{'Industry':<15} {'E_red':>10} {'E_rem':>10} {'Cost':>10} {'GDP_loss':>10} {'Job_loss':>10}")
print("-" * 75)

total_red = 0
total_cost = 0
total_gdp_loss = 0
total_job_loss = 0

for i in range(4):
    red = emission_reduction(tau, E[i], epsilon[i])
    rem = remaining_emission(tau, E[i], epsilon[i])
    cost = tax_cost(tau, E[i], epsilon[i])
    gdp_l = gdp_loss(tau, E[i], epsilon[i])
    job_l = job_loss(tau, GDP[i], E[i], Job[i], epsilon[i])
    
    total_red += red
    total_cost += cost
    total_gdp_loss += gdp_l
    total_job_loss += job_l
    
    print(f"{industries[i]:<15} {red:>10.3f} {rem:>10.3f} {cost:>10.2f} {gdp_l:>10.4f} {job_l:>10.2f}")

print("-" * 75)
print(f"{'Total':<15} {total_red:>10.3f} {total_emission(tau):>10.3f} {total_cost:>10.2f} {total_gdp_loss:>10.4f} {total_job_loss:>10.2f}")

red_pct = total_red / E_total * 100
gdp_loss_pct = total_gdp_loss / GDP_total * 100
job_loss_pct = total_job_loss / Job_total * 100

print(f"\nReduction: {total_red:.3f} billion tons ({red_pct:.1f}%)")
print(f"GDP loss: {total_gdp_loss:.4f} trillion yuan ({gdp_loss_pct:.2f}%)")
print(f"Job loss: {total_job_loss:.2f} x 10,000 ({job_loss_pct:.2f}%)")

g_jobs = green_jobs(tau)
n_jobs = net_jobs(tau)
print(f"Green jobs created: {g_jobs:.2f} x 10,000")
print(f"Net employment: {n_jobs:.2f} x 10,000 ({'+' if n_jobs > 0 else ''}{n_jobs/Job_total*100:.2f}%)")

# ============================================================
# STEP 2: EMISSION HALVING TARGET
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: EMISSION HALVING TARGET (5.0 -> 2.5 billion tons)")
print("=" * 60)

# Binary search for tau_min
tau_low, tau_high = 0, 1000
for _ in range(30):
    tau_mid = (tau_low + tau_high) / 2
    if total_emission(tau_mid) <= 2.5:
        tau_high = tau_mid
    else:
        tau_low = tau_mid

tau_half = tau_high
E_half = total_emission(tau_half)
red_half = E_total - E_half
gdp_loss_half = sum(gdp_loss(tau_half, E[i], epsilon[i]) for i in range(4))
job_loss_half = sum(job_loss(tau_half, GDP[i], E[i], Job[i], epsilon[i]) for i in range(4))

print(f"\nMinimum tax for emission halving: {tau_half:.1f} yuan/ton")
print(f"Remaining emission: {E_half:.3f} billion tons")
print(f"Reduction: {red_half:.3f} billion tons ({red_half/E_total*100:.1f}%)")
print(f"GDP loss: {gdp_loss_half:.4f} trillion yuan ({gdp_loss_half/GDP_total*100:.2f}%)")
print(f"Job loss: {job_loss_half:.2f} x 10,000 ({job_loss_half/Job_total*100:.2f}%)")

# ============================================================
# STEP 3: JOB-NEUTRAL CARBON TAX
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: JOB-NEUTRAL CARBON TAX")
print("=" * 60)

# Binary search for tau_jobs where net_jobs(tau) = 0
tau_low, tau_high = 0, 1000
for _ in range(30):
    tau_mid = (tau_low + tau_high) / 2
    if net_jobs(tau_mid) >= 0:
        tau_high = tau_mid
    else:
        tau_low = tau_mid

tau_jobs = tau_high
n_jobs_final = net_jobs(tau_jobs)
E_jobs = total_emission(tau_jobs)
red_jobs = E_total - E_jobs

print(f"\nJob-neutral tax: {tau_jobs:.1f} yuan/ton")
print(f"Net employment: {n_jobs_final:.4f} x 10,000")
print(f"Emission at job-neutral tax: {E_jobs:.3f} billion tons ({red_jobs/E_total*100:.1f}% reduction)")

# ============================================================
# STEP 4: FULL SCENARIO ANALYSIS
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: FULL SCENARIO ANALYSIS (tau = 0-500)")
print("=" * 60)

tau_values = [0, 100, 200, 300, 400, 500]
results = []

print(f"\n{'tau':>6} {'E_red%':>8} {'GDP_loss%':>10} {'Job_loss%':>10} {'Net_job%':>10}")
print("-" * 50)

for tau in tau_values:
    red = sum(emission_reduction(tau, E[i], epsilon[i]) for i in range(4))
    red_pct = red / E_total * 100
    
    gdp_l = sum(gdp_loss(tau, E[i], epsilon[i]) for i in range(4))
    gdp_l_pct = gdp_l / GDP_total * 100
    
    job_l = sum(job_loss(tau, GDP[i], E[i], Job[i], epsilon[i]) for i in range(4))
    job_l_pct = job_l / Job_total * 100
    
    n_j = net_jobs(tau)
    n_j_pct = n_j / Job_total * 100
    
    print(f"{tau:>6} {red_pct:>8.1f} {gdp_l_pct:>10.2f} {job_l_pct:>10.2f} {n_j_pct:>10.2f}")
    
    results.append({
        'tau': tau,
        'red_pct': red_pct,
        'gdp_loss_pct': gdp_l_pct,
        'job_loss_pct': job_l_pct,
        'net_job_pct': n_j_pct
    })

# ============================================================
# GENERATE FIGURES
# ============================================================
print("\n" + "=" * 60)
print("GENERATING FIGURES")
print("=" * 60)

# Fig 1: Pareto frontier (reduction vs GDP loss)
fig, ax = plt.subplots(figsize=(10, 8))

red_pcts = [r['red_pct'] for r in results]
gdp_loss_pcts = [r['gdp_loss_pct'] for r in results]

ax.plot(red_pcts, gdp_loss_pcts, 'bo-', linewidth=2, markersize=10)
for i, r in enumerate(results):
    ax.annotate(f'tau={r["tau"]}', (r['red_pct'], r['gdp_loss_pct']),
                textcoords="offset points", xytext=(10, 10), fontsize=10)

ax.axhline(y=gdp_loss_half/GDP_total*100, color='red', linestyle='--',
           label=f'Emission halving target (GDP loss={gdp_loss_half/GDP_total*100:.2f}%)')
ax.axvline(x=50, color='green', linestyle='--', label='50% reduction target')

ax.set_xlabel('Emission reduction (%)')
ax.set_ylabel('GDP loss (%)')
ax.set_title('Pareto Frontier: Emission Reduction vs GDP Loss')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/fig1_pareto.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1")

# Fig 2: Multi-objective trade-off
fig, ax1 = plt.subplots(figsize=(12, 6))

x = [r['tau'] for r in results]

ax1.plot(x, [r['red_pct'] for r in results], 'g-o', linewidth=2, label='Emission reduction (%)')
ax1.set_xlabel('Carbon tax tau (yuan/ton)')
ax1.set_ylabel('Emission reduction (%)', color='g')
ax1.tick_params(axis='y', labelcolor='g')

ax2 = ax1.twinx()
ax2.plot(x, [r['gdp_loss_pct'] for r in results], 'r-s', linewidth=2, label='GDP loss (%)')
ax2.plot(x, [r['net_job_pct'] for r in results], 'b-^', linewidth=2, label='Net employment (%)')
ax2.set_ylabel('Economic impact (%)', color='r')
ax2.tick_params(axis='y', labelcolor='r')

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title('Multi-Objective Trade-off under Carbon Tax')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('figures/fig2_tradeoff.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2")

# Fig 3: Industry-level burden
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

tau_test = 200
for i, (ax, ind) in enumerate(zip(axes.flat, industries)):
    taus = np.linspace(0, 500, 50)
    reds = [emission_reduction(t, E[i], epsilon[i]) / E[i] * 100 for t in taus]
    gdps = [gdp_loss(t, E[i], epsilon[i]) / GDP[i] * 100 for t in taus]
    
    ax.plot(taus, reds, 'g-', linewidth=2, label='Emission reduction (%)')
    ax.plot(taus, gdps, 'r-', linewidth=2, label='GDP loss (%)')
    ax.set_xlabel('Carbon tax tau (yuan/ton)')
    ax.set_title(f'{ind} (elasticity={epsilon[i]:.2f})')
    ax.legend()
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('figures/fig3_industry_burden.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3")

# ============================================================
# SAVE FROZEN NUMBERS
# ============================================================

frozen = {
    "numbers": [
        # Parameters
        {"id": "E_total", "label": "Total emission", "value": float(E_total), "tol": 0, "source": "input", "path": "params"},
        {"id": "GDP_total", "label": "Total GDP", "value": float(GDP_total), "tol": 0, "source": "input", "path": "params"},
        {"id": "Job_total", "label": "Total employment", "value": int(Job_total), "tol": 0, "source": "input", "path": "params"},
        
        # Q1: tau=200
        {"id": "tau_q1", "label": "Carbon tax (Q1)", "value": 200, "tol": 0, "source": "input", "path": "q1"},
        {"id": "red_pct_q1", "label": "Emission reduction % (tau=200)", "value": round(red_pct, 2), "tol": 0.1, "source": "model", "path": "q1"},
        {"id": "gdp_loss_pct_q1", "label": "GDP loss % (tau=200)", "value": round(gdp_loss_pct, 3), "tol": 0.01, "source": "model", "path": "q1"},
        {"id": "job_loss_pct_q1", "label": "Job loss % (tau=200)", "value": round(job_loss_pct, 3), "tol": 0.01, "source": "model", "path": "q1"},
        {"id": "net_job_pct_q1", "label": "Net employment % (tau=200)", "value": round(n_jobs/Job_total*100, 3), "tol": 0.01, "source": "model", "path": "q1"},
        
        # Q2: Emission halving
        {"id": "tau_half", "label": "Min tax for emission halving", "value": round(tau_half, 1), "tol": 1, "source": "binary_search", "path": "q2"},
        {"id": "gdp_loss_pct_half", "label": "GDP loss % at emission halving", "value": round(gdp_loss_half/GDP_total*100, 3), "tol": 0.01, "source": "model", "path": "q2"},
        {"id": "job_loss_pct_half", "label": "Job loss % at emission halving", "value": round(job_loss_half/Job_total*100, 3), "tol": 0.01, "source": "model", "path": "q2"},
        
        # Q3: Job-neutral
        {"id": "tau_jobs", "label": "Job-neutral carbon tax", "value": round(tau_jobs, 1), "tol": 1, "source": "binary_search", "path": "q3"},
        {"id": "red_pct_jobs", "label": "Emission reduction % at job-neutral tax", "value": round(red_jobs/E_total*100, 2), "tol": 0.1, "source": "model", "path": "q3"},
    ]
}

# Add scenario results
for r in results:
    for key, val in r.items():
        if key != 'tau':
            frozen["numbers"].append({
                "id": f"scenario_tau{r['tau']}_{key}",
                "label": f"{key} at tau={r['tau']}",
                "value": round(val, 4),
                "tol": 0.01,
                "source": "scenario",
                "path": "scenarios"
            })

with open('frozen_numbers.json', 'w', encoding='utf-8') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)

print(f"\nSaved frozen_numbers.json ({len(frozen['numbers'])} entries)")

print("\n" + "=" * 60)
print("SOLVER COMPLETE")
print("=" * 60)
