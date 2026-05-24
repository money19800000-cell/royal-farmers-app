#!/usr/bin/env python3
"""
Royal Farmers FC — 月度榜单更新脚本
自动检测最近有比赛的月份，更新 data.jsx 中的：
  MONTHLY_PERIOD / MONTHLY_GOALS / MONTHLY_ASSISTS / MONTHLY_APPS

月度进球/助攻：从 具体战况.csv 统计该月每场比赛的进球者/助攻者
月度出勤：从 花名册.csv 的逐场评分列（260xxx）统计该月非空出场次数

平局排序规则（出勤）：月度场次↓，总出场数↑

用法：
    python3 scripts/update_monthly.py
    python3 scripts/update_monthly.py --dry-run
    python3 scripts/update_monthly.py --month 202505   # 指定月份
"""
import csv, re, sys, os, io
from collections import defaultdict

PROJECT_DIR  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
ROSTER_CSV   = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
FIXTURES_CSV = os.path.join(DATA_DIR, "每场战报+总数据-具体战况.csv")
DATA_JSX     = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN      = "--dry-run" in sys.argv
TOP_N        = 5

# 手动指定月份（--month YYYYMM）
FORCED_MONTH = None
for arg in sys.argv[1:]:
    if re.match(r'^\d{6}$', arg):
        FORCED_MONTH = arg


def si(v):
    try: return int(float(v))
    except: return 0


def parse_date(raw):
    """返回 YYYYMMDD 格式字符串，失败返回 None"""
    d = raw.strip().split('-')[0].replace('.', '')
    if len(d) == 6 and d.startswith('2'):
        d = '20' + d
    if len(d) == 8 and d[0] == '2':
        return d
    return None


def detect_latest_month(fixtures_csv):
    """从 具体战况.csv 检测最新有比赛的月份，返回 'YYYYMM'"""
    months = set()
    with open(fixtures_csv, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    for r in rows:
        if not r or not any(c.strip() for c in r):
            continue
        date_raw = r[1].strip() if len(r) > 1 else ''
        if date_raw and re.match(r'^\d', date_raw):
            d = parse_date(date_raw)
            if d and d.startswith('2026'):
                months.add(d[:6])
    return max(months) if months else None


def parse_goals_assists_by_month(target_month):
    """
    从 具体战况.csv 统计 target_month 内每个进球者/助攻者出现次数
    返回 goals_counter, assists_counter: {name: count}
    """
    goals_counter   = defaultdict(int)
    assists_counter = defaultdict(int)

    SKIP = {'/', '', '进球没拍全', '进球没拍全1', '进球没拍全2', '进球没拍全3'}

    with open(FIXTURES_CSV, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))

    current_in_month = False
    for r in rows:
        if not r or not any(c.strip() for c in r):
            continue
        date_raw = r[1].strip() if len(r) > 1 else ''

        # 比赛头行
        if date_raw and re.match(r'^\d', date_raw) and len(r) >= 9:
            d = parse_date(date_raw)
            current_in_month = (d is not None and d[:6] == target_month)
            continue

        if not current_in_month:
            continue

        # 进球/助攻行（同 update_fixtures.py 的列偏移检测）
        col3 = r[3].strip() if len(r) > 3 else ''
        if col3 and col3 not in SKIP and not re.match(r'^\d', col3):
            # 偏移格式
            home_scorer  = r[3].strip() if len(r) > 3 else ''
            home_assist  = r[4].strip() if len(r) > 4 else ''
            away_scorer  = r[7].strip() if len(r) > 7 else ''
            away_assist  = r[8].strip() if len(r) > 8 else ''
        else:
            home_scorer  = r[4].strip() if len(r) > 4 else ''
            home_assist  = r[5].strip() if len(r) > 5 else ''
            away_scorer  = r[8].strip() if len(r) > 8 else ''
            away_assist  = r[9].strip() if len(r) > 9 else ''

        for name in [home_scorer, away_scorer]:
            if name and name not in SKIP:
                goals_counter[name] += 1
        for name in [home_assist, away_assist]:
            if name and name not in SKIP:
                assists_counter[name] += 1

    return goals_counter, assists_counter


def parse_apps_by_month(target_month):
    """
    从 花名册.csv 的逐场评分列（260xxx）统计 target_month 内每人出场次数
    返回 {name: (monthly_apps, total_career_apps)}
    """
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        content = f.read()
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')
    header = rows[hrow]

    # 找出属于 target_month 的评分列索引
    # 列头格式：260523 → 26MMDD → 月份前缀 = 26 + target_month[4:6]
    month_prefix = '26' + target_month[4:6]  # e.g. '2605'
    month_cols = [
        i for i, h in enumerate(header)
        if re.match(r'^26\d{4}$', h.strip()) and h.strip().startswith(month_prefix)
    ]

    result = {}
    skip = {'合计', '总计', '名字', '姓名', ''}
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        total_apps = si(r[6]) if len(r) > 6 else 0
        monthly = sum(1 for i in month_cols if i < len(r) and r[i].strip() != '')
        if monthly > 0:
            result[name] = (monthly, total_apps)

    return result


def get_num(name, roster_num_map):
    return roster_num_map.get(name, '')


def read_num_map():
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        content = f.read()
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')
    num_map = {}
    skip = {'合计', '总计', '名字', '姓名', ''}
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        num_map[r[0].strip()] = r[4].strip() if len(r) > 4 else ''
    return num_map


def month_label(yyyymm):
    return f"{yyyymm[:4]}年{int(yyyymm[4:6])}月"


def build_js_block(var, entries):
    """通用 JS 数组块构建"""
    lines = [f'const {var} = [']
    for e in entries:
        kv = ', '.join(f'{k}:{json_val(v)}' for k, v in e.items())
        lines.append(f'  {{{kv}}},')
    lines.append('];')
    return '\n'.join(lines)


def json_val(v):
    if isinstance(v, str):
        return f'"{v}"'
    return str(v)


def replace_block(src, var_name, new_block):
    pattern = re.compile(r'const ' + re.escape(var_name) + r' = \[.*?\];', re.DOTALL)
    m = pattern.search(src)
    if not m:
        print(f'  ⚠️  未找到 {var_name} 块，跳过')
        return src
    return src[:m.start()] + new_block + src[m.end():]


def replace_period(src, label):
    return re.sub(r'const MONTHLY_PERIOD = "[^"]*";',
                  f'const MONTHLY_PERIOD = "{label}";', src)


# ── Main ──
target_month = FORCED_MONTH or detect_latest_month(FIXTURES_CSV)
if not target_month:
    print("❌ 无法检测到2026赛季比赛月份")
    sys.exit(1)

label = month_label(target_month)
print(f"📅 目标月份：{label}（{target_month}）")

num_map = read_num_map()

# 进球/助攻
goals_ctr, assists_ctr = parse_goals_assists_by_month(target_month)
goals_top = sorted(goals_ctr.items(),   key=lambda x: x[1], reverse=True)[:TOP_N]
assists_top = sorted(assists_ctr.items(), key=lambda x: x[1], reverse=True)[:TOP_N]

# 出勤（平局时总出场少的排前）
apps_map = parse_apps_by_month(target_month)
apps_sorted = sorted(apps_map.items(),
                     key=lambda x: (-x[1][0], x[1][1]))[:TOP_N]

print(f"   月度射手 Top{TOP_N}: {[(n, g) for n, g in goals_top]}")
print(f"   月度助攻 Top{TOP_N}: {[(n, a) for n, a in assists_top]}")
print(f"   月度出勤 Top{TOP_N}: {[(n, v[0]) for n, v in apps_sorted]}")

if DRY_RUN:
    print("\n[dry-run] 未写入文件")
    sys.exit(0)

goals_entries   = [{'name': n, 'num': get_num(n, num_map), 'goals': g}   for n, g in goals_top]
assists_entries = [{'name': n, 'num': get_num(n, num_map), 'assists': a} for n, a in assists_top]
apps_entries    = [{'name': n, 'num': get_num(n, num_map), 'apps': v[0]} for n, v in apps_sorted]

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

src = replace_period(src, label)
src = replace_block(src, 'MONTHLY_GOALS',   build_js_block('MONTHLY_GOALS',   goals_entries))
src = replace_block(src, 'MONTHLY_ASSISTS', build_js_block('MONTHLY_ASSISTS', assists_entries))
src = replace_block(src, 'MONTHLY_APPS',    build_js_block('MONTHLY_APPS',    apps_entries))

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ 月度榜单已更新：{label}")
