#!/usr/bin/env python3
"""
compute_player_chemistry.py — 为每位球员计算4项化学反应数据

1. 助攻我最多的队友  (从具体战况 CSV：scorer=我, ast=对方)
2. 我助攻最多的队友  (从具体战况 CSV：ast=我, scorer=对方)
3. 共同出场胜率最好的队友  (从花名册评分列)
4. 共同出场胜率最低的队友  (从花名册评分列)

输出: PLAYER_CHEMISTRY = { "姜珂": {a2me, me2a, bestP, worstP}, ... }
"""
import csv, io, re, os, sys
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
DETAIL_CSV  = os.path.join(DATA_DIR, "每场战报+总数据-具体战况.csv")
ROSTER_CSV  = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

MIN_ASSIST_COUNT = 3   # 助攻关系最少几次才显示
MIN_LINEUP_APPS  = 30  # 共同出场最少场次

BAD = {'/', '?', '', '乌龙', 'OG', 'None', 'null',
       '进球没拍全','进球没拍全1','进球没拍全2','进球没拍全3','/?','？'}


# ── 1. 从具体战况 CSV 计算助攻关系 ─────────────────────────────────────────

def parse_assist_pairs():
    """返回两个 dict:
       a2me[scorer][assister]  = 次数  (助攻我)
       me2a[assister][scorer]  = 次数  (我助攻)
    """
    with open(DETAIL_CSV, encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))

    a2me  = defaultdict(lambda: defaultdict(int))  # [被助攻者][助攻者]
    me2a  = defaultdict(lambda: defaultdict(int))  # [助攻者][进球者]

    for row in rows:
        if not any(c.strip() for c in row):
            continue
        s1 = row[6].strip() if len(row) > 6 else ''
        s2 = row[7].strip() if len(row) > 7 else ''
        if s1.isdigit() or s2.isdigit():
            continue  # 标题行跳过

        for sc_col, ast_col in [(4, 5), (8, 9)]:
            sc  = row[sc_col].strip()  if len(row) > sc_col  else ''
            ast = row[ast_col].strip() if len(row) > ast_col else ''
            if sc in BAD or ast in BAD or not sc or not ast or sc == ast:
                continue
            a2me[sc][ast]  += 1
            me2a[ast][sc]  += 1

    return a2me, me2a


# ── 2. 从花名册 CSV 计算联合出场胜率 ──────────────────────────────────────

def parse_lineup_pairs():
    """返回 dict: lineup[(p1,p2)] = {apps, wins}

    ⚠️ 重要规则（2026-06-06 修复"跨队误判"bug）：
    两人同一天都有出场分数，仅说明两人都出勤了——不代表同队！
    内部三队赛/对内两队赛中，两人很可能被分到不同队，各自分数不同。
    只有"两人同一天分数相同"才能确认两人当天同队，
    此时才计入"共同出场"，分数=3 才计入"共同获胜"。
    """
    with open(ROSTER_CSV, encoding='utf-8-sig') as f:
        content = f.read()
    rows = list(csv.reader(io.StringIO(content)))
    hrow = next(i for i, r in enumerate(rows) if r and r[0] == '名字')
    headers = rows[hrow]

    import datetime
    today = datetime.date.today().strftime('%Y%m%d')
    match_cols = [
        i for i, h in enumerate(headers)
        if h.strip().isdigit() and len(h.strip()) == 8 and h.strip() <= today
    ]

    skip = {'合计', '总计', '名字', '姓名', ''}
    player_rows = []
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        player_rows.append((r[0].strip(), r))

    apps  = defaultdict(int)
    wins  = defaultdict(int)

    for col in match_cols:
        present = []
        for name, r in player_rows:
            val = r[col].strip() if len(r) > col else ''
            if val in ('3', '1', '-1'):
                present.append((name, int(val)))

        for i in range(len(present)):
            for j in range(i + 1, len(present)):
                n1, v1 = present[i]
                n2, v2 = present[j]
                if v1 != v2:
                    continue  # 分数不同 = 当天不同队，不计入"组合"数据（仅说明都出勤了）
                key = (min(n1, n2), max(n1, n2))
                apps[key] += 1
                if v1 == 3:
                    wins[key] += 1

    return apps, wins


# ── 3. 合并成每人的化学反应 ───────────────────────────────────────────────

def build_chemistry(a2me, me2a, apps, wins):
    # 收集所有出现过的球员
    all_players = set(a2me.keys()) | set(me2a.keys())
    for (n1, n2) in apps:
        all_players.add(n1); all_players.add(n2)

    chemistry = {}

    for name in sorted(all_players):
        entry = {}

        # 助攻我最多
        my_a2me = a2me.get(name, {})
        if my_a2me:
            best_ast = max(my_a2me, key=my_a2me.get)
            cnt = my_a2me[best_ast]
            if cnt >= MIN_ASSIST_COUNT:
                entry['a2me'] = {'name': best_ast, 'count': cnt}

        # 我助攻最多
        my_me2a = me2a.get(name, {})
        if my_me2a:
            best_target = max(my_me2a, key=my_me2a.get)
            cnt = my_me2a[best_target]
            if cnt >= MIN_ASSIST_COUNT:
                entry['me2a'] = {'name': best_target, 'count': cnt}

        # 共同出场（从 apps/wins 找此人参与的所有配对）
        pairs = []
        for (n1, n2), total in apps.items():
            if total < MIN_LINEUP_APPS:
                continue
            if n1 == name or n2 == name:
                partner = n2 if n1 == name else n1
                w    = wins.get((min(name, partner), max(name, partner)), 0)
                rate = w / total
                pairs.append({'name': partner, 'apps': total, 'wins': w, 'rate': rate})

        if pairs:
            best  = max(pairs, key=lambda x: x['rate'])
            worst = min(pairs, key=lambda x: x['rate'])
            entry['bestP']  = best
            entry['worstP'] = worst

        if entry:
            chemistry[name] = entry

    return chemistry


# ── 4. 生成 JS ─────────────────────────────────────────────────────────────

def esc(s):
    return s.replace('"', '\\"')

def build_js(chemistry):
    lines = ['const PLAYER_CHEMISTRY = {']
    for name, e in sorted(chemistry.items()):
        inner = []
        if 'a2me' in e:
            d = e['a2me']
            inner.append(f'a2me:{{name:"{esc(d["name"])}",count:{d["count"]}}}')
        if 'me2a' in e:
            d = e['me2a']
            inner.append(f'me2a:{{name:"{esc(d["name"])}",count:{d["count"]}}}')
        if 'bestP' in e:
            d = e['bestP']
            inner.append(f'bestP:{{name:"{esc(d["name"])}",apps:{d["apps"]},wins:{d["wins"]},rate:{d["rate"]:.3f}}}')
        if 'worstP' in e:
            d = e['worstP']
            inner.append(f'worstP:{{name:"{esc(d["name"])}",apps:{d["apps"]},wins:{d["wins"]},rate:{d["rate"]:.3f}}}')
        if inner:
            lines.append(f'  "{esc(name)}": {{{",".join(inner)}}},')
    lines.append('};')
    return '\n'.join(lines)


# ── Main ──────────────────────────────────────────────────────────────────

print("🧪 计算球员化学反应数据…")
a2me, me2a  = parse_assist_pairs()
apps, wins  = parse_lineup_pairs()
chemistry   = build_chemistry(a2me, me2a, apps, wins)
print(f"   覆盖球员: {len(chemistry)} 人")

# 展示几条样例
for name in ['姜珂', '金辉', '潘磊']:
    e = chemistry.get(name, {})
    print(f"   {name}: a2me={e.get('a2me',{}).get('name','—')}({e.get('a2me',{}).get('count','—')}次)  "
          f"me2a={e.get('me2a',{}).get('name','—')}({e.get('me2a',{}).get('count','—')}次)  "
          f"best={e.get('bestP',{}).get('name','—')}({e.get('bestP',{}).get('rate',0):.0%})  "
          f"worst={e.get('worstP',{}).get('name','—')}({e.get('worstP',{}).get('rate',0):.0%})")

if DRY_RUN:
    print("\n[dry-run] 未写入"); sys.exit(0)

new_block = build_js(chemistry)
with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

pat = re.compile(r'const PLAYER_CHEMISTRY = \{.*?\};', re.DOTALL)
src = pat.sub(new_block, src) if pat.search(src) else src.replace(
    'window.RF_DATA = {', new_block + '\n\nwindow.RF_DATA = {')

if 'PLAYER_CHEMISTRY' not in src[src.find('window.RF_DATA'):]:
    src = src.replace('window.RF_DATA = {', 'window.RF_DATA = { PLAYER_CHEMISTRY,')

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)
print(f"\n✅ PLAYER_CHEMISTRY 已写入 data.jsx（{len(chemistry)} 人）")
