"""校验 ModelCrew 的 Claude Code subagent 文件格式是否合法。
检查：① YAML frontmatter 能解析；② 必填字段 name/description 齐全；
③ name 合规（小写字母+连字符）；④ name 与文件名一致；⑤ 正文非空。
用法：python .claude/agents/_validate.py
"""
import os, re, sys

try:
    import yaml
    HAVE_YAML = True
except Exception:
    HAVE_YAML = False

HERE = os.path.dirname(os.path.abspath(__file__))
NAME_RE = re.compile(r'^[a-z][a-z0-9-]*$')

def parse_frontmatter(text):
    if not text.startswith('---'):
        raise ValueError('缺少 YAML frontmatter（文件未以 --- 开头）')
    parts = text.split('---', 2)
    if len(parts) < 3:
        raise ValueError('frontmatter 未正确闭合（需要第二个 ---）')
    fm_raw, body = parts[1], parts[2]
    if HAVE_YAML:
        fm = yaml.safe_load(fm_raw) or {}
    else:  # 极简回退解析（key: value 单行）
        fm = {}
        for line in fm_raw.strip().splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip()
    return fm, body.strip()

EXPECTED = [
    'modelcrew-router', 'modelcrew-analyst', 'modelcrew-scout',
    'modelcrew-modeler', 'modelcrew-solver', 'modelcrew-critic',
    'modelcrew-writer', 'modelcrew-judge',
]

def main():
    files = [f for f in os.listdir(HERE)
             if f.endswith('.md') and f.startswith('modelcrew-')]
    errors, oks = [], []
    found_names = set()
    for f in sorted(files):
        path = os.path.join(HERE, f)
        with open(path, encoding='utf-8') as fh:
            text = fh.read()
        try:
            fm, body = parse_frontmatter(text)
            name = fm.get('name', '')
            desc = fm.get('description', '')
            assert name, '缺少 name'
            assert desc, '缺少 description'
            assert NAME_RE.match(name), f'name 不合规: {name!r}'
            assert f == name + '.md', f'文件名 {f} 与 name {name!r} 不一致'
            assert len(body) > 50, '正文过短/为空'
            found_names.add(name)
            tools = fm.get('tools', '(继承全部)')
            oks.append(f'OK   {f:28s} name={name:20s} tools={tools}')
        except Exception as e:
            errors.append(f'FAIL {f:28s} -> {e}')

    print('YAML 解析库:', 'PyYAML' if HAVE_YAML else '回退简析(未装 PyYAML)')
    print('-' * 70)
    for line in oks:
        print(line)
    for line in errors:
        print(line)
    print('-' * 70)
    missing = [n for n in EXPECTED if n not in found_names]
    if missing:
        print('缺少预期子代理:', missing)
    print(f'结果: {len(oks)}/{len(files)} 通过；预期 8 个角色，'
          f'实到 {len(found_names & set(EXPECTED))} 个')
    sys.exit(1 if (errors or missing) else 0)

if __name__ == '__main__':
    main()
