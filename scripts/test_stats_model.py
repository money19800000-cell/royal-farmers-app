"""Regression cases for authoritative statistics and CSV format boundaries."""
import csv
import tempfile
import unittest
from pathlib import Path
from stats_model import parse_matches, external_stats, read_roster, EXTERNAL_TWO, normalize_type
from reconcile_stats import load_data, reconcile, validate, write_updates, ROOT

class StatsTests(unittest.TestCase):
    def csv_file(self, rows):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name)/'source.csv'
        with path.open('w', newline='') as out:
            csv.writer(out).writerows(rows)
        return path

    def test_missing_score_not_draw_and_repeated_date_not_header(self):
        path = self.csv_file([
            ['', '260226', '对外友谊赛（两队）', '场地', '蓝队', '', '', '', '对手', ''],
            ['', '260226', '', '', '甲', '乙', '', '', '', ''],
            ['', '260226', '', '', '甲', '甲', '', '', '', ''],
            ['', '261015', '外部友谊赛（两队）', '', '蓝队', '', '1', '0', '对手', ''],
        ])
        matches = parse_matches(path, '20261014')
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['result'], 'U')
        self.assertIsNone(matches[0]['homeScore'])
        self.assertEqual(matches[0]['homeScorers'], ['甲', '甲'])
        self.assertEqual(matches[0]['homeAssists'], ['乙', ''])
        summary = external_stats(matches)['all']['record']
        self.assertEqual((summary['played'], summary['drawn'], summary['pending']), (0,0,1))

    def test_invalid_date_block_cannot_become_previous_match_goals(self):
        path=self.csv_file([
            ['', '250830', '对内友谊赛（三队）', '台地球场', '蓝队', '', '1', '0', '红队', ''],
            ['', '250830', '', '', '甲', '乙', '', '', '', ''],
            ['', '2508027', '对外友谊赛（两队）', '琦逸足球场', '蓝队', '', '20', '6', '对手', ''],
            ['', '2508027', '', '琦逸足球场', '甲', '乙', '', '', '', ''],
        ])
        matches=parse_matches(path,'20261014')
        self.assertEqual(len(matches),1)
        self.assertEqual(matches[0]['homeScorers'],['甲'])

    def test_external_scope_and_away_perspective(self):
        rows=[]
        for i,kind in enumerate(['对外友谊赛（两队）','外部友谊赛（三队）','内部友谊赛（两队）']):
            rows.append(['',f'260101-{i}',kind,'','对手','','1','3','蓝队',''])
        matches=parse_matches(self.csv_file(rows),'20261014')
        r=external_stats(matches)['all']['record']
        self.assertEqual((r['played'],r['won'],r['gf'],r['ga']), (1,1,3,1))
        self.assertEqual(normalize_type('对内友谊赛(三队)'), '内部友谊赛（三队）')

    def test_roster_date_columns_include_empty_days_exclude_future(self):
        path=self.csv_file([
            ['名字','出场','进球','助攻','团队总成绩','2026出场','2026进球','2026助攻','2026团队分','20261001','20261002','20261015'],
            ['甲','2','1','0','4','2','1','0','2','3','','1'],
        ])
        players,dates,_=read_roster(path,'20261014')
        self.assertEqual([d for d,_ in dates], ['20261001','20261002'])
        self.assertEqual(players['甲']['attendance'], {'20261001':'3'})
        self.assertEqual(players['甲']['careerRating'], 3)
        self.assertEqual(players['甲']['apps'], 1)
        self.assertEqual(players['甲']['seasons'][0]['rating'], 3)

    def test_scorer_columns_never_shift_for_venue_text(self):
        path=self.csv_file([
            ['', '260514', '外部友谊赛（两队）', '球场', '蓝队', '', '2', '0', '对手', ''],
            ['', '', '', '潘磊', '姜珂', '', '', '', '', ''],
            ['', '', '', '姜珂', '潘磊', '', '', '', '', ''],
        ])
        m=parse_matches(path,'20261017')[0]
        self.assertEqual(m['homeScorers'],['姜珂','潘磊'])
        self.assertEqual(m['homeAssists'],['',''])

    def test_named_internal_team_and_combined_header_goal(self):
        path=self.csv_file([
            ['', '251122', '内部友谊赛（三队）', '', '张伟的红队', '', '1', '1', '白队', ''],
            ['', '', '', '', '潘磊', '夏泉', '', '', '姜珂', '刘洋'],
            ['', '210803', '', '', '杨勇', '马继海', '2', '0', '', ''],
            ['', '', '', '', '姜珂', '李成杰', '', '', '', ''],
        ])
        internal,combined=parse_matches(path,'20261017')
        self.assertTrue(internal['homeRf'] and internal['awayRf'])
        self.assertTrue(combined['homeRf'])
        self.assertEqual(combined['homeScorers'],['杨勇','姜珂'])
        self.assertEqual(combined['homeAssists'],['马继海','李成杰'])

    def test_repeated_detail_date_uses_matching_explicit_match_id(self):
        path=self.csv_file([
            ['342','241207','外部友谊赛（两队）','','白队','','1','0','对手',''],
            ['342','241211','外部友谊赛（两队）','','潘磊','姜珂','','','',''],
            ['343','241211','外部友谊赛（两队）','','潘磊','姜珂','','','',''],
        ])
        m=parse_matches(path,'20261017')[0]
        self.assertEqual(m['dateCode'],'20241207')
        self.assertEqual(m['homeScorers'],['潘磊'])
        self.assertTrue(any('按比赛ID' in issue for issue in m['issues']))

    def test_full_snapshot_consistency_and_idempotence(self):
        import copy
        old=load_data()
        data,matches=reconcile(copy.deepcopy(old))
        validate(data)
        second,_=reconcile(copy.deepcopy(data))
        self.assertEqual(data,second)
        self.assertEqual(write_updates((ROOT/'data.jsx').read_text(),old,data),(ROOT/'data.jsx').read_text())
        self.assertTrue(all(p['scorer'] != p['ast'] for rows in data['GOLDEN_PAIRS'].values() for p in rows))
        self.assertEqual(len(data['ROSTER_LOG_2026']), data['STATS_META']['seasonMatchDays']['2026'])
        for n in ['童超','吴能']:
            p=next(p for p in [*data['PLAYERS'],*data['PLAYER_LOOKUP'].values()] if p['name']==n)
            self.assertTrue(not p['photo'] or n in p['photo'])

if __name__=='__main__': unittest.main()
