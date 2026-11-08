"""Recount browser-cmd's two BU Bench evaluations from public verdict flags."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'results' / 'cross-judging'


def build_summary():
    manifest = json.loads((BASE / 'manifest.json').read_text())
    rows = list(csv.DictReader((ROOT / 'results' / 'tasks.csv').open()))
    categories = {r['task_id']: r['category'] for r in rows}
    task_ids = set(categories)
    excluded = {r['task_id'] for r in rows if r['not_counted'] == '1'}
    assert excluded == set(manifest['manual_failure_task_ids'])
    assert len(task_ids) == manifest['tasks'] == 100
    models = manifest['judges']
    runs = manifest['runs']
    assert len(models) == 4 and len(set(models)) == 4
    assert runs == ['browser-cmd']
    assert {p.name for p in BASE.iterdir() if p.is_dir()} == {'browser-cmd'}
    expected = {(r, p, m) for r in runs for p in ('bu-v1', 'aside') for m in models}
    verdicts = {}
    scores = []
    for record in manifest['records']:
        key = record['run'], record['protocol'], record['judge']
        assert key not in verdicts
        path = ROOT / record['path']
        assert path.resolve().is_relative_to(ROOT.resolve())
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], path
        values = json.loads(path.read_text())
        assert set(values) == task_ids, path
        for value in values.values():
            assert 'pass' in value
            assert set(value) <= {'pass', 'impossible_task', 'reached_captcha'}, path
            assert all(type(v) is bool for v in value.values()), path
        verdicts[key] = values
        raw = sum(v['pass'] for v in values.values())
        counted = sum(v['pass'] and t not in excluded for t, v in values.items())
        by_category = {}
        for category in sorted(set(categories.values())):
            selected = [t for t in task_ids if categories[t] == category]
            by_category[category] = {
                'tasks': len(selected), 'raw_pass': sum(values[t]['pass'] for t in selected),
                'counted_pass': sum(values[t]['pass'] and t not in excluded for t in selected)
                if key[0] == 'browser-cmd' else None}
        scores.append({'run': key[0], 'protocol': key[1], 'judge': key[2],
                       'raw_pass': raw, 'counted_pass': counted if key[0] == 'browser-cmd' else None,
                       'impossible': sum(v.get('impossible_task', False) for v in values.values())
                       if all('impossible_task' in v for v in values.values()) else None,
                       'categories': by_category})
    assert set(verdicts) == expected
    for model in models:
        original = json.loads((ROOT / f'results/judges/{model}.json').read_text())
        assert verdicts['browser-cmd', 'bu-v1', model] == original
    consensus = []
    agreement = []
    for run in runs:
        for protocol in ('bu-v1', 'aside'):
            js = [verdicts[run, protocol, m] for m in models]
            passed = {t for t in task_ids if all(v[t]['pass'] for v in js)}
            failed = {t for t in task_ids if all(not v[t]['pass'] for v in js)}
            consensus.append({'run': run, 'protocol': protocol, 'raw_unanimous_pass': len(passed),
                              'counted_unanimous_pass': len(passed - excluded) if run == 'browser-cmd' else None,
                              'unanimous_fail': len(failed), 'disagreement': 100 - len(passed) - len(failed)})
        for model in models:
            first, second = verdicts[run, 'bu-v1', model], verdicts[run, 'aside', model]
            agreement.append({'run': run, 'judge': model,
                              'same_verdict': sum(first[t]['pass'] == second[t]['pass'] for t in task_ids),
                              'delta_raw_pass': sum(second[t]['pass'] - first[t]['pass'] for t in task_ids)})
    return {'as_of': manifest['as_of'], 'tasks_per_score': 100,
            'scores': scores, 'consensus': consensus, 'protocol_agreement': agreement}


def verify():
    summary = build_summary()
    assert summary == json.loads((BASE / 'summary.json').read_text()), 'cross-judging summary is stale'
    for score in summary['scores']:
        counted = f", {score['counted_pass']} counted" if score['counted_pass'] is not None else ''
        print(f"{score['run']:25} {score['protocol']:16} {score['judge']:18} {score['raw_pass']}/100 raw{counted}")
    print('Cross-judging: IDs, flag-only schema, checksums, scores, categories and agreement verified')


if __name__ == '__main__':
    verify()
