#!/usr/bin/env python3
"""
compute_lineup_stats.py — 从花名册评分列计算联合阵容胜率

每个评分列 = 一场比赛，值 3=胜/1=平/-1=负/空=未参赛
对每场参赛名单求配对，统计：共同出场次数、共同获胜次数、胜率

输出: LINEUP_STATS = [{p1,p1n,p1ph,p2,p2n,p2ph,apps,wins,rate}, ...]
"""
import csv, io, re, os, sys
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = "/Users/macstudio/claude code/numbers数据来源/shanghai farmers united"
ROSTER_CSV  = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
DATA_JSX    = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN     = "--dry-run" in sys.argv

MIN_APPS   = 50   # 最少共同出场次数才上榜
TOP_N      = 30   # 输出前 N 对
TOP_PARTNER = 8   # 每人最多显示几个最佳搭档

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
    hrow = next(i for i,r in enumerate(rows) if r and r[0]=='名字')
    headers = rows[hrow]

    # 找所有比赛列（8位数字日期）
    import datetime
    today = datetime.date.today().strftime('%Y%m%d')
    match_cols = [
        i for i, h in enumerate(headers)
        if h.strip().isdigit() and len(h.strip()) == 8 and h.strip() <= today
    ]

    # 球员名 → 球衣号
    skip = {'合计','总计','名字','姓名',''}
    name2num = {}
    player_rows = []
    for r in rows[hrow+1:]:
        if not r or not r[0].strip() or r[0].strip() in skip:
            continue
        name = r[0].strip()
        num  = r[4].strip() if len(r) > 4 else ''
        name2num[name] = num
        player_rows.append((name, r))

    # 对每场比赛：统计参赛名单和结果
    # apps[pair] = 共同出场次数
    # wins[pair] = 共同获胜次数
    apps  = defaultdict(int)
    wins  = defaultdict(int)

    for col in match_cols:
        present = []  # (name, result_val)
        for name, r in player_rows:
            val = r[col].strip() if len(r) > col else ''
            if val in ('3', '1', '-1'):
                present.append((name, int(val)))

        # 对参赛名单中每对球员统计
        for i in range(len(present)):
            for j in range(i+1, len(present)):
                n1, v1 = present[i]
                n2, v2 = present[j]
                key = (min(n1,n2), max(n1,n2))
                apps[key] += 1
                if v1 == 3 and v2 == 3:
                    wins[key] += 1

    return apps, wins, name2num


def build_js(apps, wins, name2num):
    # 过滤 min_apps，按胜率排序
    pairs = [
        (k, apps[k], wins[k], wins[k]/apps[k])
        for k in apps if apps[k] >= MIN_APPS
    ]
    pairs.sort(key=lambda x: -x[3])

    lines = [f'const LINEUP_STATS = [']
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


# ── Main ──
print("👥 计算联合阵容胜率…")
apps, wins, name2num = parse()
print(f"   有效配对数（≥{MIN_APPS}场）: {sum(1 for k in apps if apps[k]>=MIN_APPS)}")
top5 = sorted([(k,apps[k],wins[k],wins[k]/apps[k]) for k in apps if apps[k]>=MIN_APPS], key=lambda x:-x[3])[:5]
for (n1,n2),a,w,r in top5:
    print(f"   {n1}+{n2}: {a}场 {w}胜 胜率{r:.1%}")

if DRY_RUN:
    print("\n[dry-run] 未写入")
    sys.exit(0)

new_block = build_js(apps, wins, name2num)

with open(DATA_JSX, encoding='utf-8') as f:
    src = f.read()

pat = re.compile(r'const LINEUP_STATS = \[.*?\];', re.DOTALL)
src = pat.sub(new_block, src) if pat.search(src) else src.replace(
    'window.RF_DATA = {', new_block + '\n\nwindow.RF_DATA = {')

if 'LINEUP_STATS' not in src[src.find('window.RF_DATA'):]:
    src = src.replace('window.RF_DATA = {', 'window.RF_DATA = { LINEUP_STATS,')

with open(DATA_JSX, 'w', encoding='utf-8') as f:
    f.write(src)
print(f"\n✅ LINEUP_STATS 已写入 data.jsx（Top{TOP_N}，≥{MIN_APPS}场门槛）")
