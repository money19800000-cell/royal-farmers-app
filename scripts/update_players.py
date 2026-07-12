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
    headers = rows[hrow]
    # 列33+ 是逐场评分列（日期格式 YYYYMMDD），从最新到最旧排列
    import datetime
    today = datetime.date.today().strftime('%Y%m%d')
    match_cols = [i for i, h in enumerate(headers)
                  if h.strip().isdigit() and len(h.strip()) == 8 and h.strip() <= today]
    recent_50_cols = match_cols[:50]  # 最近50场（列已按新→旧排列）

    skip = {'合计', '总计', '名字', '姓名', ''}
    data = {}
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        pos            = r[2].strip() if len(r) > 2 else ''
        num            = r[4].strip() if len(r) > 4 else ''
        career_apps    = si(r[6])  if len(r) > 6  else 0
        career_goals   = si(r[7])  if len(r) > 7  else 0
        career_assists = si(r[8])  if len(r) > 8  else 0
        career_rating  = sf(r[5])  if len(r) > 5  else None  # 团队总成绩

        # 最近50场出场次数（值非空 = 有出场）
        r50 = sum(1 for ci in recent_50_cols if len(r) > ci and r[ci].strip() != '')

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
            'num': num, 'pos': pos,
            'apps': career_apps, 'goals': career_goals,
            'assists': career_assists, 'rating': career_rating,
            'r50': r50,
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
        f'assists: {d["assists"]}, rating: {rating_str}, r50: {d["r50"]}, '
        f'seasons: {seasons_js(d["seasons"])}'
    )

    # 替换 apps...seasons: [...] 部分（兼容有/无 r50 字段的旧格式）
    pattern = r'apps:\s*\d+,\s*goals:\s*\d+,\s*assists:\s*\d+,\s*rating:\s*[\d.]+,(?:\s*r50:\s*\d+,)?\s*seasons:\s*\[[^\]]*(?:\[[^\]]*\][^\]]*)*\]'
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

# ── 补全 PLAYER_LOOKUP：将花名册里缺失的球员自动加入 ──────────────────────
# 条件：(有球衣号码 OR 出场≥5次) AND 未在 PLAYERS 中
print("\n🔍 检查 PLAYER_LOOKUP 缺失球员 ...")

# 提取 PLAYERS 中已有的名字（正确处理 name: "..." 格式）
players_names_in_src = set(re.findall(r'name:\s*"([^"]+)"',
    src[src.index('const PLAYERS = ['):src.index('\n];', src.index('const PLAYERS = [')) + 3]))

# 提取 PLAYER_LOOKUP 中已有的名字
lookup_start = src.index('const PLAYER_LOOKUP = {')
lookup_end   = src.index('\n};', lookup_start) + 3
lookup_names_in_src = set(re.findall(r'"([^"]+)":\s*\{name:', src[lookup_start:lookup_end]))

known_names = players_names_in_src | lookup_names_in_src
known_names_lower = {n.lower() for n in known_names}  # for case-insensitive dedup

def lookup_entry_js(name, d):
    """生成 PLAYER_LOOKUP 的单条 JS 字符串"""
    num_val  = int(d['num']) if d['num'].isdigit() else f'"{d["num"]}"' if d['num'] else '""'
    pos_val  = d['pos'] or '—'
    seasons_str = seasons_js(d['seasons'])
    rating_str  = str(d['rating']) if d['rating'] is not None else '0'
    if '.' not in str(rating_str): rating_str += '.0'
    esc_name = name.replace('"', '\\"')
    return (
        f'  "{esc_name}": {{name:"{esc_name}",num:{num_val},pos:"{pos_val}",'
        f'birth:"—",nation:"中国",apps:{d["apps"]},goals:{d["goals"]},'
        f'assists:{d["assists"]},r50:{d["r50"]},seasons:{seasons_str}}},'
    )

# 找出需要补充的球员（有号码 OR 出场≥5次，且不在已知集合里）
to_add = []
for name, d in roster.items():
    if name.lower() in known_names_lower:  # case-insensitive: "Joe" won't re-add "JOE"
        continue
    has_num = bool(d['num'])
    if has_num or d['apps'] >= 1:  # lowered from 5 → 1: any player who has appeared
        to_add.append((name, d))

to_add.sort(key=lambda x: -x[1]['apps'])  # 按出场数降序
print(f"   需要补充到 PLAYER_LOOKUP：{len(to_add)} 人")
for n, d in to_add[:10]:
    print(f"   + {d['num']:4s}号 {n:15s} 出场:{d['apps']}")
if len(to_add) > 10:
    print(f"   ... 另 {len(to_add)-10} 人")

if DRY_RUN:
    print("\n[dry-run] 未写入文件")
    sys.exit(0)

new_block = 'const PLAYERS = [' + '\n'.join(updated_lines) + '\n];'
new_src   = header[:-len('const PLAYERS = [')] + new_block + footer

# ── 更新 PLAYER_LOOKUP 中已有条目的 r50（以及 apps/goals/assists/seasons）──
lk_start = new_src.index('const PLAYER_LOOKUP = {')
lk_end   = new_src.index('\n};', lk_start)
lk_block = new_src[lk_start:lk_end + 3]

lookup_updated = 0
def update_lookup_line(line):
    global lookup_updated
    m = re.search(r'name:"([^"]+)"', line)
    if not m:
        return line
    name = m.group(1)
    if name not in roster:
        return line
    d = roster[name]
    # 整行重新生成，同步 apps/goals/assists/seasons/r50
    new_line = lookup_entry_js(name, d)
    if new_line.rstrip(',') != line.rstrip(','):
        lookup_updated += 1
    return new_line

lk_lines = lk_block.split('\n')
lk_lines = [update_lookup_line(l) for l in lk_lines]
new_lk_block = '\n'.join(lk_lines)
new_src = new_src[:lk_start] + new_lk_block + new_src[lk_end + 3:]

# 将新条目插入 PLAYER_LOOKUP（在最后一个已有条目之后、 }; 之前）
if to_add:
    new_entries = '\n'.join(lookup_entry_js(name, d) for name, d in to_add)
    lk_start2 = new_src.index('const PLAYER_LOOKUP = {')
    lk_end2   = new_src.index('\n};', lk_start2)
    new_src   = new_src[:lk_end2] + '\n' + new_entries + new_src[lk_end2:]

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(new_src)

print(f"\n✅ data.jsx 已更新：PLAYERS {len(changes)} 名同步，PLAYER_LOOKUP 更新 {lookup_updated} 名 / 新增 {len(to_add)} 名")
