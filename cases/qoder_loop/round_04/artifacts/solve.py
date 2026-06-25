"""
Round 04: Supply Chain Network Resilience
Methods: Dijkstra shortest path, Centrality analysis, Node failure simulation
"""

import os
import json
import heapq
import numpy as np
from collections import defaultdict, deque
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Change to script directory so relative paths work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# DATA: Supply Chain Network
# ============================================================

nodes = ['S1', 'S2', 'S3', 'M1', 'M2', 'M3', 'M4', 'D1', 'D2', 'D3', 'R1', 'R2']
node_idx = {n: i for i, n in enumerate(nodes)}

# Edges: (from, to, cost, reliability, capacity)
edges = [
    ('S1', 'M1', 8, 0.95, 50),
    ('S1', 'M2', 12, 0.90, 40),
    ('S2', 'M1', 10, 0.92, 45),
    ('S2', 'M3', 7, 0.88, 55),
    ('S3', 'M2', 9, 0.93, 50),
    ('S3', 'M4', 11, 0.85, 35),
    ('M1', 'D1', 6, 0.96, 60),
    ('M1', 'D2', 14, 0.87, 30),
    ('M2', 'D1', 13, 0.89, 35),
    ('M2', 'D2', 8, 0.94, 45),
    ('M3', 'D2', 10, 0.91, 40),
    ('M3', 'D3', 9, 0.93, 50),
    ('M4', 'D3', 7, 0.95, 55),
    ('D1', 'R1', 5, 0.97, 70),
    ('D2', 'R1', 11, 0.90, 40),
    ('D2', 'R2', 8, 0.94, 50),
    ('D3', 'R2', 6, 0.96, 65),
]

# Build adjacency list
adj = defaultdict(list)
for src, dst, cost, rel, cap in edges:
    adj[src].append((dst, cost, rel, cap))

# ============================================================
# STEP 1: DIJKSTRA SHORTEST PATH (S1 -> R1)
# ============================================================
print("=" * 60)
print("STEP 1: DIJKSTRA SHORTEST PATH (S1 -> R1)")
print("=" * 60)

def dijkstra(source, target, adj, nodes):
    """Dijkstra algorithm with path reconstruction"""
    dist = {n: float('inf') for n in nodes}
    prev = {n: None for n in nodes}
    dist[source] = 0
    pq = [(0, source)]
    visited = set()
    
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        if u == target:
            break
        for v, cost, rel, cap in adj[u]:
            if v not in visited and dist[u] + cost < dist[v]:
                dist[v] = dist[u] + cost
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
    
    # Reconstruct path
    path = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    path = path[::-1]
    
    # Calculate path reliability
    reliability = 1.0
    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        for dst, cost, rel, cap in adj[u]:
            if dst == v:
                reliability *= rel
                break
    
    return dist[target], path, reliability

cost_orig, path_orig, rel_orig = dijkstra('S1', 'R1', adj, nodes)

print(f"Shortest path: {' -> '.join(path_orig)}")
print(f"Total cost: {cost_orig}")
print(f"Path reliability: {rel_orig:.4f}")
print()

# ============================================================
# STEP 2: CENTRALITY ANALYSIS
# ============================================================
print("=" * 60)
print("STEP 2: CENTRALITY ANALYSIS")
print("=" * 60)

# 2.1 Degree centrality
degree = defaultdict(int)
in_degree = defaultdict(int)
out_degree = defaultdict(int)

for src, dst, cost, rel, cap in edges:
    out_degree[src] += 1
    in_degree[dst] += 1
    degree[src] += 1
    degree[dst] += 1

print("\nDegree Centrality:")
for n in nodes:
    print(f"  {n}: in={in_degree[n]}, out={out_degree[n]}, total={degree[n]}")

# 2.2 Betweenness centrality (unweighted for simplicity)
def shortest_paths_all_pairs(nodes, adj):
    """BFS to find all shortest paths (unweighted)"""
    paths = {}
    for src in nodes:
        dist = {n: float('inf') for n in nodes}
        prev = defaultdict(list)
        dist[src] = 0
        queue = deque([src])
        while queue:
            u = queue.popleft()
            for v, cost, rel, cap in adj[u]:
                if dist[v] == float('inf'):
                    dist[v] = dist[u] + 1
                    queue.append(v)
                if dist[v] == dist[u] + 1:
                    prev[v].append(u)
        paths[src] = prev
    return paths

def count_paths(src, dst, prev):
    """Count number of shortest paths from src to dst"""
    if src == dst:
        return 1
    if not prev[dst]:
        return 0
    return sum(count_paths(src, p, prev) for p in prev[dst])

def betweenness_centrality(nodes, adj):
    """Calculate betweenness centrality"""
    cb = {n: 0.0 for n in nodes}
    all_prev = shortest_paths_all_pairs(nodes, adj)
    
    for s in nodes:
        for t in nodes:
            if s == t:
                continue
            sigma_st = count_paths(s, t, all_prev[s])
            if sigma_st == 0:
                continue
            # Count paths through each node
            for v in nodes:
                if v == s or v == t:
                    continue
                sigma_sv = count_paths(s, v, all_prev[s])
                sigma_vt = count_paths(v, t, all_prev[v])
                if sigma_sv > 0 and sigma_vt > 0:
                    cb[v] += sigma_sv * sigma_vt / sigma_st
    
    # Normalize
    n = len(nodes)
    norm = (n - 1) * (n - 2)
    for v in cb:
        cb[v] /= norm
    
    return cb

cb = betweenness_centrality(nodes, adj)
print("\nBetweenness Centrality (normalized):")
cb_sorted = sorted(cb.items(), key=lambda x: x[1], reverse=True)
for n, c in cb_sorted:
    print(f"  {n}: {c:.4f}")

# 2.3 Closeness centrality
def closeness_centrality(nodes, adj):
    """Calculate closeness centrality"""
    cc = {}
    for src in nodes:
        dist = {n: float('inf') for n in nodes}
        dist[src] = 0
        queue = deque([src])
        while queue:
            u = queue.popleft()
            for v, cost, rel, cap in adj[u]:
                if dist[v] == float('inf'):
                    dist[v] = dist[u] + 1
                    queue.append(v)
        # Sum of distances
        total_dist = sum(d for d in dist.values() if d != float('inf'))
        reachable = sum(1 for d in dist.values() if d != float('inf'))
        if reachable > 1:
            cc[src] = (reachable - 1) / total_dist
        else:
            cc[src] = 0.0
    return cc

cc = closeness_centrality(nodes, adj)
print("\nCloseness Centrality:")
cc_sorted = sorted(cc.items(), key=lambda x: x[1], reverse=True)
for n, c in cc_sorted:
    print(f"  {n}: {c:.4f}")

# Identify most critical node
print("\n" + "=" * 60)
print("CRITICAL NODE IDENTIFICATION")
print("=" * 60)
critical_scores = {}
for n in nodes:
    # Normalize each metric to 0-1 and sum
    deg_norm = degree[n] / max(degree.values())
    cb_norm = cb[n] / max(cb.values()) if max(cb.values()) > 0 else 0
    cc_norm = cc[n] / max(cc.values()) if max(cc.values()) > 0 else 0
    critical_scores[n] = (deg_norm + cb_norm + cc_norm) / 3

critical_sorted = sorted(critical_scores.items(), key=lambda x: x[1], reverse=True)
print("\nComposite Criticality Score (avg of 3 normalized metrics):")
for n, s in critical_sorted:
    print(f"  {n}: {s:.4f}")

most_critical = critical_sorted[0][0]
print(f"\nMost critical node: {most_critical}")

# ============================================================
# STEP 3: NODE FAILURE SIMULATION (Remove M1)
# ============================================================
print("\n" + "=" * 60)
print(f"STEP 3: NODE FAILURE SIMULATION (Remove {most_critical})")
print("=" * 60)

# Create new adjacency list without M1
nodes_fail = [n for n in nodes if n != most_critical]
adj_fail = defaultdict(list)
for src, dst, cost, rel, cap in edges:
    if src != most_critical and dst != most_critical:
        adj_fail[src].append((dst, cost, rel, cap))

# Re-run Dijkstra
cost_fail, path_fail, rel_fail = dijkstra('S1', 'R1', adj_fail, nodes_fail)

print(f"\nOriginal path: {' -> '.join(path_orig)} (cost={cost_orig}, rel={rel_orig:.4f})")
if cost_fail < float('inf'):
    print(f"New path (without {most_critical}): {' -> '.join(path_fail)} (cost={cost_fail}, rel={rel_fail:.4f})")
    cost_increase = (cost_fail - cost_orig) / cost_orig * 100
    rel_change = (rel_fail - rel_orig) / rel_orig * 100
    print(f"Cost increase: +{cost_increase:.1f}%")
    print(f"Reliability change: {rel_change:+.1f}%")
else:
    print(f"No path from S1 to R1 after removing {most_critical}!")
    cost_increase = float('inf')
    rel_change = -100.0

# Network connectivity after failure
print(f"\nNetwork connectivity after removing {most_critical}:")
reachable_from_s1 = set()
queue = deque(['S1'])
while queue:
    u = queue.popleft()
    if u in reachable_from_s1:
        continue
    reachable_from_s1.add(u)
    for v, cost, rel, cap in adj_fail[u]:
        if v not in reachable_from_s1:
            queue.append(v)

unreachable = set(nodes_fail) - reachable_from_s1
print(f"  Nodes reachable from S1: {len(reachable_from_s1)}/{len(nodes_fail)}")
if unreachable:
    print(f"  Unreachable nodes: {unreachable}")
else:
    print(f"  All nodes still reachable from S1")

# ============================================================
# GENERATE FIGURES
# ============================================================
print("\n" + "=" * 60)
print("GENERATING FIGURES")
print("=" * 60)

# Fig 1: Network topology with centrality heatmap
fig, ax = plt.subplots(figsize=(12, 8))

# Node positions (manual layout for clarity)
pos = {
    'S1': (1, 6), 'S2': (1, 4), 'S3': (1, 2),
    'M1': (4, 7), 'M2': (4, 5), 'M3': (4, 3), 'M4': (4, 1),
    'D1': (7, 6), 'D2': (7, 4), 'D3': (7, 2),
    'R1': (10, 5), 'R2': (10, 3)
}

# Draw edges
for src, dst, cost, rel, cap in edges:
    x = [pos[src][0], pos[dst][0]]
    y = [pos[src][1], pos[dst][1]]
    ax.annotate('', xy=(pos[dst][0], pos[dst][1]), xytext=(pos[src][0], pos[src][1]),
                arrowprops=dict(arrowstyle='->', color='gray', alpha=0.6))

# Draw nodes with centrality heatmap
cb_values = [cb[n] for n in nodes]
cb_min, cb_max = min(cb_values), max(cb_values)
for n in nodes:
    color_val = (cb[n] - cb_min) / (cb_max - cb_min) if cb_max > cb_min else 0
    color = plt.cm.Reds(color_val)
    circle = plt.Circle(pos[n], 0.3, color=color, ec='black', linewidth=2)
    ax.add_patch(circle)
    ax.text(pos[n][0], pos[n][1], n, ha='center', va='center', fontsize=10, fontweight='bold')

ax.set_xlim(0, 11)
ax.set_ylim(0, 8)
ax.set_aspect('equal')
ax.set_title('Supply Chain Network (node color = betweenness centrality)')
ax.axis('off')

# Add colorbar
sm = plt.cm.ScalarMappable(cmap=plt.cm.Reds, norm=plt.Normalize(vmin=cb_min, vmax=cb_max))
sm.set_array([])
cbar = plt.colorbar(sm, ax=ax, label='Betweenness Centrality')

plt.tight_layout()
plt.savefig('figures/fig1_network_topology.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig1")

# Fig 2: Centrality comparison bar chart
fig, axes = plt.subplots(1, 3, figsize=(15, 5))

# Degree
deg_vals = [degree[n] for n in nodes]
axes[0].barh(nodes, deg_vals, color='steelblue')
axes[0].set_xlabel('Degree')
axes[0].set_title('Degree Centrality')
axes[0].axvline(np.mean(deg_vals), color='red', linestyle='--', label=f'Mean={np.mean(deg_vals):.1f}')
axes[0].legend()

# Betweenness
cb_vals = [cb[n] for n in nodes]
axes[1].barh(nodes, cb_vals, color='coral')
axes[1].set_xlabel('Betweenness (normalized)')
axes[1].set_title('Betweenness Centrality')
axes[1].axvline(np.mean(cb_vals), color='red', linestyle='--', label=f'Mean={np.mean(cb_vals):.3f}')
axes[1].legend()

# Closeness
cc_vals = [cc[n] for n in nodes]
axes[2].barh(nodes, cc_vals, color='seagreen')
axes[2].set_xlabel('Closeness')
axes[2].set_title('Closeness Centrality')
axes[2].axvline(np.mean(cc_vals), color='red', linestyle='--', label=f'Mean={np.mean(cc_vals):.3f}')
axes[2].legend()

plt.tight_layout()
plt.savefig('figures/fig2_centrality_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig2")

# Fig 3: Path comparison (original vs failure)
fig, ax = plt.subplots(figsize=(10, 6))

categories = ['Cost', 'Reliability (%)']
original_vals = [cost_orig, rel_orig * 100]
failure_vals = [cost_fail if cost_fail < float('inf') else cost_orig * 2, rel_fail * 100 if cost_fail < float('inf') else 0]

x = np.arange(len(categories))
width = 0.35

bars1 = ax.bar(x - width/2, original_vals, width, label='Original (with M1)', color='steelblue')
bars2 = ax.bar(x + width/2, failure_vals, width, label='Failure (without M1)', color='coral')

ax.set_ylabel('Value')
ax.set_title('Path Comparison: S1 -> R1')
ax.set_xticks(x)
ax.set_xticklabels(categories)
ax.legend()

# Add value labels
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig('figures/fig3_path_comparison.png', dpi=150, bbox_inches='tight')
plt.close()
print("Saved fig3")

# ============================================================
# SAVE FROZEN NUMBERS
# ============================================================

frozen = {
    "numbers": [
        # Network stats
        {"id": "n_nodes", "label": "Number of nodes", "value": 12, "tol": 0, "source": "input", "path": "network"},
        {"id": "n_edges", "label": "Number of edges", "value": 17, "tol": 0, "source": "input", "path": "network"},
        
        # Q1: Shortest path
        {"id": "orig_path_cost", "label": "Original S1->R1 cost", "value": int(cost_orig), "tol": 0, "source": "dijkstra", "path": "q1"},
        {"id": "orig_path_rel", "label": "Original S1->R1 reliability", "value": round(rel_orig, 4), "tol": 0.0001, "source": "dijkstra", "path": "q1"},
        {"id": "orig_path_len", "label": "Original path length (nodes)", "value": len(path_orig), "tol": 0, "source": "dijkstra", "path": "q1"},
    ]
}

# Add path nodes
for i, n in enumerate(path_orig):
    frozen["numbers"].append({
        "id": f"orig_path_node_{i}",
        "label": f"Original path node {i}",
        "value": nodes.index(n),
        "tol": 0,
        "source": "dijkstra",
        "path": "q1.path"
    })

# Q2: Centrality
for n in nodes:
    frozen["numbers"].append({
        "id": f"degree_{n}",
        "label": f"Degree of {n}",
        "value": degree[n],
        "tol": 0,
        "source": "centrality",
        "path": "q2.degree"
    })
    frozen["numbers"].append({
        "id": f"betweenness_{n}",
        "label": f"Betweenness of {n}",
        "value": round(cb[n], 4),
        "tol": 0.0001,
        "source": "centrality",
        "path": "q2.betweenness"
    })
    frozen["numbers"].append({
        "id": f"closeness_{n}",
        "label": f"Closeness of {n}",
        "value": round(cc[n], 4),
        "tol": 0.0001,
        "source": "centrality",
        "path": "q2.closeness"
    })

# Most critical node
frozen["numbers"].append({
    "id": "most_critical_node",
    "label": "Most critical node (index)",
    "value": nodes.index(most_critical),
    "tol": 0,
    "source": "centrality",
    "path": "q2"
})

# Q3: Failure simulation
if cost_fail < float('inf'):
    frozen["numbers"].append({
        "id": "fail_path_cost",
        "label": f"S1->R1 cost without {most_critical}",
        "value": int(cost_fail),
        "tol": 0,
        "source": "failure_sim",
        "path": "q3"
    })
    frozen["numbers"].append({
        "id": "fail_path_rel",
        "label": f"S1->R1 reliability without {most_critical}",
        "value": round(rel_fail, 4),
        "tol": 0.0001,
        "source": "failure_sim",
        "path": "q3"
    })
    frozen["numbers"].append({
        "id": "cost_increase_pct",
        "label": "Cost increase after failure (%)",
        "value": round(cost_increase, 1),
        "tol": 0.1,
        "source": "failure_sim",
        "path": "q3"
    })
else:
    frozen["numbers"].append({
        "id": "fail_path_cost",
        "label": f"S1->R1 cost without {most_critical}",
        "value": -1,
        "tol": 0,
        "source": "failure_sim",
        "path": "q3"
    })

frozen["numbers"].append({
    "id": "reachable_after_fail",
    "label": "Nodes reachable from S1 after failure",
    "value": len(reachable_from_s1),
    "tol": 0,
    "source": "failure_sim",
    "path": "q3"
})

with open('frozen_numbers.json', 'w', encoding='utf-8') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)

print(f"\nSaved frozen_numbers.json ({len(frozen['numbers'])} entries)")

print("\n" + "=" * 60)
print("SOLVER COMPLETE")
print("=" * 60)
