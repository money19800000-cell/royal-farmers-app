"""Canonical roster/match rules. Pure readers; never alter the source CSV files."""
from __future__ import annotations

import csv
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DATA_DIR = Path(__file__).resolve().parents[3] / 'data/shanghai-farmers-united'
SKIP_NAMES = {'', '名字', '姓名', '合计', '总计'}
INTERNAL_TEAMS = {'蓝队', '红队', '白队', '黄队', '绿队', '黑队', '一队', '二队'}
BAD_NAMES = {'', '/', '?', '？', 'None', 'null', 'OG', '乌龙'}
EXTERNAL_TWO = '外部友谊赛（两队）'
MATCH_TYPES = {EXTERNAL_TWO, '外部友谊赛（三队）', '内部友谊赛（两队）', '内部友谊赛（三队）'}


def today_code():
    return datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y%m%d')


def number(raw, default=0):
    try:
        return float(raw) if '.' in str(raw) else int(raw)
    except (ValueError, TypeError):
        return default


def date_code(raw):
    digits = raw.strip().split('-')[0].replace('.', '')
    if len(digits) == 6:
        digits = '20' + digits
    if not re.fullmatch(r'20\d{6}', digits):
        return None
    try:
        date(int(digits[:4]), int(digits[4:6]), int(digits[6:]))
        return digits
    except ValueError:
        return None


def display_date(code):
    return f'{code[:4]}.{code[4:6]}.{code[6:]}'


def normalize_type(raw):
    return raw.strip().replace('对外', '外部').replace('对内', '内部').replace('內部', '内部').replace('(', '（').replace(')', '）')


def is_rf(raw):
    return raw in INTERNAL_TEAMS or 'Royal Farmers' in raw or '皇家农' in raw


def person(raw):
    raw = raw.strip()
    return '' if raw in BAD_NAMES or '没拍全' in raw or '?' in raw or '？' in raw else raw


def read_roster(path=None, as_of=None):
    as_of = as_of or today_code()
    with (path or DATA_DIR / '花名册-球队花名册.csv').open(encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    start = next(i for i, r in enumerate(rows) if r and r[0].strip() == '名字')
    headers = [h.strip() for h in rows[start]]
    columns = {h: i for i, h in enumerate(headers) if h}
    dates = sorted((h, i) for i, h in enumerate(headers) if re.fullmatch(r'20\d{6}', h) and h <= as_of)
    if len({d for d, _ in dates}) != len(dates):
        raise ValueError('Duplicate roster match-day columns')
    years = sorted({h[:4] for h in headers if re.fullmatch(r'20\d{2}出场', h)})
    players = {}
    for row in rows[start + 1:]:
        if not row or row[0].strip() in SKIP_NAMES:
            continue
        def cell(k):
            i = columns.get(k)
            return row[i].strip() if i is not None and i < len(row) else ''
        name = row[0].strip()
        if name in players:
            raise ValueError(f'Duplicate player: {name}')
        seasons = []
        for year in years:
            s = {'year': year, 'apps': number(cell(year+'出场')), 'goals': number(cell(year+'进球')), 'assists': number(cell(year+'助攻')), 'rating': number(cell(year+'团队分'), None)}
            if any(s[k] for k in ('apps', 'goals', 'assists')):
                seasons.append(s)
        apps = number(cell('出场'))
        team_score = number(cell('团队总成绩'), None)
        attendance = {d: row[i].strip() for d, i in dates if i < len(row) and row[i].strip()}
        p = {'name': name, 'num': cell('号码'), 'pos': cell('位置') or '—', 'birth': cell('出生日期') or '—', 'nation': cell('国籍') or '—',
             'apps': apps, 'goals': number(cell('进球')), 'assists': number(cell('助攻')), 'rating': team_score,
             'careerRating': team_score / apps if team_score is not None and apps else None,
             'seasons': seasons, 'r50': sum(d in attendance for d, _ in dates[-50:]), 'attendance': attendance}
        # Preserve source totals; discrepancies are reported rather than invented corrections.
        p['sourceDifference'] = {k: p[k] - sum(s[k] for s in seasons) for k in ('apps', 'goals', 'assists')}
        p['rawSummary'] = {k: p[k] for k in ('apps', 'goals', 'assists', 'rating')}
        # The exported career-score formula stops before 2026. Recompute attendance
        # and scores from dated cells instead, excluding prefilled future columns.
        p['apps'] = len(attendance)
        p['rating'] = sum(number(value) for value in attendance.values())
        p['careerRating'] = p['rating'] / p['apps'] if p['apps'] else None
        by_year = {s['year']: s for s in seasons}
        for year in years:
            cells = [value for day,value in attendance.items() if day.startswith(year)]
            season = by_year.setdefault(year, {'year':year, 'apps':0, 'goals':0, 'assists':0, 'rating':None})
            season['apps'] = len(cells)
            season['rating'] = sum(number(value) for value in cells) / len(cells) if cells else None
        p['seasons'] = [by_year[y] for y in years if any(by_year[y][k] for k in ('apps','goals','assists'))]
        players[name] = p
    return players, dates, years


def parse_matches(path=None, as_of=None):
    as_of = as_of or today_code()
    with (path or DATA_DIR / '每场战报+总数据-具体战况.csv').open(encoding='utf-8-sig') as f:
        rows = list(csv.reader(f))
    matches = []
    current = None
    for line, cells in enumerate(rows, 1):
        r = [v.strip() for v in cells] + [''] * max(0, 10 - len(cells))
        code = date_code(r[1])
        # A malformed dated block must never bleed into the previous fixture.
        if r[1] and code is None:
            current = None
            continue
        has_score = r[6].isdigit() or r[7].isdigit()
        # Repeated-date goal rows in 2024/2025 are not match headers.
        header = code and (has_score or (is_rf(r[4]) and bool(r[8])) or (is_rf(r[8]) and bool(r[4])))
        if header:
            current = None
            if code > as_of:
                continue
            hs = int(r[6]) if r[6].isdigit() else None
            away_score = int(r[7]) if r[7].isdigit() else None
            known = hs is not None and away_score is not None
            comp = normalize_type(r[2]) or '性质待补录'
            # Some historical rows combine date/score with the first scorer and
            # assist, without team labels. Preserve that event instead of
            # treating the player's name as a non-club team and dropping a game.
            combined = bool(has_score and person(r[4]) and person(r[5])
                            and not is_rf(r[4]) and not r[8] and not r[9])
            internal = comp.startswith('内部友谊赛')
            current = {'id': f'{r[1]}:{line}', 'date': display_date(code), 'dateCode': code, 'sourceLine': line, 'sourceMatchId': r[0],
                       'home': 'Royal Farmers' if combined else 'Royal Farmers'+r[4] if r[4] in INTERNAL_TEAMS else r[4],
                       'away': 'Royal Farmers'+r[8] if r[8] in INTERNAL_TEAMS else r[8],
                       'homeRf': combined or internal or is_rf(r[4]), 'awayRf': internal or is_rf(r[8]),
                       'homeScore': hs, 'awayScore': away_score, 'scoreKnown': known,
                       'comp': comp, 'venue': r[3] or '场地待补录',
                       'result': ('W' if hs > away_score else 'L' if hs < away_score else 'D') if known else 'U',
                       'homeScorers': [], 'homeAssists': [], 'awayScorers': [], 'awayAssists': [], 'issues': []}
            matches.append(current)
            if not combined:
                continue
            current['issues'].append(f'第{line}行合并比分及首条进球，球队名称未填写')
        if current is None:
            continue
        if code and code != current['dateCode']:
            # A repeated detail date can be a copy/paste error. A matching
            # explicit match ID ties it to its header; never borrow another
            # date without this evidence (or across an invalid dated block).
            if not r[0] or r[0] != current['sourceMatchId']:
                continue
            current['issues'].append(f'第{line}行日期与比赛表头不一致，按比赛ID归入{current["date"]}')
        # The CSV schema fixes scorers at columns 4/8 and assists at 5/9.
        # Never infer a shifted schema from text in the venue column: that
        # silently swaps scorers and assists (e.g. the 2026-05-14 fixture).
        for side, scorer, assist in [('home', r[4], r[5]), ('away', r[8], r[9])]:
            if not scorer or scorer == '/':
                continue
            clean_scorer = scorer if person(scorer) or scorer in {'乌龙', 'OG'} else '进球者待确认'
            clean_assist = person(assist)
            if clean_assist and clean_assist == person(scorer):
                current['issues'].append(f'第{line}行同人进球和助攻，助攻待确认')
                clean_assist = ''
            current[side+'Scorers'].append(clean_scorer)
            current[side+'Assists'].append(clean_assist)
    for m in matches:
        if not m['scoreKnown']:
            m['issues'].append('比分待补录，不计入胜平负')
        for side in ('home', 'away'):
            score = m[side+'Score']
            recorded = len(m[side+'Scorers'])
            if score is not None and recorded != score:
                m['issues'].append(f'{"主" if side == "home" else "客"}队比分{score}，进球明细{recorded}条')
    return sorted(matches, key=lambda m: m['dateCode'], reverse=True)


def external_stats(matches):
    selected = [m for m in matches if m['comp'] == EXTERNAL_TWO and m['homeRf'] != m['awayRf']]
    def aggregate(items):
        record = dict(played=0, won=0, drawn=0, lost=0, gf=0, ga=0, gd=0, pending=0)
        goals, assists = Counter(), Counter()
        results = []
        for m in items:
            own, other = ('home', 'away') if m['homeRf'] else ('away', 'home')
            gf, ga = m[own+'Score'], m[other+'Score']
            outcome = ('W' if gf > ga else 'L' if gf < ga else 'D') if m['scoreKnown'] else 'U'
            results.append({'date': m['date'], 'rfTeam': m[own], 'opp': m[other], 'rfScore': gf, 'oppScore': ga, 'result': outcome})
            if not m['scoreKnown']:
                record['pending'] += 1
                continue
            record['played'] += 1
            record[{'W': 'won', 'L': 'lost', 'D': 'drawn'}[outcome]] += 1
            record['gf'] += gf
            record['ga'] += ga
            goals.update(n for n in m[own+'Scorers'] if person(n) and n != '进球者待确认')
            assists.update(n for n in m[own+'Assists'] if person(n))
        record['gd'] = record['gf'] - record['ga']
        return {'record': record, 'scorers': [{'name': n, 'goals': v} for n, v in goals.most_common(10)],
                'assists': [{'name': n, 'assists': v} for n, v in assists.most_common(10)], 'matches': results}
    years = sorted({m['dateCode'][:4] for m in selected})
    return {'all': aggregate(selected), 'seasons': [{'season': y, **aggregate([m for m in selected if m['dateCode'].startswith(y)])} for y in years]}


def invalid_match_dates(path=None):
    """Expose malformed dated match headers for human review, without guessing dates."""
    issues = []
    with (path or DATA_DIR / '每场战报+总数据-具体战况.csv').open(encoding='utf-8-sig') as f:
        for line, row in enumerate(csv.reader(f), 1):
            if len(row) > 8 and row[1].strip() and not date_code(row[1]) and (row[6].strip().isdigit() or row[7].strip().isdigit()):
                issues.append({'sourceLine': line, 'sourceMatchId': r[0], 'rawDate': row[1], 'home': row[4], 'away': row[8]})
    return issues
