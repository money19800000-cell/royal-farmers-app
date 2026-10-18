"""Bind data, calculation rules and updater to one verifiable website release."""
from __future__ import annotations
import argparse
import ast
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'sync-status.json'
BASE_FILES = ['data.jsx', 'components.jsx', 'app.jsx', 'data.min.js', 'components.min.js',
              'app.min.js', 'index.html', 'site.css', 'players.css', 'colors_and_type.css',
              'mobile.css', 'ib-fund-data.js', 'docs/milestone-consistency.md',
              'docs/milestone-source-rules.md', 'docs/sync-workflow.md']


def release_files(root=ROOT):
    files = set(BASE_FILES)
    # Include the actual updater, its entry points and local Python dependencies.
    # This prevents a new calculation rule from being published without its
    # exporter/helper, tests, or the updater that invokes it.
    pending = ['daily_update.sh', 'build.sh', 'release_manifest.py', 'reconcile_stats.py',
               'export_numbers_csv.py', 'check_milestones.py', 'generate_daily_report.py']
    pending += [p.name for p in (root/'scripts').glob('test_*.py')]
    while pending:
        name = pending.pop()
        rel = 'scripts/'+name
        path = root/rel
        if rel in files or not path.is_file():
            continue
        files.add(rel)
        source = path.read_text()
        if name.endswith('.sh'):
            pending += re.findall(r'([A-Za-z_][A-Za-z_0-9]*\.py)', source)
        elif name.endswith('.py'):
            for node in ast.walk(ast.parse(source)):
                modules = ([node.module] if isinstance(node, ast.ImportFrom) else
                           [a.name for a in node.names] if isinstance(node, ast.Import) else [])
                pending += [m.split('.')[0]+'.py' for m in modules if m]
    return sorted(files)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_manifest(root=ROOT):
    # Import here so unit tests can exercise file verification independently.
    from reconcile_stats import load_data
    from check_milestones import MILESTONE_RULE_VERSION
    data = load_data()
    return dict(ruleVersion=MILESTONE_RULE_VERSION, asOf=data['STATS_META']['asOf'],
                milestoneCount=len(data['MILESTONES']),
                milestones=[{'id':m['id'], 'date':m['date']} for m in data['MILESTONES']],
                files={name:digest(root/name) for name in release_files(root)})


def verify_local(root=ROOT):
    manifest = json.loads((root/MANIFEST).read_text())
    if set(manifest['files']) != set(release_files(root)):
        raise ValueError('发布文件清单已变化，请重新构建')
    changed = [name for name,expected in manifest['files'].items()
               if not (root/name).is_file() or digest(root/name) != expected]
    if changed:
        raise ValueError('构建后文件已变化，禁止混合版本发布：'+', '.join(changed))
    return manifest


def copy_release(destination, root=ROOT):
    manifest = verify_local(root)
    for name in [*manifest['files'], MANIFEST]:
        target = destination/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root/name, target)


def verify_remote(base_url, root=ROOT):
    manifest = verify_local(root)
    token = digest(root/MANIFEST)[:16]
    def fetch(name):
        return subprocess.check_output(['curl','-fsSL','--connect-timeout','10','--max-time','20',
                                        base_url.rstrip('/')+'/'+name+'?release='+token])
    remote = json.loads(fetch(MANIFEST))
    if remote != manifest:
        raise ValueError('线上版本清单尚未更新')
    for name in ['index.html','data.min.js','components.min.js','app.min.js']:
        if hashlib.sha256(fetch(name)).hexdigest() != manifest['files'][name]:
            raise ValueError('线上文件版本不一致：'+name)
    print(f'线上验证通过：{manifest["milestoneCount"]} 条里程碑，规则 {manifest["ruleVersion"]}')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write',action='store_true')
    group.add_argument('--check',action='store_true')
    group.add_argument('--copy',type=Path)
    group.add_argument('--verify-url')
    args=parser.parse_args()
    if args.write:
        (ROOT/MANIFEST).write_text(json.dumps(make_manifest(),ensure_ascii=False,indent=2)+'\n')
    elif args.check:verify_local()
    elif args.copy:copy_release(args.copy)
    else:verify_remote(args.verify_url)


if __name__=='__main__':main()
