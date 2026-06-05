#!/usr/bin/env python3
"""
compute_season_match_stats.py — 从具体战况 CSV 统计各赛季外部对战胜负平

输出: SEASON_MATCH_STATS = {
  '2021': { w:N, d:N, l:N, gf:N, ga:N, total:N },
  ...
  '2026': { ... },
}
"""
import csv, re, os, sys
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
DETAIL_CSV  = os.path.join(DATA_DIR, "每场战报+总数据-具体战况.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

# 皇家农民工内部队名（颜色队名 = 我方队）
RF_TEAMS = {'蓝队','白队','红队','绿队','黑队','黄队','一队','二队'}


def row_year(row):
    """从 r[1] 提取年份 YYYY"""
    v = row[1].strip() if len(row) > 1 else ''
    digits = v.split('-')[0]
    if len(digits) == 6 and digits.isdigit():
        return str(2000 + int(digits[:2]))
    return None


def is_header(row):
    s1 = row[6].strip() if len(row) > 6 else ''
    s2 = row[7].strip() if len(row) > 7 else ''
    return s1.isdigit() or s2.isdigit()


def is_rf(name):
    return name in RF_TEAMS


def parse():
    with open(DETAIL_CSV, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))

    stats = defaultdict(lambda: {'w':0,'d':0,'l':0,'gf':0,'ga':0})
    cur_year = None

    for row in rows:
        if not any(c.strip() for c in row):
            continue
        if is_header(row):
            y = row_year(row)
            if y:
                cur_year = y

            if cur_year is None:
                continue

            # 用队名判断是否外部赛（颜色队名=RF队，其他=外部队）
            # 比赛类型关键词仅作辅助参考（旧赛季 r[2] 为空）
            match_type = row[2].strip() if len(row) > 2 else ''
            # 如果 match_type 明确是内部赛则跳过
            if '内部' in match_type or '对内' in match_type:
                continue

            home = row[4].strip() if len(row) > 4 else ''
            away = row[8].strip() if len(row) > 8 else ''
            try:
                hs = int(row[6].strip())
                as_ = int(row[7].strip())
            except (ValueError, IndexError):
                continue

            # 确定哪方是我们（颜色队名=RF队），哪方是外部
            home_rf = is_rf(home)
            away_rf = is_rf(away)

            if home_rf and away_rf:
                continue  # 双方都是内部队，跳过
            if not home_rf and not away_rf:
                continue  # 双方都是外部队，跳过

            # 从我们的角度看结果
            if home_rf:
                rf_score, opp_score = hs, as_
            else:
                rf_score, opp_score = as_, hs

            st = stats[cur_year]
            st['gf'] += rf_score
            st['ga'] += opp_score
            if rf_score > opp_score:
                st['w'] += 1
            elif rf_score == opp_score:
                st['d'] += 1
            else:
                st['l'] += 1

    # 计算 total
    for yr, st in stats.items():
        st['total'] = st['w'] + st['d'] + st['l']

    return stats


def build_js(stats):
    years = ['2021','2022','2023','2024','2025','2026']
    lines = ['const SEASON_MATCH_STATS = {']
    for yr in years:
        st = stats.get(yr, {'w':0,'d':0,'l':0,'gf':0,'ga':0,'total':0})
        avg = round(st['gf'] / st['total'], 1) if st['total'] > 0 else 0
        lines.append(
            f"  '{yr}': {{w:{st['w']},d:{st['d']},l:{st['l']},"
            f"gf:{st['gf']},ga:{st['ga']},total:{st['total']},avgGF:{avg}}},"
        )
    lines.append('};')
    return '\n'.join(lines)


# ── Main ──
print("📊 统计各赛季外部对战战绩…")
stats = parse()
for yr in ['2021','2022','2023','2024','2025','2026']:
    st = stats.get(yr, {})
    print(f"   {yr}: {st.get('total',0)}场 {st.get('w',0)}胜{st.get('d',0)}平{st.get('l',0)}负  进{st.get('gf',0)}")

if DRY_RUN:
    print("\n[dry-run] 未写入文件")
    sys.exit(0)

new_block = build_js(stats)

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

pat = re.compile(r'const SEASON_MATCH_STATS = \{.*?\};', re.DOTALL)
if pat.search(src):
    src = pat.sub(new_block, src)
else:
    src = src.replace('window.RF_DATA = {', new_block + '\n\nwindow.RF_DATA = {')

if 'SEASON_MATCH_STATS' not in src[src.find('window.RF_DATA'):]:
    src = src.replace('window.RF_DATA = {', 'window.RF_DATA = { SEASON_MATCH_STATS,')

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print("\n✅ SEASON_MATCH_STATS 已写入 data.jsx")
