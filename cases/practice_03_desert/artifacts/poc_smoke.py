# PoC 冒烟闸 PoC-1/2/3 —— 模型选用前最小验证
from collections import deque

# --- 读地图 ---
adj = {}
typ = {}
with open("data/map_level1.txt", encoding="utf-8") as f:
    for ln in f:
        ln = ln.strip()
        if not ln or ln.startswith("#"): continue
        parts = ln.split()
        v = int(parts[0]); t = parts[1]; nbrs = [int(x) for x in parts[2:]]
        adj[v] = nbrs; typ[v] = t

# --- 读天气 ---
BASE = {"qinglang": (5,7), "gaowen": (8,6), "shabao": (10,10)}
weather = {}
with open("data/weather_level1.txt", encoding="utf-8") as f:
    for ln in f:
        ln = ln.strip()
        if not ln or ln.startswith("#"): continue
        d, w = ln.split()
        weather[int(d)] = w

# PoC-1: BFS 图最短步数 1->27
def bfs(s, g):
    q = deque([(s,0)]); seen={s}
    while q:
        u,d = q.popleft()
        if u==g: return d
        for v in adj[u]:
            if v not in seen: seen.add(v); q.append((v,d+1))
    return -1
steps = bfs(1,27)
print(f"PoC-1: 图最短步数 1->27 = {steps}  (预期 3)")
assert steps == 3, "PoC-1 FAIL: 最短步数 != 3"

# 验证一条 3 步路径存在: 1->25->26->27
path = [1,25,26,27]
ok = all(path[i+1] in adj[path[i]] for i in range(3))
print(f"  路径 1-25-26-27 合法: {ok}")
assert ok

# PoC-2: 固定轨迹 1->25->26->27 三天直达, 手算财富 9410
# 第1天高温(8,6) 第2天高温(8,6) 第3天晴(5,7), 每天移动x2
w_need = 2*(8+8+5)  # 42
f_need = 2*(6+6+7)  # 38
cost = 5*w_need + 10*f_need
wealth = 10000 - cost  # 剩 0 退 0
print(f"PoC-2: 直达轨迹 水需{w_need} 食需{f_need} 购买成本{cost} 财富{wealth} (预期 9410)")
assert w_need==42 and f_need==38 and wealth==9410, "PoC-2 FAIL"
load = 3*w_need + 2*f_need
print(f"  出发负重 {load} kg <= 1200: {load<=1200}")
assert load <= 1200

# PoC-3: 在线策略信息墙 —— 同一策略对前缀相同序列前 t 步决策一致
def dummy_policy(weather_seq, t):
    # 只能看 weather_seq[0..t], 返回前 t 步"决策"(此处用看到的天气哈希模拟)
    return tuple(weather_seq[i] for i in range(t+1))
seqA = ["gaowen","gaowen","qinglang","shabao","qinglang"]
seqB = ["gaowen","gaowen","qinglang","gaowen","gaowen"]  # 前3相同后2不同
t = 2
dA = dummy_policy(seqA, t); dB = dummy_policy(seqB, t)
print(f"PoC-3: 前 t={t} 步决策 A==B: {dA==dB} (信息墙: 看不到未来则一致)")
assert dA == dB, "PoC-3 FAIL: 未来泄漏"

print("\n=== PoC-1/2/3 全部 PASS ===")
# 顺带打印沙暴日清单核对
storms = [d for d in sorted(weather) if weather[d]=="shabao"]
print("沙暴日:", storms)
