#!/usr/bin/env python3
"""Compute milestone crossing dates from chronological match detail.

Goals/assists use the match CSV; attendance uses roster date columns.
Both the daily updater and final build call this same calculation.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from stats_model import read_roster, parse_matches, person, today_code
from sync_player_photos import parse_photos

ROOT = Path(__file__).resolve().parents[1]
METRIC_LABELS = {'apps': '出场', 'goals': '进球', 'assists': '助攻'}


def compute_milestones(roster=None, matches=None, as_of=None, photos=None):
    as_of = as_of or today_code()
    if roster is None:
        roster = read_roster(as_of=as_of)[0]
    if matches is None:
        matches = parse_matches(as_of=as_of)
    if photos is None:
        photos = parse_photos()
    # Aggregate same-day fixtures before accumulating; CSV order is irrelevant.
    events = defaultdict(lambda: defaultdict(Counter))
    for match in matches:
        day = match['dateCode']
        if day > as_of:
            continue
        for side in ('home', 'away'):
            if not match[side+'Rf']:
                continue
            for metric, field in [('goals', 'Scorers'), ('assists', 'Assists')]:
                for name in match[side+field]:
                    if person(name) and name != '进球者待确认':
                        events[person(name)][metric][day] += 1

    milestones = []
    # Match detail is the source of truth for goals/assists. Summary differences
    # must neither erase a recorded crossing nor invent an unrecorded one.
    for name in sorted(set(roster) | set(events)):
        player = roster.get(name, {})
        displayName = f"{player['num']}号{name}" if player.get('num') else name
        for metric, label in METRIC_LABELS.items():
            days = (Counter({d: 1 for d in player.get('attendance', {}) if d <= as_of})
                    if metric == 'apps' else events[name][metric])
            careerTotal = 0
            seasonTotals = Counter()
            for day, count in sorted(days.items()):
                year = int(day[:4])
                for scope, before in [('career', careerTotal), ('season', seasonTotals[year])]:
                    after = before + count
                    for threshold in range((before // 100 + 1) * 100, after + 1, 100):
                        eventType = f'{scope}_{metric}'
                        milestones.append(dict(
                            id=f'{name}:{eventType}:{year if scope == "season" else "all"}:{threshold}',
                            date=f'{day[:4]}-{day[4:6]}-{day[6:]}', dateStatus='exact',
                            achievedYear=year, name=name, num=player.get('num', ''), photo=photos.get(name),
                            label=f'{displayName}{"生涯" if scope == "career" else f" {year}赛季"}{label}达{threshold}',
                            type=eventType, value=threshold, season=year if scope == 'season' else None,
                            dateReason='', dateSource='roster_attendance' if metric == 'apps' else 'match_details',
                        ))
                careerTotal += count
                seasonTotals[year] += count
    return sorted(milestones, key=lambda m: (m['date'], m['id']))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    milestones = compute_milestones()
    pending = sum(m['dateStatus'] != 'exact' for m in milestones)
    print(f'里程碑 {len(milestones)} 条；日期已核实 {len(milestones)-pending} 条，待核实 {pending} 条')
    if not args.dry_run:
        path = ROOT / 'data.jsx'
        block = 'const MILESTONES = ' + json.dumps(milestones, ensure_ascii=False, indent=2) + ';'
        source, count = re.subn(r'const MILESTONES = \[[\s\S]*?\];', lambda _: block, path.read_text(), count=1)
        if count != 1:
            raise ValueError('Expected exactly one MILESTONES block')
        path.write_text(source)


if __name__ == '__main__':
    main()
