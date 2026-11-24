"""Missing months remain navigable without fabricated goals, assists or honors."""
import copy
import unittest
from monthly_calendar import calendar_month_keys
from reconcile_stats import load_data, reconcile


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
        data, _ = reconcile(copy.deepcopy(before))
        months = [row for row in data['MONTHLY_HISTORY'] if row['period'].startswith('2022年')]
        self.assertEqual([row['period'] for row in months], [f'2022年{m}月' for m in range(12, 0, -1)])
        for month in (4, 5):
            label = f'2022年{month}月'
            row = next(row for row in months if row['period'] == label)
            self.assertEqual(row['sourceMatchCount'], 0)
            self.assertEqual(row['sourceAttendanceDays'], 0)
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


if __name__ == '__main__':
    unittest.main()
