"""Step 4: x = reel plays / max(author's median views of recent videos, x_floor). Output: work/scored.json.

usage: python3 score.py <run_dir>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import defaultdict
from common import args, med, rnd

run, _ = args('score.py <run_dir>')
rows = run.load('merged.json'); P = run.load('profiles.json', default={})
floor = run.cfg['x_floor']
for r in rows:
    p = P.get(r['user'].lower()) or {}
    r.update(followers=p.get('followers'), med=p.get('med'), bio=p.get('bio'), cat=p.get('cat'), biz=p.get('biz'), country=p.get('country'))
    r['x'] = round(r['plays'] / max(p['med'], floor), 2) if p.get('med') else None
run.save('scored.json', rows)
by = defaultdict(list)
for r in rows:
    by[r['lang']].append(r)
print(f"x computed for {sum(1 for r in rows if r['x'])} of {len(rows)} reels")
for l, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
    print(f"{l}: reels {len(v)}, with x {sum(1 for r in v if r['x'])}, median x {rnd(med([r['x'] for r in v]))}, median plays {med([r['plays'] for r in v])}")
