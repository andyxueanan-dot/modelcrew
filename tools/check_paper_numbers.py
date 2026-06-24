"""论文散文数字校验器 (paper-prose number checker)。

`check_frozen.py` 只保证 frozen_numbers.json 的冻结值与脚本 results.json 一致；
它**不检查论文正文（散文）里手写的数字是否还等于权威值**。本工具补这一环——
把"Critic 手写临时脚本抓出散文里残留旧值"的能力沉淀成常驻工具。

做法：对每个冻结数字，逐一核对它声明 cited_in 的论文文件——
该文件里**找不到**与冻结值数值相符的数 → FAIL：多半是散文残留了旧值、或引用过期；
报告时附上"最近的可疑值"帮人定位那个没同步的旧值。

设计取向：**registry 即契约**——把论文依赖的关键数字都登记进 frozen_numbers.json，
presence 检查即可精准抓"正确值缺失/被旧值顶替"，且零误报。不做全文近邻扫描
（点估计与其 CI 端点天然紧挨，全文近邻告警噪声大、会训练人忽略告警）。

数值比对（非字符串渲染）天然容忍 1.323≡1.3230 这类尾零/精度差；
对每个文本里的数还附带"百分数解读"（x 与 x/100），故 0.8286 写成 "82.86%" 也能匹配。

用法：python tools/check_paper_numbers.py            # 跑全部 case
      python tools/check_paper_numbers.py <case_dir> # 只跑一个（相对仓库根）
退出码：有 FAIL=1，全过=0，与 check_frozen.py 一致。
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CASES = [
    "cases/2024_mcm_c_tennis",
    "cases/credit_default_fintech",
    "cases/2024_logistics_siting",
    "cases/demo_dispatch_simpson",
]

# 抓数字：可选正负号（含 Unicode 减号已先归一化为 ASCII），整数+可选小数
NUM_RE = re.compile(r"[+\-]?\d+(?:\.\d+)?")
NEAR_REL = 0.03  # 近邻 WARN 的相对窗口


def normalize(text):
    """Unicode 减号→ASCII；去掉数字内的千分位逗号（如 4,418,714.9）。"""
    text = text.replace("−", "-").replace("–", "-")
    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    return text


def extract_numbers(text):
    """返回 (值, 小数位数) 列表；小数位数用于舍入感知匹配。"""
    out = []
    for m in NUM_RE.finditer(text):
        tok = m.group()
        try:
            v = float(tok)
        except ValueError:
            continue
        ndec = len(tok.split(".")[1]) if "." in tok else 0
        out.append((v, ndec))
    return out


def interps(x, ndec):
    """文本数 x 的"分数值"解读：原值（小数位 ndec），或它是百分数 /100（小数位 ndec+2）。"""
    return ((x, ndec), (x / 100.0, ndec + 2))


def matches(x, ndec, value, tol):
    """舍入感知：散文写 d 位小数时，只要 value 舍入到 d 位等于它即算相符
    （半个最低位单位的容差）。故 0.156 写成 0.16 接受，但 0.7527 写成 0.76 不接受。"""
    for iv, dec in interps(x, ndec):
        half_ulp = 0.5 * 10 ** (-dec) + 1e-9
        if abs(iv - value) <= max(tol, half_ulp):
            return True
    return False


def near_miss(x, ndec, value, tol):
    """很近但不相等：相对 NEAR_REL 内、却超出 tol（FAIL 时帮人定位疑似旧值）。"""
    scale = abs(value) if value else 1.0
    for iv, dec in interps(x, ndec):
        half_ulp = 0.5 * 10 ** (-dec) + 1e-9
        if max(tol, half_ulp) < abs(iv - value) <= NEAR_REL * scale:
            return True
    return False


def check_case(case_dir):
    fn_path = os.path.join(ROOT, case_dir, "artifacts", "frozen_numbers.json")
    if not os.path.exists(fn_path):
        print(f"  [缺失] {fn_path}")
        return 1, 0
    with open(fn_path, encoding="utf-8") as f:
        spec = json.load(f)

    file_cache = {}
    # cited_in 文件可能在 case 根（如 README.md）、artifacts/（如 6_paper.md）、submission/、仓库根。
    # case 根优先于 artifacts/——"README.md"按惯例指 case 自述，而非 artifacts/README.md。
    search_dirs = [os.path.join(ROOT, case_dir),
                   os.path.join(ROOT, case_dir, "artifacts"),
                   os.path.join(ROOT, "submission"), ROOT]

    def load(rel):
        if rel not in file_cache:
            file_cache[rel] = None
            for d in search_dirs:
                p = os.path.join(d, rel)
                if os.path.exists(p):
                    with open(p, encoding="utf-8") as fh:
                        file_cache[rel] = extract_numbers(normalize(fh.read()))
                    break
        return file_cache[rel]

    fails = warns = checks = 0
    for item in spec["numbers"]:
        value = float(item["value"])
        tol = float(item.get("tol", 0)) or 0.0005
        cited = [c.strip() for c in item.get("cited_in", "").split(",") if c.strip()]
        # 只核对论文/散文类文件（.md / .tex），跳过 json/数据
        cited = [c for c in cited if c.endswith((".md", ".tex"))]
        for rel in cited:
            nums = load(rel)
            if nums is None:
                print(f"  FAIL {item['id']:22s} cited_in 文件不存在: {rel}")
                fails += 1
                continue
            checks += 1
            if any(matches(x, d, value, tol) for x, d in nums):
                continue  # 正确值在场即过（CI 端点等近邻数是合法的别的量，不告警）
            # 没找到正确值 → 散文多半残留了旧值；附最近的可疑值帮人定位
            near = sorted({x for x, d in nums if near_miss(x, d, value, tol)})[:3]
            hint = f"，最近的可疑值 {near}（疑旧值未同步）" if near else ""
            print(f"  FAIL {item['id']:22s} {rel}: 找不到冻结值 {value}（{item['label']}）{hint}")
            fails += 1

    return fails, checks


def main():
    cases = [sys.argv[1]] if len(sys.argv) > 1 else CASES
    tf = tc = 0
    for c in cases:
        print(f"== {c} ==")
        f, n = check_case(c)
        tf += f; tc += n
        print()
    print("=" * 60)
    print(f"汇总：{tc - tf}/{tc} 处散文引用与冻结值相符；FAIL={tf}")
    sys.exit(1 if tf else 0)


if __name__ == "__main__":
    main()
