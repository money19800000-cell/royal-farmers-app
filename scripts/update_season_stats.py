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
RATE_RECORD_THRESHOLD = 0.40   # 场均纪录门槛：出场 > 赛季总场次 × 40%

SEASON_GOAL_COLS = {'2021': 10, '2022': 14, '2023': 18, '2024': 22, '2025': 26, '2026': 30}
SEASON_ASST_COLS = {'2021': 11, '2022': 15, '2023': 19, '2024': 23, '2025': 27, '2026': 31}

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

# 同号码冲突时，名称优先覆盖（如22号有麦超和鲍梁剑；6号有陶骏和朱寿卿）
NAME_PHOTO_OVERRIDE = {
    "鲍梁剑": "assets/players/22号鲍梁剑.jpeg",
    "朱寿卿": "assets/players/56号朱寿卿.jpeg",
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


def compute_season_rate_records():
    """
    计算赛季场均进球/助攻最高纪录，门槛：出场 > 赛季场次 × 40%
    返回 (best_gpg, best_apg)，每项含 rate/name/num/yr/ctx/goals_or_assists
    """
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        content = f.read()
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')
    skip = {'合计', '总计', '名字', '姓名', ''}

    best_gpg = {'rate': 0.0, 'name': '', 'num': '', 'yr': '', 'goals': 0, 'apps': 0}
    best_apg = {'rate': 0.0, 'name': '', 'num': '', 'yr': '', 'assists': 0, 'apps': 0}

    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        num  = r[4].strip() if len(r) > 4 else ''
        for yr, match_count in SEASON_MATCHES.items():
            ac = SEASON_APP_COLS[yr]
            gc = SEASON_GOAL_COLS[yr]
            sc = SEASON_ASST_COLS[yr]
            try:
                apps   = int(r[ac]) if len(r) > ac and r[ac].strip().isdigit() else 0
                goals  = int(r[gc]) if len(r) > gc and r[gc].strip().isdigit() else 0
                assists= int(r[sc]) if len(r) > sc and r[sc].strip().isdigit() else 0
            except Exception:
                continue
            if apps <= match_count * RATE_RECORD_THRESHOLD:
                continue
            gpg = goals   / apps
            apg = assists / apps
            if gpg > best_gpg['rate']:
                best_gpg = {'rate': gpg, 'name': name, 'num': num,
                            'yr': yr, 'goals': goals, 'apps': apps}
            if apg > best_apg['rate']:
                best_apg = {'rate': apg, 'name': name, 'num': num,
                            'yr': yr, 'assists': assists, 'apps': apps}

    return best_gpg, best_apg


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

# ── 场均纪录 ──
print("\n📊 计算赛季场均纪录（门槛>40%）...")
best_gpg, best_apg = compute_season_rate_records()
print(f"   场均进球最高: {best_gpg['name']}({best_gpg['num']}号) {best_gpg['yr']}赛季 "
      f"{best_gpg['goals']}球/{best_gpg['apps']}场 = {best_gpg['rate']:.2f}球/场")
print(f"   场均助攻最高: {best_apg['name']}({best_apg['num']}号) {best_apg['yr']}赛季 "
      f"{best_apg['assists']}助/{best_apg['apps']}场 = {best_apg['rate']:.2f}次/场")

# ── 评分榜 ──
print("\n⭐ 计算评分榜 ...")
ratings_all, ratings_by_season = read_ratings(name_to_num)
print(f"   历史评分榜：{len(ratings_all)} 人（门槛>{int(sum(SEASON_MATCHES.values())*RATING_THRESHOLD)}场）")
for yr in ['2026','2025','2024','2023','2022','2021']:
    lst = ratings_by_season[yr]
    print(f"   {yr}评分榜：{len(lst)} 人  Top3: {[(p['name'], round(p['rating'],2)) for p in lst[:3]]}")

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

# ── 更新 RECORDS.season 场均纪录 ──
def update_records_season_rates(src, gpg, apg, ntn):
    """在 RECORDS.season 数组中插入/替换场均进球和场均助攻纪录"""
    gpg_photo = get_photo(gpg['name'], gpg['num'])
    apg_photo = get_photo(apg['name'], apg['num'])
    gpg_photo_str = f'"{gpg_photo}"' if gpg_photo else 'null'
    apg_photo_str = f'"{apg_photo}"' if apg_photo else 'null'

    gpg_entry = (
        f'{{label:"单赛季场均进球",icon:"⚽",value:{gpg["rate"]:.2f},unit:"球/场",'
        f'holder:"{gpg["name"]}",num:"{gpg["num"]}",'
        f'ctx:"{gpg["yr"]}赛季 · {gpg["apps"]}场/{gpg["goals"]}球",'
        f'photo:{gpg_photo_str}}}'
    )
    apg_entry = (
        f'{{label:"单赛季场均助攻",icon:"👟",value:{apg["rate"]:.2f},unit:"次/场",'
        f'holder:"{apg["name"]}",num:"{apg["num"]}",'
        f'ctx:"{apg["yr"]}赛季 · {apg["apps"]}场/{apg["assists"]}助",'
        f'photo:{apg_photo_str}}}'
    )
    # 替换已有条目
    import re as _re
    for old_pat, new_entry in [
        (r'\{label:"单赛季场均进球"[^}]*\}', gpg_entry),
        (r'\{label:"单赛季场均助攻"[^}]*\}', apg_entry),
    ]:
        if _re.search(old_pat, src):
            src = _re.sub(old_pat, new_entry, src)
        else:
            # 在 season: [ 的最后一项前插入
            src = src.replace(
                '  ],\n  match:',
                f'    {new_entry},\n  ],\n  match:'
            )
    return src

src = update_records_season_rates(src, best_gpg, best_apg, name_to_num)

# ── 新增：单月最多进球 / 单月最多助攻 / 赛季场均评分最高 ──────────────────
def compute_monthly_and_rating_records(src):
    """从 data.jsx 中的 MONTHLY_HISTORY 和 RATINGS_* 计算三条新纪录"""
    # 1. 从 MONTHLY_HISTORY 找单月最多进球 / 单月最多助攻
    mh = re.search(r'const MONTHLY_HISTORY = \[(.*?)\];', src, re.DOTALL)
    best_mg = best_ma = None  # (count, name, num, period, apps_in_month)
    if mh:
        for mt in re.finditer(
            r'period: "([^"]+)", goals: \[([^\]]*)\], assists: \[([^\]]*)\], apps: \[([^\]]*)\]',
            mh.group(1)
        ):
            period = mt.group(1)
            # 进球
            top_goals = re.findall(r'name:"([^"]+)", num:"([^"]*)", goals:(\d+)', mt.group(2))
            if top_goals:
                n, nu, g = top_goals[0]; g = int(g)
                # 找该球员在同月的出场数
                ap_list = re.findall(r'name:"([^"]+)", num:"[^"]*", apps:(\d+)', mt.group(4))
                ap = next((int(v) for nm, v in ap_list if nm == n), 0)
                if best_mg is None or g > best_mg[0]:
                    best_mg = (g, n, nu, period, ap)
            # 助攻
            top_assists = re.findall(r'name:"([^"]+)", num:"([^"]*)", assists:(\d+)', mt.group(3))
            if top_assists:
                n, nu, a = top_assists[0]; a = int(a)
                ap_list = re.findall(r'name:"([^"]+)", num:"[^"]*", apps:(\d+)', mt.group(4))
                ap = next((int(v) for nm, v in ap_list if nm == n), 0)
                if best_ma is None or a > best_ma[0]:
                    best_ma = (a, n, nu, period, ap)

    # 2. 从 RATINGS_* 找赛季场均评分最高（出场≥30）
    best_rat = None  # (rating, name, num, yr, apps)
    for yr in ['2021','2022','2023','2024','2025','2026']:
        rm = re.search(rf'const RATINGS_{yr} = \[(.*?)\];', src, re.DOTALL)
        if not rm: continue
        for m2 in re.finditer(
            r'name:"([^"]+)",num:"([^"]*)",photo:[^,]+,apps:(\d+),rating:([\d.\-]+)',
            rm.group(1)
        ):
            n, nu, apps_s, rat_s = m2.groups()
            if int(apps_s) >= 30 and float(rat_s) > (best_rat[0] if best_rat else -999):
                best_rat = (float(rat_s), n, nu, yr, int(apps_s))

    return best_mg, best_ma, best_rat


def update_records_monthly_rating(src, best_mg, best_ma, best_rat):
    """在 RECORDS.season 末尾插入/替换三条月度/评分纪录"""
    def make_photo_str(name, num):
        ph = get_photo(name, num)
        return f'"{ph}"' if ph else 'null'

    entries_to_upsert = []
    if best_mg:
        g, n, nu, period, ap = best_mg
        ap_ctx = f" · {ap}场" if ap else ""
        entries_to_upsert.append((
            '单月最多进球',
            f'{{label:"单月最多进球",icon:"🌋",value:{g},unit:"球",'
            f'holder:"{n}",num:"{nu}",'
            f'ctx:"{period}{ap_ctx}",'
            f'photo:{make_photo_str(n, nu)}}}'
        ))
    if best_ma:
        a, n, nu, period, ap = best_ma
        ap_ctx = f" · {ap}场" if ap else ""
        entries_to_upsert.append((
            '单月最多助攻',
            f'{{label:"单月最多助攻",icon:"🎯",value:{a},unit:"次",'
            f'holder:"{n}",num:"{nu}",'
            f'ctx:"{period}{ap_ctx}",'
            f'photo:{make_photo_str(n, nu)}}}'
        ))
    if best_rat:
        rat, n, nu, yr, apps = best_rat
        entries_to_upsert.append((
            '赛季场均评分最高',
            f'{{label:"赛季场均评分最高",icon:"⭐",value:{rat:.2f},unit:"分/场",'
            f'holder:"{n}",num:"{nu}",'
            f'ctx:"{yr}赛季 · {apps}场 · 出场≥30",'
            f'photo:{make_photo_str(n, nu)}}}'
        ))

    for label, new_entry in entries_to_upsert:
        old_pat = rf'\{{label:"{re.escape(label)}"[^}}]*\}}'
        if re.search(old_pat, src):
            src = re.sub(old_pat, new_entry, src)
        else:
            src = src.replace(
                '  ],\n  match:',
                f'    {new_entry},\n  ],\n  match:'
            )
    return src


best_mg, best_ma, best_rat = compute_monthly_and_rating_records(src)
if best_mg:  print(f"   单月最多进球: {best_mg[1]} {best_mg[3]} {best_mg[0]}球 {best_mg[4]}场")
if best_ma:  print(f"   单月最多助攻: {best_ma[1]} {best_ma[3]} {best_ma[0]}次 {best_ma[4]}场")
if best_rat: print(f"   赛季场均评分: {best_rat[1]} {best_rat[3]}赛季 {best_rat[0]:.2f} {best_rat[4]}场")

src = update_records_monthly_rating(src, best_mg, best_ma, best_rat)

# ── 更新 RECORDS.career（生涯三项纪录）──────────────────────────────────────
def update_records_career(src, goals_raw, assists_raw, apps_raw, ntn):
    """用 GOALS_ALL/ASSISTS_ALL/APPS_ALL 的第一条数据更新 RECORDS.career 中的生涯三项纪录"""
    if not goals_raw or not assists_raw or not apps_raw:
        return src
    # 第一名（姜珂）的各项数据
    top_g = goals_raw[0];   g_name = top_g['name'];   g_val = top_g['val'];   g_apps = top_g['apps']
    top_a = assists_raw[0]; a_name = top_a['name'];   a_val = top_a['val'];   a_apps = top_a['apps']
    top_p = apps_raw[0];    p_name = top_p['name'];   p_apps = top_p['val']

    # 生涯最多进球
    src = re.sub(
        r'(\{label:"生涯最多进球"[^}]*value:)\d+',
        lambda m: m.group(0).replace(m.group(1) + m.group(0).split('value:')[1].split(',')[0],
                                      m.group(1) + str(g_val)), src)
    # 生涯最多助攻
    src = re.sub(
        r'(\{label:"生涯最多助攻"[^}]*value:)\d+',
        lambda m: m.group(0).replace(m.group(1) + m.group(0).split('value:')[1].split(',')[0],
                                      m.group(1) + str(a_val)), src)
    # 生涯最多出场 ctx（包含进球+助攻数）
    src = re.sub(
        r'(label:"生涯最多出场"[^}]*ctx:")[^"]*"',
        f'\\g<1>{g_val}球 · {a_val}助"', src)
    # 最高助攻效率 value + ctx（用 a_apps 和 a_val 重算）
    if a_apps > 0:
        eff = round(a_val / a_apps, 2)
        src = re.sub(
            r'(label:"最高助攻效率"[^}]*value:)"[\d.]+"',
            f'\\g<1>"{eff}"', src)
        src = re.sub(
            r'(label:"最高助攻效率"[^}]*ctx:")[^"]*"',
            f'\\g<1>出场40+ · {a_val}次/{a_apps}场"', src)
    # 非No.10最多进球：找第一个不是 g_name 的进球榜球员
    non10_g = next((p for p in goals_raw if p['name'] != g_name), None)
    if non10_g:
        src = re.sub(
            r'(label:"非No\.10最多进球"[^}]*value:)\d+',
            lambda m: m.group(0).replace(m.group(1) + m.group(0).split('value:')[1].split(',')[0],
                                          m.group(1) + str(non10_g['val'])), src)
        # 非No.10最多出场 ctx（进球数）
        src = re.sub(
            r'(label:"非No\.10最多出场"[^}]*ctx:")[^"]*"',
            f'\\g<1>{non10_g["val"]}球"', src)
    return src


# 精确替换：直接用字符串匹配
def update_records_career_precise(src, goals_raw, assists_raw, apps_raw):
    """精确替换 RECORDS.career 中几个关键数值，避免正则复杂性"""
    if not goals_raw or not assists_raw:
        return src
    g_val  = goals_raw[0]['val']
    g_apps = goals_raw[0]['apps']
    a_val  = assists_raw[0]['val']
    a_apps = assists_raw[0]['apps']
    g_name = goals_raw[0]['name']
    non10  = next((p for p in goals_raw if p['name'] != g_name), None)

    import datetime
    now_ym = datetime.date.today().strftime('%Y年%-m月')

    # 替换生涯最多进球 value
    src = re.sub(r'(label:"生涯最多进球",icon:"⚽",value:)\d+', rf'\g<1>{g_val}', src)
    # 替换生涯最多助攻 value
    src = re.sub(r'(label:"生涯最多助攻",icon:"👟",value:)\d+', rf'\g<1>{a_val}', src)
    # 替换生涯最多出场 ctx
    src = re.sub(r'(label:"生涯最多出场"[^}]*ctx:")[^"]*"', rf'\g<1>{g_val}球 · {a_val}助"', src)
    # 替换最高助攻效率 value + ctx
    if a_apps > 0:
        eff = round(a_val / a_apps, 2)
        src = re.sub(r'(label:"最高助攻效率"[^}]*value:)"[\d.]+"', rf'\g<1>"{eff}"', src)
        src = re.sub(r'(label:"最高助攻效率"[^}]*ctx:")[^"]*"',
                     rf'\g<1>出场40+ · {a_val}次/{a_apps}场"', src)
    # 替换非No.10最多进球 value + 非No.10最多出场 ctx
    if non10:
        src = re.sub(r'(label:"非No\.10最多进球"[^}]*value:)\d+', rf'\g<1>{non10["val"]}', src)
        src = re.sub(r'(label:"非No\.10最多出场"[^}]*ctx:")[^"]*"', rf'\g<1>{non10["val"]}球"', src)
    return src


# ── 更新 RECORDS.club 历史总场次 ────────────────────────────────────────────
def update_records_club_total(src, mc):
    """更新 RECORDS.club 中的历史总场次 value 和 ctx 月份"""
    import datetime
    ym = datetime.date.today().strftime('%Y年%-m月')
    src = re.sub(r'(label:"历史总场次"[^}]*value:)\d+', rf'\g<1>{mc}', src)
    src = re.sub(r'(label:"历史总场次"[^}]*ctx:)"截至\d+年\d+月"',
                 rf'\g<1>"截至{ym}"', src)
    return src


print("\n🔢 更新 RECORDS.career + RECORDS.club ...")
src = update_records_career_precise(src, goals_all_raw, assists_all_raw, apps_all_raw)
src = update_records_club_total(src, match_count)
print(f"   生涯最多进球={goals_all_raw[0]['val']}  生涯最多助攻={assists_all_raw[0]['val']}")
print(f"   历史总场次={match_count}")

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ data.jsx 已更新：")
print(f"   GOALS26={len(goals26)} ASSISTS26={len(assists26)} APPS26={len(apps26)}")
print(f"   GOALS_ALL={len(goals_all_raw)} ASSISTS_ALL={len(assists_all_raw)} APPS_ALL={len(apps_all_raw)}")
print(f"   MATCH_COUNT={match_count}")
print(f"   RATINGS_ALL={len(ratings_all)} + 各赛季评分榜已写入")
print(f"   RECORDS.season 场均进球/助攻 + 单月/评分纪录已更新")
print(f"   RECORDS.career + RECORDS.club 已同步")
