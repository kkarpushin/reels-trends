"""Step 6b: country the account is based in (Instagram "About this account") for leader authors. Paid Apify plans only.

usage: python3 about.py <run_dir> [--dry]
Updates work/profiles.json with "country".
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concurrent.futures as cf
from common import ACTOR_PROFILE, Apify, args

run, opts = args('about.py <run_dir> [--dry]')
acc = run.account()
if not run.cfg['country_for_leaders']:
    raise SystemExit('country_for_leaders is off in config')
if not acc.get('paid'):
    raise SystemExit('skipped: the "about" section is available on paid Apify plans only')
L = run.load('leaders.json'); P = run.load('profiles.json', default={})
users = sorted({r['user'] for r in L if r['user'] and not (P.get(r['user'].lower()) or {}).get('country')})
api = Apify(run.dir)
price = api.price(ACTOR_PROFILE, acc.get('tier', 'FREE'), events=['profile', 'about-account'])
print(f"leader authors without country {len(users)}, about ${len(users) * price:.2f}, budget left ${run.remaining():.2f}")
if '--dry' in opts or not users:
    raise SystemExit
if len(users) * price > run.remaining():
    raise SystemExit('Not enough budget for countries. Set "country_for_leaders": false or raise budget_usd.')

def job(chunk, i):
    d, it = api.run(ACTOR_PROFILE, {'usernames': chunk, 'includeAboutSection': True}, len(chunk) * price * 1.2 + 0.05)
    run.record('about', f'chunk{i}', d.get('usageTotalUsd'))
    print('about chunk', i, d['status'], len(it), f"${d.get('usageTotalUsd') or 0:.3f}", flush=True)
    return it

n = 0
chunks = [users[i:i + 60] for i in range(0, len(users), 60)]
with cf.ThreadPoolExecutor(min(len(chunks), 8)) as ex:
    for it in ex.map(lambda a: job(*a), [(c, i) for i, c in enumerate(chunks)]):
        for p in it:
            u = (p.get('username') or '').lower()
            c = (p.get('about') or {}).get('country') if isinstance(p.get('about'), dict) else None
            if c:
                P.setdefault(u, {})['country'] = c; n += 1
run.save('profiles.json', P)
print(f'countries found {n} of {len(users)}; run total ${run.spent():.2f}')
