#!/usr/bin/env python3
"""
compute_lineup_stats.py — 从花名册评分列计算联合阵容胜率

每个评分列 = 一个比赛日，值 3=胜/1=平/-1=负/空=未出场
⚠️ 重要规则（2026-06-06 修复"跨队误判"bug）：
  两人同一天都有分数，仅说明两人都出勤了——不代表同队！
  内部三队赛/对内两队赛中，两人很可能被分到不同队，各自分数不同。
  只有"两人同一天分数相同"才能确认两人当天同队，
  此时才计入"共同出场"，分数=3 才计入"共同获胜"。
  即：v1 == v2 → 同队出场；v1 == v2 == '3' → 同队获胜。

对每场参赛名单求"同队"配对，统计：共同出场次数、共同获胜次数、胜率

输出:
  LINEUP_STATS  — 按胜率排序的 Top N 对（主榜展示用）
  LINEUP_ALL    — 所有 ≥MIN_APPS 的配对查询字典（自由组合2人即时查询）
  MATCH_DATA    — 每位球员的逐场参赛字符串（自由组合3人实时计算，按"分数相同"判同队）
"""
import csv, io, re, os, sys
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
ROSTER_CSV  = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

MIN_APPS   = 20   # 最少共同出场次数才上榜/入字典
TOP_N      = 30   # LINEUP_STATS 展示前 N 对

PHOTO_MAP = {
    "1":"assets/players/22号麦超.jpeg","10":"assets/players/10号姜珂.jpeg",
    "14":"assets/players/14号夏浩.jpeg","17":"assets/players/17号张伟.jpeg",
    "18":"assets/players/18号黄纲.jpeg","22":"assets/players/22号鲍梁剑.jpeg",
    "24":"assets/players/24号陆晓巍.jpeg","25":"assets/players/25号鲁尼.jpeg",
    "33":"assets/players/33号季贝赢.jpeg","38":"assets/players/38号鲍澜云.jpeg",
    "41":"assets/players/41号老吴.jpeg","44":"assets/players/44号倪海.jpeg",
    "56":"assets/players/56号朱寿卿.jpeg","6":"assets/players/6号陶骏.jpeg",
    "68":"assets/players/68号王刚.jpeg","76":"assets/players/76号薛峰.jpeg",
    "81":"assets/players/81号金辉.jpeg","88":"assets/players/88号王积鹏.jpeg",
    "92":"assets/players/92号圣托尔多.jpeg","98":"assets/players/98号姚魏.jpeg",
}
NAME_PHOTO = {"朱寿卿":"assets/players/56号朱寿卿.jpeg"}

def photo(name, num):
    if name in NAME_PHOTO: return NAME_PHOTO[name]
    return PHOTO_MAP.get(str(num))


def parse():
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
    name2num = {}
    player_rows = []
    for r in rows[hrow + 1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        num  = r[4].strip() if len(r) > 4 else ''
        name2num[name] = num
        player_rows.append((name, r))

    # 逐场统计
    apps  = defaultdict(int)
    wins  = defaultdict(int)
    # MATCH_DATA: 每位球员逐场参赛字符串
    # 字符：'3'=胜, '1'=平, 'L'=负, ' '=未参赛
    match_data = {name: [] for name, _ in player_rows}

    for col in match_cols:
        present = []
        for name, r in player_rows:
            val = r[col].strip() if len(r) > col else ''
            if val == '3':
                match_data[name].append('3')
                present.append((name, 3))
            elif val == '1':
                match_data[name].append('1')
                present.append((name, 1))
            elif val == '-1':
                match_data[name].append('L')
                present.append((name, -1))
            else:
                match_data[name].append(' ')

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

    # 把列表转成字符串
    match_data_str = {name: ''.join(chars) for name, chars in match_data.items()}

    return apps, wins, name2num, match_data_str


def build_lineup_stats(apps, wins, name2num):
    pairs = [
        (k, apps[k], wins[k], wins[k] / apps[k])
        for k in apps if apps[k] >= MIN_APPS
    ]
    pairs.sort(key=lambda x: -x[3])
    lines = ['const LINEUP_STATS = [']
    for (n1, n2), total, w, rate in pairs[:TOP_N]:
        num1 = name2num.get(n1, '')
        num2 = name2num.get(n2, '')
        ph1  = photo(n1, num1)
        ph2  = photo(n2, num2)
        sp1  = f'"{ph1}"' if ph1 else 'null'
        sp2  = f'"{ph2}"' if ph2 else 'null'
        lines.append(
            f'  {{p1:"{n1}",p1n:"{num1}",p1ph:{sp1},'
            f'p2:"{n2}",p2n:"{num2}",p2ph:{sp2},'
            f'apps:{total},wins:{w},rate:{rate:.3f}}},'
        )
    lines.append('];')
    return '\n'.join(lines)


def build_lineup_all(apps, wins):
    """生成所有 ≥MIN_APPS 的配对字典，用于自由组合2人即时查询"""
    lines = ['const LINEUP_ALL = {']
    for (n1, n2) in sorted(apps):
        a = apps[(n1, n2)]
        if a < MIN_APPS:
            continue
        w = wins.get((n1, n2), 0)
        r = w / a
        n1e = n1.replace('"', '\\"')
        n2e = n2.replace('"', '\\"')
        lines.append(f'  "{n1e}|{n2e}":{{apps:{a},wins:{w},rate:{r:.3f}}},')
    lines.append('};')
    return '\n'.join(lines)


def build_match_data(match_data_str, name2num):
    """生成紧凑的逐场参赛字符串，用于自由组合3人实时计算"""
    lines = ['const MATCH_DATA = {']
    for name, s in sorted(match_data_str.items()):
        # 只保留有出场记录的球员（避免全空字符串浪费空间）
        if s.replace(' ', ''):
            ne = name.replace('"', '\\"')
            lines.append(f'  "{ne}":"{s}",')
    lines.append('};')
    return '\n'.join(lines)


# ── Main ──
print("👥 计算联合阵容数据（门槛≥20场）…")
apps, wins, name2num, match_data_str = parse()

valid = sum(1 for k in apps if apps[k] >= MIN_APPS)
print(f"   有效配对数（≥{MIN_APPS}场）: {valid}")
print(f"   MATCH_DATA 球员数: {sum(1 for s in match_data_str.values() if s.replace(' ',''))}")

top5 = sorted(
    [(k, apps[k], wins[k], wins[k] / apps[k]) for k in apps if apps[k] >= MIN_APPS],
    key=lambda x: -x[3]
)[:5]
for (n1, n2), a, w, r in top5:
    print(f"   {n1}+{n2}: {a}场 {w}胜 {r:.1%}")

if DRY_RUN:
    print("\n[dry-run] 未写入"); sys.exit(0)

ls_block  = build_lineup_stats(apps, wins, name2num)
la_block  = build_lineup_all(apps, wins)
md_block  = build_match_data(match_data_str, name2num)

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

def upsert(src, var, new_block):
    pat = re.compile(rf'const {re.escape(var)} = [\[{{].*?[\]}};]', re.DOTALL)
    # 更宽松的替换：从 const VAR 到第一个独立的 }; 或 ];
    pat2 = re.compile(rf'const {re.escape(var)} = (?:\[|\{{).*?(?:\]|\}});', re.DOTALL)
    if pat2.search(src):
        return pat2.sub(new_block, src)
    return src.replace('window.RF_DATA = {', new_block + '\n\nwindow.RF_DATA = {')

src = upsert(src, 'LINEUP_STATS', ls_block)
src = upsert(src, 'LINEUP_ALL',   la_block)
src = upsert(src, 'MATCH_DATA',   md_block)

for var in ['LINEUP_STATS', 'LINEUP_ALL', 'MATCH_DATA']:
    if var not in src[src.find('window.RF_DATA'):]:
        src = src.replace('window.RF_DATA = {', f'window.RF_DATA = {{ {var},')

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)

print(f"\n✅ 已写入 data.jsx:")
print(f"   LINEUP_STATS: Top{TOP_N}（≥{MIN_APPS}场，按胜率）")
print(f"   LINEUP_ALL:   {valid} 对查询字典")
print(f"   MATCH_DATA:   逐场参赛字符串（自由组合3人用）")
