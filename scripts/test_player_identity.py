"""CSV edits must replace cached identities and every derived statistic."""
import copy
import csv
import json
import tempfile
import unittest
from pathlib import Path

from reconcile_stats import load_data, rebuild_player_profiles, reconcile, validate
from stats_model import parse_matches, read_roster


class PlayerIdentityTests(unittest.TestCase):
    def test_rename_removal_and_correction_use_latest_csv_on_every_read(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'roster.csv'
            headers = ['名字', '号码', '位置', '出场', '进球', '助攻',
                       '2026出场', '2026进球', '2026助攻', '20261112']
            def writeRows(rows):
                with path.open('w', newline='') as output:
                    csv.writer(output).writerows([headers, *rows])
            writeRows([['旧名字', '8', '前卫', 1, 2, 1, 1, 2, 1, 3]])
            data = {'PLAYERS': [{'name': '旧名字', 'staleField': 99}], 'PLAYER_LOOKUP': {}}
            roster = read_roster(path, '20261122')[0]
            rebuild_player_profiles(data, roster, {})
            writeRows([['新名字', '8', '后卫', 1, 3, 0, 1, 3, 0, 3],
                       ['新增球员', '', '', 1, 0, 0, 1, 0, 0, 1]])
            roster = read_roster(path, '20261122')[0]
            profiles = rebuild_player_profiles(data, roster, {})
            self.assertEqual(set(profiles), {'新名字', '新增球员'})
            self.assertEqual(profiles['新名字']['goals'], 3)
            self.assertEqual(profiles['新名字']['assists'], 0)
            self.assertEqual(profiles['新名字']['pos'], '后卫')
            self.assertNotIn('旧名字', json.dumps(data, ensure_ascii=False))
            self.assertNotIn('staleField', json.dumps(data))

    def test_case_changes_replace_cached_profile_without_losing_featured_selection(self):
        data = {'PLAYERS': [{'name': 'carlo', 'goals': 999}],
                'PLAYER_LOOKUP': {'Carlo': {'name': 'Carlo', 'goals': 888}}}
        roster = {'Carlo': {'name': 'Carlo', 'goals': 3, 'attendance': {}}}
        profiles = rebuild_player_profiles(data, roster, {'Carlo': 'portrait.jpeg'})
        self.assertEqual(len(data['PLAYERS']), 1)
        self.assertEqual(data['PLAYER_LOOKUP'], {})
        self.assertEqual(profiles['Carlo']['goals'], 3)
        self.assertEqual(profiles['Carlo']['photo'], 'portrait.jpeg')

    def test_match_names_normalize_before_aggregation_and_self_assist_check(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'matches.csv'
            with path.open('w', newline='') as output:
                csv.writer(output).writerows([
                    ['', '261112', '内部友谊赛（两队）', '', '红队', '', 3, 1, '蓝队', ''],
                    ['', '', '', '', 'carlo', 'YETI', '', '', '未知访客', ''],
                    ['', '', '', '', 'Carlo', 'yeti', '', '', '', ''],
                    ['', '', '', '', 'CARLO', 'carlo', '', '', '', ''],
                ])
            match = parse_matches(path, '20261122', roster={'Carlo': {}, 'Yeti': {}})[0]
            self.assertEqual(match['homeScorers'], ['Carlo'] * 3)
            self.assertEqual(match['homeAssists'], ['Yeti', 'Yeti', ''])
            self.assertEqual(match['awayScorers'], ['未知访客'])

    def test_empty_or_ambiguous_roster_stops_sync(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'roster.csv'
            for names in [[], ['Carlo', 'carlo']]:
                with self.subTest(names=names):
                    with path.open('w', newline='') as output:
                        csv.writer(output).writerows([['名字'], *[[name] for name in names]])
                    with self.assertRaises(ValueError):
                        read_roster(path, '20261122')

    def test_stale_cache_cannot_affect_profiles_rankings_records_or_totals(self):
        baseline, _ = reconcile(copy.deepcopy(load_data()))
        polluted = copy.deepcopy(baseline)
        ghost = copy.deepcopy(polluted['PLAYERS'][0])
        ghost.update(name='已改名的缓存球员', goals=99999, assists=88888, apps=77777)
        polluted['PLAYERS'].append(ghost)
        polluted['PLAYER_LOOKUP']['失效查找项'] = {**ghost, 'name': '失效查找项'}
        polluted['PLAYERS'][0].update(goals=123456, staleField=True)
        for field in ['GOALS_ALL', 'APPS_ALL', 'MONTHLY_HISTORY', 'MILESTONES']:
            polluted[field] = [ghost]
        polluted['PLAYER_CHEMISTRY'] = {ghost['name']: {}}
        actual, _ = reconcile(polluted)
        self.assertEqual(actual, baseline)
        validate(actual)
        self.assertEqual(actual['STATS_META']['archivedPlayers'], 0)

    def test_monthly_and_chemistry_use_roster_spelling(self):
        data, _ = reconcile(copy.deepcopy(load_data()), '20261122')
        november = next(row for row in data['MONTHLY_HISTORY'] if row['period'] == '2026年11月')
        self.assertEqual([p['goals'] for p in november['recordGoals'] if p['name'] == 'Carlo'], [3])
        self.assertFalse(any(p['name'] == 'carlo' for p in november['recordGoals']))
        self.assertEqual(data['PLAYER_CHEMISTRY']['Carlo']['a2me']['count'], 3)
        self.assertNotIn('carlo', data['PLAYER_CHEMISTRY'])
        self.assertNotIn('yeti的意大利回来的朋友', json.dumps(data, ensure_ascii=False))


if __name__ == '__main__':
    unittest.main()
