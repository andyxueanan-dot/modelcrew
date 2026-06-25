import numpy as np
from collections import defaultdict, deque
import heapq
import os, json, copy
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# DATA: City Emergency Evacuation Network
# ============================================================
nodes = ['S1','S2','S3','M1','M2','M3','M4','T1','T2','T3']
node_idx = {n: i for i, n in enumerate(nodes)}
n_nodes = len(nodes)

# Edges: (from, to, time, capacity)
edges_raw = [
    ('S1','M1', 5, 200),
    ('S1','M2', 8, 350),
    ('S2','M1', 6, 250),
    ('S2','M3', 4, 180),
    ('S3','M3', 7, 300),
    ('S3','M4', 5, 220),
    ('M1','M2', 3, 150),
    ('M2','M4', 6, 280),
    ('M1','T1', 10, 400),
    ('M2','T1', 7, 180),
    ('M2','T2', 9, 320),
    ('M3','T2', 8, 250),
    ('M3','T3', 5, 200),
    ('M4','T2', 6, 350),
    ('M4','T3', 4, 150),
    ('S1','M3', 12, 100),
    ('M1','M4', 11, 120),
    ('S2','M2', 9, 200),
    ('M3','M2', 7, 160),
    ('M3','M4', 8, 180),
]

print("=" * 60)
print("ROUND 10: CITY EMERGENCY EVACUATION NETWORK")
print("=" * 60)

# Build adjacency structures
def build_graph(edges, nodes_list):
    """Build adjacency list with time and capacity."""
    adj = defaultdict(list)  # adj[u] = [(v, time, cap)]
    adj_time = defaultdict(list)  # for Dijkstra
    node_set = set(nodes_list)
    for u, v, t, c in edges:
        if u in node_set and v in node_set:
            adj[u].append((v, t, c))
            adj_time[u].append((v, t))
    return adj, adj_time

adj_full, adj_time_full = build_graph(edges_raw, nodes)

# ============================================================
# STEP 1: DIJKSTRA SHORTEST PATH
# ============================================================
print("\n" + "=" * 60)
print("STEP 1: DIJKSTRA SHORTEST PATHS")
print("=" * 60)

def dijkstra(adj_time, source, nodes_list):
    """Dijkstra from source, returns (dist, prev) dicts."""
    dist = {n: float('inf') for n in nodes_list}
    prev = {n: None for n in nodes_list}
    dist[source] = 0
    pq = [(0, source)]
    visited = set()
    
    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        for v, w in adj_time.get(u, []):
            if v not in visited and d + w < dist[v]:
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(pq, (dist[v], v))
    
    return dist, prev

def get_path(prev, target):
    """Reconstruct path from prev dict."""
    path = []
    node = target
    while node is not None:
        path.append(node)
        node = prev[node]
    return path[::-1]

# Shortest paths from each source to each target
sources = ['S1', 'S2', 'S3']
targets = ['T1', 'T2', 'T3']

print("\nShortest paths (time in minutes):")
all_shortest = {}
for s in sources:
    dist, prev = dijkstra(adj_time_full, s, nodes)
    for t in targets:
        path = get_path(prev, t)
        time_total = dist[t]
        all_shortest[(s,t)] = (path, time_total)
        print(f"  {s}->{t}: {' -> '.join(path)}, time={time_total}min")

# ============================================================
# STEP 2: YEN'S K-SHORTEST PATHS (K=3)
# ============================================================
print("\n" + "=" * 60)
print("STEP 2: YEN'S K-SHORTEST PATHS (S1->T1, K=3)")
print("=" * 60)

# Build edge lookup for time and capacity
edge_time = {}
edge_cap = {}
for u, v, t, c in edges_raw:
    edge_time[(u,v)] = t
    edge_cap[(u,v)] = c

def path_cost(path):
    """Calculate total time cost of a path."""
    return sum(edge_time.get((path[j], path[j+1]), 9999) for j in range(len(path)-1))

def path_min_cap(path):
    """Calculate minimum capacity along a path."""
    caps = [edge_cap.get((path[j], path[j+1]), 0) for j in range(len(path)-1)]
    return min(caps) if caps else 0

def yen_k_shortest(adj_time, source, target, nodes_list, K=3):
    """Yen's algorithm for K shortest loopless paths."""
    dist, prev = dijkstra(adj_time, source, nodes_list)
    if dist[target] == float('inf'):
        return [], []
    
    A = [get_path(prev, target)]
    A_costs = [path_cost(A[0])]
    B = []  # candidate paths with costs
    B_costs = []
    
    for k in range(1, K):
        prev_path = A[k-1]
        for i in range(len(prev_path) - 1):
            spur_node = prev_path[i]
            root_path = prev_path[:i+1]
            
            # Build modified adjacency: remove edges sharing root path prefix
            adj_mod = defaultdict(list)
            removed_edges = set()
            for p in A:
                if len(p) > i and p[:i+1] == root_path:
                    removed_edges.add((p[i], p[i+1]))
            
            for u in adj_time:
                for v, w in adj_time[u]:
                    if (u, v) not in removed_edges:
                        adj_mod[u].append((v, w))
            
            # Remove root path nodes except spur node
            root_nodes = set(root_path[:-1])
            adj_filt = defaultdict(list)
            for u in adj_mod:
                if u in root_nodes:
                    continue
                for v, w in adj_mod[u]:
                    if v not in root_nodes:
                        adj_filt[u].append((v, w))
            
            dist_spur, prev_spur = dijkstra(adj_filt, spur_node, nodes_list)
            
            if dist_spur[target] < float('inf'):
                spur_path = get_path(prev_spur, target)
                total_path = root_path[:-1] + spur_path
                total_cost = path_cost(total_path)
                
                # Check not duplicate
                is_dup = False
                for bp, bc in zip(B, B_costs):
                    if bp == total_path:
                        is_dup = True
                        break
                if not is_dup and total_path not in A:
                    B.append(total_path)
                    B_costs.append(total_cost)
        
        if not B:
            break
        
        # Pick lowest cost candidate
        best_idx = min(range(len(B_costs)), key=lambda x: B_costs[x])
        A.append(B.pop(best_idx))
        A_costs.append(B_costs.pop(best_idx))
    
    return A, A_costs

paths_s1t1, costs_s1t1 = yen_k_shortest(adj_time_full, 'S1', 'T1', nodes, K=3)
print(f"\nK=3 shortest paths from S1 to T1:")
for i, (path, cost) in enumerate(zip(paths_s1t1, costs_s1t1)):
    mc = path_min_cap(path)
    print(f"  Path {i+1}: {' -> '.join(path)}, time={cost}min, min_capacity={mc}")

# ============================================================
# STEP 3: MAX FLOW (Edmonds-Karp)
# ============================================================
print("\n" + "=" * 60)
print("STEP 3: MAX FLOW (S1->T1, Edmonds-Karp)")
print("=" * 60)

def build_capacity_matrix(edges, nodes_list):
    """Build capacity matrix for max flow."""
    n = len(nodes_list)
    idx = {nd: i for i, nd in enumerate(nodes_list)}
    cap = np.zeros((n, n), dtype=int)
    for u, v, t, c in edges:
        if u in idx and v in idx:
            cap[idx[u]][idx[v]] += c
    return cap, idx

def edmonds_karp(cap_matrix, source_idx, sink_idx):
    """Edmonds-Karp max flow algorithm."""
    n = cap_matrix.shape[0]
    residual = cap_matrix.copy()
    max_flow = 0
    
    while True:
        # BFS to find augmenting path
        parent = [-1] * n
        parent[source_idx] = source_idx
        queue = deque([source_idx])
        
        while queue and parent[sink_idx] == -1:
            u = queue.popleft()
            for v in range(n):
                if parent[v] == -1 and residual[u][v] > 0:
                    parent[v] = u
                    queue.append(v)
        
        if parent[sink_idx] == -1:
            break
        
        # Find bottleneck
        path_flow = float('inf')
        v = sink_idx
        while v != source_idx:
            u = parent[v]
            path_flow = min(path_flow, residual[u][v])
            v = u
        
        # Update residual
        v = sink_idx
        while v != source_idx:
            u = parent[v]
            residual[u][v] -= path_flow
            residual[v][u] += path_flow
            v = u
        
        max_flow += path_flow
    
    return max_flow, residual

# Max flow from S1 to T1
cap_matrix, node_idx_map = build_capacity_matrix(edges_raw, nodes)
s1_idx = node_idx_map['S1']
t1_idx = node_idx_map['T1']
max_flow_s1t1, residual = edmonds_karp(cap_matrix, s1_idx, t1_idx)

print(f"\nMax flow S1->T1: {max_flow_s1t1} people/hour")

# Find min cut (bottleneck edges)
print("\nMin-cut edges (bottleneck):")
# BFS on residual from source
visited = set()
queue = deque([s1_idx])
visited.add(s1_idx)
while queue:
    u = queue.popleft()
    for v in range(n_nodes):
        if v not in visited and residual[u][v] > 0:
            visited.add(v)
            queue.append(v)

for u in visited:
    for v in range(n_nodes):
        if v not in visited and cap_matrix[u][v] > 0:
            print(f"  {nodes[u]} -> {nodes[v]}: capacity={cap_matrix[u][v]}, flow used={cap_matrix[u][v] - residual[u][v]}")

# Max flow from all sources to all targets (super source/sink)
print("\n\nMax flow (all S -> all T, super source/sink):")
# Add super source (SS) connected to S1, S2, S3 with infinite capacity
# Add super sink (TT) connected from T1, T2, T3 with infinite capacity
n_ext = n_nodes + 2
ss_idx = n_nodes  # super source
tt_idx = n_nodes + 1  # super sink
cap_ext = np.zeros((n_ext, n_ext), dtype=int)
cap_ext[:n_nodes, :n_nodes] = cap_matrix
for s in ['S1', 'S2', 'S3']:
    cap_ext[ss_idx][node_idx_map[s]] = 10000  # "infinite"
for t in ['T1', 'T2', 'T3']:
    cap_ext[node_idx_map[t]][tt_idx] = 10000

max_flow_all, _ = edmonds_karp(cap_ext, ss_idx, tt_idx)
print(f"  Max flow (all sources -> all sinks): {max_flow_all} people/hour")

# ============================================================
# STEP 4: VERTEX & EDGE CONNECTIVITY
# ============================================================
print("\n" + "=" * 60)
print("STEP 4: VERTEX & EDGE CONNECTIVITY")
print("=" * 60)

# Build undirected adjacency for connectivity analysis
def build_undirected(edges, nodes_list):
    adj = defaultdict(set)
    node_set = set(nodes_list)
    for u, v, t, c in edges:
        if u in node_set and v in node_set:
            adj[u].add(v)
            adj[v].add(u)
    return adj

adj_undirected = build_undirected(edges_raw, nodes)

def bfs_reachable(adj, source, nodes_list, exclude=None):
    """BFS to find reachable nodes."""
    if exclude is None:
        exclude = set()
    visited = set()
    queue = deque([source])
    visited.add(source)
    while queue:
        u = queue.popleft()
        for v in adj.get(u, []):
            if v not in visited and v not in exclude:
                visited.add(v)
                queue.append(v)
    return visited

# Check if graph is connected
reachable_all = bfs_reachable(adj_undirected, 'S1', nodes)
is_connected = len(reachable_all) == n_nodes
print(f"\nGraph connected: {is_connected} (reachable from S1: {len(reachable_all)}/{n_nodes})")

# Vertex connectivity (approximate: try removing subsets)
# For small graphs, use the minimum vertex cut between all pairs
def vertex_connectivity(adj, nodes_list, sources, targets):
    """Compute vertex connectivity between sources and targets."""
    min_cut = float('inf')
    for s in sources:
        for t in targets:
            # Try removing 1, 2, 3... nodes
            for k in range(1, len(nodes_list)):
                found_cut = False
                # Try all combinations of k nodes (excluding s and t)
                from itertools import combinations
                candidates = [n for n in nodes_list if n != s and n != t]
                for combo in combinations(candidates, k):
                    exclude = set(combo)
                    reachable = bfs_reachable(adj, s, nodes_list, exclude)
                    if t not in reachable:
                        found_cut = True
                        break
                if found_cut:
                    min_cut = min(min_cut, k)
                    break
    return min_cut

# Compute vertex connectivity for S->T pairs
kappa = vertex_connectivity(adj_undirected, nodes, sources, targets)
print(f"\nVertex connectivity kappa(S->T): {kappa}")

# Find articulation points (cut vertices)
def find_articulation_points(adj, nodes_list):
    """Find articulation points using Tarjan's algorithm."""
    visited = set()
    disc = {}
    low = {}
    parent = {}
    ap = set()
    timer = [0]
    
    def dfs(u):
        children = 0
        visited.add(u)
        disc[u] = low[u] = timer[0]
        timer[0] += 1
        
        for v in adj.get(u, []):
            if v not in visited:
                children += 1
                parent[v] = u
                dfs(v)
                low[u] = min(low[u], low[v])
                
                if parent.get(u) is None and children > 1:
                    ap.add(u)
                if parent.get(u) is not None and low[v] >= disc[u]:
                    ap.add(u)
            elif v != parent.get(u):
                low[u] = min(low[u], disc[v])
    
    for n in nodes_list:
        if n not in visited:
            parent[n] = None
            dfs(n)
    
    return ap

articulation_points = find_articulation_points(adj_undirected, nodes)
print(f"\nArticulation points (cut vertices): {sorted(articulation_points)}")

# Edge connectivity (minimum edge cut)
# For directed graph, use max flow between all pairs
print("\nEdge connectivity (max-flow based):")
min_edge_cut = float('inf')
min_edge_pair = None
for s in sources:
    for t in targets:
        cap_m, idx_m = build_capacity_matrix(edges_raw, nodes)
        # Set all capacities to 1 for edge connectivity
        cap_m_unit = (cap_m > 0).astype(int)
        flow, _ = edmonds_karp(cap_m_unit, idx_m[s], idx_m[t])
        print(f"  {s}->{t}: edge connectivity = {flow}")
        if flow < min_edge_cut:
            min_edge_cut = flow
            min_edge_pair = (s, t)

print(f"\nMinimum edge connectivity lambda: {min_edge_cut} (pair: {min_edge_pair[0]}->{min_edge_pair[1]})")

# ============================================================
# STEP 5: NODE FAILURE SIMULATION
# ============================================================
print("\n" + "=" * 60)
print("STEP 5: NODE FAILURE SIMULATION")
print("=" * 60)

hubs = ['M1', 'M2', 'M3', 'M4']

def analyze_failure(adj_time, edges, all_nodes, failed_nodes):
    """Analyze network after removing failed nodes."""
    remaining = [n for n in all_nodes if n not in failed_nodes]
    adj_fail = defaultdict(list)
    for u, v, t, c in edges:
        if u in remaining and v in remaining:
            adj_fail[u].append((v, t))
    
    results = {}
    for s in sources:
        if s in failed_nodes:
            continue
        dist, prev = dijkstra(adj_fail, s, remaining)
        for t in targets:
            if t in failed_nodes:
                continue
            results[(s,t)] = dist.get(t, float('inf'))
    
    return results

print("\nSingle-node failure (travel time after removal):")
print(f"  {'Failed':>8} | {'S1-T1':>8} {'S1-T2':>8} {'S1-T3':>8} {'S2-T1':>8} {'S2-T2':>8} {'S2-T3':>8} {'S3-T1':>8} {'S3-T2':>8} {'S3-T3':>8}")
print(f"  {'None':>8} | ", end="")
baseline = analyze_failure(adj_time_full, edges_raw, nodes, set())
for key in sorted(baseline.keys()):
    val = baseline[key]
    print(f"{val:>8}", end=" ")
print()

failure_results = {}
for hub in hubs:
    failed = {hub}
    results = analyze_failure(adj_time_full, edges_raw, nodes, failed)
    failure_results[hub] = results
    print(f"  {hub:>8} | ", end="")
    for key in sorted(baseline.keys()):
        val = results.get(key, float('inf'))
        if val == float('inf'):
            print(f"{'INF':>8}", end=" ")
        else:
            print(f"{val:>8}", end=" ")
    print()

# Count disconnected pairs
print("\nDisconnected S->T pairs after single-node failure:")
for hub in hubs:
    inf_count = sum(1 for v in failure_results[hub].values() if v == float('inf'))
    total = len(baseline)
    print(f"  Remove {hub}: {inf_count}/{total} pairs disconnected")

# Double-node failure: M1+M3
print("\n\nDouble-node failure (M1+M3 simultaneously):")
results_double = analyze_failure(adj_time_full, edges_raw, nodes, {'M1', 'M3'})
for key in sorted(baseline.keys()):
    val = results_double.get(key, float('inf'))
    base = baseline[key]
    if val == float('inf'):
        print(f"  {key[0]}->{key[1]}: DISCONNECTED (was {base}min)")
    else:
        print(f"  {key[0]}->{key[1]}: {val}min (was {base}min, +{val-base}min)")

inf_double = sum(1 for v in results_double.values() if v == float('inf'))
print(f"\n  Total disconnected: {inf_double}/{len(baseline)} pairs")

# ============================================================
# STEP 6: VISUALIZATION
# ============================================================
print("\n" + "=" * 60)
print("STEP 6: GENERATING FIGURES")
print("=" * 60)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Node positions
pos = {
    'S1': (0, 2), 'S2': (0, 1), 'S3': (0, 0),
    'M1': (1, 2.5), 'M2': (1, 1.5), 'M3': (1, 0.5), 'M4': (1, -0.5),
    'T1': (2, 2), 'T2': (2, 1), 'T3': (2, 0),
}

node_colors = {
    'S1': 'red', 'S2': 'red', 'S3': 'red',
    'M1': 'orange', 'M2': 'orange', 'M3': 'orange', 'M4': 'orange',
    'T1': 'green', 'T2': 'green', 'T3': 'green',
}

# Figure 1: Network topology
fig, ax = plt.subplots(figsize=(12, 8))
for u, v, t, c in edges_raw:
    x = [pos[u][0], pos[v][0]]
    y = [pos[u][1], pos[v][1]]
    ax.annotate('', xy=(x[1], y[1]), xytext=(x[0], y[0]),
                arrowprops=dict(arrowstyle='->', color='gray', lw=1.5))
    mx, my = (x[0]+x[1])/2, (y[0]+y[1])/2
    ax.text(mx, my+0.08, f'{t}min/{c}', fontsize=6, ha='center', color='navy')

for node, (x, y) in pos.items():
    ax.scatter(x, y, c=node_colors[node], s=300, zorder=5, edgecolors='black', linewidth=1.5)
    ax.text(x, y, node, ha='center', va='center', fontsize=10, fontweight='bold', zorder=6)

legend_elements = [
    mpatches.Patch(color='red', label='Danger Zone'),
    mpatches.Patch(color='orange', label='Hub'),
    mpatches.Patch(color='green', label='Shelter'),
]
ax.legend(handles=legend_elements, loc='upper right')
ax.set_title('City Emergency Evacuation Network\n(edge labels: time(min)/capacity(people/h))')
ax.set_xlim(-0.3, 2.5)
ax.set_ylim(-1, 3)
ax.axis('off')
plt.tight_layout()
plt.savefig('figures/fig1_topology.png', dpi=150)
plt.close()
print("  Saved fig1_topology.png")

# Figure 2: K-shortest paths S1->T1
fig, ax = plt.subplots(figsize=(12, 8))
colors_path = ['red', 'blue', 'green']
for i, (path, cost) in enumerate(zip(paths_s1t1, costs_s1t1)):
    for j in range(len(path)-1):
        u, v = path[j], path[j+1]
        x = [pos[u][0], pos[v][0]]
        y = [pos[u][1], pos[v][1]]
        offset = i * 0.05
        ax.annotate('', xy=(x[1], y[1]+offset), xytext=(x[0], y[0]+offset),
                    arrowprops=dict(arrowstyle='->', color=colors_path[i], lw=2.5))

for node, (x, y) in pos.items():
    ax.scatter(x, y, c=node_colors[node], s=300, zorder=5, edgecolors='black', linewidth=1.5)
    ax.text(x, y, node, ha='center', va='center', fontsize=10, fontweight='bold', zorder=6)

legend_path = [mpatches.Patch(color=colors_path[i], label=f'Path {i+1}: {costs_s1t1[i]}min') for i in range(len(paths_s1t1))]
ax.legend(handles=legend_path, loc='upper right')
ax.set_title('K=3 Shortest Paths: S1 -> T1')
ax.set_xlim(-0.3, 2.5)
ax.set_ylim(-1, 3)
ax.axis('off')
plt.tight_layout()
plt.savefig('figures/fig2_k_paths.png', dpi=150)
plt.close()
print("  Saved fig2_k_paths.png")

# Figure 3: Failure impact comparison
fig, ax = plt.subplots(figsize=(10, 6))
fail_labels = ['None'] + hubs + ['M1+M3']
disconnected_counts = [0]
for hub in hubs:
    disconnected_counts.append(sum(1 for v in failure_results[hub].values() if v == float('inf')))
disconnected_counts.append(inf_double)

colors_bar = ['gray'] + ['coral']*4 + ['darkred']
ax.bar(fail_labels, disconnected_counts, color=colors_bar, edgecolor='black')
ax.set_xlabel('Failed Node(s)')
ax.set_ylabel('Disconnected S->T Pairs')
ax.set_title('Node Failure Impact: Disconnected Source-Target Pairs')
ax.set_ylim(0, 10)
ax.grid(axis='y', alpha=0.3)
for i, v in enumerate(disconnected_counts):
    ax.text(i, v + 0.2, str(v), ha='center', fontweight='bold')
plt.tight_layout()
plt.savefig('figures/fig3_failure.png', dpi=150)
plt.close()
print("  Saved fig3_failure.png")

# ============================================================
# STEP 7: FROZEN NUMBERS
# ============================================================
print("\n" + "=" * 60)
print("STEP 7: SAVING FROZEN NUMBERS")
print("=" * 60)

frozen = {"numbers": []}

# Shortest path times
for (s, t), (path, time_val) in all_shortest.items():
    if time_val == float('inf'):
        frozen["numbers"].append({
            "id": f"shortest_{s}_{t}",
            "label": f"Shortest path time {s}->{t} (DISCONNECTED)",
            "value": -1,
            "tol": 0,
            "source": "dijkstra",
            "path": "solve.py"
        })
    else:
        frozen["numbers"].append({
            "id": f"shortest_{s}_{t}",
            "label": f"Shortest path time {s}->{t}",
            "value": int(time_val),
            "tol": 0,
            "source": "dijkstra",
            "path": "solve.py"
        })

# K-shortest path times
for i, (path, cost) in enumerate(zip(paths_s1t1, costs_s1t1)):
    frozen["numbers"].append({
        "id": f"k_path_{i+1}_time",
        "label": f"K-shortest path {i+1} time S1->T1",
        "value": int(cost),
        "tol": 0,
        "source": "yen_k_shortest",
        "path": "solve.py"
    })

# Max flow
frozen["numbers"].append({
    "id": "max_flow_S1_T1",
    "label": "Max flow S1->T1",
    "value": int(max_flow_s1t1),
    "tol": 0,
    "source": "edmonds_karp",
    "path": "solve.py"
})
frozen["numbers"].append({
    "id": "max_flow_all",
    "label": "Max flow all sources to all sinks",
    "value": int(max_flow_all),
    "tol": 0,
    "source": "edmonds_karp",
    "path": "solve.py"
})

# Connectivity
frozen["numbers"].append({
    "id": "vertex_connectivity_kappa",
    "label": "Vertex connectivity kappa",
    "value": int(kappa),
    "tol": 0,
    "source": "vertex_connectivity",
    "path": "solve.py"
})
frozen["numbers"].append({
    "id": "edge_connectivity_lambda",
    "label": "Minimum edge connectivity lambda",
    "value": int(min_edge_cut),
    "tol": 0,
    "source": "edge_connectivity",
    "path": "solve.py"
})

# Failure results
for hub in hubs:
    inf_count = sum(1 for v in failure_results[hub].values() if v == float('inf'))
    frozen["numbers"].append({
        "id": f"failure_{hub}_disconnected",
        "label": f"Disconnected pairs when {hub} fails",
        "value": int(inf_count),
        "tol": 0,
        "source": "node_failure",
        "path": "solve.py"
    })

frozen["numbers"].append({
    "id": "failure_M1M3_disconnected",
    "label": "Disconnected pairs when M1+M3 fail",
    "value": int(inf_double),
    "tol": 0,
    "source": "node_failure",
    "path": "solve.py"
})

with open('frozen_numbers.json', 'w', encoding='utf-8') as f:
    json.dump(frozen, f, indent=2, ensure_ascii=False)
print(f"Saved {len(frozen['numbers'])} frozen numbers")

print("\n" + "=" * 60)
print("ROUND 10 SOLVER COMPLETE")
print("=" * 60)
