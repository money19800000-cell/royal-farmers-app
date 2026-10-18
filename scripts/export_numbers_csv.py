#!/usr/bin/env python3
"""
Royal Farmers FC — Numbers → CSV 导出脚本
直接读取 iCloud 上的 .numbers 文件，无需打开 Numbers App

依赖: pip install numbers-parser
运行: python3 scripts/export_numbers_csv.py
"""
import csv
import os
import sys
import datetime
import tempfile
from pathlib import Path

try:
    import numbers_parser
except ImportError:
    print("❌ 缺少依赖: pip install numbers-parser")
    sys.exit(1)

NUMBERS_FILE = (
    "/Users/macstudio/Library/Mobile Documents/"
    "com~apple~Numbers/Documents/shanghai farmers united.numbers"
)
OUTPUT_DIR = (
    "/Users/macstudio/Documents/Codex/codex-claude-code-projects/royal-farmers-fc/data/shanghai-farmers-united"
)

# 需要导出的表：(sheet名, table名, 输出文件名)
EXPORT_TABLES = [
    ("花名册",         "球队花名册",                    "花名册-球队花名册.csv"),
    ("每场战报+总数据", "总出场数",                     "每场战报+总数据-总出场数.csv"),
    ("每场战报+总数据", "具体战况",                     "每场战报+总数据-具体战况.csv"),
    ("每场战报+总数据", "总射手榜",                     "每场战报+总数据-总射手榜.csv"),
    ("每场战报+总数据", "总助攻榜",                     "每场战报+总数据-总助攻榜.csv"),
    ("每场战报+总数据", "记录",                         "每场战报+总数据-记录.csv"),
    ("每场战报+总数据", "最佳11人",                     "每场战报+总数据-最佳11人.csv"),
    ("每场战报+总数据", "最佳8人",                      "每场战报+总数据-最佳8人.csv"),
    ("每场战报+总数据", "团队场均成绩积分（出场大于40）", "每场战报+总数据-团队场均成绩积分（出场大于40）.csv"),
]


def cell_to_str(cell) -> str:
    """将单元格值转为 CSV 字符串，保持与手动导出格式一致"""
    v = cell.value
    if v is None:
        return ""
    # 整数浮点（如 327.0 → "327"，260604.0 → "260604"）
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return str(v)
    if isinstance(v, datetime.datetime):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, datetime.date):
        return v.strftime("%Y-%m-%d")
    return str(v)


def export_table(doc, sheet_name: str, table_name: str, output_path: str) -> bool:
    sheet = next((s for s in doc.sheets if s.name == sheet_name), None)
    if not sheet:
        print(f"   ⚠️  未找到 sheet: {sheet_name!r}")
        return False
    table = next((t for t in sheet.tables if t.name == table_name), None)
    if not table:
        print(f"   ⚠️  未找到 table: {table_name!r}")
        return False

    rows = list(table.rows())
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow([cell_to_str(c) for c in row])

    # 统计非空行数
    data_rows = sum(1 for r in rows if any(c.value is not None for c in r))
    print(f"   ✅ {output_path.split('/')[-1]}  ({len(rows)} 行, {data_rows} 非空行)")
    return True


OPTIONAL_TABLES = {'每场战报+总数据-团队场均成绩积分（出场大于40）.csv'}


def export_tables(doc, output_dir):
    """Do not mix yesterday's CSV with a partially failed fresh export."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.csv-export-', dir=destination) as folder:
        exported, missing = [], []
        for sheet_name, table_name, filename in EXPORT_TABLES:
            if export_table(doc, sheet_name, table_name, str(Path(folder)/filename)):
                exported.append(filename)
            elif filename not in OPTIONAL_TABLES:
                missing.append(filename)
        if missing:
            raise RuntimeError('必要数据表导出失败，保留上次完整 CSV 并停止同步：' + ', '.join(missing))
        for filename in exported:
            (Path(folder)/filename).replace(destination/filename)
        print(f'✅ 完整数据快照已更新：{len(exported)} 张表；缺失的旧辅助表不参与统计')


if __name__ == "__main__":
    print(f"📋 读取 Numbers 文件: {os.path.basename(NUMBERS_FILE)}")
    if not os.path.exists(NUMBERS_FILE):
        sys.exit('❌ Numbers 文件不存在，请先完成 iCloud 同步')
    export_tables(numbers_parser.Document(NUMBERS_FILE), OUTPUT_DIR)
