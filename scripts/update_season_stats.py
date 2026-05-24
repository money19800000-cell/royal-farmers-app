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

# MATCH_COUNT = 总出场数.csv 里第一条数据的 total 列
match_count = apps_all_raw[0]['total'] if apps_all_raw and 'total' in apps_all_raw[0] else 0
print(f"   总场次 MATCH_COUNT = {match_count}")
print(f"   历史射手榜：{len(goals_all_raw)} 人")
print(f"   历史助攻榜：{len(assists_all_raw)} 人")
print(f"   历史出场榜：{len(apps_all_raw)} 人")

# 打印 2026 榜单预览
print(f"\n🥅 GOALS26 Top5：", [(p['name'], p['goals']) for p in goals26[:5]])
print(f"👟 ASSISTS26 Top5：", [(p['name'], p['assists']) for p in assists26[:5]])
print(f"📅 APPS26 Top5：",   [(p['name'], p['apps']) for p in apps26[:5]])

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

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ data.jsx 已更新：")
print(f"   GOALS26={len(goals26)} ASSISTS26={len(assists26)} APPS26={len(apps26)}")
print(f"   GOALS_ALL={len(goals_all_raw)} ASSISTS_ALL={len(assists_all_raw)} APPS_ALL={len(apps_all_raw)}")
print(f"   MATCH_COUNT={match_count}")
