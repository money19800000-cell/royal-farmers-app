"""Repair evidenced away-column shifts in memory; never rewrite source files."""
from collections import Counter, defaultdict
from copy import deepcopy


def normalize_match_columns(rows, dateCode, isTeam, person):
    normalized = []
    corrections = []
    shiftedHeader = None
    for line, cells in enumerate(rows, 1):
        row = [cell.strip() for cell in cells] + [''] * max(0, 11 - len(cells))
        code = dateCode(row[1])
        hasScore = row[6].isdigit() or row[7].isdigit()
        if row[1] and (code is None or hasScore):
            shiftedHeader = None
            if code and hasScore and not row[8] and isTeam(row[9]):
                shiftedHeader = (line, row[1], code)
                row[8], row[9] = row[9], ''
        elif row[1] and shiftedHeader and row[1] != shiftedHeader[1]:
            shiftedHeader = None
        # A shifted team label alone is insufficient: some fixtures have a
        # shifted header but ordinary detail columns. Require the extra assist
        # cell (including an explicit '/') and an empty ordinary scorer cell.
        if shiftedHeader and line != shiftedHeader[0] and not row[8] and person(row[9]) and row[10]:
            corrections.append(dict(sourceLine=line, headerLine=shiftedHeader[0],
                                    sourceMatchId=shiftedHeader[1], dateCode=shiftedHeader[2],
                                    rawScorer=row[8], rawAssist=row[9], scorer=row[9], assist=row[10]))
            row[8], row[9], row[10] = row[9], row[10], ''
        normalized.append(row)
    return normalized, corrections


def reconcile_roster_columns(players, rawRows, corrections, dateCode, person, asOf):
    """Apply only proven column deltas, with guards against double correction.

    Numbers formulas count the fixed goal/assist columns. Check each affected
    season against those raw counts before changing it, and accept an already
    corrected summary unchanged. An unrelated difference remains an error.
    """
    rawTotals = Counter()
    year = None
    for cells in rawRows:
        row = [cell.strip() for cell in cells] + [''] * max(0, 10 - len(cells))
        if row[1]:
            code = dateCode(row[1])
            year = code[:4] if code else None
        if year:
            for metric, columns in [('goals', (4, 8)), ('assists', (5, 9))]:
                for column in columns:
                    if person(row[column]):
                        rawTotals[year, row[column], metric] += 1
    deltas = Counter()
    evidence = defaultdict(list)
    for correction in corrections:
        if correction['dateCode'] > asOf:
            continue
        year = correction['dateCode'][:4]
        for metric, rawKey, fixedKey in [('goals', 'rawScorer', 'scorer'), ('assists', 'rawAssist', 'assist')]:
            for field, sign in [(rawKey, -1), (fixedKey, 1)]:
                name = person(correction[field])
                if name in players:
                    key = (year, name, metric)
                    deltas[key] += sign
                    evidence[key].append(correction['sourceLine'])
    for player in players.values():
        player['rawSeasons'] = deepcopy(player['seasons'])
        player['sourceCorrections'] = []
    for (year, name, metric), delta in sorted(deltas.items()):
        if not delta:
            continue
        player = players[name]
        season = next((season for season in player['seasons'] if season['year'] == year), None)
        rawTotal = rawTotals[year, name, metric]
        fixedTotal = rawTotal + delta
        if season is None or season[metric] not in (rawTotal, fixedTotal) or fixedTotal < 0:
            raise ValueError(f'错列修正与汇总不一致：{name} {year} {metric}；需核查源表')
        before = season[metric]
        season[metric] = fixedTotal
        player['sourceCorrections'].append(dict(year=year, metric=metric, rawColumnTotal=rawTotal,
                                               before=before, after=fixedTotal, sourceLines=sorted(set(evidence[year, name, metric]))))
    for player in players.values():
        for metric in {item['metric'] for item in player['sourceCorrections']}:
            before = sum(season[metric] for season in player['rawSeasons'])
            after = sum(season[metric] for season in player['seasons'])
            if player[metric] not in (before, after):
                raise ValueError(f'错列修正与生涯汇总不一致：{player["name"]} {metric}；需核查源表')
            player[metric] = after
