#!/usr/bin/env python3
"""
Royal Farmers FC — PLAYERS 数组同步脚本
从花名册.csv 更新 data.jsx PLAYERS 块中每个球员的：
  apps / goals / assists / rating（career totals）
  seasons[]（逐赛季数据，只含有出场记录的年份）

不修改：num / name / pos / birth / nation / photo（固定字段）

用法：
    python3 scripts/update_players.py
    python3 scripts/update_players.py --dry-run
"""
import csv, io, re, sys, os, json

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
ROSTER_CSV  = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

# 花名册赛季列映射（每赛季4列：出场/进球/助攻/评分）
SEASONS_MAP = {
    2021: (9,  10, 11, 12),
    2022: (13, 14, 15, 16),
    2023: (17, 18, 19, 20),
    2024: (21, 22, 23, 24),
    2025: (25, 26, 27, 28),
    2026: (29, 30, 31, 32),
}


def si(v):
    try: return int(float(v))
    except: return 0


def sf(v):
    try: return round(float(v), 2)
    except: return None


def read_roster():
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        content = f.read()
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')
    skip = {'合计', '总计', '名字', '姓名', ''}
    data = {}
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        career_apps    = si(r[6])  if len(r) > 6  else 0
        career_goals   = si(r[7])  if len(r) > 7  else 0
        career_assists = si(r[8])  if len(r) > 8  else 0
        career_rating  = sf(r[5])  if len(r) > 5  else None  # 团队总成绩

        seasons = []
        for yr, (ca, cg, css, cr) in SEASONS_MAP.items():
            a  = si(r[ca])  if len(r) > ca  else 0
            g  = si(r[cg])  if len(r) > cg  else 0
            s  = si(r[css]) if len(r) > css else 0
            rt = sf(r[cr])  if len(r) > cr  else None
            if a > 0 or g > 0 or s > 0:
                entry = {'year': str(yr), 'apps': a, 'goals': g, 'assists': s}
                if rt is not None:
                    entry['rating'] = rt
                seasons.append(entry)

        data[name] = {
            'apps': career_apps, 'goals': career_goals,
            'assists': career_assists, 'rating': career_rating,
            'seasons': seasons,
        }
    return data


def seasons_js(seasons):
    parts = []
    for s in seasons:
        kv = ','.join(
            f'{k}:{json.dumps(v) if isinstance(v, str) else v}'
            for k, v in s.items()
        )
        parts.append('{' + kv + '}')
    return '[' + ','.join(parts) + ']'


def update_player_line(line, roster):
    """替换一行 PLAYERS 数据中的统计字段，返回 (new_line, changed, name)"""
    m = re.search(r'name:\s*"([^"]+)"', line)
    if not m:
        return line, False, None
    name = m.group(1)
    if name not in roster:
        return line, False, name

    d = roster[name]
    rating_str = str(d['rating']) if d['rating'] is not None else '0'
    # 确保 rating 有小数点（JS 兼容）
    if '.' not in rating_str:
        rating_str += '.0'

    new_stats = (
        f'apps: {d["apps"]}, goals: {d["goals"]}, '
        f'assists: {d["assists"]}, rating: {rating_str}, '
        f'seasons: {seasons_js(d["seasons"])}'
    )

    # 替换 apps...seasons: [...] 部分
    pattern = r'apps:\s*\d+,\s*goals:\s*\d+,\s*assists:\s*\d+,\s*rating:\s*[\d.]+,\s*seasons:\s*\[[^\]]*(?:\[[^\]]*\][^\]]*)*\]'
    new_line, count = re.subn(pattern, new_stats, line)
    changed = count > 0 and new_line != line
    return new_line, changed, name


# ── Main ──
print("📋 读取花名册 CSV ...")
roster = read_roster()
print(f"   花名册球员数：{len(roster)}")

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

# 找 PLAYERS 块范围
players_start = src.index('const PLAYERS = [')
players_end   = src.index('\n];', players_start) + 3

header = src[:players_start + len('const PLAYERS = [')]
footer = src[players_end:]
block_lines = src[players_start + len('const PLAYERS = ['):players_end - 2].split('\n')

updated_lines = []
changes = []
not_found = []

for line in block_lines:
    new_line, changed, name = update_player_line(line, roster)
    updated_lines.append(new_line)
    if changed:
        changes.append(name)
    elif name and name not in roster:
        not_found.append(name)

print(f"\n✏️  更新球员：{len(changes)} 名")
for n in changes:
    d = roster[n]
    print(f"   {n}: apps={d['apps']} goals={d['goals']} assists={d['assists']}")

if not_found:
    print(f"\n⚠️  PLAYERS中有但花名册中无（已略过）：{not_found}")

if DRY_RUN:
    print("\n[dry-run] 未写入文件")
    sys.exit(0)

new_block = 'const PLAYERS = [' + '\n'.join(updated_lines) + '\n];'
new_src = header[:-len('const PLAYERS = [')] + new_block + footer

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(new_src)

print(f"\n✅ data.jsx PLAYERS 已更新（{len(changes)} 名球员同步）")
