#!/usr/bin/env python3
"""Royal Farmers FC — 球员出勤率热力图数据生成脚本"""
import os, sys, re, csv
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
ROSTER_CSV  = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv
SKIP_ROSTER = {'合计', '总计', '名字', '姓名', ''}
MIN_APPS    = 30
MAX_PLAYERS = 30


def main():
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))

    hrow = next(i for i, r in enumerate(rows) if r and r[0].strip() == '名字')
    headers = [h.strip() for h in rows[hrow]]

    # 日期列：格式 YYYYMMDD，按日期升序
    date_cols = sorted(
        [(i, h) for i, h in enumerate(headers) if h.isdigit() and len(h) == 8],
        key=lambda x: x[1]
    )

    # 所有月份（YYYY-MM），保持升序唯一
    periods = sorted(set(d[:4] + '-' + d[4:6] for _, d in date_cols))

    # 每月总场次（该月有多少个比赛日）
    totals = [sum(1 for _, d in date_cols if d[:4] + '-' + d[4:6] == p) for p in periods]

    # 球员每月出场次数
    player_stats = {}
    for row in rows[hrow + 1:]:
        if not row or not row[0].strip() or row[0].strip() in SKIP_ROSTER:
            continue
        name = row[0].strip()
        num  = row[4].strip() if len(row) > 4 else ''
        monthly = defaultdict(int)
        for col_idx, date_str in date_cols:
            val = row[col_idx].strip() if len(row) > col_idx else ''
            if val:  # 非空 = 出场
                monthly[date_str[:4] + '-' + date_str[4:6]] += 1
        total = sum(monthly.values())
        if total >= MIN_APPS:
            player_stats[name] = {
                'name': name, 'num': num, 'total': total,
                'monthly': [monthly.get(p, 0) for p in periods]
            }

    players = sorted(player_stats.values(), key=lambda x: -x['total'])[:MAX_PLAYERS]

    # 生成 JS block
    periods_str = '[' + ','.join(f'"{p}"' for p in periods) + ']'
    totals_str  = '[' + ','.join(str(t) for t in totals) + ']'
    players_parts = []
    for p in players:
        m = '[' + ','.join(str(x) for x in p['monthly']) + ']'
        players_parts.append(f'{{name:"{p["name"]}",num:"{p["num"]}",total:{p["total"]},monthly:{m}}}')
    players_str = '[\n  ' + ',\n  '.join(players_parts) + '\n]'

    block = (
        '// [AUTO] ATTENDANCE_HEATMAP — computed by compute_attendance_heatmap.py\n'
        f'const ATTENDANCE_HEATMAP = {{\n'
        f'  periods: {periods_str},\n'
        f'  totals: {totals_str},\n'
        f'  players: {players_str}\n'
        f'}};\n'
    )

    if DRY_RUN:
        print(block[:2000])
        print(f'\n... periods={len(periods)}, players={len(players)}')
        return

    with open(DATA_JSX, encoding='utf-8') as f:
        content = f.read()

    # 替换已有 block（从 AUTO 注释到行首的 `};` 结束）
    pattern = r'// \[AUTO\] ATTENDANCE_HEATMAP.*?^\};\n'
    if re.search(pattern, content, re.DOTALL | re.MULTILINE):
        new_content = re.sub(pattern, block, content, flags=re.DOTALL | re.MULTILINE)
    else:
        # 在 window.RF_DATA = { 之前插入
        insert_pos = content.find('window.RF_DATA = {')
        if insert_pos == -1:
            print('ERROR: window.RF_DATA not found in data.jsx')
            sys.exit(1)
        new_content = content[:insert_pos] + block + '\n' + content[insert_pos:]

    with open(DATA_JSX, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f'✅ ATTENDANCE_HEATMAP updated: {len(periods)} months × {len(players)} players')


if __name__ == '__main__':
    main()
