"""Missing months remain navigable without fabricated goals, assists or honors."""
import copy
import unittest
from unittest.mock import patch
from monthly_calendar import calendar_month_keys
from reconcile_stats import load_data, reconcile
from stats_model import read_roster, parse_matches


class MonthlyCalendarTests(unittest.TestCase):
    def test_gaps_fill_between_observed_months(self):
        self.assertEqual(calendar_month_keys({'202203', '202206'}, '20220630'),
                         ['202206', '202205', '202204', '202203'])

    def test_year_boundary_and_future_sources(self):
        self.assertEqual(calendar_month_keys({'202112', '202303'}, '20220201'),
                         ['202202', '202201', '202112'])

    def test_empty_history_still_includes_current_month(self):
        self.assertEqual(calendar_month_keys([], '20261125'), ['202611'])
        self.assertEqual(calendar_month_keys(['202612'], '20261125'), ['202611'])

    def test_invalid_months_cannot_silently_shift_the_calendar(self):
        with self.assertRaises(ValueError):
            calendar_month_keys(['202213'], '20230101')

    def test_real_2022_months_are_present_without_inventing_rankings(self):
        before = load_data()
        data, matches = reconcile(copy.deepcopy(before))
        roster, _, _ = read_roster()
        months = [row for row in data['MONTHLY_HISTORY'] if row['period'].startswith('2022年')]
        self.assertEqual([row['period'] for row in months], [f'2022年{m}月' for m in range(12, 0, -1)])
        for month in (4, 5):
            label = f'2022年{month}月'
            row = next(row for row in months if row['period'] == label)
            prefix = f'2022{month:02d}'
            matchCount = sum(m['dateCode'].startswith(prefix) for m in matches)
            attendanceCount = len({day for player in roster.values() for day in player['attendance'] if day.startswith(prefix)})
            # Follow fresh source evidence, so later backfills are allowed.
            self.assertEqual(row['sourceMatchCount'], matchCount)
            self.assertEqual(row['sourceAttendanceDays'], attendanceCount)
            if not matchCount and not attendanceCount:
                for key in ['goals', 'assists', 'apps', 'recordGoals', 'recordAssists']:
                    self.assertEqual(row[key], [])
                self.assertFalse(any(h['period'] == label for honors in data['PLAYER_HONORS'].values() for h in honors))
        for label in ['2022年3月', '2022年6月']:
            old = next(row for row in before['MONTHLY_HISTORY'] if row['period'] == label)
            new = next(row for row in months if row['period'] == label)
            for key in ['goals', 'assists', 'apps', 'recordGoals', 'recordAssists']:
                self.assertEqual(old[key], new[key])
            self.assertGreater(new['sourceMatchCount'], 0)
        self.assertEqual(data['MONTHLY_PERIOD'], data['MONTHLY_HISTORY'][0]['period'])
        self.assertEqual(data['PLAYER_HONORS'], before['PLAYER_HONORS'])
        self.assertEqual(data['RECORDS'], before['RECORDS'])

    def test_backfilled_match_replaces_empty_month_on_next_build(self):
        roster = read_roster()[0]
        matches = [m for m in parse_matches(roster=roster) if not m['dateCode'].startswith('202204')]
        before = load_data()
        with patch('reconcile_stats.parse_matches', return_value=matches):
            empty, _ = reconcile(copy.deepcopy(before))
        match = {**matches[0], 'id': '220410:backfill', 'dateCode': '20220410', 'date': '2022.04.10',
                 'homeRf': True, 'awayRf': False, 'homeScorers': ['姜珂'], 'homeAssists': ['金辉'],
                 'awayScorers': [], 'awayAssists': [], 'homeScore': 1, 'awayScore': 0,
                 'scoreKnown': True, 'result': 'W', 'sourceCorrections': []}
        with patch('reconcile_stats.parse_matches', return_value=[*matches, match]):
            updated, _ = reconcile(copy.deepcopy(empty))
        month = next(row for row in updated['MONTHLY_HISTORY'] if row['period'] == '2022年4月')
        self.assertEqual(month['sourceMatchCount'], 1)
        self.assertEqual([(p['name'], p['goals']) for p in month['goals']], [('姜珂', 1)])
        self.assertEqual([(p['name'], p['assists']) for p in month['assists']], [('金辉', 1)])


if __name__ == '__main__':
    unittest.main()
