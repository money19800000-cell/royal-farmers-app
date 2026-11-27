"""Regression checks for partner direction, evidence, ties and attendance scope."""
import copy
import csv
import json
import subprocess
import unittest
from pathlib import Path
from relationship_stats import compute_relationships, compute_coattendance
from stats_model import DATA_DIR, read_roster, parse_matches
from reconcile_stats import ROOT, load_data, reconcile


def fixture(scorers, assists, rf=True, day='20260101'):
    return dict(id=day+':1', dateCode=day, date=f'{day[:4]}.{day[4:6]}.{day[6:]}',
                home='甲队', away='乙队', sourceLine=1,
                homeRf=rf, awayRf=False, homeScorers=scorers, homeAssists=assists,
                awayScorers=[], awayAssists=[], homeEventLines=list(range(2, len(scorers)+2)))


def player(attendance=None):
    return {'num': '', 'attendance': attendance or {}, 'seasons': [{'year': '2026'}]}


class RelationshipTests(unittest.TestCase):
    def test_tied_partners_all_survive_and_have_matching_direction_and_evidence(self):
        roster = {name: player() for name in ['甲', '乙', '丙']}
        matches = [fixture(['甲', '甲', '乙'], ['乙', '丙', '甲'])]
        data = compute_relationships(roster, matches, {})['PLAYER_CHEMISTRY']
        self.assertEqual(set(data['甲']['a2me']['names']), {'乙', '丙'})
        self.assertEqual(data['甲']['a2me']['count'], 1)
        self.assertEqual(data['甲']['me2a']['names'], ['乙'])
        self.assertEqual({e['sourceLine'] for e in data['甲']['a2meEvents']}, {2, 3})
        self.assertEqual([e['sourceLine'] for e in data['甲']['me2aEvents']], [4])
        self.assertEqual(data, compute_relationships(roster, list(reversed(matches)), {})['PLAYER_CHEMISTRY'])

    def test_guest_links_count_but_unknown_opponents_and_placeholder_goals_do_not(self):
        roster = {'甲': player(), '乙': player()}
        match = fixture(['甲', '外援朋友', '对手', '乌龙球', '甲', '外部一'],
                        ['乙', '甲', '甲', '甲', '甲', '外部二'], rf=False)
        data = compute_relationships(roster, [match], {})['PLAYER_CHEMISTRY']
        self.assertEqual(data['甲']['a2me']['name'], '乙')
        self.assertEqual(data['甲']['me2a']['name'], '外援朋友')
        for invalid in ['对手', '乌龙球', '外部一', '外部二']:
            self.assertNotIn(invalid, data)

    def test_personal_links_do_not_depend_on_global_top_twenty(self):
        scorers = [f'球员{i}' for i in range(21) for _ in range(2)] + ['新人']
        assists = [f'搭档{i}' for i in range(21) for _ in range(2)] + ['朋友']
        data = compute_relationships({'新人': player()}, [fixture(scorers, assists)], {})
        self.assertFalse(any(row['scorer'] == '新人' for row in data['GOLDEN_PAIRS']['all']))
        self.assertEqual(data['PLAYER_CHEMISTRY']['新人']['a2me']['count'], 1)
        self.assertEqual(len(data['GOLDEN_PAIRS']['all']), 21)  # retain cutoff ties

    def test_assist_network_uses_all_partners_before_selecting_hubs(self):
        chemistry = {'甲': {'me2aPartners': [{'name': f'搭档{i}', 'count': 1} for i in range(25)]},
                     '乙': {'me2aPartners': [{'name': '丙', 'count': 20}]}, '丙': {}}
        source = (ROOT/'components.jsx').read_text()
        function = source[source.index('function getAssistNetworkTotals('):source.index('function getCoattendance(')]
        js = function + '\nprocess.stdout.write(JSON.stringify(getAssistNetworkTotals('+json.dumps(chemistry)+')))'
        result = json.loads(subprocess.check_output(['node', '-e', js], text=True))
        self.assertEqual(result['astTotal'], {'甲': 25, '乙': 20})
        self.assertEqual(len(result['astMap']['甲']), 25)

    def test_coattendance_counts_different_results_and_nonstandard_scores(self):
        dates = [(f'2026010{i}', i) for i in range(1, 5)]
        roster = {'甲': player(dict(zip([d for d, _ in dates], ['3', '3', '1', '2']))),
                  '乙': player(dict(zip([d for d, _ in dates], ['3', '-1', '1', '3']))),
                  '丙': player({'20260101': '3', '20260102': '-1'})}
        data = compute_coattendance(roster, dates, {})
        pair = dict(apps=4, wins=1, rate=0.25)
        self.assertEqual(data['LINEUP_ALL'], {})
        self.assertEqual(data['MATCH_DATA']['甲'], '331U')
        self.assertEqual(data['LINEUP_STATS'], [])  # rank gate, not free-search gate
        source = (ROOT/'components.jsx').read_text()
        function = source[source.index('function getCoattendance('):source.index('function PlayerModal(')]
        js = function + '\nprocess.stdout.write(JSON.stringify([getCoattendance(["甲","乙"],'+json.dumps(data['MATCH_DATA'])+'),getCoattendance(["甲","乙","丙"],'+json.dumps(data['MATCH_DATA'])+')]))'
        two, three = json.loads(subprocess.check_output(['node', '-e', js], text=True))
        self.assertEqual(two, pair)
        self.assertEqual(three, dict(apps=2, wins=1, rate=0.5))

    def test_full_lineup_candidate_set_available_for_each_sort_order(self):
        dates = [(f'202601{i:02d}', i) for i in range(1, 22)]
        roster = {f'球员{i}': player({d: '3' for d, _ in dates}) for i in range(8)}
        data = compute_coattendance(roster, dates, {})
        self.assertEqual(len(data['LINEUP_STATS']), 28)
        self.assertTrue(all(row['apps'] == 21 for row in data['LINEUP_STATS']))

    def test_yeti_counts_independently_match_raw_csv_rows(self):
        roster = read_roster()[0]
        matches = parse_matches(roster=roster)
        chemistry = compute_relationships(roster, matches, {})['PLAYER_CHEMISTRY']['Yeti']
        with (DATA_DIR/'每场战报+总数据-具体战况.csv').open() as source:
            rawRows = list(csv.reader(source))
        # Live CSV totals grow with new matches; derive expectations independently.
        for key, scorer, assister in [('a2me', 'yeti', '姜珂'), ('me2a', '姜珂', 'yeti')]:
            independent = [line for line, row in enumerate(rawRows, 1) for g, a in [(4, 5), (8, 9)]
                           if len(row) > a and row[g].strip().casefold() == scorer and row[a].strip().casefold() == assister]
            self.assertTrue(independent)
            partner = assister if key == 'a2me' else scorer
            actual = next(row for row in chemistry[key+'Partners'] if row['name'].casefold() == partner)
            self.assertEqual(actual['count'], len(independent))
            if partner in [name.casefold() for name in chemistry[key]['names']]:
                self.assertEqual(sorted(event['sourceLine'] for event in chemistry[key+'Events']
                                        if event['partner'].casefold() == partner), independent)

    def test_individual_guest_statistics_agree_across_features(self):
        data, _ = reconcile(copy.deepcopy(load_data()))
        september = next(row for row in data['MONTHLY_HISTORY'] if row['period'] == '2026年9月')
        # Sep 19: 邓楠 played for 汽车人; two 周潍 assists were omitted by RF-side filtering.
        partners = data['PLAYER_CHEMISTRY']['邓楠']['a2mePartners']
        self.assertGreaterEqual(next(row['count'] for row in partners if row['name'] == '周潍'), 2)
        self.assertTrue(any(row['name'] == '邓楠' and row['goals'] >= 4 for row in september['recordGoals']))


if __name__ == '__main__':
    unittest.main()
