"""Step 6a: speech transcripts of the leaders (apple_yang/instagram-transcripts-scraper). Output: work/transcripts.json {code: text}.

usage: python3 transcripts.py <run_dir> [--dry]
Free Apify plans allow 5 links per run, so the script splits into runs of 5 there.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concurrent.futures as cf
from common import ACTOR_TRANSCRIPT, Apify, args

run, opts = args('transcripts.py <run_dir> [--dry]')
if not run.cfg['transcripts']:
    raise SystemExit('transcripts disabled in config')
L = run.load('leaders.json')
done = run.load('transcripts.json', default={})
todo = [r['code'] for r in L if r['code'] not in done]
api = Apify(run.dir)
acc = run.account()
price = api.price(ACTOR_TRANSCRIPT, acc.get('tier', 'FREE'))
size = 40 if acc.get('paid') else 5
print(f"leaders {len(L)}, to transcribe {len(todo)}, about ${len(todo) * price:.2f}, runs of {size}, budget left ${run.remaining():.2f}")
if '--dry' in opts or not todo:
    raise SystemExit
if len(todo) * price > run.remaining():
    raise SystemExit('Not enough budget for transcripts. Skip them (set "transcripts": false) or raise budget_usd.')

def code_of(t):
    c = t.get('code') or t.get('shortCode')
    if c:
        return c
    u = t.get('url') or t.get('inputUrl') or ''
    p = [x for x in u.split('/') if x]
    return p[p.index('reel') + 1] if 'reel' in p and p.index('reel') + 1 < len(p) else None

def job(g, i):
    d, it = api.run(ACTOR_TRANSCRIPT, {'bulkUrls': [f'https://www.instagram.com/reel/{c}/' for c in g]}, len(g) * price * 1.3 + 0.05)
    run.record('transcripts', f'g{i}', d.get('usageTotalUsd'))
    print('transcripts', i, d['status'], len(it), f"${d.get('usageTotalUsd') or 0:.3f}", flush=True)
    return it

groups = [todo[i:i + size] for i in range(0, len(todo), size)]
with cf.ThreadPoolExecutor(min(len(groups), 8 if acc.get('paid') else 3)) as ex:
    for it in ex.map(lambda a: job(*a), [(g, i) for i, g in enumerate(groups)]):
        for t in it:
            if isinstance(t, dict) and code_of(t):
                done[code_of(t)] = (t.get('text') or t.get('transcript') or '').strip()
run.save('transcripts.json', done)
print(f"with speech {sum(1 for c in (r['code'] for r in L) if done.get(c))} of {len(L)}; run total ${run.spent():.2f}")
