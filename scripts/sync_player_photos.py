#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描 assets/players/ 目录，把新增图片路径写入 data.jsx 中 PLAYERS 数组的球员条目。
只处理同时含有 num: / name: / pos: / nation: 的完整球员档案行，不碰比赛记录。
"""

import re
import sys
from pathlib import Path

SRC_DIR  = Path(__file__).parent.parent
DATA_JSX = SRC_DIR / "data.jsx"
PHOTO_DIR = SRC_DIR / "assets" / "players"

# 完整球员档案行的特征：同时包含这几个字段
PLAYER_LINE_FIELDS = {"num:", "name:", "pos:", "nation:"}


def parse_photos() -> dict[str, str]:
    """返回 {姓名: 相对路径}"""
    photos = {}
    for f in PHOTO_DIR.glob("*.jpeg"):
        m = re.match(r"^\d+号(.+)\.jpeg$", f.name)
        if m:
            photos[m.group(1)] = f"assets/players/{f.name}"
    return photos


def is_player_line(line: str) -> bool:
    """判断是否为 PLAYERS 数组中的完整球员档案行"""
    return all(field in line for field in PLAYER_LINE_FIELDS)


def sync(data: str, photos: dict[str, str]) -> tuple[str, int]:
    lines = data.splitlines(keepends=True)
    count = 0

    for i, line in enumerate(lines):
        if not is_player_line(line):
            continue

        m = re.search(r'name:\s*"([^"]+)"', line)
        if not m:
            continue
        name = m.group(1)
        if name not in photos:
            continue
        path = photos[name]

        # 已有正确路径 → 跳过
        if f'photo: "{path}"' in line:
            continue

        # photo: null → 替换
        if re.search(r'photo:\s*null', line):
            lines[i] = re.sub(r'photo:\s*null', f'photo: "{path}"', line)
            count += 1
            print(f"  ✅ {name}: null → {path}")
            continue

        # 已有其他路径 → 不覆盖
        if re.search(r'photo:\s*"', line):
            continue

        # 无 photo 字段 → 在行末 } 前插入
        new_line = re.sub(
            r'(\s*}\s*,?\s*\n?)$',
            lambda mo: f', photo: "{path}"{mo.group(1)}',
            line
        )
        if new_line != line:
            lines[i] = new_line
            count += 1
            print(f"  ✅ {name}: 新增 → {path}")

    return "".join(lines), count


def main():
    if not DATA_JSX.exists():
        print(f"❌ 找不到 {DATA_JSX}")
        sys.exit(1)

    photos = parse_photos()
    print(f"📷 找到 {len(photos)} 张球员图片")

    data = DATA_JSX.read_text(encoding="utf-8")
    new_data, count = sync(data, photos)

    if count == 0:
        print("所有图片已绑定，无需更新")
        return

    DATA_JSX.write_text(new_data, encoding="utf-8")
    print(f"\n✅ data.jsx 更新完成，共绑定 {count} 个球员")


if __name__ == "__main__":
    main()
