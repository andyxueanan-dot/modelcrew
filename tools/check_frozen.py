"""数字可追溯校验器 (frozen-numbers checker)。

为"反幻觉 / 可复现"主张提供自动化保障：
1. 读各案例 artifacts/frozen_numbers.json（论文引用数字的唯一真相源）；
2. 回到脚本产出的源 JSON，按 path 取值，核对冻结值是否仍一致（防止论文数字与脚本输出漂移）；
3. mtime 检查：若任一 input（solve.py / 数据）比源结果 JSON 更新，则报 ⚠️ STALE
   ——意味着结果可能过期，需重跑脚本后刷新 frozen_numbers。

用法：python tools/check_frozen.py
退出码：全部通过=0，有不一致/缺文件=1（STALE 仅告警，不致失败）。

借鉴 math-modeling-skills 的 frozen_numbers 思路，独立重写。
"""
import json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
    "cases/2024_mcm_c_tennis",
    "cases/credit_default_fintech",
]


def dig(obj, path):
    """按 path 取值。path 可为点分字符串，或段列表（键名本身含点时用列表）。
    数字段当列表下标。"""
    segs = path if isinstance(path, list) else path.split(".")
    cur = obj
    for seg in segs:
        if isinstance(cur, list):
            cur = cur[int(seg)]
        else:
            cur = cur[seg]
    return cur


def check_case(case_dir):
    fn_path = os.path.join(ROOT, case_dir, "artifacts", "frozen_numbers.json")
    if not os.path.exists(fn_path):
        print(f"  [缺失] {fn_path}")
        return 1, 0
    with open(fn_path, encoding="utf-8") as f:
        spec = json.load(f)

    fails = 0
    src_cache = {}
    src_mtimes = {}

    for item in spec["numbers"]:
        src_rel = item["source"]
        src_abs = os.path.join(ROOT, case_dir, src_rel)
        if src_rel not in src_cache:
            if not os.path.exists(src_abs):
                print(f"  FAIL {item['id']:22s} 源文件不存在: {src_rel}")
                fails += 1
                continue
            with open(src_abs, encoding="utf-8") as f:
                src_cache[src_rel] = json.load(f)
            src_mtimes[src_rel] = os.path.getmtime(src_abs)
        try:
            actual = dig(src_cache[src_rel], item["path"])
        except (KeyError, IndexError, ValueError) as e:
            print(f"  FAIL {item['id']:22s} path 取值失败 {item['path']!r}: {e}")
            fails += 1
            continue
        tol = item.get("tol", 0)
        ok = abs(float(actual) - float(item["value"])) <= tol
        mark = "OK  " if ok else "FAIL"
        if not ok:
            fails += 1
        print(f"  {mark} {item['id']:22s} 冻结={item['value']:<10} 实测={actual:<12} ({item['label']})")

    # 新鲜度检查
    stale = []
    newest_input = 0.0
    for inp in spec.get("inputs", []):
        p = os.path.join(ROOT, case_dir, inp)
        if os.path.exists(p):
            newest_input = max(newest_input, os.path.getmtime(p))
    for src_rel, mt in src_mtimes.items():
        if newest_input > mt + 1:  # 输入比结果新（留 1s 容差）
            stale.append(src_rel)
    if stale:
        print(f"  ⚠️ STALE: 输入(solve.py/数据)比结果更新，建议重跑后刷新 → {stale}")

    return fails, len(spec["numbers"])


def main():
    total_fail = total_num = 0
    for c in CASES:
        print(f"== {c} ==")
        f, n = check_case(c)
        total_fail += f
        total_num += n
        print()
    print("=" * 56)
    print(f"汇总：{total_num - total_fail}/{total_num} 个冻结数字与脚本输出一致")
    sys.exit(1 if total_fail else 0)


if __name__ == "__main__":
    main()
