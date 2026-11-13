"""Regressions for evidenced shifts, summary repair and future source fixes."""
import csv
import tempfile
import unittest
from pathlib import Path

from stats_model import parse_matches, read_roster, invalid_match_dates, today_code
from check_milestones import compute_milestones, validate_coverage


class SourceColumnTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)

    def write_csv(self, name, rows):
        path = self.root / name
        with path.open('w', newline='') as out:
            csv.writer(out).writerows(rows)
        return path

    def match_rows(self):
        return [
            ['', '260131-1', '内部友谊赛（三队）', '', '红队', '', '0', '2', '', '蓝队', ''],
            ['', '', '', '', '', '', '', '', '', '甲', '乙'],
            ['', '', '', '', '', '', '', '', '乙', '甲', ''],
        ]

    def test_header_and_detail_evidence_preserve_standard_rows(self):
        path = self.write_csv('match.csv', self.match_rows())
        before = path.read_bytes()
        match = parse_matches(path, '20261113')[0]
        self.assertEqual(match['away'], 'Royal Farmers蓝队')
        self.assertEqual(match['awayScorers'], ['甲', '乙'])
        self.assertEqual(match['awayAssists'], ['乙', '甲'])
        self.assertEqual([c['sourceLine'] for c in match['sourceCorrections']], [2])
        self.assertEqual(path.read_bytes(), before)

    def test_extra_cell_without_shifted_header_is_not_reinterpreted(self):
        rows = self.match_rows()
        rows[0][8:10] = ['蓝队', '']
        match = parse_matches(self.write_csv('match.csv', rows), '20261113')[0]
        self.assertEqual(match['awayScorers'], ['乙'])
        self.assertEqual(match['sourceCorrections'], [])

    def test_invalid_date_and_new_fixture_reset_shift_evidence(self):
        rows = self.match_rows()[:2] + [
            ['', '260132', '', '', '红队', '', '0', '1', '', '蓝队', ''],
            ['', '', '', '', '', '', '', '', '', '丙', '丁'],
            ['', '260201', '内部友谊赛（三队）', '', '红队', '', '0', '1', '蓝队', '', ''],
            ['', '', '', '', '', '', '', '', '', '丙', '丁'],
        ]
        path = self.write_csv('match.csv', rows)
        matches = parse_matches(path, '20261113')
        self.assertEqual(sum(len(m['sourceCorrections']) for m in matches), 1)
        self.assertEqual(matches[0]['awayScorers'], [])
        self.assertEqual(invalid_match_dates(path)[0]['rawDate'], '260132')

    def test_summary_delta_and_already_corrected_summary(self):
        matchPath = self.write_csv('match.csv', self.match_rows())
        headers = ['名字', '出场', '进球', '助攻', '2026出场', '2026进球', '2026助攻']
        for goals, assists in [(0, 2), (1, 1)]:
            with self.subTest(goals=goals):
                rosterPath = self.write_csv('roster.csv', [headers, ['甲', 0, goals, assists, 0, goals, assists]])
                before = rosterPath.read_bytes()
                players, _, _ = read_roster(rosterPath, '20261113', match_path=matchPath)
                self.assertEqual((players['甲']['goals'], players['甲']['assists']), (1, 1))
                self.assertEqual(players['甲']['rawSummary']['assists'], assists)
                self.assertEqual(rosterPath.read_bytes(), before)
        rosterPath = self.write_csv('roster.csv', [headers, ['甲', 0, 0, 100, 0, 0, 100]])
        with self.assertRaisesRegex(ValueError, '错列修正与汇总不一致'):
            read_roster(rosterPath, '20261113', match_path=matchPath)

    def test_production_corrections_keep_milestone_gate(self):
        asOf = today_code()
        roster = read_roster(as_of=asOf)[0]
        matches = parse_matches(as_of=asOf)
        player = roster['张伟']
        shifted = [m for m in matches if m['id'].split(':')[0] in ('260131-4', '260131-5')]
        self.assertEqual(sum(m['awayScorers'].count('张伟') for m in shifted), 3)
        milestones = compute_milestones(roster, matches, asOf, {})
        validate_coverage(roster, milestones, asOf)
        if player['assists'] < 100:
            self.assertFalse(any(m['name'] == '张伟' and m['type'] == 'career_assists' for m in milestones))


if __name__ == '__main__':
    unittest.main()
