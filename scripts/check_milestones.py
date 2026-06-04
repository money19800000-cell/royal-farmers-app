#!/usr/bin/env python3
"""
Royal Farmers FC — 里程碑检测 & 更新脚本
每次更新 CSV 数据后运行此脚本。

用法：
    python3 scripts/check_milestones.py
    python3 scripts/check_milestones.py --dry-run   # 只检测不写入
"""
import csv, io, json, datetime, re, sys, os
from collections import defaultdict

PROJECT_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH       = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united/花名册-球队花名册.csv"
FIXTURES_CSV   = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united/每场战报+总数据-具体战况.csv"
DATA_JSX       = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN        = "--dry-run" in sys.argv

PHOTO_MAP = {
    "姜珂":  "assets/players/10号姜珂.jpeg",
    "金辉":  "assets/players/81号金辉.jpeg",
    "麦超":  "assets/players/22号麦超.jpeg",
    "张伟":  "assets/players/17号张伟.jpeg",
    "夏浩":  "assets/players/14号夏浩.jpeg",
    "鲍梁剑":"assets/players/22号鲍梁剑.jpeg",
    "朱寿卿":"assets/players/56号朱寿卿.jpeg",
    "季贝赢":"assets/players/33号季贝赢.jpeg",
    "彭利平":"assets/players/33号彭利平.jpeg",
    "鲍澜云":"assets/players/38号鲍澜云.jpeg",
    "倪海":  "assets/players/44号倪海.jpeg",
    "陆晓巍":"assets/players/24号陆晓巍.jpeg",
    "鲁尼":  "assets/players/25号鲁尼.jpeg",
    "王刚":  "assets/players/68号王刚.jpeg",
    "薛峰":  "assets/players/76号薛峰.jpeg",
    "王积鹏":"assets/players/88号王积鹏.jpeg",
    "姚魏":  "assets/players/98号姚魏.jpeg",
    "圣托尔多":"assets/players/92号圣托尔多.jpeg",
    "陶骏":  "assets/players/6号陶骏.jpeg",
    "黄纲":  "assets/players/18号黄纲.jpeg",
    "老吴":  "assets/players/41号老吴.jpeg",
}
SKIP = {'合计', '总计', '', '名字', '姓名'}
CSV_SEASONS = [2021, 2022, 2023, 2024, 2025, 2026]
METRIC_LABELS = {"apps": "出场", "goals": "进球", "assists": "助攻"}


def si(v):
    try: return int(float(v))
    except: return 0


def sf(v):
    try: return round(float(v), 2)
    except: return None


def parse_actual_match_dates():
    """
    从 具体战况.csv 解析每个赛季的实际比赛日期集合。
    返回 {year: sorted list of datetime.date}
    """
    dates_by_year = defaultdict(set)
    try:
        with open(FIXTURES_CSV, encoding='utf-8-sig') as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        return {}

    for r in rows:
        if not r or not any(c.strip() for c in r):
            continue
        date_raw = r[1].strip() if len(r) > 1 else ''
        if not date_raw or not re.match(r'^\d', date_raw):
            continue
        d = date_raw.strip().split('-')[0].replace('.', '')
        if len(d) == 6 and d.startswith('2'):
            d = '20' + d
        if len(d) == 8:
            try:
                yr, mo, dy = int(d[:4]), int(d[4:6]), int(d[6:8])
                dates_by_year[yr].add(datetime.date(yr, mo, dy))
            except ValueError:
                pass

    return {yr: sorted(dates) for yr, dates in dates_by_year.items()}


def parse_player_match_stats():
    """
    从 具体战况.csv 逐场解析每位球员的进球/助攻数据。
    返回 {player_name: [(date, goals, assists), ...]} 按日期正序排列。
    进球在 col[4](主) 或 col[8](客)，助攻在 col[5](主) 或 col[9](客)。
    """
    try:
        with open(FIXTURES_CSV, encoding='utf-8-sig') as f:
            rows = list(csv.reader(f))
    except FileNotFoundError:
        return {}

    # 先按比赛分组：{(date, match_id): {player: {goals, assists}}}
    match_stats = []   # list of (date, {player: {'goals':n,'assists':n}})
    current_date = None
    current_players = defaultdict(lambda: {'goals': 0, 'assists': 0})

    for r in rows:
        date_raw = r[1].strip() if len(r) > 1 else ''
        if date_raw and re.match(r'^\d{6}-\d+', date_raw):
            # 保存上一场
            if current_date:
                match_stats.append((current_date, dict(current_players)))
            raw = date_raw.split('-')[0]
            try:
                yr = 2000 + int(raw[:2])
                mo = int(raw[2:4])
                dy = int(raw[4:6])
                current_date = datetime.date(yr, mo, dy)
                current_players = defaultdict(lambda: {'goals': 0, 'assists': 0})
            except:
                current_date = None
        elif current_date:
            # 进球行：col[4]=主队进球者, col[5]=主队助攻者, col[8]=客队进球者, col[9]=客队助攻者
            h_scorer  = r[4].strip() if len(r) > 4 else ''
            h_assist  = r[5].strip() if len(r) > 5 else ''
            a_scorer  = r[8].strip() if len(r) > 8 else ''
            a_assist  = r[9].strip() if len(r) > 9 else ''
            for scorer in [h_scorer, a_scorer]:
                if scorer and scorer not in ('/', ''):
                    current_players[scorer]['goals'] += 1
            for assist in [h_assist, a_assist]:
                if assist and assist not in ('/', ''):
                    current_players[assist]['assists'] += 1

    # 最后一场
    if current_date:
        match_stats.append((current_date, dict(current_players)))

    # 按日期正序（旧→新）
    match_stats.sort(key=lambda x: x[0])

    # 转为 {player: [(date, goals, assists), ...]}
    player_stats = defaultdict(list)
    for date, players in match_stats:
        for pname, stat in players.items():
            if stat['goals'] > 0 or stat['assists'] > 0:
                player_stats[pname].append((date, stat['goals'], stat['assists']))

    return dict(player_stats)


def find_exact_milestone_date(player_name, metric, threshold, career_before_season,
                               match_data_for_season):
    """
    在逐场数据中精确查找达到 threshold 的比赛日期。
    career_before_season: 该赛季开始前的生涯累计值
    match_data_for_season: [(date, goals, assists), ...] 正序
    返回 date 字符串，若找不到返回 None。
    """
    running = career_before_season
    for date, goals, assists in match_data_for_season:
        val = goals if metric == 'goals' else assists
        prev = running
        running += val
        if prev < threshold <= running:
            return date.strftime("%Y-%m-%d")
    return None


def parse_player_app_dates():
    """
    从花名册 CSV 读取每位球员的逐场出场日期（按时间正序）。
    花名册的日期列（YYYYMMDD 8位）非空 = 该场有出场记录。
    返回 {player_name: [datetime.date, ...]}（升序）
    """
    try:
        with open(CSV_PATH, encoding='utf-8-sig') as f:
            content = f.read()
    except FileNotFoundError:
        return {}
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0].strip() == '名字')
    headers = rows[hrow]

    # 找出所有日期列（YYYYMMDD 格式），按日期升序排列
    date_cols = []
    for idx, h in enumerate(headers):
        h = h.strip()
        if len(h) == 8 and h.isdigit():
            try:
                yr, mo, dy = int(h[:4]), int(h[4:6]), int(h[6:8])
                date_cols.append((datetime.date(yr, mo, dy), idx))
            except ValueError:
                pass
    date_cols.sort(key=lambda x: x[0])   # 升序（旧→新）

    result = {}
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in SKIP:
            continue
        name = r[0].strip()
        played = [d for d, ci in date_cols if ci < len(r) and r[ci].strip()]
        if played:
            result[name] = played
    return result


# 全局：实际比赛日期表（按年）
MATCH_DATES_BY_YEAR = parse_actual_match_dates()

# 全局：逐场球员数据（用于进球/助攻精确里程碑日期）
PLAYER_MATCH_STATS = parse_player_match_stats()

# 全局：每位球员的精确出场日期列表（用于出场里程碑精确日期）
PLAYER_APP_DATES = parse_player_app_dates()


def snap_to_match_date(computed: datetime.date, year: int) -> datetime.date:
    """
    将估算日期吸附到该赛季最近的真实比赛日。
    优先选择 ≤ computed 的最近比赛日；若没有则取最早的未来比赛日。
    """
    dates = MATCH_DATES_BY_YEAR.get(year, [])
    if not dates:
        return computed
    before = [d for d in dates if d <= computed]
    after  = [d for d in dates if d > computed]
    if before and after:
        nb, na = before[-1], after[0]
        return nb if (computed - nb).days <= (na - computed).days else na
    return before[-1] if before else after[0]


def approx_date(year, fraction):
    """
    估算里程碑达成的日期，并吸附到该赛季最近的真实比赛日。
    动态使用赛季最后一场比赛日期作为终点（不再硬编码）。
    """
    if year < 2026:
        start = datetime.date(year, 3, 1)
        end   = datetime.date(year, 12, 15)
    else:
        start = datetime.date(2026, 3, 1)
        dates_2026 = MATCH_DATES_BY_YEAR.get(2026, [])
        end = dates_2026[-1] if dates_2026 else datetime.date(2026, 5, 23)
    total_days = (end - start).days
    day_offset  = int(max(0.01, min(0.99, fraction)) * total_days)
    computed    = start + datetime.timedelta(days=day_offset)
    snapped     = snap_to_match_date(computed, year)
    return snapped.strftime("%Y-%m-%d")


def compute_milestones():
    """从花名册 CSV 计算所有里程碑事件"""
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')

    milestones = []
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in SKIP:
            continue
        pname = r[0].strip()
        num   = r[4].strip() if len(r) > 4 else ''
        total_apps    = si(r[6]) if len(r) > 6 else 0
        total_goals   = si(r[7]) if len(r) > 7 else 0
        total_assists = si(r[8]) if len(r) > 8 else 0
        if total_apps == 0:
            continue

        seasons = []
        for i, yr in enumerate(CSV_SEASONS):
            b = 9 + i * 4
            if b + 3 < len(r):
                seasons.append({
                    'year':    yr,
                    'apps':    si(r[b]),
                    'goals':   si(r[b + 1]),
                    'assists': si(r[b + 2]),
                    'rating':  sf(r[b + 3]),
                })

        pre = {
            'apps':    max(0, total_apps    - sum(s['apps']    for s in seasons)),
            'goals':   max(0, total_goals   - sum(s['goals']   for s in seasons)),
            'assists': max(0, total_assists - sum(s['assists'] for s in seasons)),
        }
        career  = dict(pre)
        # 统一名字格式：10号姜珂
        name_display = f"{num}号{pname}" if num else pname
        photo        = PHOTO_MAP.get(pname)

        # 获取该球员在 具体战况.csv 中的逐场数据（按年份过滤）
        player_matches_raw = PLAYER_MATCH_STATS.get(pname, [])

        for s in seasons:
            yr = s['year']

            # 过滤出该赛季的逐场数据（正序）
            season_match_data = [(d, g, a) for d, g, a in player_matches_raw
                                 if d.year == yr]

            for metric in ['apps', 'goals', 'assists']:
                old, add = career[metric], s[metric]
                new = old + add
                lbl = METRIC_LABELS[metric]

                # 生涯里程碑
                for h in range(old // 100 + 1, new // 100 + 1):
                    thr  = h * 100
                    exact = None
                    if metric == 'apps':
                        # 直接从花名册精确找第 thr 场出场日期
                        app_dates = PLAYER_APP_DATES.get(pname, [])
                        if len(app_dates) >= thr:
                            exact = app_dates[thr - 1].strftime("%Y-%m-%d")
                    elif metric in ('goals', 'assists') and season_match_data:
                        exact = find_exact_milestone_date(
                            pname, metric, thr, old, season_match_data)
                    if exact:
                        date_str = exact
                    else:
                        frac = (thr - old) / add if add > 0 else 0.5
                        date_str = approx_date(yr, frac)
                    milestones.append({
                        'date':   date_str,
                        'name':   pname, 'num': num, 'photo': photo,
                        'label':  f"{name_display}生涯{lbl}达{thr}",
                        'type':   f"career_{metric}",
                        'value':  thr, 'season': None,
                    })

                # 赛季里程碑
                sv = s[metric]
                for h in range(1, sv // 100 + 1):
                    thr  = h * 100
                    exact = None
                    if metric == 'apps':
                        # 精确找该赛季第 thr 场出场日期（在该年所有出场里的第 thr 场）
                        season_app_dates = [d for d in PLAYER_APP_DATES.get(pname, [])
                                            if d.year == yr]
                        if len(season_app_dates) >= thr:
                            exact = season_app_dates[thr - 1].strftime("%Y-%m-%d")
                    elif metric in ('goals', 'assists') and season_match_data:
                        exact = find_exact_milestone_date(
                            pname, metric, thr, 0, season_match_data)
                    if exact:
                        date_str = exact
                    else:
                        frac = thr / sv if sv > 0 else 0.5
                        date_str = approx_date(yr, frac)
                    milestones.append({
                        'date':   date_str,
                        'name':   pname, 'num': num, 'photo': photo,
                        'label':  f"{name_display} {yr}赛季{lbl}达{thr}",
                        'type':   f"season_{metric}",
                        'value':  thr, 'season': yr,
                    })

                career[metric] = new

    milestones.sort(key=lambda m: m['date'])
    return milestones


def build_js(milestones):
    lines = ["const MILESTONES = ["]
    for m in milestones:
        pv    = f'"{m["photo"]}"' if m["photo"] else "null"
        sv    = str(m["season"]) if m["season"] else "null"
        nv    = f'"{m["num"]}"' if m["num"] else '""'
        label = m["label"].replace('"', '\\"')
        lines.append(
            f'  {{date:"{m["date"]}",name:"{m["name"]}",num:{nv},'
            f'photo:{pv},label:"{label}",type:"{m["type"]}",value:{m["value"]},season:{sv}}},'
        )
    lines.append("];")
    return "\n".join(lines)


def get_existing_labels(src):
    ms_start = src.find("const MILESTONES = [")
    ms_end   = src.find("];", ms_start) + 2
    ms_block = src[ms_start:ms_end]
    return set(re.findall(r'label:"([^"]+)"', ms_block))


# ── Main ──
print("🔍 读取花名册 CSV 并计算里程碑...")
all_milestones = compute_milestones()

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

existing = get_existing_labels(src)
new_ones = [m for m in all_milestones if m['label'] not in existing]
removed  = [lb for lb in existing if not any(m['label'] == lb for m in all_milestones)]

print(f"   现有里程碑：{len(existing)} 条")
print(f"   重新计算：  {len(all_milestones)} 条")
print(f"   新增事件：  {len(new_ones)} 条")
if removed:
    print(f"   移除事件：  {len(removed)} 条（数据回退）")

if new_ones:
    print("\n✨ 新里程碑事件：")
    for m in new_ones:
        print(f"   {m['date']} | {m['label']}")
else:
    print("\n✅ 无新里程碑，数据已是最新")

if not DRY_RUN:
    new_js  = build_js(all_milestones)
    new_src = re.sub(r'const MILESTONES = \[[\s\S]*?\];', new_js, src)
    with open(DATA_JSX, 'w', encoding='utf-8') as f:
        f.write(new_src)
    print(f"\n📝 data.jsx 已更新（共 {len(all_milestones)} 条里程碑）")
else:
    print("\n[dry-run] 未写入文件")
