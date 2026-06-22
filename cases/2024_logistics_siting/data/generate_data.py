"""生成 communities.csv（应急选址案例的固定合成数据）。

可复核性：固定 np.random.default_rng(42)，逐字节可复现已提交的 data/communities.csv。
明确记录"由 5 个居住组团生成"——便于 Critic 独立核对组团结构（回应审计意见）。
运行：cd cases/2024_logistics_siting && python data/generate_data.py
"""
import numpy as np, csv, os

rng = np.random.default_rng(42)
# 5 个居住组团（城市的 5 个聚居区）：中心坐标 + 人口密度权重
centers = [(12, 12), (12, 78), (80, 15), (82, 80), (48, 46)]
clust_pop = [1.0, 1.0, 1.2, 0.9, 1.4]

rows = []
cid = 0
for k, (cx, cy) in enumerate(centers):
    n = rng.integers(10, 15)              # 每组团 10–14 个社区
    for _ in range(n):
        x = np.clip(rng.normal(cx, 6), 0, 100)
        y = np.clip(rng.normal(cy, 6), 0, 100)
        pop = int(np.clip(rng.normal(5000 * clust_pop[k], 1500), 500, None))
        rows.append((cid, round(float(x), 2), round(float(y), 2), pop))
        cid += 1

out = os.path.join(os.path.dirname(__file__), "communities.csv")
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["id", "x", "y", "population"])
    w.writerows(rows)
print(f"生成 {len(rows)} 个社区（来自 5 个组团）→ {out}")
print("总人口", sum(r[3] for r in rows))
