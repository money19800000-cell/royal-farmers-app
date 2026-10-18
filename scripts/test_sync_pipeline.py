"""Production failure checks for CSV snapshots and rule/data release pairing."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from release_manifest import release_files, digest, verify_local, copy_release, BASE_FILES
from export_numbers_csv import export_tables, EXPORT_TABLES, OPTIONAL_TABLES


class SyncPipelineTests(unittest.TestCase):
    def test_required_export_failure_keeps_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/EXPORT_TABLES[0][2]
            target.write_text('previous snapshot')
            def export(doc,sheet,table,path):
                if path.endswith(EXPORT_TABLES[1][2]):return False
                Path(path).write_text('new snapshot')
                return True
            with patch('export_numbers_csv.export_table',side_effect=export):
                with self.assertRaisesRegex(RuntimeError,'必要数据表'):
                    export_tables(None,folder)
            self.assertEqual(target.read_text(),'previous snapshot')

    def test_only_obsolete_optional_table_can_be_missing(self):
        with tempfile.TemporaryDirectory() as folder:
            def export(doc,sheet,table,path):
                if Path(path).name in OPTIONAL_TABLES:return False
                Path(path).write_text('fresh')
                return True
            with patch('export_numbers_csv.export_table',side_effect=export):
                export_tables(None,folder)
            self.assertTrue((Path(folder)/'每场战报+总数据-具体战况.csv').exists())

    def test_release_rejects_rule_change_after_build(self):
        with tempfile.TemporaryDirectory() as folder, tempfile.TemporaryDirectory() as dest:
            root=Path(folder);(root/'scripts').mkdir()
            for name in BASE_FILES:
                (root/name).parent.mkdir(parents=True,exist_ok=True)
                (root/name).write_text('artifact')
            (root/'scripts/build.sh').write_text('python3 scripts/reconcile_stats.py')
            (root/'scripts/reconcile_stats.py').write_text('import check_milestones')
            calculator=root/'scripts/check_milestones.py';calculator.write_text('RULE = 1')
            (root/'scripts/daily_update.sh').write_text('bash scripts/build.sh')
            (root/'sync-status.json').write_text(json.dumps({'files':{p:digest(root/p) for p in release_files(root)}}))
            copy_release(Path(dest),root)
            self.assertTrue((Path(dest)/'scripts/check_milestones.py').exists())
            calculator.write_text('RULE = 2')
            with self.assertRaisesRegex(ValueError,'混合版本'):
                copy_release(Path(dest),root)

    def test_real_manifest_includes_updater_rules_and_all_tests(self):
        files=release_files()
        for name in ['daily_update.sh','export_numbers_csv.py','stats_model.py','check_milestones.py',
                     'reconcile_stats.py','test_milestones.py','test_sync_pipeline.py','roster_columns.py']:
            self.assertIn('scripts/'+name,files)
