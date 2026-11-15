"""Regression tests for ranking independent streaks rather than player bests."""
import unittest
from datetime import date, timedelta

from reconcile_stats import compute_streaks, rank_streak_runs, streak_runs


def match_days(count):
    return [(date(2025, 12, 27) + timedelta(days=index)).strftime('%Y%m%d')
            for index in range(count)]


class StreakRecordTests(unittest.TestCase):
    def test_same_player_can_rank_nineteen_and_eighteen_wins(self):
        days = match_days(38)
        attendance = {day: ('-1' if index == 19 else '3') for index, day in enumerate(days)}
        bests, rankings = compute_streaks(
            {'姜珂': {'num': '10', 'attendance': attendance}}, days, {}, {})
        rows = rankings['win']
        self.assertEqual([row['count'] for row in rows], [19, 18])
        self.assertEqual([row['name'] for row in rows], ['姜珂', '姜珂'])
        self.assertEqual([row['rank'] for row in rows], [1, 2])
        self.assertEqual(bests['姜珂']['win']['count'], 19)
        self.assertLess(rows[0]['to'], rows[1]['from'])
        self.assertEqual(len({row['id'] for row in rows}), 2)

    def test_all_five_categories_keep_separate_runs_across_years(self):
        days = match_days(12)
        attendance = {day: ('-1' if index == 5 else '3')
                      for index, day in enumerate(days) if index != 6}
        events = {day: {'甲'} for index, day in enumerate(days) if index not in (5, 6)}
        bests, rankings = compute_streaks(
            {'甲': {'num': '10', 'attendance': attendance}}, days, events, events)
        for key, rows in rankings.items():
            with self.subTest(category=key):
                self.assertEqual([row['count'] for row in rows], [6, 5] if key == 'apps' else [5, 5])
                self.assertEqual([row['rank'] for row in rows], [1, 2] if key == 'apps' else [1, 1])
                self.assertEqual(len({row['id'] for row in rows}), 2)
                self.assertEqual(bests['甲'][key]['from'], rows[0]['from'])

    def test_absence_breaks_attendance_but_not_personal_win_streak(self):
        days = match_days(6)
        attendance = {day: '3' for index, day in enumerate(days) if index != 2}
        _, rankings = compute_streaks({'甲': {'attendance': attendance}}, days, {}, {})
        self.assertEqual([row['count'] for row in rankings['win']], [5])
        self.assertEqual([row['count'] for row in rankings['apps']], [3, 2])

    def test_unconfirmed_attended_day_breaks_goal_and_assist_streaks(self):
        days = match_days(5)
        attendance = {day: '3' for day in days}
        events = {day: {'甲'} for index, day in enumerate(days) if index != 2}
        _, rankings = compute_streaks({'甲': {'attendance': attendance}}, days, events, events)
        for key in ('goal', 'assist'):
            self.assertEqual([row['count'] for row in rankings[key]], [2, 2])
            self.assertLess(rankings[key][0]['to'], rankings[key][1]['from'])

    def test_cutoff_includes_tied_records_from_same_player(self):
        rows = [{'name': '甲', 'count': count, 'from': day, 'to': day, 'id': day}
                for day, count in zip(match_days(12), [30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 21, 20])]
        ranked = rank_streak_runs(list(reversed(rows)))
        self.assertEqual(len(ranked), 11)
        self.assertEqual([row['rank'] for row in ranked[-2:]], [10, 10])
        self.assertNotIn(20, [row['count'] for row in ranked])

    def test_runs_do_not_expand_into_overlapping_subruns(self):
        days = match_days(5)
        self.assertEqual(streak_runs(days, lambda day: True), [
            {'count': 5, 'from': '2025.12.27', 'to': '2025.12.31'}])
        self.assertEqual(streak_runs(days, lambda day: False), [])
        self.assertEqual(streak_runs([], lambda day: True), [])
        self.assertEqual(rank_streak_runs([]), [])


if __name__ == '__main__':
    unittest.main()
