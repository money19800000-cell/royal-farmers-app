#!/usr/bin/env python3
"""
Royal Farmers FC — 赛程 & 战报更新脚本
从 具体战况.csv 全量重建 FIXTURES，自动同步最近一场和最近7场。

用法：
    python3 scripts/update_fixtures.py
    python3 scripts/update_fixtures.py --dry-run   # 只打印不写入
"""
import csv, re, sys, os, json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united/每场战报+总数据-具体战况.csv"
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

# 内部队名自动加前缀
INTERNAL_TEAMS = {'蓝队','红队','白队','黄队','绿队','黑队'}
PREFIX = "Royal Farmers"

# 默认球场（内部比赛无记录时使用）
DEFAULT_VENUE = "台地花园球场"

# 只处理 2026 赛季（可调整）
TARGET_YEAR = "2026"


def parse_date(raw: str):
    """
    将 CSV 日期码转成 "YYYY.MM.DD" 格式。
    支持格式：260523-1 / 260521 / 20260514 / 2026.05.09 等
    返回 (sort_key, display)，sort_key 用于排序
    """
    d = raw.strip().split('-')[0]   # 去掉 "-N" 后缀
    d = d.replace('.', '')          # 去掉可能的点号
    if len(d) == 6 and d.startswith('2'):
        # 260523 → 20260523
        d = '20' + d
    if len(d) == 8 and d.startswith('2026'):
        year, month, day = d[:4], d[4:6], d[6:8]
        display  = f"{year}.{month}.{day}"
        sort_key = f"{year}{month}{day}"
        return sort_key, display
    return None, None


def team_name(raw: str) -> str:
    raw = raw.strip()
    if raw in INTERNAL_TEAMS:
        return f"{PREFIX}{raw}"
    return raw


def clean_person(name: str) -> str:
    """过滤掉非人名占位符"""
    name = name.strip()
    skip = {'/', '', '进球没拍全', '进球没拍全1', '进球没拍全2', '进球没拍全3'}
    return '' if name in skip else name


def parse_matches_from_csv():
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))

    matches = []
    current = None

    for r in rows:
        if not r or not any(c.strip() for c in r):
            continue

        date_raw = r[1].strip() if len(r) > 1 else ''

        # ── Match header row ──
        if date_raw and re.match(r'^\d', date_raw) and len(r) >= 9:
            # Save previous match if valid
            if current:
                matches.append(current)
            sort_key, display = parse_date(date_raw)
            if not sort_key:
                current = None
                continue

            # Only process target year
            if not sort_key.startswith(TARGET_YEAR):
                current = None
                continue

            home_raw  = r[4].strip() if len(r) > 4 else ''
            away_raw  = r[8].strip() if len(r) > 8 else ''
            comp      = r[2].strip() if len(r) > 2 else ''
            venue_raw = r[3].strip() if len(r) > 3 else ''

            try:
                hs = int(r[6].strip()) if len(r) > 6 and r[6].strip() else 0
                as_ = int(r[7].strip()) if len(r) > 7 and r[7].strip() else 0
            except ValueError:
                hs, as_ = 0, 0

            venue = venue_raw or DEFAULT_VENUE
            result = 'W' if hs > as_ else ('L' if hs < as_ else 'D')

            current = {
                'sort_key':    sort_key,
                'date':        display,
                'home':        team_name(home_raw),
                'homeScore':   hs,
                'awayScore':   as_,
                'away':        team_name(away_raw),
                'comp':        comp,
                'result':      result,
                'venue':       venue,
                'homeScorers': [],
                'awayScorers': [],
                'homeAssists': [],
                'awayAssists': [],
            }
            continue

        # ── Goal / assist row ──
        if current is None:
            continue

        # 列偏移检测：某些比赛（如 20260514）进球行整体左移1列
        # 正常: col3=空, col4=主进球, col5=主助攻, col8=客进球, col9=客助攻
        # 偏移: col3=主进球, col4=主助攻（此时 col3 非空）
        col3 = r[3].strip() if len(r) > 3 else ''
        if col3 and col3 not in {'/', ''} and not re.match(r'^\d', col3):
            # 偏移格式
            home_scorer = clean_person(col3)
            home_assist = clean_person(r[4]) if len(r) > 4 else ''
            away_scorer = clean_person(r[7]) if len(r) > 7 else ''
            away_assist = clean_person(r[8]) if len(r) > 8 else ''
        else:
            # 正常格式
            home_scorer = clean_person(r[4]) if len(r) > 4 else ''
            home_assist = clean_person(r[5]) if len(r) > 5 else ''
            away_scorer = clean_person(r[8]) if len(r) > 8 else ''
            away_assist = clean_person(r[9]) if len(r) > 9 else ''

        if home_scorer:
            current['homeScorers'].append(home_scorer)
        if home_assist:
            current['homeAssists'].append(home_assist)
        if away_scorer:
            current['awayScorers'].append(away_scorer)
        if away_assist:
            current['awayAssists'].append(away_assist)

    # Save last match
    if current:
        matches.append(current)

    # Sort newest first
    matches.sort(key=lambda m: m['sort_key'], reverse=True)
    return matches


def match_to_js(m) -> str:
    def js_arr(lst):
        if not lst:
            return '[]'
        items = ','.join(f'"{x}"' for x in lst)
        return f'[{items}]'

    return (
        f'  {{ date: "{m["date"]}", home: "{m["home"]}", homeScore: {m["homeScore"]}, '
        f'awayScore: {m["awayScore"]}, away: "{m["away"]}", comp: "{m["comp"]}", '
        f'result: "{m["result"]}", venue: "{m["venue"]}", '
        f'homeScorers: {js_arr(m["homeScorers"])}, awayScorers: {js_arr(m["awayScorers"])}, '
        f'homeAssists: {js_arr(m["homeAssists"])}, awayAssists: {js_arr(m["awayAssists"])} }}'
    )


# ── Main ──
print("📋 解析 具体战况.csv ...")
matches = parse_matches_from_csv()
print(f"   {TARGET_YEAR} 赛季共解析：{len(matches)} 场")

# Read existing FIXTURES
with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

fixtures_start = src.find('const FIXTURES = [')
fixtures_end   = src.find('];', fixtures_start) + 2
old_block = src[fixtures_start:fixtures_end]
existing_count = len(re.findall(r'date:\s*"', old_block))

# Detect new matches (dates not in existing FIXTURES)
existing_dates = set(re.findall(r'date:\s*"([^"]+)"', old_block))
new_matches = [m for m in matches if not any(
    d == m['date'] for d in existing_dates
) or True]  # always rebuild for accuracy

# Build new FIXTURES block
date_comments = {}
lines = ['const FIXTURES = [']
prev_date = None
for m in matches:
    if m['date'] != prev_date:
        lines.append(f'  // {m["date"]}')
        prev_date = m['date']
    lines.append(match_to_js(m) + ',')
lines.append('];')
new_fixtures_js = '\n'.join(lines)

# Detect differences
new_count = len(matches)
new_dates_set = {m['date'] for m in matches}
added_dates = new_dates_set - existing_dates

print(f"   现有记录：{existing_count} 场 (最新: {sorted(existing_dates)[-1] if existing_dates else '—'})")
print(f"   更新后：  {new_count} 场 (最新: {matches[0]['date'] if matches else '—'})")

if added_dates:
    print(f"\n✨ 新增比赛日期：{sorted(added_dates, reverse=True)}")
    for d in sorted(added_dates, reverse=True):
        day_matches = [m for m in matches if m['date'] == d]
        for m in day_matches:
            print(f"   {m['date']} | {m['home']} {m['homeScore']}:{m['awayScore']} {m['away']} ({m['comp']})")
else:
    print("\n✅ 无新比赛，赛程已是最新")

if not DRY_RUN:
    new_src = src[:fixtures_start] + new_fixtures_js + src[fixtures_end:]
    with open(DATA_JSX, 'w', encoding='utf-8') as f:
        f.write(new_src)
    print(f"\n📝 data.jsx FIXTURES 已更新（{new_count} 场）")
    print(f"   最近一场：{matches[0]['date']} | {matches[0]['home']} {matches[0]['homeScore']}:{matches[0]['awayScore']} {matches[0]['away']}")
else:
    print("\n[dry-run] 未写入文件")
