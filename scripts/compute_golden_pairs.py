#!/usr/bin/env python3
"""
compute_golden_pairs.py — 从具体战况 CSV 计算黄金搭档数据

处理两种格式：
  旧格式 (2021-2024.6, 2025.12+): r[0]='', r[1]=日期(仅标题行), r[6]/r[7] 比分
  新格式 (2024.7-2025.11):         r[0]=场次号, r[1]=日期(每行), r[6]/r[7] 比分

输出: GOLDEN_PAIRS = { all:[...], '2021':[...], ..., '2026':[...] }
"""
import csv, io, re, os, sys
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
DETAIL_CSV  = os.path.join(DATA_DIR, "每场战报+总数据-具体战况.csv")
ROSTER_CSV  = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv
TOP_ALL     = 20
TOP_SEASON  = 12

BAD = {
    '/', '?', '', '乌龙', 'OG', 'None', 'null',
    '进球没拍全', '进球没拍全1', '进球没拍全2', '进球没拍全3',
    '/', '？',   # 全角问号
}

PHOTO_MAP = {
    "1":  "assets/players/22号麦超.jpeg",
    "10": "assets/players/10号姜珂.jpeg",
    "14": "assets/players/14号夏浩.jpeg",
    "17": "assets/players/17号张伟.jpeg",
    "18": "assets/players/18号黄纲.jpeg",
    "22": "assets/players/22号鲍梁剑.jpeg",
    "24": "assets/players/24号陆晓巍.jpeg",
    "25": "assets/players/25号鲁尼.jpeg",
    "33": "assets/players/33号季贝赢.jpeg",
    "38": "assets/players/38号鲍澜云.jpeg",
    "41": "assets/players/41号老吴.jpeg",
    "44": "assets/players/44号倪海.jpeg",
    "56": "assets/players/56号朱寿卿.jpeg",
    "68": "assets/players/68号王刚.jpeg",
    "6":  "assets/players/6号陶骏.jpeg",
    "76": "assets/players/76号薛峰.jpeg",
    "81": "assets/players/81号金辉.jpeg",
    "88": "assets/players/88号王积鹏.jpeg",
    "92": "assets/players/92号圣托尔多.jpeg",
    "98": "assets/players/98号姚魏.jpeg",
}
NAME_PHOTO_OVERRIDE = {
    "朱寿卿": "assets/players/56号朱寿卿.jpeg",
}

def get_photo(name, num):
    if name in NAME_PHOTO_OVERRIDE:
        return NAME_PHOTO_OVERRIDE[name]
    return PHOTO_MAP.get(str(num))


def read_name_to_num():
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')
    skip = {'合计', '总计', '名字', '姓名', ''}
    d = {}
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        d[r[0].strip()] = r[4].strip() if len(r) > 4 else ''
    return d


def is_header(row):
    """比赛标题行：r[6] 或 r[7] 有数字（比分）"""
    s1 = row[6].strip() if len(row) > 6 else ''
    s2 = row[7].strip() if len(row) > 7 else ''
    return s1.isdigit() or s2.isdigit()


def row_year(row):
    """从 r[1] 提取赛季年份（YYMMDD 或 YYMMDD-N 格式）"""
    v = row[1].strip() if len(row) > 1 else ''
    digits = v.split('-')[0]
    if len(digits) == 6 and digits.isdigit():
        yy = int(digits[:2])
        return str(2000 + yy)
    return None


def goal_pairs(row):
    """从进球行提取 (scorer, assist) 对"""
    pairs = []
    for sc_col, ast_col in [(4, 5), (8, 9)]:
        sc  = row[sc_col].strip()  if len(row) > sc_col  else ''
        ast = row[ast_col].strip() if len(row) > ast_col else ''
        if sc not in BAD and ast not in BAD and sc and ast and sc != ast:
            pairs.append((sc, ast))
    return pairs


def parse_all_pairs():
    with open(DETAIL_CSV, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))

    meaningful = [(r) for r in rows if any(c.strip() for c in r)]

    pairs_all    = defaultdict(int)
    pairs_season = defaultdict(lambda: defaultdict(int))
    cur_year     = None

    for row in meaningful:
        if is_header(row):
            y = row_year(row)
            if y:
                cur_year = y
        else:
            if not cur_year:
                continue
            for sc, ast in goal_pairs(row):
                key = sc + '\x00' + ast
                pairs_all[key]              += 1
                pairs_season[cur_year][key] += 1

    return pairs_all, pairs_season


def top_pairs(tally, n, n2n):
    result = []
    for key, cnt in sorted(tally.items(), key=lambda x: -x[1])[:n]:
        sc, ast = key.split('\x00')
        s_num   = n2n.get(sc,  '')
        a_num   = n2n.get(ast, '')
        s_photo = get_photo(sc,  s_num)
        a_photo = get_photo(ast, a_num)
        sp = f'"{s_photo}"' if s_photo else 'null'
        ap = f'"{a_photo}"' if a_photo else 'null'
        result.append(
            f'  {{scorer:"{sc}",sNum:"{s_num}",ast:"{ast}",aNum:"{a_num}",'
            f'count:{cnt},sPhoto:{sp},aPhoto:{ap}}}'
        )
    return result


def build_js_block(pairs_all, pairs_season, n2n):
    years = ['2021', '2022', '2023', '2024', '2025', '2026']
    lines = ['const GOLDEN_PAIRS = {']

    # all-time
    all_entries = top_pairs(pairs_all, TOP_ALL, n2n)
    lines.append('  all: [')
    lines.extend([e + ',' for e in all_entries])
    lines.append('  ],')

    # per-season
    for yr in years:
        tally = pairs_season.get(yr, {})
        entries = top_pairs(tally, TOP_SEASON, n2n)
        lines.append(f'  \'{yr}\': [')
        lines.extend([e + ',' for e in entries])
        lines.append('  ],')

    lines.append('};')
    return '\n'.join(lines)


# ── Main ──
print("🤝 计算黄金搭档数据…")
n2n = read_name_to_num()
pairs_all, pairs_season = parse_all_pairs()

print(f"   全部搭档组合数: {len(pairs_all)}")
for yr in ['2021','2022','2023','2024','2025','2026']:
    top = sorted(pairs_season.get(yr, {}).items(), key=lambda x: -x[1])[:1]
    if top:
        sc, ast = top[0][0].split('\x00')
        print(f"   {yr} Top1: {sc}→{ast} {top[0][1]}次")

if DRY_RUN:
    print("\n[dry-run] 未写入文件")
    sys.exit(0)

new_block = build_js_block(pairs_all, pairs_season, n2n)

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

# 替换或插入 GOLDEN_PAIRS 块
pat = re.compile(r'const GOLDEN_PAIRS = \{.*?\};', re.DOTALL)
if pat.search(src):
    src = pat.sub(new_block, src)
else:
    # 插入到 window.RF_DATA 之前
    src = src.replace('window.RF_DATA = {', new_block + '\n\nwindow.RF_DATA = {')

# 确保 GOLDEN_PAIRS 在 window.RF_DATA 导出里
if 'GOLDEN_PAIRS' not in src[src.find('window.RF_DATA'):]:
    src = src.replace('window.RF_DATA = {', 'window.RF_DATA = { GOLDEN_PAIRS,')

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ GOLDEN_PAIRS 已写入 data.jsx（全榜 Top{TOP_ALL}，各赛季 Top{TOP_SEASON}）")
