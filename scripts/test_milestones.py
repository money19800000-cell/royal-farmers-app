"""Regression coverage for detail-based milestone dates and build persistence."""
import copy
import unittest
from check_milestones import compute_milestones
from stats_model import read_roster, parse_matches, today_code


def player(goals=200, seasonGoals=None, years=None):
    return {'name': '甲', 'num': '10', 'apps': 0, 'goals': goals, 'assists': 0,
            'attendance': {}, 'seasons': years or [{'year':'2026', 'apps':0, 'goals':goals if seasonGoals is None else seasonGoals, 'assists':0}]}


def match(day, goals, away=None):
    return {'dateCode':day, 'homeRf':True, 'awayRf':False, 'homeScorers':['甲']*goals,
            'homeAssists':[], 'awayScorers':away or [], 'awayAssists':[]}


class MilestoneTests(unittest.TestCase):
    def compute(self, p, matches):
        return compute_milestones({'甲':p}, matches, '20261016', {})

    def test_summary_difference_does_not_erase_recorded_crossing(self):
        rows=self.compute(player(), [match('20261015',198)])
        self.assertEqual(len(rows),2)
        self.assertTrue(all(m['date']=='2026-10-15' and m['value']==100 for m in rows))
        self.assertEqual(len({m['id'] for m in rows}),len(rows))

    def test_exact_equality_and_cross_multiple_thresholds(self):
        rows=self.compute(player(201),[match('20260101',99),match('20261015',102)])
        self.assertTrue(all(m['date']=='2026-10-15' for m in rows))
        self.assertEqual({m['value'] for m in rows},{100,200})

    def test_detail_thresholds_override_smaller_summary(self):
        rows=self.compute(player(100),[match('20261015',250)])
        self.assertEqual(len(rows),4)
        self.assertEqual({m['value'] for m in rows}, {100,200})
        self.assertTrue(all(m['date']=='2026-10-15' for m in rows))

    def test_order_same_day_opponents_and_future(self):
        matches=[match('20261015',50,['甲']*400),match('20260101',100),match('20261015',50),match('20261017',100)]
        rows=self.compute(player(),matches)
        self.assertEqual(rows,self.compute(player(),list(reversed(matches))))
        self.assertEqual({m['date'] for m in rows if m['value']==200},{'2026-10-15'})

    def test_career_conflict_is_not_assumed_opening_balance(self):
        rows=self.compute(player(300,200),[match('20261015',200)])
        career=[m for m in rows if m['type']=='career_goals']
        self.assertEqual(len(career),2)
        self.assertTrue(all(m['date']=='2026-10-15' and m['achievedYear']==2026 for m in career))
        self.assertTrue(all(m['date'] for m in rows if m['type']=='season_goals'))

    def test_dynamic_seasons_and_career_carry(self):
        p=player(200,years=[{'year':'2027','apps':0,'goals':50,'assists':0},{'year':'2026','apps':0,'goals':150,'assists':0}])
        rows=compute_milestones({'甲':p},[match('20260101',150),match('20270101',50)],'20270102',{})
        self.assertEqual(next(m['date'] for m in rows if m['type']=='career_goals' and m['value']==200),'2027-01-01')

    def test_attendance_dates_override_stale_summary(self):
        from datetime import date,timedelta
        days={(date(2026,1,1)+timedelta(days=i)).strftime('%Y%m%d'):'3' for i in range(100)}
        p=player(0);p['attendance']=days;p['apps']=99;p['seasons'][0]['apps']=100
        rows=self.compute(p,[])
        self.assertEqual(len(rows),2)
        self.assertTrue(all(m['date']=='2026-04-10' for m in rows))

    def test_real_csv_crossings_and_build_use_same_model(self):
        from collections import Counter, defaultdict
        from reconcile_stats import load_data, reconcile
        asOf=today_code()
        roster=read_roster(as_of=asOf)[0]
        matches=parse_matches(as_of=asOf)
        rows=compute_milestones(roster,matches,asOf,{})
        expected=defaultdict(Counter)
        for m in matches:
            for side in ('home','away'):
                if m[side+'Rf']:
                    for metric,field in [('goals','Scorers'),('assists','Assists')]:
                        for name in m[side+field]:
                            if name in roster:
                                expected[name,metric][m['dateCode']]+=1
        for name,p in roster.items():
            expected[name,'apps'].update(p['attendance'].keys())
        keys=set()
        for m in rows:
            self.assertTrue(m['date'] and m['dateStatus']=='exact')
            day=m['date'].replace('-','');metric=m['type'].split('_')[1]
            days=expected[m['name'],metric]
            eligible=[(d,c) for d,c in days.items() if m['season'] is None or d.startswith(str(m['season']))]
            self.assertLess(sum(c for d,c in eligible if d<day),m['value'])
            self.assertGreaterEqual(sum(c for d,c in eligible if d<=day),m['value'])
            keys.add(m['id'])
        self.assertEqual(len(keys),len(rows))
        for (name,metric),days in expected.items():
            for threshold in range(100,sum(days.values())+1,100):
                self.assertIn(f'{name}:career_{metric}:all:{threshold}',keys)
        data,_=reconcile(copy.deepcopy(load_data()))
        self.assertEqual([(m['id'],m['date']) for m in data['MILESTONES']],[(m['id'],m['date']) for m in rows])

    def test_assists_internal_sides_and_player_missing_from_roster(self):
        m=match('20261015',0)
        m.update(homeAssists=['乙']*60,awayRf=True,awayAssists=['乙']*40)
        rows=self.compute(player(0),[m])
        self.assertEqual(len(rows),2)
        self.assertTrue(all(m['name']=='乙' and m['date']=='2026-10-15' and m['value']==100 for m in rows))

if __name__=='__main__': unittest.main()
