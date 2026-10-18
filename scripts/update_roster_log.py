#!/usr/bin/env python3
"""Synchronize the 2026 per-match attendance log used by Ranking Race.

The season leaderboard gives authoritative totals, but the race chart needs the
date-level matrix in 花名册 to plot a truthful cumulative trajectory. Keeping
this generated prevents the chart from flatlining when only the leaderboard is
updated.
"""

import csv
import datetime
import io
import json
import os
import re
import sys


PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = "/Users/macstudio/Documents/Codex/codex-claude-code-projects/royal-farmers-fc/data/shanghai-farmers-united"
ROSTER_CSV = os.path.join(DATA_DIR, "花名册-球队花名册.csv")
DATA_JSX = os.path.join(PROJECT_DIR, "data.jsx")
DRY_RUN = "--dry-run" in sys.argv
SKIP_NAMES = {"合计", "总计", "名字", "姓名", ""}


def read_attendance_log():
    with open(ROSTER_CSV, encoding="utf-8-sig") as file:
        rows = list(csv.reader(io.StringIO(file.read())))

    header_index = next(i for i, row in enumerate(rows) if row and row[0] == "名字")
    headers = rows[header_index]
    today = datetime.date.today().strftime("%Y%m%d")
    match_columns = [
        (index, value.strip())
        for index, value in enumerate(headers)
        if value.strip().isdigit()
        and len(value.strip()) == 8
        and value.strip().startswith("2026")
        and value.strip() <= today
    ]

    duplicate_dates = {date for _, date in match_columns if sum(d == date for _, d in match_columns) > 1}
    if duplicate_dates:
        raise ValueError(f"花名册包含重复比赛日期，无法无损映射：{sorted(duplicate_dates)}")

    log = []
    for column_index, compact_date in sorted(match_columns, key=lambda item: item[1]):
        attendees = []
        for row in rows[header_index + 1:]:
            if not row or not row[0].strip() or row[0].strip() in SKIP_NAMES:
                continue
            if len(row) > column_index and row[column_index].strip():
                attendees.append(row[0].strip())
        log.append({
            "date": f"{compact_date[:4]}.{compact_date[4:6]}.{compact_date[6:]}",
            "attendees": attendees,
        })
    return log


def render_log(log):
    lines = ["const ROSTER_LOG_2026 = ["]
    for entry in log:
        names = json.dumps(entry["attendees"], ensure_ascii=False, separators=(",", ":"))
        lines.append(f'  {{date:"{entry["date"]}",attendees:{names}}},')
    lines.append("];")
    return "\n".join(lines)


log = read_attendance_log()
if not log:
    raise ValueError("未找到截至今日的 2026 逐场出勤列")

with open(DATA_JSX, encoding="utf-8") as file:
    source = file.read()

replacement = render_log(log)
pattern = r"const ROSTER_LOG_2026 = \[.*?\n\];(?=\n\nconst MATCH_DATA)"
updated_source, replacements = re.subn(pattern, replacement, source, count=1, flags=re.DOTALL)
if replacements != 1:
    raise ValueError("未找到唯一的 ROSTER_LOG_2026 数据块")

if not DRY_RUN and updated_source != source:
    with open(DATA_JSX, "w", encoding="utf-8") as file:
        file.write(updated_source)

print(
    f"✅ ROSTER_LOG_2026 updated: {len(log)} 场，"
    f"{log[0]['date']} → {log[-1]['date']}，"
    f"最新场出勤 {len(log[-1]['attendees'])} 人"
)
if DRY_RUN:
    print("[dry-run] 未写入 data.jsx")
