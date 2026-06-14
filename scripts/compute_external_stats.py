#!/usr/bin/env python3
"""
compute_external_stats.py — 外部友谊赛（两队）统计
从 具体战况.csv 提取所有年份的外部两队赛数据，计算：
  - 每赛季战绩（场/胜/平/负/进/失/净）
  - 每赛季最佳射手、助攻王（Top 10）
  - 每赛季赛果列表（供前端展示）

输出: EXTERNAL_MATCH_STATS = { seasons:[...], all:{...} }
"""
import csv, re, sys, os, json
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united/每场战报+总数据-具体战况.csv"
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

INTERNAL_TEAMS = {'蓝队','红队','白队','黄队','绿队','黑队'}
RF_PREFIX      = "Royal Farmers"
DEFAULT_VENUE  = "台地花园球场"
BAD_NAMES = {'/', '', '乌龙', 'OG', '进球没拍全',
             '进球没拍全1','进球没拍全2','进球没拍全3','？','?'}


def parse_date(raw):
    d = raw.strip().split('-')[0].replace('.', '')
    if len(d) == 6 and d.startswith('2'):
        d = '20' + d
    if len(d) == 8 and d.isdigit():
        return d[:4], f"{d[:4]}.{d[4:6]}.{d[6:8]}"
    return None, None


def team_name(raw):
    raw = raw.strip()
    return f"{RF_PREFIX}{raw}" if raw in INTERNAL_TEAMS else raw


def clean(name):
    name = name.strip()
    return '' if name in BAD_NAMES else name


def parse_matches():
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))

    matches = []
    current = None

    for r in rows:
        if not r or not any(c.strip() for c in r):
            continue

        date_raw = r[1].strip() if len(r) > 1 else ''

        # Match header: date in col1, score digits in col6/7
        if date_raw and re.match(r'^\d', date_raw) and len(r) >= 9:
            s1 = r[6].strip() if len(r) > 6 else ''
            s2 = r[7].strip() if len(r) > 7 else ''
            if not (s1.isdigit() or s2.isdigit()):
                # Goal row in new-era format (every row has date)
                if current and '外部' in (current.get('comp','')) and '两队' in (current.get('comp','')):
                    col3 = r[3].strip() if len(r) > 3 else ''
                    # In new format: col4=scorer, col5=assist (home), col8=scorer, col9=assist (away)
                    sc_h  = clean(r[4]) if len(r) > 4 else ''
                    ast_h = clean(r[5]) if len(r) > 5 else ''
                    sc_a  = clean(r[8]) if len(r) > 8 else ''
                    ast_a = clean(r[9]) if len(r) > 9 else ''
                    if sc_h:
                        current['homeScorers'].append(sc_h)
                        current['homeAssists'].append(ast_h)
                    if sc_a:
                        current['awayScorers'].append(sc_a)
                        current['awayAssists'].append(ast_a)
                continue

            # Save previous
            if current:
                matches.append(current)

            year, display = parse_date(date_raw)
            if not year:
                current = None
                continue

            comp      = r[2].strip() if len(r) > 2 else ''
            venue_raw = r[3].strip() if len(r) > 3 else ''
            home_raw  = r[4].strip() if len(r) > 4 else ''
            away_raw  = r[8].strip() if len(r) > 8 else ''

            try:
                hs  = int(r[6].strip()) if s1.isdigit() else 0
                as_ = int(r[7].strip()) if s2.isdigit() else 0
            except ValueError:
                hs, as_ = 0, 0

            current = {
                'year':         year,
                'date':         display,
                'home':         team_name(home_raw),
                'homeScore':    hs,
                'awayScore':    as_,
                'away':         team_name(away_raw),
                'comp':         comp,
                'venue':        venue_raw or DEFAULT_VENUE,
                'homeScorers':  [],
                'homeAssists':  [],
                'awayScorers':  [],
                'awayAssists':  [],
            }
            continue

        # Goal row (old format): col1 is empty, col2=homeScorer, col3=homeAssist
        if current is None:
            continue
        if not ('外部' in current.get('comp','') and '两队' in current.get('comp','')):
            continue

        col3 = r[3].strip() if len(r) > 3 else ''
        # Offset detection: col3 has scorer (old format shifted)
        if col3 and col3 not in {'/', ''} and not re.match(r'^\d', col3):
            sc_h  = clean(col3)
            ast_h = clean(r[4]) if len(r) > 4 else ''
            sc_a  = clean(r[7]) if len(r) > 7 else ''
            ast_a = clean(r[8]) if len(r) > 8 else ''
        else:
            sc_h  = clean(r[4]) if len(r) > 4 else ''
            ast_h = clean(r[5]) if len(r) > 5 else ''
            sc_a  = clean(r[8]) if len(r) > 8 else ''
            ast_a = clean(r[9]) if len(r) > 9 else ''

        if sc_h:
            current['homeScorers'].append(sc_h)
            current['homeAssists'].append(ast_h)
        if sc_a:
            current['awayScorers'].append(sc_a)
            current['awayAssists'].append(ast_a)

    if current:
        matches.append(current)

    # Keep only 外部友谊赛（两队）with Royal Farmers as one side
    external = []
    for m in matches:
        if '外部' not in m['comp'] or '两队' not in m['comp']:
            continue
        rf_home = m['home'].startswith(RF_PREFIX)
        rf_away = m['away'].startswith(RF_PREFIX)
        if not rf_home and not rf_away:
            continue
        external.append(m)

    return external


def rf_perspective(m):
    """Return match stats from Royal Farmers' perspective."""
    rf_home = m['home'].startswith(RF_PREFIX)
    rf_score  = m['homeScore'] if rf_home else m['awayScore']
    opp_score = m['awayScore'] if rf_home else m['homeScore']
    opp       = m['away']      if rf_home else m['home']
    scorers   = m['homeScorers'] if rf_home else m['awayScorers']
    assists   = m['homeAssists'] if rf_home else m['awayAssists']
    result    = 'W' if rf_score > opp_score else ('L' if rf_score < opp_score else 'D')
    return {
        'date':       m['date'],
        'rfTeam':     m['home'] if rf_home else m['away'],
        'opp':        opp,
        'rfScore':    rf_score,
        'oppScore':   opp_score,
        'result':     result,
        'scorers':    scorers,
        'assists':    assists,
    }


def aggregate(processed_list):
    rec = dict(played=0, won=0, drawn=0, lost=0, gf=0, ga=0)
    scorer_cnt = defaultdict(int)
    assist_cnt  = defaultdict(int)
    for p in processed_list:
        rec['played'] += 1
        rec[{'W':'won','D':'drawn','L':'lost'}[p['result']]] += 1
        rec['gf'] += p['rfScore']
        rec['ga'] += p['oppScore']
        for name in p['scorers']:
            if name:
                scorer_cnt[name] += 1
        for name in p['assists']:
            if name:
                assist_cnt[name] += 1
    rec['gd'] = rec['gf'] - rec['ga']
    top_scorers = sorted(scorer_cnt.items(), key=lambda x: (-x[1], x[0]))[:10]
    top_assists = sorted(assist_cnt.items(),  key=lambda x: (-x[1], x[0]))[:10]
    return rec, top_scorers, top_assists


def build_js(stats):
    def record_js(r):
        return (f'{{played:{r["played"]},won:{r["won"]},drawn:{r["drawn"]},'
                f'lost:{r["lost"]},gf:{r["gf"]},ga:{r["ga"]},gd:{r["gd"]}}}')

    def players_js(lst, key):
        items = ','.join(f'{{name:"{n}",{key}:{c}}}' for n, c in lst)
        return f'[{items}]'

    def matches_js(lst):
        parts = []
        for p in lst:
            s = (f'{{date:"{p["date"]}",rfTeam:"{p["rfTeam"]}",opp:"{p["opp"]}",'
                 f'rfScore:{p["rfScore"]},oppScore:{p["oppScore"]},result:"{p["result"]}"}}')
            parts.append(s)
        return f'[{",".join(parts)}]'

    lines = ['const EXTERNAL_MATCH_STATS = {']
    lines.append('  seasons: [')
    for s in stats['seasons']:
        r, sc, ast = s['record'], s['scorers'], s['assists']
        lines.append(f'    {{season:"{s["season"]}",'
                     f'record:{record_js(r)},'
                     f'scorers:{players_js(sc,"goals")},'
                     f'assists:{players_js(ast,"assists")},'
                     f'matches:{matches_js(s["matches"])}}},')
    lines.append('  ],')

    r, sc, ast = stats['all']['record'], stats['all']['scorers'], stats['all']['assists']
    lines.append(f'  all:{{record:{record_js(r)},'
                 f'scorers:{players_js(sc,"goals")},'
                 f'assists:{players_js(ast,"assists")}}},')
    lines.append('};')
    return '\n'.join(lines)


# ── Main ──
print("⚽ 解析外部友谊赛（两队）数据 ...")
matches = parse_matches()
print(f"   共 {len(matches)} 场")

# Group by season
by_year = defaultdict(list)
for m in matches:
    by_year[m['year']].append(rf_perspective(m))

# Build per-season stats
season_stats = []
all_processed = []
for year in sorted(by_year.keys()):
    processed = by_year[year]
    rec, sc, ast = aggregate(processed)
    season_stats.append({
        'season':  year,
        'record':  rec,
        'scorers': sc,
        'assists': ast,
        'matches': sorted(processed, key=lambda x: x['date'], reverse=True),
    })
    all_processed.extend(processed)
    print(f"   {year}: {rec['played']}场 {rec['won']}胜{rec['drawn']}平{rec['lost']}负  "
          f"进{rec['gf']}失{rec['ga']}  "
          f"射手第1: {sc[0][0] if sc else '—'}({sc[0][1] if sc else 0}球)")

all_rec, all_sc, all_ast = aggregate(all_processed)

final = {
    'seasons': season_stats,
    'all': {'record': all_rec, 'scorers': all_sc, 'assists': all_ast},
}

if DRY_RUN:
    print("\n[dry-run] 未写入"); sys.exit(0)

new_block = build_js(final)

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

import re as re2
pat = re2.compile(r'const EXTERNAL_MATCH_STATS = \{.*?\};', re2.DOTALL)
if pat.search(src):
    src = pat.sub(new_block, src)
else:
    # Insert before window.RF_DATA
    src = src.replace('window.RF_DATA = {', new_block + '\n\nwindow.RF_DATA = {')
    # Register in RF_DATA export
    src = src.replace('window.RF_DATA = {', 'window.RF_DATA = { EXTERNAL_MATCH_STATS,')

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)
print(f"\n✅ EXTERNAL_MATCH_STATS 已写入 data.jsx（{len(season_stats)} 赛季，共 {len(all_processed)} 场）")
