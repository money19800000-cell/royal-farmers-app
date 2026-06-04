#!/usr/bin/env python3
"""
Royal Farmers FC — 连续纪录计算脚本
计算 5 种个人连续纪录并写入 data.jsx 的 RECORDS.streak：
  1. 连续胜利  — 花名册评分列，连续出场值均为 3
  2. 连续不败  — 花名册评分列，连续出场值均非 -1
  3. 连续进球  — 出场期间，连续场次有进球（对比具体战况.csv）
  4. 连续助攻  — 出场期间，连续场次有助攻（对比具体战况.csv）
  5. 连续出场  — 全队所有场次中，连续每场均有出场记录

用法：
    python3 scripts/update_streaks.py
    python3 scripts/update_streaks.py --dry-run
"""
import csv, io, re, sys, os
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
ROSTER_CSV  = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
BATTLE_CSV  = os.path.join(DATA_DIR, "每场战报+总数据-具体战况.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

# 球员照片目录映射（号码 → 路径）
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
    "26": "assets/players/38号鲍澜云.jpeg",  # 鲍澜云当前号码26，照片文件名保留旧号38
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
    "鲍梁剑": "assets/players/22号鲍梁剑.jpeg",
}

BAD_NAMES = {'/', '', '进球没拍全', '进球没拍全1', '进球没拍全2', '进球没拍全3',
             '？', '?', '乌龙', 'None', 'null'}
SKIP_ROSTER = {'合计', '总计', '名字', '姓名', ''}

# 花名册赛季出场列索引（固定结构，每赛季占 4 列：出场/进球/助攻/团队分）
SEASON_APP_COLS = {'2021': 9, '2022': 13, '2023': 17, '2024': 21, '2025': 25, '2026': 29}
SEASONS = ['2021', '2022', '2023', '2024', '2025', '2026']


def fmt_date(d8):
    return f"{d8[:4]}.{d8[4:6]}.{d8[6:]}"


def parse_date_code(raw):
    """把 YYMMDD / YYYYMMDD / YYMMDD-N 统一转为 8 位 YYYYMMDD，失败返回 None"""
    if not raw:
        return None
    d = raw.strip().split('-')[0].replace('.', '')
    if not d.isdigit():
        return None
    if len(d) == 6:
        d = '20' + d
    if len(d) == 8:
        return d
    return None


def longest_streak(bool_seq):
    """返回最长连续 True 子串的 (长度, 起始索引, 结束索引)"""
    best = (0, 0, 0)
    cur_len, cur_start = 0, 0
    for i, v in enumerate(bool_seq):
        if v:
            if cur_len == 0:
                cur_start = i
            cur_len += 1
            if cur_len > best[0]:
                best = (cur_len, cur_start, i)
        else:
            cur_len = 0
    return best


# ── Step 1: 解析花名册 ──────────────────────────────────────────────────────
print("📋 读取花名册 CSV ...")
with open(ROSTER_CSV, encoding='utf-8') as f:
    content = f.read()
rows = list(csv.reader(io.StringIO(content)))

hrow_idx = next(i for i, r in enumerate(rows) if r and r[0].strip() == '名字')
headers  = rows[hrow_idx]

# 找日期列（YYYYMMDD），按时间排序
date_col_pairs = sorted(
    [(h.strip(), i) for i, h in enumerate(headers)
     if h.strip().isdigit() and len(h.strip()) == 8],
    key=lambda x: x[0]
)
all_dates  = [d for d, _ in date_col_pairs]   # 全队比赛日期时间线（升序）
n_dates    = len(all_dates)
date_set   = set(all_dates)

# 球员数据：name → {num, apps: {date: score_str}}
players = {}
for r in rows[hrow_idx + 1:]:
    if not r or not r[0].strip() or r[0].strip() in SKIP_ROSTER:
        continue
    name = r[0].strip()
    num  = r[4].strip() if len(r) > 4 else ''
    apps = {}
    for date, col_idx in date_col_pairs:
        val = r[col_idx].strip() if len(r) > col_idx else ''
        if val:
            apps[date] = val
    season_apps = {}
    for yr, col in SEASON_APP_COLS.items():
        v = r[col].strip() if len(r) > col else ''
        season_apps[yr] = int(v) if v.lstrip('-').isdigit() else 0

    players[name] = {'num': num, 'apps': apps, 'season_apps': season_apps}

print(f"   共 {len(players)} 名球员，全队 {n_dates} 场比赛")


# ── Step 2: 解析具体战况.csv ────────────────────────────────────────────────
print("\n📋 读取具体战况 CSV ...")
with open(BATTLE_CSV, encoding='utf-8') as f:
    battle_lines = f.read().split('\n')

# day_scorers[date]  = set of scorer names
# day_assists[date]  = set of assister names
day_scorers  = defaultdict(set)
day_assists  = defaultdict(set)

current_date = None
for line in battle_lines:
    cols = [c.strip() for c in line.split(',')]
    if not any(cols):
        continue

    date_raw = cols[1] if len(cols) > 1 else ''
    date_str = parse_date_code(date_raw)

    # ── 比赛表头行 ──
    # 特征：col[1] 有日期码 且 col[6] 是数字（比分）
    if date_str and len(cols) > 6 and cols[6].isdigit():
        current_date = date_str
        continue

    if current_date is None:
        continue

    # ── 进球 / 助攻行 ──
    # 有些 2026 比赛（如 20260514）进球行整体左移一列：col[3]=进球者, col[4]=助攻者
    # 普通格式：col[4]=主队进球者, col[5]=主队助攻者, col[8]=客队进球者, col[9]=客队助攻者
    col3 = cols[3] if len(cols) > 3 else ''
    shifted = (
        not date_raw            # 非 2024-2025 含完整上下文的行（其 col[1] 有日期）
        and col3
        and col3 not in BAD_NAMES
        and not col3[0].isdigit()
    )

    if shifted:
        home_sc = col3
        home_as = cols[4] if len(cols) > 4 else ''
        away_sc = ''
        away_as = ''
    else:
        home_sc = cols[4] if len(cols) > 4 else ''
        home_as = cols[5] if len(cols) > 5 else ''
        away_sc = cols[8] if len(cols) > 8 else ''
        away_as = cols[9] if len(cols) > 9 else ''

    for name in (home_sc, away_sc):
        if name and name not in BAD_NAMES:
            day_scorers[current_date].add(name)
    for name in (home_as, away_as):
        if name and name not in BAD_NAMES:
            day_assists[current_date].add(name)

battle_dates = set(day_scorers.keys()) | set(day_assists.keys())
if battle_dates:
    print(f"   覆盖 {len(battle_dates)} 天比赛数据 | "
          f"{fmt_date(min(battle_dates))} — {fmt_date(max(battle_dates))}")


# ── Step 3: 计算连续纪录 ────────────────────────────────────────────────────
print("\n🔍 计算连续纪录 ...")

best = {k: {'count': 0, 'name': '', 'num': '', 'from': '', 'to': ''}
        for k in ('win', 'unbeat', 'goal', 'assist', 'apps')}

# 个人连续纪录字典（出场≥5次才收录，减少数据量）
player_streaks = {}   # name → {apps, goal, assist}
MIN_APPS_FOR_PERSONAL = 5

for name, pdata in players.items():
    num  = pdata['num']
    apps = pdata['apps']
    played_dates = sorted(apps.keys())
    if not played_dates:
        continue
    total_apps = len(played_dates)

    # ── 1. 连续胜利 ──
    win_seq = [apps[d] == '3' for d in played_dates]
    wlen, ws, we = longest_streak(win_seq)
    if wlen > best['win']['count']:
        best['win'] = {'count': wlen, 'name': name, 'num': num,
                       'from': played_dates[ws], 'to': played_dates[we]}

    # ── 2. 连续不败 ──
    unb_seq = [apps[d] != '-1' for d in played_dates]
    ulen, us, ue = longest_streak(unb_seq)
    if ulen > best['unbeat']['count']:
        best['unbeat'] = {'count': ulen, 'name': name, 'num': num,
                          'from': played_dates[us], 'to': played_dates[ue]}

    # ── 3. 连续进球 & 4. 连续助攻（仅在具体战况有数据的出场日）──
    played_in_battle = [d for d in played_dates if d in battle_dates]
    p_goal = p_assist = None
    if played_in_battle:
        goal_seq   = [name in day_scorers.get(d, set()) for d in played_in_battle]
        assist_seq = [name in day_assists.get(d, set()) for d in played_in_battle]

        glen, gs, ge = longest_streak(goal_seq)
        if glen > best['goal']['count']:
            best['goal'] = {'count': glen, 'name': name, 'num': num,
                            'from': played_in_battle[gs], 'to': played_in_battle[ge]}
        if glen > 0:
            p_goal = {'count': glen,
                      'from': fmt_date(played_in_battle[gs]),
                      'to':   fmt_date(played_in_battle[ge])}

        alen, as_, ae = longest_streak(assist_seq)
        if alen > best['assist']['count']:
            best['assist'] = {'count': alen, 'name': name, 'num': num,
                              'from': played_in_battle[as_], 'to': played_in_battle[ae]}
        if alen > 0:
            p_assist = {'count': alen,
                        'from': fmt_date(played_in_battle[as_]),
                        'to':   fmt_date(played_in_battle[ae])}

    # ── 5. 连续出场（全队每场均有出场，缺一即断）──
    app_seq = [d in apps for d in all_dates]
    applen, app_s, app_e = longest_streak(app_seq)
    if applen > best['apps']['count']:
        best['apps'] = {'count': applen, 'name': name, 'num': num,
                        'from': all_dates[app_s], 'to': all_dates[app_e]}

    # ── 收集个人连续纪录（出场≥5次）──
    if total_apps >= MIN_APPS_FOR_PERSONAL:
        entry = {}
        if applen > 0:
            entry['apps'] = {'count': applen,
                             'from': fmt_date(all_dates[app_s]),
                             'to':   fmt_date(all_dates[app_e])}
        if wlen > 0:
            entry['win'] = {'count': wlen,
                            'from': fmt_date(played_dates[ws]),
                            'to':   fmt_date(played_dates[we])}
        if ulen > 0:
            entry['unbeaten'] = {'count': ulen,
                                 'from': fmt_date(played_dates[us]),
                                 'to':   fmt_date(played_dates[ue])}
        if p_goal:
            entry['goal'] = p_goal
        if p_assist:
            entry['assist'] = p_assist
        if entry:
            player_streaks[name] = entry


for key, r in best.items():
    nm = f"{r['num']}号{r['name']}" if r['num'] else r['name']
    print(f"  {key:6s}: {nm:12s} · {r['count']}场 · "
          f"{fmt_date(r['from'])} — {fmt_date(r['to'])}")


# ── Step 3b: 全勤元老（每个赛季均有出场）──────────────────────────────────
print("\n🎖️ 计算全勤元老 ...")
allseason = []
for name, pdata in players.items():
    sa = pdata['season_apps']
    if all(sa.get(yr, 0) > 0 for yr in SEASONS):
        total = sum(sa[yr] for yr in SEASONS)
        allseason.append({
            'name':  name,
            'num':   pdata['num'],
            'total': total,
            'apps':  [sa[yr] for yr in SEASONS],
        })
allseason.sort(key=lambda p: p['total'], reverse=True)
print(f"   共 {len(allseason)} 人（6个赛季全勤）")
for p in allseason[:5]:
    print(f"    {p['num']:3s}号 {p['name']:6s}  总出场 {p['total']}  各赛季: {p['apps']}")


# ── Step 4: 生成 JS 并写入 data.jsx ────────────────────────────────────────
def photo(num, name=''):
    if name and name in NAME_PHOTO_OVERRIDE:
        p = NAME_PHOTO_OVERRIDE[name]
    else:
        p = PHOTO_MAP.get(num)
    return f'"{p}"' if p else 'null'


def streak_js():
    lines = ['const STREAK_RECORDS = [']
    configs = [
        ('win',    '🏆', '连续胜利',
         lambda r: f"连续{r['count']}场告捷 · 全程零败"),
        ('unbeat', '🛡️', '连续不败',
         lambda r: f"连续{r['count']}场不败 · 无一输球"),
        ('goal',   '⚽', '连续进球',
         lambda r: f"连续{r['count']}场取得进球"),
        ('assist', '👟', '连续助攻',
         lambda r: f"连续{r['count']}场送出助攻"),
        ('apps',   '🏃', '连续出场',
         lambda r: f"连续{r['count']}场出场未中断"),
    ]
    for key, icon, label, ctx_fn in configs:
        r = best[key]
        name  = r['name']
        num   = r['num']
        frm   = fmt_date(r['from'])
        to    = fmt_date(r['to'])
        ctx   = ctx_fn(r)
        lines.append(
            f'  {{label:"{label}",icon:"{icon}",value:{r["count"]},unit:"场",'
            f'holder:"{name}",num:"{num}",photo:{photo(num, name)},'
            f'from:"{frm}",to:"{to}",ctx:"{ctx}"}},'
        )
    lines.append('];')
    return '\n'.join(lines)


def player_streaks_js():
    lines = ['const PLAYER_STREAKS = {']
    for name, entry in sorted(player_streaks.items()):
        parts = []
        for key in ('apps', 'win', 'unbeaten', 'goal', 'assist'):
            if key in entry:
                e = entry[key]
                parts.append(f'{key}:{{count:{e["count"]},from:"{e["from"]}",to:"{e["to"]}"}}'  )
        if parts:
            esc = name.replace('"', '\\"')
            lines.append(f'  "{esc}": {{{", ".join(parts)}}},')
    lines.append('};')
    return '\n'.join(lines)


def allseason_js():
    lines = ['const ALLSEASON_PLAYERS = [']
    for p in allseason:
        apps_arr = '[' + ','.join(str(x) for x in p['apps']) + ']'
        lines.append(
            f'  {{name:"{p["name"]}",num:"{p["num"]}",photo:{photo(p["num"], p["name"])},'
            f'total:{p["total"]},apps:{apps_arr}}},'
        )
    lines.append('];')
    return '\n'.join(lines)


streak_block         = streak_js()
allseason_block      = allseason_js()
player_streaks_block = player_streaks_js()

print(f"\n📝 生成 STREAK_RECORDS 块（{len(best)} 条）")
print(f"📝 生成 ALLSEASON_PLAYERS 块（{len(allseason)} 人）")
print(f"📝 生成 PLAYER_STREAKS 块（{len(player_streaks)} 人）")

if DRY_RUN:
    print(allseason_block[:400] + '\n...')
    print("\n[dry-run] 未写入文件")
    sys.exit(0)

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

# ── 写入 STREAK_RECORDS ──
pat_streak = re.compile(r'const STREAK_RECORDS = \[.*?\];', re.DOTALL)
if pat_streak.search(src):
    src = pat_streak.sub(streak_block, src)
else:
    src = src.replace('const RECORDS = {', streak_block + '\n\nconst RECORDS = {')

# ── 写入 ALLSEASON_PLAYERS ──
pat_all = re.compile(r'const ALLSEASON_PLAYERS = \[.*?\];', re.DOTALL)
if pat_all.search(src):
    src = pat_all.sub(allseason_block, src)
else:
    src = src.replace('const RECORDS = {', allseason_block + '\n\nconst RECORDS = {')

# ── 写入 PLAYER_STREAKS ──
pat_ps = re.compile(r'const PLAYER_STREAKS = \{.*?\};', re.DOTALL)
if pat_ps.search(src):
    src = pat_ps.sub(player_streaks_block, src)
else:
    src = src.replace('const STREAK_RECORDS', player_streaks_block + '\n\nconst STREAK_RECORDS')

# ── 确保所有常量都在 window.RF_DATA 里 ──
for const_name in ('STREAK_RECORDS', 'ALLSEASON_PLAYERS', 'PLAYER_STREAKS'):
    export_line = src[src.find('window.RF_DATA'):]
    if const_name not in export_line:
        src = src.replace('window.RF_DATA = {', f'window.RF_DATA = {{ {const_name},')

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ data.jsx 已更新 — STREAK_RECORDS + ALLSEASON_PLAYERS + PLAYER_STREAKS 写入完毕")
