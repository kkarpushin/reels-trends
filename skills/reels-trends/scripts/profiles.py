"""Step 3: author profiles for authors with at least one reel above their language floor (incremental, already fetched are skipped).

usage: python3 profiles.py <run_dir> [--dry] [--max N]
Output: work/profiles.json {username: {followers, med (median views of recent videos), bio, cat, biz, country}}.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concurrent.futures as cf
from common import ACTOR_PROFILE, Apify, args, med

run, opts = args('profiles.py <run_dir> [--dry] [--max N]')
pc = run.cfg['profiles']
rows = run.load('merged.json')
floor = pc['floor_by_lang']
mx = int(opts[opts.index('--max') + 1]) if '--max' in opts else int(pc['max_authors'])
auth = []
for r in rows:  # rows are sorted by plays, so the cap keeps the authors of the biggest reels
    if r['user'] and r['plays'] >= floor.get(r['lang'], floor.get('default', 10000)) and r['user'] not in auth:
        auth.append(r['user'])
auth = auth[:mx]
old = run.load('raw_profiles.json', default=[])
have = {(p.get('username') or '').lower() for p in old}
need = [a for a in auth if a.lower() not in have]
api = Apify(run.dir)
acc = run.account()
price = api.price(ACTOR_PROFILE, acc.get('tier', 'FREE'), events=['profile'])
cost = len(need) * price
print(f'authors above floor {len(auth)}, to fetch {len(need)}, about ${cost:.2f} (${price:.4f} each), budget left ${run.remaining():.2f}')
if '--dry' in opts:
    raise SystemExit
if cost > run.remaining():
    raise SystemExit('Not enough budget. Raise profiles.floor_by_lang, pass --max N, or raise budget_usd.')

def job(chunk, i):
    d, it = api.run(ACTOR_PROFILE, {'usernames': chunk}, len(chunk) * price * 1.2 + 0.05)
    run.record('profiles', f'chunk{i}', d.get('usageTotalUsd'))
    print('profiles chunk', i, d['status'], len(it), f"${d.get('usageTotalUsd') or 0:.3f}", flush=True)
    return it

new = []
chunks = [need[i:i + pc['chunk']] for i in range(0, len(need), pc['chunk'])]
if chunks:
    with cf.ThreadPoolExecutor(min(len(chunks), 20 if acc.get('paid') else 3)) as ex:
        for it in ex.map(lambda a: job(*a), [(c, i) for i, c in enumerate(chunks)]):
            new += it
prof = old + [p for p in new if isinstance(p, dict) and p.get('username')]
run.save('raw_profiles.json', prof)
P = run.load('profiles.json', default={})
for p in prof:
    u = (p.get('username') or '').lower()
    views = [x.get('videoViewCount') or x.get('videoPlayCount') for x in (p.get('latestPosts') or []) if (x.get('videoViewCount') or x.get('videoPlayCount'))]
    about = p.get('about') if isinstance(p.get('about'), dict) else {}
    P[u] = dict(P.get(u, {}), followers=p.get('followersCount'), biz=p.get('isBusinessAccount'), cat=p.get('businessCategoryName'),
                bio=(p.get('biography') or '')[:220], verified=p.get('verified'), med=med(views), nv=len(views), fullName=p.get('fullName'),
                **({'country': about.get('country')} if about.get('country') else {}))
run.save('profiles.json', P)
print(f"profiles {len(P)}, with a views median {sum(1 for v in P.values() if v.get('med'))}; run total ${run.spent():.2f}")
