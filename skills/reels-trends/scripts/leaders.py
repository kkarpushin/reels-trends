"""Step 5: pick leaders = global top by x (with a plays floor) + global top by plays + top by x inside each language.

usage: python3 leaders.py <run_dir>
Output: work/leaders.json (codes and reasons). Transcripts, frames and labels live in separate files, so re-running is safe.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter, defaultdict
from common import args

run, _ = args('leaders.py <run_dir>')
c = run.cfg['leaders']
rows = run.load('scored.json')
sel = {}
def add(rs, why):
    for r in rs:
        sel.setdefault(r['code'], dict(code=r['code'], user=r['user'], lang=r['lang'], plays=r['plays'], x=r['x'], why=[]))['why'].append(why)

add(sorted([r for r in rows if r['x'] and r['plays'] >= c['x_min_plays']], key=lambda r: -r['x'])[:c['top_x']], 'x')
add(sorted(rows, key=lambda r: -r['plays'])[:c['top_plays']], 'plays')
by = defaultdict(list)
for r in rows:
    if r['x'] and r['plays'] >= c['lang_min_plays'].get(r['lang'], c['lang_min_plays_default']):
        by[r['lang']].append(r)
for l, v in by.items():
    if len(v) >= c['lang_min_reels'] and l != 'xx':
        add(sorted(v, key=lambda r: -r['x'])[:c['lang_quota'].get(l, c['lang_quota_default'])], 'lang')
cnt, out = Counter(), []
for r in sorted(sel.values(), key=lambda r: (-(r['x'] or 0), -r['plays'])):
    if cnt[r['user']] < c['per_author']:
        out.append(r); cnt[r['user']] += 1
run.save('leaders.json', out)
print(f"leaders {len(out)} from {len(cnt)} authors; by language {Counter(r['lang'] for r in out).most_common()}; "
      f"reasons {dict(Counter(w for r in out for w in r['why']))}")
