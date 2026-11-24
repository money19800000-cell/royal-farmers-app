#!/usr/bin/env python3
"""Shared updater used by legacy entry points and the final reconciliation."""
import argparse
import copy
from reconcile_stats import ROOT, load_data, write_updates
from relationship_stats import compute_relationships, compute_coattendance
from stats_model import read_roster, parse_matches
from sync_player_photos import parse_photos


def main(mode='all'):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    roster, dates, _ = read_roster()
    photos = parse_photos()
    oldData = load_data()
    data = copy.deepcopy(oldData)
    if mode in ('all', 'assists'):
        data.update(compute_relationships(roster, parse_matches(roster=roster), photos))
    if mode in ('all', 'attendance'):
        data.update(compute_coattendance(roster, dates, photos))
    if not args.dry_run:
        path = ROOT / 'data.jsx'
        temp = path.with_suffix('.jsx.tmp')
        temp.write_text(write_updates(path.read_text(), oldData, data))
        temp.replace(path)
    print(f'✅ 关系统计已按统一规则重算：{mode}' + (' [dry-run]' if args.dry_run else ''))


if __name__ == '__main__':
    main()
