#!/usr/bin/env python3
"""
Royal Farmers FC — 月度榜单更新脚本
自动检测所有有数据的月份，更新 data.jsx 中的：
  MONTHLY_PERIOD / MONTHLY_GOALS / MONTHLY_ASSISTS / MONTHLY_APPS  (当月，向后兼容)
  MONTHLY_HISTORY  (全历史月度数据，用于轮播)

月度进球/助攻：从 具体战况.csv 统计该月每场比赛的进球者/助攻者
月度出勤：从 花名册.csv 的逐场评分列（260xxx）统计该月非空出场次数
平局排序规则（出勤）：月度场次↓，总出场数↑

用法：
    python3 scripts/update_monthly.py
    python3 scripts/update_monthly.py --dry-run
    python3 scripts/update_monthly.py --month 202505   # 只处理指定月
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

FORCED_MONTH = None
for arg in sys.argv[1:]:
    if re.match(r'^\d{6}$', arg):
        FORCED_MONTH = arg


def si(v):
    try: return int(float(v))
    except: return 0


def parse_date(raw):
    d = raw.strip().split('-')[0].replace('.', '')
    if len(d) == 6 and d.startswith('2'):
        d = '20' + d
    if len(d) == 8 and d[0] == '2':
        return d
    return None


def detect_all_months(fixtures_csv):
    """从 具体战况.csv 检测所有有比赛的 2026 月份，降序返回"""
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
    return sorted(months, reverse=True)  # 最新在前


def parse_goals_assists_by_month(target_month, rows):
    goals_counter   = defaultdict(int)
    assists_counter = defaultdict(int)
    SKIP = {'/', '', '进球没拍全', '进球没拍全1', '进球没拍全2', '进球没拍全3'}
    current_in_month = False
    for r in rows:
        if not r or not any(c.strip() for c in r):
            continue
        date_raw = r[1].strip() if len(r) > 1 else ''
        if date_raw and re.match(r'^\d', date_raw) and len(r) >= 9:
            d = parse_date(date_raw)
            current_in_month = (d is not None and d[:6] == target_month)
            continue
        if not current_in_month:
            continue
        col3 = r[3].strip() if len(r) > 3 else ''
        if col3 and col3 not in SKIP and not re.match(r'^\d', col3):
            scorers  = [r[3].strip(), r[7].strip()]
            assists_ = [r[4].strip(), r[8].strip()]
        else:
            scorers  = [r[4].strip(), r[8].strip()]
            assists_ = [r[5].strip(), r[9].strip()]
        for name in scorers:
            if name and name not in SKIP: goals_counter[name] += 1
        for name in assists_:
            if name and name not in SKIP: assists_counter[name] += 1
    return goals_counter, assists_counter


def parse_apps_by_month(target_month, header, data_rows):
    month_prefix = '26' + target_month[4:6]
    month_cols = [
        i for i, h in enumerate(header)
        if re.match(r'^26\d{4}$', h.strip()) and h.strip().startswith(month_prefix)
    ]
    result = {}
    skip = {'合计', '总计', '名字', '姓名', ''}
    for r in data_rows:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        total_apps = si(r[6]) if len(r) > 6 else 0
        monthly = sum(1 for i in month_cols if i < len(r) and r[i].strip() != '')
        if monthly > 0:
            result[name] = (monthly, total_apps)
    return result


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


def json_val(v):
    return f'"{v}"' if isinstance(v, str) else str(v)


def entries_js(lst):
    return ', '.join('{' + ', '.join(f'{k}:{json_val(v)}' for k, v in e.items()) + '}' for e in lst)


def build_simple_block(var, entries):
    lines = [f'const {var} = [']
    for e in entries:
        kv = ', '.join(f'{k}:{json_val(v)}' for k, v in e.items())
        lines.append(f'  {{{kv}}},')
    lines.append('];')
    return '\n'.join(lines)


def build_history_block(all_months_data):
    """生成 MONTHLY_HISTORY JS 数组"""
    lines = ['const MONTHLY_HISTORY = [']
    for m in all_months_data:
        goals_js   = entries_js(m['goals'])
        assists_js = entries_js(m['assists'])
        apps_js    = entries_js(m['apps'])
        lines.append(f'  {{ period: "{m["period"]}", goals: [{goals_js}], assists: [{assists_js}], apps: [{apps_js}] }},')
    lines.append('];')
    return '\n'.join(lines)


def replace_block(src, var_name, new_block):
    pattern = re.compile(r'const ' + re.escape(var_name) + r' = \[.*?\];', re.DOTALL)
    m = pattern.search(src)
    if not m:
        return None, src  # not found
    return True, src[:m.start()] + new_block + src[m.end():]


def replace_or_insert_history(src, new_block):
    """替换 MONTHLY_HISTORY，不存在则插在 window.RF_DATA 行之前"""
    found, src2 = replace_block(src, 'MONTHLY_HISTORY', new_block)
    if found:
        return src2
    # 插入到 window.RF_DATA 行之前
    idx = src.find('window.RF_DATA')
    if idx == -1:
        return src + '\n' + new_block + '\n'
    return src[:idx] + new_block + '\n' + src[idx:]


def replace_period(src, label):
    return re.sub(r'const MONTHLY_PERIOD = "[^"]*";',
                  f'const MONTHLY_PERIOD = "{label}";', src)


# ── Main ──

# 读取 CSV 数据（一次性，供所有月份复用）
print("📋 读取花名册 & 战况 CSV ...")
with open(FIXTURES_CSV, encoding='utf-8-sig') as f:
    fixture_rows = list(csv.reader(f))

with open(ROSTER_CSV, encoding='utf-8-sig') as f:
    roster_content = f.read()
roster_rows = list(csv.reader(io.StringIO(roster_content)))
hrow = next(i for i, r in enumerate(roster_rows) if r and r[0] == '名字')
roster_header = roster_rows[hrow]
roster_data   = roster_rows[hrow + 1:]

num_map = read_num_map()

# 确定处理哪些月份
if FORCED_MONTH:
    all_months = [FORCED_MONTH]
else:
    all_months = detect_all_months(FIXTURES_CSV)

if not all_months:
    print("❌ 无法检测到2026赛季比赛月份")
    sys.exit(1)

print(f"   检测到月份：{all_months}")

# 每个月计算 Top5
all_months_data = []
for m in all_months:
    label = month_label(m)
    goals_ctr, assists_ctr = parse_goals_assists_by_month(m, fixture_rows)
    apps_map = parse_apps_by_month(m, roster_header, roster_data)

    goals_top   = sorted(goals_ctr.items(),   key=lambda x: x[1], reverse=True)[:TOP_N]
    assists_top = sorted(assists_ctr.items(), key=lambda x: x[1], reverse=True)[:TOP_N]
    apps_sorted = sorted(apps_map.items(),    key=lambda x: (-x[1][0], x[1][1]))[:TOP_N]

    goals_e   = [{'name': n, 'num': num_map.get(n,''), 'goals': g}   for n, g in goals_top]
    assists_e = [{'name': n, 'num': num_map.get(n,''), 'assists': a} for n, a in assists_top]
    apps_e    = [{'name': n, 'num': num_map.get(n,''), 'apps': v[0]} for n, v in apps_sorted]

    all_months_data.append({'period': label, 'goals': goals_e, 'assists': assists_e, 'apps': apps_e})
    print(f"   {label}: 射手{len(goals_e)} 助攻{len(assists_e)} 出勤{len(apps_e)}")

# 最新月份数据（向后兼容）
latest = all_months_data[0] if not FORCED_MONTH else all_months_data[0]
print(f"\n✨ 最新月：{latest['period']}")
print(f"   射手 Top5: {[(e['name'], e['goals']) for e in latest['goals']]}")
print(f"   助攻 Top5: {[(e['name'], e['assists']) for e in latest['assists']]}")
print(f"   出勤 Top5: {[(e['name'], e['apps']) for e in latest['apps']]}")

if DRY_RUN:
    print("\n[dry-run] 未写入文件")
    sys.exit(0)

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

# 更新向后兼容变量
src = replace_period(src, latest['period'])
_, src = replace_block(src, 'MONTHLY_GOALS',   build_simple_block('MONTHLY_GOALS',   latest['goals']))
_, src = replace_block(src, 'MONTHLY_ASSISTS', build_simple_block('MONTHLY_ASSISTS', latest['assists']))
_, src = replace_block(src, 'MONTHLY_APPS',    build_simple_block('MONTHLY_APPS',    latest['apps']))

# 更新 / 插入 MONTHLY_HISTORY
src = replace_or_insert_history(src, build_history_block(all_months_data))

# 确保 window.RF_DATA 包含 MONTHLY_HISTORY
if 'MONTHLY_HISTORY' not in src.split('window.RF_DATA')[1].split(';')[0]:
    src = src.replace(
        'window.RF_DATA = {',
        'window.RF_DATA = { MONTHLY_HISTORY,'
    )

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ 月度榜单已全量更新（{len(all_months_data)} 个月）")
