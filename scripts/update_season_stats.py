#!/usr/bin/env python3
"""
Royal Farmers FC — 赛季榜单更新脚本
从 CSV 自动更新 data.jsx 中的：
  GOALS26 / ASSISTS26 / APPS26 / MATCH_COUNT
  GOALS_ALL / ASSISTS_ALL / APPS_ALL

用法：
    python3 scripts/update_season_stats.py
    python3 scripts/update_season_stats.py --dry-run
"""
import csv, re, sys, os, io

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
ROSTER_CSV  = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
GOALS_CSV   = os.path.join(DATA_DIR, "每场战报+总数据-总射手榜.csv")
ASSISTS_CSV = os.path.join(DATA_DIR, "每场战报+总数据-总助攻榜.csv")
APPS_CSV    = os.path.join(DATA_DIR, "每场战报+总数据-总出场数.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

TOP_N       = 10   # 2026赛季榜单 Top N
TOP_ALL     = 999  # 历史全员榜，不限制


def si(v):
    try: return int(float(v))
    except: return 0


def count_matches_from_roster():
    """从花名册 CSV 的日期列（格式 YYYYMMDD）统计截至今日的总场次"""
    import datetime
    today = datetime.date.today().strftime('%Y%m%d')
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        content = f.read()
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')
    headers = rows[hrow]
    count = sum(
        1 for h in headers
        if h.strip().isdigit() and len(h.strip()) == 8 and h.strip() <= today
    )
    return count


def read_roster():
    """
    读取花名册，返回：
      name_to_num: dict  name→jersey_num(str)
      players_2026: list  [{name, num, apps, goals, assists}]，仅 2026 有出场的球员
    """
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        content = f.read()
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')

    name_to_num  = {}
    players_2026 = []
    skip = {'合计', '总计', '名字', '姓名', ''}

    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        num  = r[4].strip() if len(r) > 4 else ''
        name_to_num[name] = num

        apps26    = si(r[29]) if len(r) > 29 else 0
        goals26   = si(r[30]) if len(r) > 30 else 0
        assists26 = si(r[31]) if len(r) > 31 else 0

        if apps26 > 0:
            players_2026.append({
                'name': name, 'num': num,
                'apps': apps26, 'goals': goals26, 'assists': assists26,
            })

    return name_to_num, players_2026


def read_ranking_csv(path, val_col, apps_col, total_col=None):
    """
    读取排名 CSV，返回 [{name, val, apps[, total]}]
    val_col: 目标数值列索引（进球/助攻/出场）
    """
    with open(path, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '排名')

    result = []
    skip = {'合计', '总计', '名字', '姓名', ''}
    for r in rows[hrow + 1:]:
        if not r or len(r) <= max(val_col, apps_col):
            continue
        name = r[1].strip() if len(r) > 1 else ''
        if not name or name in skip:
            continue
        val  = si(r[val_col])
        apps = si(r[apps_col])
        if val == 0:
            continue
        entry = {'name': name, 'val': val, 'apps': apps}
        if total_col is not None and len(r) > total_col:
            entry['total'] = si(r[total_col])
        result.append(entry)
    return result


def js_arr_goals26(lst):
    lines = ['const GOALS26 = [']
    for p in lst:
        lines.append(f'  {{name:"{p["name"]}",num:"{p["num"]}",goals:{p["goals"]},apps:{p["apps"]}}},')
    lines.append('];')
    return '\n'.join(lines)


def js_arr_assists26(lst):
    lines = ['const ASSISTS26 = [']
    for p in lst:
        lines.append(f'  {{name:"{p["name"]}",num:"{p["num"]}",assists:{p["assists"]},apps:{p["apps"]}}},')
    lines.append('];')
    return '\n'.join(lines)


def js_arr_apps26(lst, max_apps):
    lines = ['const APPS26 = [']
    for p in lst:
        pct = f'{p["apps"] / max_apps * 100:.2f}%' if max_apps > 0 else '0%'
        lines.append(f'  {{name:"{p["name"]}",num:"{p["num"]}",apps:{p["apps"]},pct:"{pct}"}},')
    lines.append('];')
    return '\n'.join(lines)


def js_arr_goals_all(lst, name_to_num):
    lines = ['const GOALS_ALL = [']
    for p in lst:
        num = name_to_num.get(p['name'], '')
        lines.append(f'  {{name:"{p["name"]}",num:"{num}",goals:{p["val"]},apps:{p["apps"]}}},')
    lines.append('];')
    return '\n'.join(lines)


def js_arr_assists_all(lst, name_to_num):
    lines = ['const ASSISTS_ALL = [']
    for p in lst:
        num = name_to_num.get(p['name'], '')
        lines.append(f'  {{name:"{p["name"]}",num:"{num}",assists:{p["val"]},apps:{p["apps"]}}},')
    lines.append('];')
    return '\n'.join(lines)


def js_arr_apps_all(lst, name_to_num, match_count):
    lines = ['const APPS_ALL = [']
    for p in lst:
        num = name_to_num.get(p['name'], '')
        pct = f'{p["val"] / match_count * 100:.1f}%' if match_count > 0 else '0%'
        lines.append(f'  {{name:"{p["name"]}",num:"{num}",apps:{p["val"]},total:{match_count},pct:"{pct}"}},')
    lines.append('];')
    return '\n'.join(lines)


# ── 评分榜配置 ──────────────────────────────────────────────────────────────
SEASON_APP_COLS    = {'2021': 9,  '2022': 13, '2023': 17, '2024': 21, '2025': 25, '2026': 29}
SEASON_RATING_COLS = {'2021': 12, '2022': 16, '2023': 20, '2024': 24, '2025': 28, '2026': 32}
SEASON_MATCHES     = {'2021': 68, '2022': 79, '2023': 97, '2024': 104, '2025': 94, '2026': 38}
RATING_THRESHOLD   = 0.25   # 出场 > 赛季总场次 × 25% 才上榜

PHOTO_MAP = {
    "10": "assets/players/10号姜珂.jpeg",
    "14": "assets/players/14号夏浩.jpeg",
    "17": "assets/players/17号张伟.jpeg",
    "18": "assets/players/18号黄纲.jpeg",
    "22": "assets/players/22号麦超.jpeg",   # 同号22：麦超/鲍梁剑，名称覆盖见 NAME_PHOTO_OVERRIDE
    "24": "assets/players/24号陆晓巍.jpeg",
    "25": "assets/players/25号鲁尼.jpeg",
    "33": "assets/players/33号季贝赢.jpeg",
    "38": "assets/players/38号鲍澜云.jpeg",
    "26": "assets/players/38号鲍澜云.jpeg",
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

# 同号码冲突时，名称优先覆盖（如22号有麦超和鲍梁剑）
NAME_PHOTO_OVERRIDE = {
    "鲍梁剑": "assets/players/22号鲍梁剑.jpeg",
}

def get_photo(name, num):
    """按名称→号码顺序查找照片路径"""
    if name in NAME_PHOTO_OVERRIDE:
        return NAME_PHOTO_OVERRIDE[name]
    p = PHOTO_MAP.get(num)
    return p

def sf(v):
    """安全转浮点，失败返回 None"""
    try:
        f = float(v)
        return f if f != 0 else None
    except:
        return None


def read_ratings(name_to_num):
    """
    从花名册读取全量球员评分数据，返回：
      all_time:    [{name,num,apps,rating}]  历史加权平均，出场>总场次*25%
      by_season:   {'2026': [...], '2025': [...], ...}  各赛季，出场>赛季场次*25%
    """
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        content = f.read()
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')
    skip = {'合计', '总计', '名字', '姓名', ''}

    seasons = list(SEASON_APP_COLS.keys())   # ['2021','2022',...]
    total_matches = sum(SEASON_MATCHES.values())

    all_time_list  = []
    by_season      = {yr: [] for yr in seasons}

    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        num  = name_to_num.get(name, r[4].strip() if len(r) > 4 else '')

        # ── 各赛季 ──
        season_data = {}
        for yr in seasons:
            ac = SEASON_APP_COLS[yr]
            rc = SEASON_RATING_COLS[yr]
            apps   = si(r[ac])   if len(r) > ac else 0
            rating = sf(r[rc].strip()) if len(r) > rc else None
            season_data[yr] = {'apps': apps, 'rating': rating}

            thresh = SEASON_MATCHES[yr] * RATING_THRESHOLD
            if apps > thresh and rating is not None:
                by_season[yr].append({'name': name, 'num': num, 'apps': apps, 'rating': rating})

        # ── 历史加权平均 ──
        # 官方总出场数来自花名册 col 6（与 APPS_ALL 一致），而非赛季累加
        official_apps = si(r[6]) if len(r) > 6 else 0
        weighted_sum  = sum(
            season_data[yr]['apps'] * season_data[yr]['rating']
            for yr in seasons
            if season_data[yr]['rating'] is not None and season_data[yr]['apps'] > 0
        )
        valid_apps = sum(
            season_data[yr]['apps']
            for yr in seasons
            if season_data[yr]['rating'] is not None and season_data[yr]['apps'] > 0
        )
        if valid_apps > 0:
            w_rating = weighted_sum / valid_apps
        else:
            continue

        thresh_all = total_matches * RATING_THRESHOLD
        if official_apps > thresh_all:
            all_time_list.append({'name': name, 'num': num, 'apps': official_apps, 'rating': round(w_rating, 2)})

    # 排序：评分从高到低
    all_time_list.sort(key=lambda p: p['rating'], reverse=True)
    for yr in seasons:
        by_season[yr].sort(key=lambda p: p['rating'], reverse=True)

    return all_time_list, by_season


def js_arr_ratings(var_name, lst, name_to_num):
    """生成评分榜 JS 常量块"""
    lines = [f'const {var_name} = [']
    for p in lst:
        num   = p['num']
        photo = get_photo(p['name'], num)
        photo_str = f'"{photo}"' if photo else 'null'
        lines.append(
            f'  {{name:"{p["name"]}",num:"{num}",photo:{photo_str},'
            f'apps:{p["apps"]},rating:{p["rating"]:.2f}}},'
        )
    lines.append('];')
    return '\n'.join(lines)


def replace_block(src, var_name, new_block):
    """替换 data.jsx 中 `const VAR_NAME = [...]` 块"""
    pattern = re.compile(r'const ' + re.escape(var_name) + r' = \[.*?\];', re.DOTALL)
    m = pattern.search(src)
    if not m:
        print(f'  ⚠️  未找到 {var_name} 块，跳过')
        return src
    return src[:m.start()] + new_block + src[m.end():]


def replace_match_count(src, count):
    return re.sub(r'const MATCH_COUNT = \d+;', f'const MATCH_COUNT = {count};', src)


# ── Main ──
print("📋 读取花名册 CSV ...")
name_to_num, players_2026 = read_roster()

print(f"   2026赛季有出场球员：{len(players_2026)} 人")

# 2026 榜单
goals26   = sorted(players_2026, key=lambda p: p['goals'],   reverse=True)[:TOP_N]
assists26 = sorted(players_2026, key=lambda p: p['assists'], reverse=True)[:TOP_N]
apps26    = sorted(players_2026, key=lambda p: p['apps'],    reverse=True)[:TOP_N]
max_apps26 = apps26[0]['apps'] if apps26 else 1

print("\n📋 读取历史排名 CSV ...")
goals_all_raw   = read_ranking_csv(GOALS_CSV,   val_col=2, apps_col=3)
assists_all_raw = read_ranking_csv(ASSISTS_CSV, val_col=2, apps_col=3)
apps_all_raw    = read_ranking_csv(APPS_CSV,    val_col=2, apps_col=2, total_col=3)

# MATCH_COUNT = 花名册 CSV 日期列数量（截至今日），比总出场数.csv 更新及时
match_count = count_matches_from_roster()
print(f"   总场次 MATCH_COUNT = {match_count}")
print(f"   历史射手榜：{len(goals_all_raw)} 人")
print(f"   历史助攻榜：{len(assists_all_raw)} 人")
print(f"   历史出场榜：{len(apps_all_raw)} 人")

# 打印 2026 榜单预览
print(f"\n🥅 GOALS26 Top5：", [(p['name'], p['goals']) for p in goals26[:5]])
print(f"👟 ASSISTS26 Top5：", [(p['name'], p['assists']) for p in assists26[:5]])
print(f"📅 APPS26 Top5：",   [(p['name'], p['apps']) for p in apps26[:5]])

# ── 评分榜 ──
print("\n⭐ 计算评分榜 ...")
ratings_all, ratings_by_season = read_ratings(name_to_num)
print(f"   历史评分榜：{len(ratings_all)} 人（门槛>{int(sum(SEASON_MATCHES.values())*RATING_THRESHOLD)}场）")
for yr in ['2026','2025','2024','2023','2022','2021']:
    lst = ratings_by_season[yr]
    print(f"   {yr}评分榜：{len(lst)} 人  Top3: {[(p['name'],p['rating']) for p in lst[:3]]}")

if DRY_RUN:
    print("\n[dry-run] 未写入文件")
    sys.exit(0)

# 读取并更新 data.jsx
with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

src = replace_block(src, 'GOALS26',   js_arr_goals26(goals26))
src = replace_block(src, 'ASSISTS26', js_arr_assists26(assists26))
src = replace_block(src, 'APPS26',    js_arr_apps26(apps26, max_apps26))
src = replace_match_count(src, match_count)
src = replace_block(src, 'GOALS_ALL',   js_arr_goals_all(goals_all_raw, name_to_num))
src = replace_block(src, 'ASSISTS_ALL', js_arr_assists_all(assists_all_raw, name_to_num))
src = replace_block(src, 'APPS_ALL',    js_arr_apps_all(apps_all_raw, name_to_num, match_count))

# ── 写入评分榜 ──
def upsert_block(src, var_name, new_block):
    """替换已有块，或在 RECORDS = { 前插入"""
    pat = re.compile(r'const ' + re.escape(var_name) + r' = \[.*?\];', re.DOTALL)
    if pat.search(src):
        return pat.sub(new_block, src)
    # 插入到 STREAK_RECORDS 之前（保持顺序）
    return src.replace('const STREAK_RECORDS', new_block + '\n\nconst STREAK_RECORDS')

src = upsert_block(src, 'RATINGS_ALL',  js_arr_ratings('RATINGS_ALL',  ratings_all,                name_to_num))
for yr in ['2026','2025','2024','2023','2022','2021']:
    src = upsert_block(src, f'RATINGS_{yr}', js_arr_ratings(f'RATINGS_{yr}', ratings_by_season[yr], name_to_num))

# 确保 RATINGS_* 在 window.RF_DATA 导出里
rating_vars = ['RATINGS_ALL'] + [f'RATINGS_{yr}' for yr in ['2026','2025','2024','2023','2022','2021']]
export_line = src[src.find('window.RF_DATA'):]
for rv in rating_vars:
    if rv not in export_line:
        src = src.replace('window.RF_DATA = {', f'window.RF_DATA = {{ {rv},')

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ data.jsx 已更新：")
print(f"   GOALS26={len(goals26)} ASSISTS26={len(assists26)} APPS26={len(apps26)}")
print(f"   GOALS_ALL={len(goals_all_raw)} ASSISTS_ALL={len(assists_all_raw)} APPS_ALL={len(apps_all_raw)}")
print(f"   MATCH_COUNT={match_count}")
print(f"   RATINGS_ALL={len(ratings_all)} + 各赛季评分榜已写入")
