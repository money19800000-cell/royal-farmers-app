#!/usr/bin/env python3
"""Rebuild player profiles from the latest roster CSV, including renames/removals.

Usage: python3 scripts/update_players.py [--dry-run]
The final build uses this same profile rule; cached stats are never a source.
"""
import argparse
import copy
from reconcile_stats import ROOT, load_data, rebuild_player_profiles, write_updates
from stats_model import read_roster
from sync_player_photos import parse_photos


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    roster, _, _ = read_roster()
    oldData = load_data()
    data = copy.deepcopy(oldData)
    profiles = rebuild_player_profiles(data, roster, parse_photos())
    oldNames = {p['name'] for p in [*oldData['PLAYERS'], *oldData['PLAYER_LOOKUP'].values()]}
    print(f'最新花名册：{len(profiles)} 人；移除失效名字：{len(oldNames - profiles.keys())}；新增名字：{len(profiles.keys() - oldNames)}')
    if args.dry_run:
        print('[dry-run] 未写入文件')
        return
    path = ROOT / 'data.jsx'
    updated = write_updates(path.read_text(), oldData, data)
    temp = path.with_suffix('.jsx.tmp')
    temp.write_text(updated)
    temp.replace(path)
    print('✅ PLAYERS / PLAYER_LOOKUP 已按最新 CSV 重建')


if __name__ == '__main__':
    main()
