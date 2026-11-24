"""Personal assist links and co-attendance, without inferring team membership."""
from collections import Counter, defaultdict
from itertools import combinations
from stats_model import person

MIN_LINEUP_APPS = 20


def compute_relationships(roster, matches, photos):
    pairEvents = defaultdict(list)
    seasonCounts = defaultdict(Counter)
    for match in matches:
        for side in ('home', 'away'):
            for index, (scorer, assister) in enumerate(zip(match[side+'Scorers'], match[side+'Assists'])):
                if not person(scorer) or not person(assister) or scorer == assister:
                    continue
                # Personal records include registered players guesting for the
                # other side; unrelated external opponents are not club players.
                if not match[side+'Rf'] and scorer not in roster and assister not in roster:
                    continue
                pair = (scorer, assister)
                pairEvents[pair].append({'date': match['date'], 'matchId': match['id'],
                                        'home': match['home'], 'away': match['away'], 'side': side,
                                        'eventIndex': index, 'sourceLine': match.get(side+'EventLines', [])[index]
                                        if index < len(match.get(side+'EventLines', [])) else match['sourceLine']})
                seasonCounts[match['dateCode'][:4]][pair] += 1
    received, given = defaultdict(list), defaultdict(list)
    for (scorer, assister), events in pairEvents.items():
        received[scorer].append({'name': assister, 'count': len(events)})
        given[assister].append({'name': scorer, 'count': len(events)})
    chemistry = {}
    for name in sorted(received.keys() | given.keys()):
        entry = {}
        for key, rankings in [('a2me', received[name]), ('me2a', given[name])]:
            if not rankings:
                continue
            rankings.sort(key=lambda row: (-row['count'], row['name']))
            leaders = [row['name'] for row in rankings if row['count'] == rankings[0]['count']]
            entry[key] = {**rankings[0], 'names': leaders}
            # Only top links need event detail; every partner retains its count.
            entry[key+'Partners'] = rankings
            entry[key+'Events'] = sorted([
                {**event, 'partner': partner}
                for partner in leaders
                for event in pairEvents[(name, partner) if key == 'a2me' else (partner, name)]
            ], key=lambda event: (event['date'], event['sourceLine'], event['partner']))
        chemistry[name] = entry
    allCounts = Counter({pair: len(events) for pair, events in pairEvents.items()})
    years = sorted({season['year'] for player in roster.values() for season in player.get('seasons', [])})
    goldenPairs = {}
    for period in ['all', *years]:
        counts = allCounts if period == 'all' else seasonCounts[period]
        ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        limit = 20 if period == 'all' else 12
        # Include all ties at the leaderboard cutoff.
        cutoff = ordered[min(limit, len(ordered))-1][1] if ordered else 0
        goldenPairs[period] = [dict(scorer=g, ast=a, count=count,
            sNum=roster.get(g, {}).get('num', ''), aNum=roster.get(a, {}).get('num', ''),
            sPhoto=photos.get(g), aPhoto=photos.get(a))
            for (g, a), count in ordered if count >= cutoff]
    return {'PLAYER_CHEMISTRY': chemistry, 'GOLDEN_PAIRS': goldenPairs}


def compute_coattendance(roster, dates, photos):
    apps, wins = Counter(), Counter()
    matchData = {name: ''.join({'3': '3', '1': '1', '-1': 'L'}.get(player['attendance'][day], 'U')
                              if day in player['attendance'] else ' ' for day, _ in dates)
                 for name, player in roster.items() if player['attendance']}
    for day, _ in dates:
        present = sorted(name for name, player in roster.items() if day in player['attendance'])
        for pair in combinations(present, 2):
            apps[pair] += 1
            if all(roster[name]['attendance'][day] == '3' for name in pair):
                wins[pair] += 1
    allPairs = {'|'.join(pair): dict(apps=count, wins=wins[pair], rate=wins[pair]/count)
                for pair, count in sorted(apps.items()) if count >= MIN_LINEUP_APPS}
    # Preserve the full eligible set so changing sort order cannot lose leaders.
    rankings = [dict(p1=a, p2=b, p1n=roster[a]['num'], p2n=roster[b]['num'],
                     p1ph=photos.get(a), p2ph=photos.get(b), **allPairs[a+'|'+b])
                for (a, b), count in apps.items() if count >= MIN_LINEUP_APPS]
    rankings.sort(key=lambda row: (-row['rate'], -row['apps'], row['p1'], row['p2']))
    return {'LINEUP_ALL': allPairs, 'LINEUP_STATS': rankings, 'MATCH_DATA': matchData}
