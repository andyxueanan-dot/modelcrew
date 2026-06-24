"""确定性生成应急调度数据（内置辛普森悖论，无随机，字节级可复现）。

设计（供复核）：
- 严重度 Low 的按时率整体高、High 整体低；
- 策略 A 主要承接 Low（容易），B 主要承接 High（困难）——severity 是混杂变量；
- 分层看 B 在两层都不低于 A，但汇总看 A 远高于 B（辛普森悖论）。

各格按时人数/总数（写死）：
            Low                 High
  A     270/300 (90.0%)      20/50  (40.0%)     -> A 合计 290/350 = 82.857%
  B      47/50  (94.0%)     135/300 (45.0%)     -> B 合计 182/350 = 52.000%
  分层： Low  B 94.0% >= A 90.0%
         High B 45.0% >= A 40.0%
  汇总： A 82.857% >> B 52.000%   <-- naive 误判 A 更优
"""
import csv, os

CELLS = [
    # policy, severity, n_total, n_on_time
    ("A", "Low",  300, 270),
    ("A", "High",  50,  20),
    ("B", "Low",   50,  47),
    ("B", "High", 300, 135),
]

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "dispatch.csv")
    rows = []
    cid = 1
    for policy, severity, n_total, n_ok in CELLS:
        for i in range(n_total):
            on_time = 1 if i < n_ok else 0
            rows.append((cid, policy, severity, on_time))
            cid += 1
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["call_id", "policy", "severity", "on_time"])
        w.writerows(rows)
    print(f"wrote {len(rows)} rows -> {out}")

if __name__ == "__main__":
    main()
