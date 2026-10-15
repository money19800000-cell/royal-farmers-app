#!/usr/bin/env python3
"""Final, deterministic statistics reconciliation before bundling.

Legacy update scripts may still refresh other features. This final pass owns the
shared roster totals, eligibility, records, match parsing and attendance models.
Original CSVs and their conflicting totals are never rewritten.
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from stats_model import read_roster, parse_matches, external_stats, person, today_code, display_date, invalid_match_dates
from sync_player_photos import parse_photos
from check_milestones import compute_milestones

ROOT = Path(__file__).resolve().parents[1]


def load_data():
    code = "const fs=require('fs'),vm=require('vm');const c={window:{}};vm.createContext(c);vm.runInContext(fs.readFileSync(process.argv[1],'utf8'),c);process.stdout.write(JSON.stringify(c.window.RF_DATA));"
    return json.loads(subprocess.check_output(['node', '-e', code, str(ROOT/'data.jsx')], text=True))


def ranked(players, key):
    return sorted(players, key=lambda p: (-p[key], p['name']))


def reconcile(data, as_of=None):
    as_of = as_of or today_code()
    roster, dates, years = read_roster(as_of=as_of)
    matches = parse_matches(as_of=as_of)
    photos = parse_photos()
    old_players = {p['name']: p for p in [*data['PLAYER_LOOKUP'].values(), *data['PLAYERS']]}
    aliases = {name.casefold(): name for name in roster}
    profiles = {}
    for name, p in old_players.items():
        if name.casefold() not in aliases:
            # Do not discard historical players simply because a roster row disappeared.
            profiles[name] = {**p, 'r50': 0, 'archivedStats': True, 'careerRating': None}
    for name, p in roster.items():
        previous = next((v for n, v in old_players.items() if n.casefold() == name.casefold()), {})
        profiles[name] = {**previous, **{k: v for k, v in p.items() if k != 'attendance'}, 'photo': photos.get(name), 'archivedStats': False}
    featured = {aliases.get(p['name'].casefold(), p['name']) for p in data['PLAYERS']}
    data['PLAYERS'] = [profiles[n] for n in profiles if n in featured]
    data['PLAYER_LOOKUP'] = {n: p for n, p in profiles.items() if n not in featured}
    # Historical snapshots remain explicit, and all displayed profiles are eligible
    # for the same full historical leaderboards rather than silently disappearing.
    all_players = list(profiles.values())
    current_year = as_of[:4]
    season_counts = {y: sum(d.startswith(y) for d, _ in dates) for y in years}
    data['MATCH_COUNT'] = len(dates)
    data['STATS_META'] = {'asOf': as_of, 'lastMatchDay': dates[-1][0] if dates else None,
                          'seasonMatchDays': season_counts, 'ratingThreshold': 0.25, 'rateThreshold': 0.4,
                          'archivedPlayers': sum(bool(p.get('archivedStats')) for p in all_players),
                          'sourceDifferences': [{'name': p['name'], **p['sourceDifference']} for p in roster.values() if any(p['sourceDifference'].values())]}
    for key, var in [('goals', 'GOALS_ALL'), ('assists', 'ASSISTS_ALL'), ('apps', 'APPS_ALL')]:
        rows = [{**{k: p.get(k) for k in ('name', 'num', 'photo', 'apps')}, key: p[key], 'archivedStats': p.get('archivedStats', False)} for p in ranked(all_players, key) if p[key] > 0]
        if key == 'apps':
            for p in rows:
                p.update(total=len(dates), pct=f"{p['apps']/len(dates)*100:.1f}%")
        data[var] = rows
    season_players = []
    for p in all_players:
        for s in p.get('seasons', []):
            if s['year'] == current_year:
                season_players.append({**p, **s})
    for key, var in [('goals', 'GOALS26'), ('assists', 'ASSISTS26'), ('apps', 'APPS26')]:
        rows = [{k: p.get(k) for k in ('name', 'num', 'apps', key)} for p in ranked(season_players, key) if p[key] > 0][:10]
        if key == 'apps':
            for p in rows:
                p['pct'] = f"{p['apps']/season_counts[current_year]*100:.2f}%" if season_counts[current_year] else '—'
        data[var] = rows
    data['RATINGS_ALL'] = ranked([{'name': p['name'], 'num': p['num'], 'photo': p.get('photo'), 'apps': p['apps'], 'rating': p['careerRating']}
                               for p in all_players if p.get('careerRating') is not None and p['apps'] > len(dates)*0.25], 'rating')
    for year in years:
        data['RATINGS_'+year] = ranked([{'name': p['name'], 'num': p['num'], 'photo': p.get('photo'), 'apps': s['apps'], 'rating': s['rating']}
                                     for p in all_players for s in p.get('seasons', []) if s['year'] == year and s.get('rating') is not None and s['apps'] > season_counts[year]*0.25], 'rating')
    data['FIXTURES'] = [m for m in matches if m['dateCode'].startswith(current_year)]
    data['EXTERNAL_MATCH_STATS'] = external_stats(matches)
    external_by_year = {s['season']: s for s in data['EXTERNAL_MATCH_STATS']['seasons']}
    data['SEASON_MATCH_STATS'] = {}
    for year in years:
        r = external_by_year.get(year, {'record': {}})['record']
        total = r.get('played', 0)
        data['SEASON_MATCH_STATS'][year] = {'w': r.get('won', 0), 'd': r.get('drawn', 0), 'l': r.get('lost', 0), 'gf': r.get('gf', 0), 'ga': r.get('ga', 0), 'total': total, 'avgGF': round(r.get('gf', 0)/total, 1) if total else 0, 'pending': r.get('pending', 0)}
    periods = sorted({d[:6] for d, _ in dates})
    data['ATTENDANCE_HEATMAP'] = {'periods': [p[:4]+'-'+p[4:] for p in periods], 'totals': [sum(d.startswith(p) for d, _ in dates) for p in periods], 'players': []}
    attendance_rows = []
    for p in roster.values():
        monthly = [sum(d.startswith(period) for d in p['attendance']) for period in periods]
        attendance_rows.append({'name': p['name'], 'num': p['num'], 'total': sum(monthly), 'monthly': monthly})
    data['ATTENDANCE_HEATMAP']['players'] = ranked([p for p in attendance_rows if p['total'] >= 30], 'total')[:30]
    data['ROSTER_LOG_2026'] = [{'date': display_date(d), 'attendees': [p['name'] for p in roster.values() if d in p['attendance']]} for d, _ in dates if d.startswith(current_year)]
    data['JOIN_ATTENDANCE'] = {}
    for p in roster.values():
        if not p['attendance']:
            continue
        first = min(p['attendance'])
        total = len(p['attendance'])
        count = sum(d >= first for d, _ in dates)
        data['JOIN_ATTENDANCE'][p['name'].lower()] = {'name': p['name'], 'firstAppearance': display_date(first).replace('.', '-'), 'totalApps': total, 'teamMatches': count, 'rate': total/count}
    data['ALLSEASON_PLAYERS'] = [{'name': p['name'], 'num': p['num'], 'photo': p.get('photo'), 'apps': [next(s['apps'] for s in p['seasons'] if s['year'] == y) for y in years], 'total': p['apps']}
                               for p in ranked(all_players, 'apps') if all(any(s['year'] == y and s['apps'] > 0 for s in p.get('seasons', [])) for y in years)]
    # Monthly goals/assists count only RF sides; own goals remain team events only.
    month_stats = defaultdict(lambda: {'goals': Counter(), 'assists': Counter()})
    for m in matches:
        target = month_stats[m['dateCode'][:6]]
        for side in ('home', 'away'):
            if not m[side+'Rf']:
                continue
            target['goals'].update(n for n in m[side+'Scorers'] if person(n) and n != '进球者待确认')
            target['assists'].update(n for n in m[side+'Assists'] if person(n))
    month_keys = sorted(set(month_stats) | set(periods) | {as_of[:6]}, reverse=True)
    history = []
    for period in month_keys:
        row = {'period': f'{period[:4]}年{int(period[4:])}月'}
        for key, field in [('goals', 'recordGoals'), ('assists', 'recordAssists')]:
            entries = [{'name': n, 'num': profiles.get(n, {}).get('num', ''), key: v} for n, v in sorted(month_stats[period][key].items(), key=lambda x: (-x[1], x[0]))]
            row[key] = entries[:5]
            row[field] = entries[:20]
        apps = [{'name': p['name'], 'num': p['num'], 'apps': sum(d.startswith(period) for d in p['attendance'])} for p in roster.values()]
        row['apps'] = ranked([p for p in apps if p['apps']], 'apps')[:5]
        history.append(row)
    data['MONTHLY_HISTORY'] = history
    latest = next(m for m in history if m['period'] == f'{as_of[:4]}年{int(as_of[4:6])}月')
    data['MONTHLY_PERIOD'] = latest['period']
    for key in ('goals', 'assists', 'apps'):
        data['MONTHLY_'+key.upper()] = latest[key]
    honors = defaultdict(list)
    for row in history:
        for key, label in [('goals', '月度最佳射手'), ('assists', '月度助攻王')]:
            entries = row[key]
            for p in entries:
                if p[key] == entries[0][key]:
                    honors[p['name']].append({'period': row['period'], 'award': label})
    for year in years:
        candidates = [{**p, **s} for p in all_players for s in p.get('seasons', []) if s['year'] == year]
        for key, label in [('goals', '赛季最佳射手'), ('assists', '赛季助攻王'), ('apps', '赛季出勤王')]:
            top = ranked(candidates, key)
            for p in top:
                if p[key] > 0 and p[key] == top[0][key]:
                    honors[p['name']].append({'period': year+'赛季', 'award': label})
    data['PLAYER_HONORS'] = dict(honors)
    def card(label, icon, p, val, unit, ctx):
        return {'label': label, 'icon': icon, 'value': round(val, 2), 'unit': unit, 'holder': p.get('name'), 'num': p.get('num', ''), 'photo': p.get('photo'), 'ctx': ctx}
    career = []
    for key, label, icon, unit in [('goals', '生涯最多进球', '⚽', '球'), ('assists', '生涯最多助攻', '👟', '次'), ('apps', '生涯最多出场', '🏃', '场')]:
        p = ranked(all_players, key)[0]
        career.append(card(label, icon, p, p[key], unit, f"{p['apps']}场出场 · 花名册汇总"))
    for key, label, icon, unit in [('goals', '最高进球效率', '🎯', '球/场'), ('assists', '最高助攻效率', '🎪', '次/场')]:
        p = max((p for p in all_players if p['apps'] > 40), key=lambda p: p[key]/p['apps'])
        career.append(card(label, icon, p, p[key]/p['apps'], unit, f"{p[key]}/{p['apps']}场 · 出场>40"))
    for key, label, icon, unit in [('goals', '非No.10最多进球', '⚽', '球'), ('assists', '非No.10最多助攻', '👟', '次'), ('apps', '非No.10最多出场', '🏃', '场')]:
        p = ranked([p for p in all_players if str(p.get('num')) != '10' and p['name'] != '姜珂'], key)[0]
        career.append(card(label, icon, p, p[key], unit, f"{p['apps']}场出场"))
    season_cards = []
    season_rows = [{**p, **s} for p in all_players for s in p.get('seasons', []) if s['apps'] > 0]
    for label in ['单赛季最多进球', '单赛季最多助攻', '单赛季最多出场', '单赛季进球(非No.10)', '单赛季助攻(非No.10)', '单赛季场均进球', '单赛季场均助攻', '单月最多进球', '单月最多助攻', '赛季场均评分最高']:
        metric = 'rating' if '评分' in label else 'assists' if '助攻' in label else 'apps' if '出场' in label else 'goals'
        unit = {'rating': '分/场', 'assists': '次', 'apps': '场', 'goals': '球'}[metric]
        icon = {'rating': '⭐', 'assists': '👟', 'apps': '🏃', 'goals': '⚽'}[metric]
        if label.startswith('单月'):
            field = 'recordGoals' if metric == 'goals' else 'recordAssists'
            candidates = [{**p, 'period': m['period']} for m in history for p in m[field]]
            p = max(candidates, key=lambda p: p[metric])
            season_cards.append(card(label, icon, {**profiles.get(p['name'], {}), **p}, p[metric], unit, p['period']))
            continue
        candidates = season_rows
        if '非No.10' in label:
            candidates = [p for p in candidates if str(p.get('num')) != '10' and p['name'] != '姜珂']
        rate = '场均' in label and metric != 'rating'
        if rate:
            candidates = [p for p in candidates if p['apps'] > season_counts[p['year']]*0.4]
            unit += '/场'
        if metric == 'rating':
            candidates = [p for p in candidates if p['apps'] >= 30 and p.get('rating') is not None]
        p = max(candidates, key=lambda p: p[metric]/p['apps'] if rate else p[metric])
        season_cards.append(card(label, icon, p, p[metric]/p['apps'] if rate else p[metric], unit, f"{p['year']}赛季 · {p['apps']}场" + (' · 出场≥30' if metric == 'rating' else '')))
    match_candidates = []
    for m in matches:
        for side in ('home', 'away'):
            if not m[side+'Rf']:
                continue
            goals = Counter(n for n in m[side+'Scorers'] if person(n) and n != '进球者待确认')
            assists = Counter(n for n in m[side+'Assists'] if person(n))
            for n in goals.keys() | assists.keys():
                match_candidates.append({'name': n, 'goals': goals[n], 'assists': assists[n], 'contributions': goals[n]+assists[n], 'match': m})
    match_cards = []
    for key, label, icon, unit in [('goals','个人单场最多进球','⚽','球'),('assists','个人单场最多助攻','👟','次'),('contributions','单场进球+助攻','🌟','贡献')]:
        p = max(match_candidates, key=lambda p: p[key])
        m = p['match']
        match_cards.append(card(label, icon, {**profiles.get(p['name'], {}), 'name': p['name']}, p[key], unit, f"{m['date']} · 战报已确认明细"))
    known = [m for m in matches if m['scoreKnown'] and (m['homeRf'] or m['awayRf'])]
    m = max(known, key=lambda m: m['homeScore']+m['awayScore'])
    match_cards.append(card('单场两队总进球','🔥',{},m['homeScore']+m['awayScore'],'球',f"{m['date']} · {m['home']} {m['homeScore']}:{m['awayScore']} {m['away']}"))
    outsiders = [m for m in known if m['homeRf'] != m['awayRf'] and m['comp'] == '外部友谊赛（两队）']
    def margin(m):
        return (m['homeScore']-m['awayScore']) * (1 if m['homeRf'] else -1)
    m = max(outsiders, key=margin)
    match_cards.append(card('历史最大净胜球','💪',{},margin(m),'球',f"{m['date']} · 对外两队赛 · {m['homeScore']}:{m['awayScore']}"))
    data['RECORDS'] = {'career': career, 'season': season_cards, 'match': match_cards, 'club': [
        card('创队年份','🗓️',{},2020,'年','2021年起有统计数据；此前部分比赛缺失'),
        card('历史总场次','🏟️',{},len(dates),'个比赛日','花名册日期列 · 排除未来排期'),
        card('历史档案球员','👥',{},len(all_players),'人','含当前花名册及保留的历史档案'),
        card('历史总进球','⚽',{},sum(p['goals'] for p in all_players),'球','球员档案个人进球合计；不含乌龙及未归属进球'),
        card('历史总助攻','👟',{},sum(p['assists'] for p in all_players),'次','球员档案已登记助攻合计；缺失录像不补估') ]}
    # Assist relationships share the same validated events as monthly records.
    pair_counts = defaultdict(Counter)
    day_goals, day_assists = defaultdict(set), defaultdict(set)
    for m in matches:
        for side in ('home', 'away'):
            if not m[side+'Rf']:
                continue
            for goal, assist in zip(m[side+'Scorers'], m[side+'Assists']):
                if person(goal) and goal != '进球者待确认':
                    day_goals[m['dateCode']].add(goal)
                if person(assist):
                    day_assists[m['dateCode']].add(assist)
                if not person(goal) or goal == '进球者待确认' or not person(assist):
                    continue
                for period in ('all', m['dateCode'][:4]):
                    pair_counts[period][(goal, assist)] += 1
    data['GOLDEN_PAIRS'] = {}
    for period in ['all', *years]:
        pairs = sorted(pair_counts[period].items(), key=lambda item: (-item[1], item[0]))
        data['GOLDEN_PAIRS'][period] = [dict(scorer=g, ast=a, count=count,
            sNum=profiles.get(g, {}).get('num', ''), aNum=profiles.get(a, {}).get('num', ''),
            sPhoto=photos.get(g), aPhoto=photos.get(a)) for (g,a),count in pairs[:20 if period == 'all' else 12]]
    chemistry = defaultdict(dict)
    for (g,a),count in sorted(pair_counts['all'].items(), key=lambda item: (-item[1], item[0])):
        chemistry[g].setdefault('a2me', dict(name=a, count=count))
        chemistry[a].setdefault('me2a', dict(name=g, count=count))
    data['PLAYER_CHEMISTRY'] = dict(chemistry)
    # An unrecorded day interrupts a confirmed goal/assist streak; never bridge gaps.
    def best_run(days, predicate):
        best, current = [], []
        for day in days:
            current = [*current, day] if predicate(day) else []
            if len(current) > len(best):
                best = current
        return dict(count=len(best), **({'from': display_date(best[0]), 'to': display_date(best[-1])} if best else {}))
    data['PLAYER_STREAKS'] = {}
    for name, p in roster.items():
        attendance = p['attendance']
        days = sorted(attendance)
        if len(days) < 5:
            continue
        values = {
            'apps': best_run([d for d,_ in dates], lambda d: d in attendance),
            'win': best_run(days, lambda d: attendance[d] == '3'),
            'unbeaten': best_run(days, lambda d: attendance[d] in {'3','1'}),
            'nowin': best_run(days, lambda d: attendance[d] in {'-1','1'}),
            'goal': best_run(days, lambda d: name in day_goals[d]),
            'assist': best_run(days, lambda d: name in day_assists[d]),
        }
        data['PLAYER_STREAKS'][name] = {k:v for k,v in values.items() if v['count']}
    streaks = []
    for key,label,icon in [('win','连续胜利','🏆'),('unbeaten','连续不败','🛡️'),('goal','连续进球','⚽'),('assist','连续助攻','👟'),('apps','连续出场','🏃')]:
        candidates = [(name,values[key]) for name,values in data['PLAYER_STREAKS'].items() if key in values]
        name, value = max(candidates, key=lambda item: item[1]['count'])
        streaks.append({**card(label,icon,profiles[name],value['count'],'个比赛日','个人出勤日连续记录；进球助攻仅计已确认战报'), 'from':value['from'], 'to':value['to']})
    data['STREAK_RECORDS'] = streaks
    # These are same-result estimates, not proof of same-team membership.
    pair_apps, pair_wins = Counter(), Counter()
    data['MATCH_DATA'] = {n: ''.join({'3':'3','1':'1','-1':'L'}.get(p['attendance'].get(d), ' ') for d,_ in dates) for n,p in roster.items() if p['attendance']}
    for day,_ in dates:
        groups = defaultdict(list)
        for name,p in roster.items():
            result = p['attendance'].get(day)
            if result in {'3','1','-1'}:
                groups[result].append(name)
        for result,names in groups.items():
            names.sort()
            for i,name in enumerate(names):
                for other in names[i+1:]:
                    pair_apps[(name,other)] += 1
                    if result == '3': pair_wins[(name,other)] += 1
    data['LINEUP_ALL'] = {'|'.join(pair):dict(apps=count,wins=pair_wins[pair],rate=round(pair_wins[pair]/count,3)) for pair,count in sorted(pair_apps.items()) if count >= 20}
    lineup = []
    for (a,b),count in pair_apps.items():
        if count < 20: continue
        lineup.append(dict(p1=a,p2=b,p1n=roster[a]['num'],p2n=roster[b]['num'],p1ph=photos.get(a),p2ph=photos.get(b),apps=count,wins=pair_wins[(a,b)],rate=round(pair_wins[(a,b)]/count,3)))
    data['LINEUP_STATS'] = sorted(lineup,key=lambda p:(-p['rate'],-p['apps'],p['p1'],p['p2']))[:20]
    data['MILESTONES'] = compute_milestones(roster, matches, as_of, photos)
    # Old auxiliary caches also carry portraits; shirts must never identify people.
    def fix_photos(value):
        if isinstance(value, list):
            for child in value: fix_photos(child)
        elif isinstance(value, dict):
            for name_key, photo_key in [('name','photo'),('holder','photo'),('p1','p1ph'),('p2','p2ph')]:
                if name_key in value and photo_key in value:
                    value[photo_key] = photos.get(value[name_key])
            for child in value.values(): fix_photos(child)
    fix_photos(data)
    # Snapshot-level quality summary makes unresolved raw evidence visible.
    data['DATA_QUALITY'] = {'invalidMatchDates': invalid_match_dates(), 'unknownScores': sum(not m['scoreKnown'] for m in matches), 'matchIssues': sum(bool(m['issues']) for m in matches),
                            'rawTotalDifferences': data['STATS_META']['sourceDifferences']}
    return data, matches


def js_value(value):
    raw = json.dumps(value, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return re.sub(r'"([A-Za-z_][A-Za-z_0-9]*)":', r'\1:', raw)


def write_updates(source, old, new):
    for key, val in new.items():
        if key in old and old[key] == val:
            continue
        # Keep one entry per line for older metadata refresh scripts.
        if isinstance(val, list):
            literal = '[\n' + '\n'.join('  '+js_value(v)+',' for v in val) + '\n]'
        elif isinstance(val, dict):
            literal = '{\n' + '\n'.join('  '+json.dumps(k, ensure_ascii=False)+':'+js_value(v)+',' for k,v in val.items()) + '\n}'
        else:
            literal = js_value(val)
        block = f'const {key} = {literal};'
        pattern = rf'const {re.escape(key)} = (?:\[.*?\n\]|\{{.*?\n\}}|[^\n;]*);'
        source, count = re.subn(pattern, lambda _: block, source, count=1, flags=re.S)
        if not count:
            source = source.replace('window.RF_DATA = {', block+'\n\nwindow.RF_DATA = { '+key+',', 1)
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    import copy
    old = load_data()
    data, matches = reconcile(copy.deepcopy(old))
    validate(data)
    if not args.check:
        source = (ROOT/'data.jsx').read_text()
        updated = write_updates(source, old, data)
        temp = ROOT/'data.jsx.tmp'
        temp.write_text(updated)
        temp.replace(ROOT/'data.jsx')
    print(f"Statistics reconciled: {data['MATCH_COUNT']} match days, {len(data['GOALS_ALL'])} scorers, {len(matches)} recorded fixtures; raw differences: {len(data['STATS_META']['sourceDifferences'])}")


def validate(data):
    players = data['PLAYERS'] + list(data['PLAYER_LOOKUP'].values())
    assert len({p['name'] for p in players}) == len(players)
    for field, var in [('goals','GOALS_ALL'),('assists','ASSISTS_ALL'),('apps','APPS_ALL')]:
        assert {p['name']:p[field] for p in players if p[field]>0} == {p['name']:p[field] for p in data[var]}
    assert sum(data['STATS_META']['seasonMatchDays'].values()) == data['MATCH_COUNT']
    assert sum(data['ATTENDANCE_HEATMAP']['totals']) == data['MATCH_COUNT']
    for season in data['EXTERNAL_MATCH_STATS']['seasons']:
        r = season['record']
        assert r['played'] == r['won']+r['drawn']+r['lost']
        assert r['played'] == data['SEASON_MATCH_STATS'][season['season']]['total']
        assert r['pending'] == sum(m['result']=='U' for m in season['matches'])
    for p in players:
        if not p.get('archivedStats'):
            assert p['apps'] == sum(s['apps'] for s in p['seasons'])
            if p['apps']:
                assert abs(p['careerRating'] - sum((s['rating'] or 0)*s['apps'] for s in p['seasons'])/p['apps']) < 1e-9
    for p in data['RATINGS_ALL']:
        profile = next(x for x in players if x['name']==p['name'])
        assert p['rating'] == profile['careerRating']
    for m in data['FIXTURES']:
        assert (m['result']=='U') == (not m['scoreKnown'])


if __name__ == '__main__':
    main()
