"""Step 1: find reels for every segment (language/market) of config.json inside the date window.

usage: python3 search.py <run_dir> [--dry] [--engine memo23|hashtag] [--deadline SEC] [--only SEG[,SEG]] [--tag NAME]

memo23 engine (paid Apify plans): keyword search plus hashtag feeds, date and min-views filters applied by the actor, misses are free.
hashtag engine (free plan): apify/instagram-hashtag-scraper on hashtags and keywords, every returned post is billed, dates are
filtered later in merge.py. Raw results go to work/raw/<engine>__<SEG>__<nn>.json. Runs past the deadline are aborted, their data is kept.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concurrent.futures as cf, json, os, re, time
from common import ACTOR_SEARCH, ACTOR_HASHTAG, Apify, args, window

run, opts = args('search.py <run_dir> [--dry] [--engine memo23|hashtag] [--deadline SEC] [--only SEG] [--tag NAME]')
cfg, sc = run.cfg, run.cfg['search']
acc = run.account()
def opt(name, default=None):
    return opts[opts.index(name) + 1] if name in opts and opts.index(name) + 1 < len(opts) else default
engine = opt('--engine') or acc.get('engine') or ('memo23' if acc.get('paid') else 'hashtag')
only = set((opt('--only') or '').split(',')) - {''}
tag = opt('--tag', '')
d_from, d_to, _, _ = window(cfg)
deadline_sec = int(opt('--deadline', sc['deadline_sec']))
api = Apify(run.dir)
tier = acc.get('tier', 'FREE')
os.makedirs(run.p('raw'), exist_ok=True)

def norm_q(q):
    return [q, sc['default_max_per_query']] if isinstance(q, str) else [q[0], int(q[1])]

jobs = []
if engine == 'memo23':
    price = api.price(ACTOR_SEARCH, tier)
    for seg, s in cfg['segments'].items():
        if only and seg not in only:
            continue
        qs = [norm_q(q) for q in s.get('queries', [])]
        n = max(1, int(sc['queries_per_run']))
        for i in range(0, len(qs), n):
            part = qs[i:i + n]
            mx = max(m for _, m in part)
            inp = dict(queries=[q for q, _ in part], maxResultsPerQuery=mx, oldestPostDate=str(d_from), newestPostDate=str(d_to),
                       contentType='reels_only', hashtagFeedType='top', searchCoverage=sc['coverage'], minimumViews=int(s.get('min_views', 0)))
            jobs.append(dict(actor=ACTOR_SEARCH, inp=inp, n=len(part) * mx, tag=f'memo23__{seg}__{tag}{i // n:02d}', seg=seg))
else:
    price = api.price(ACTOR_HASHTAG, tier)
    for seg, s in cfg['segments'].items():
        if only and seg not in only:
            continue
        tags = s.get('hashtags') or [re.sub(r'[\s#]+', '', norm_q(q)[0]) for q in s.get('queries', [])]
        tags = list(dict.fromkeys(t.lstrip('#') for t in tags if t))
        for i in range(0, len(tags), 3):
            part = tags[i:i + 3]
            jobs.append(dict(actor=ACTOR_HASHTAG, inp=dict(hashtags=part, resultsType='reels', resultsLimit=sc['hashtag_results']),
                             n=len(part) * sc['hashtag_results'], tag=f'hashtag__{seg}__{tag}h{i // 3:02d}', seg=seg))
        kws = [norm_q(q)[0] for q in s.get('queries', []) if ' ' in norm_q(q)[0]]
        for i in range(0, len(kws), 3):
            part = kws[i:i + 3]
            jobs.append(dict(actor=ACTOR_HASHTAG, inp=dict(hashtags=part, keywordSearch=True, resultsType='reels', resultsLimit=sc['keyword_results']),
                             n=len(part) * sc['keyword_results'], tag=f'hashtag__{seg}__{tag}k{i // 3:02d}', seg=seg))

for j in jobs:
    j['cap'] = j['n'] * price + 0.03
total = sum(j['cap'] for j in jobs)
left = run.remaining()
if total > left and jobs:
    # shrink per-run result caps proportionally so the worst case fits the remaining budget
    k = max(0.05, (left - 0.03 * len(jobs)) / max(total - 0.03 * len(jobs), 1e-9))
    for j in jobs:
        key = 'maxResultsPerQuery' if j['actor'] == ACTOR_SEARCH else 'resultsLimit'
        j['inp'][key] = max(5, int(j['inp'][key] * k))
        per = len(j['inp'].get('queries') or j['inp'].get('hashtags'))
        j['n'] = per * j['inp'][key]
        j['cap'] = j['n'] * price + 0.03
    print(f'NOTE: worst case ${total:.2f} was above the remaining budget ${left:.2f}; result caps scaled by {k:.2f}')
    total = sum(j['cap'] for j in jobs)

print(f"engine {engine}, window {d_from}..{d_to}, segments {len({j['seg'] for j in jobs})}, runs {len(jobs)}, "
      f"price/result ${price:.4f}, worst case ${total:.2f}, budget left ${left:.2f}")
if engine == 'memo23':
    print('memo23 bills only reels that pass the date and views filters, so the real spend is usually 30-60% of the worst case')
if '--dry' in opts or not jobs:
    for j in jobs[:200]:
        print(' ', j['tag'], json.dumps(j['inp'].get('queries') or j['inp'].get('hashtags'), ensure_ascii=False), 'cap $%.2f' % j['cap'])
    raise SystemExit

deadline = time.time() + deadline_sec
spent = 0.0

def do(j):
    d, it = api.run(j['actor'], j['inp'], j['cap'], deadline=deadline, memory=512 if j['actor'] == ACTOR_SEARCH else None)
    json.dump(it, open(run.p('raw', j['tag'] + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    run.record('search', j['tag'], d.get('usageTotalUsd'))
    return j['tag'], d['status'], len(it), d.get('usageTotalUsd') or 0

workers = 24 if acc.get('paid') else 4
with cf.ThreadPoolExecutor(min(workers, len(jobs))) as ex:
    for f in cf.as_completed([ex.submit(do, j) for j in jobs]):
        try:
            t, st, n, usd = f.result()
            spent += usd
            print(t, st, n, 'reels', f'${usd:.3f}', flush=True)
        except Exception as e:
            print('ERROR', e, flush=True)
print(f'DONE search ${spent:.2f}; run total ${run.spent():.2f} of ${cfg["budget_usd"]}', flush=True)
