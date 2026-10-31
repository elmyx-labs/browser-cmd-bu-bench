#!/usr/bin/env python3
"""Recount every score from the per-judge verdicts and check the task table against them."""
import csv
import json
from pathlib import Path

from verify_cross_judging import verify

ROOT = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader(open(ROOT / 'results' / 'tasks.csv')))
assert len(rows) == 100 and len({row['task_id'] for row in rows}) == 100
judges = {path.stem: json.loads(path.read_text()) for path in sorted((ROOT / 'results' / 'judges').glob('*.json'))}
assert len(judges) == 4
for name, verdicts in judges.items():
    assert all(int(verdicts[row['task_id']]['pass']) == int(row[name]) for row in rows)
    raw = sum(int(row[name]) for row in rows)
    counted = sum(int(row[name]) and not int(row['not_counted']) for row in rows)
    print(f'{name:18} {counted}/100 counted, {raw}/100 as judged')
categories = sorted({row['category'] for row in rows})
for category in categories:
    part = [row for row in rows if row['category'] == category]
    print(f'{category:18}', ' '.join(f"{sum(int(row[name]) and not int(row['not_counted']) for row in part)}/{len(part)}" for name in judges))
agreed = sum(all(int(row[name]) for name in judges) and not int(row['not_counted']) for row in rows)
print('all four pass:', agreed)

verify()
