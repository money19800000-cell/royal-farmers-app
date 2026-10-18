#!/usr/bin/env python3
"""从逐场花名册计算首次出场及加盟后出勤率；由每日更新流程调用。"""
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_DIR = Path(__file__).resolve().parents[1]
ROSTER_CSV = PROJECT_DIR.parents[1] / 'data/shanghai-farmers-united/花名册-球队花名册.csv'


def compute_attendance(rows, today):
    headerRow = next(i for i, row in enumerate(rows) if row and row[0].strip() == '名字')
    headers = [cell.strip() for cell in rows[headerRow]]
    playerRows = [row for row in rows[headerRow + 1:] if row and row[0].strip() not in {'', '合计', '总计', '名字', '姓名'}]
    # 排除未来排期及整列空白的未进行比赛；保留每一个比赛列（同日多场也分别计数）。
    matchColumns = sorted((date, index) for index, date in enumerate(headers)
                          if re.fullmatch(r'\d{8}', date) and date <= today
                          and any(index < len(row) and row[index].strip() for row in playerRows))
    result = {}
    appsColumn = headers.index('出场')
    for row in playerRows:
        firstIndex = next((i for i, (_, column) in enumerate(matchColumns)
                           if column < len(row) and row[column].strip()), None)
        if firstIndex is None:
            continue
        date = matchColumns[firstIndex][0]
        teamMatches = len(matchColumns) - firstIndex
        totalApps = int(float(row[appsColumn] or 0))
        result[row[0].strip().lower()] = {
            'name': row[0].strip(), 'firstAppearance': f'{date[:4]}-{date[4:6]}-{date[6:]}',
            'totalApps': totalApps, 'teamMatches': teamMatches,
            'rate': totalApps / teamMatches,
        }
    return result


def main():
    with ROSTER_CSV.open(encoding='utf-8-sig') as source:
        stats = compute_attendance(list(csv.reader(source)), datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d'))
    path = PROJECT_DIR / 'data.jsx'
    content = path.read_text()
    block = '// [AUTO] JOIN_ATTENDANCE — computed by compute_join_attendance.py\nconst JOIN_ATTENDANCE = ' + json.dumps(stats, ensure_ascii=False, indent=2) + ';\n'
    pattern = r'// \[AUTO\] JOIN_ATTENDANCE.*?^};\n'
    if re.search(pattern, content, re.S | re.M):
        content = re.sub(pattern, lambda _: block, content, flags=re.S | re.M)
    else:
        content = content.replace('window.RF_DATA = {', block + '\nwindow.RF_DATA = { JOIN_ATTENDANCE,', 1)
    path.write_text(content)
    print(f'JOIN_ATTENDANCE updated: {len(stats)} players')


if __name__ == '__main__':
    main()
