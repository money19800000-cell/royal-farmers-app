"""Run with python -m unittest discover -s scripts -p test_football_editorial.py."""
import datetime as dt
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import football_editorial as editorial


class EditorialTests(unittest.TestCase):
    def setUp(self):
        self.article = {'headline': '榜首之争仍有悬念', 'deck': '进球与助攻记录勾勒球队本月轮廓',
                        'story': '有据可查的球队记录。' * 25, 'watch': '关注下一场比赛后的榜单变化'}

    def test_rejects_short_or_unsupported_copy(self):
        self.assertTrue(editorial._valid_editorial(self.article))
        for story in ('只有一句话', self.article['story'] + '记者获悉'):
            self.assertFalse(editorial._valid_editorial({**self.article, 'story': story}))

    def test_independent_qwenpaw_review_required(self):
        calls = []
        def converse(prompt, session):
            calls.append(session)
            answer = self.article if len(calls) == 1 else {'approved': True, 'issues': [], 'article': self.article}
            return {'answer': json.dumps(answer, ensure_ascii=False)}
        with tempfile.TemporaryDirectory() as folder, patch.object(editorial, '__file__', str(Path(folder) / 'scripts' / 'football_editorial.py')), patch.dict(sys.modules, {'qwenpaw_bridge': SimpleNamespace(converse=converse)}):
            article, source = editorial._call_local_model(editorial.MATCH_TEMPLATE, {'reportDate': '2026-10-25'})
            self.assertEqual(article, self.article)
            self.assertEqual(source, 'qwenpaw:default-reviewed')
            self.assertEqual(len(set(calls)), 2)

    def test_failed_review_blocks_publication(self):
        def converse(prompt, session):
            return {'answer': json.dumps({'approved': False, 'issues': ['缺少事实依据'], 'article': self.article}, ensure_ascii=False)}
        with tempfile.TemporaryDirectory() as folder, patch.object(editorial, '__file__', str(Path(folder) / 'scripts' / 'football_editorial.py')), patch.dict(sys.modules, {'qwenpaw_bridge': SimpleNamespace(converse=converse)}):
            with self.assertRaises(RuntimeError):
                editorial._call_local_model(editorial.MATCH_TEMPLATE, {'reportDate': '2026-10-25'})

    def test_match_and_month_stats_keep_separate_scopes(self):
        facts = editorial.build_fact_pack({'FIXTURES': [{'home': '蓝队', 'away': '红队', 'homeScore': 0, 'awayScore': 1}],
                                          'MONTHLY_GOALS': [{'name': '甲', 'goals': 13}]}, dt.date(2026, 10, 25), editorial.MATCH_TEMPLATE)
        self.assertEqual(facts['latestMatch']['topScorers'], [])
        self.assertEqual(facts['monthlyGoals'][0]['goals'], 13)


if __name__ == '__main__':
    unittest.main()
