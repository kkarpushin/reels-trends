"""Step 0: check the Apify account (plan, spend this cycle, limit) and pick the search engine.

usage: python3 check.py <run_dir> [--smoke]
--smoke runs one tiny paid search (about $0.02) to confirm the search actor still works.
Writes work/account.json: {"plan", "tier", "paid", "engine", "cycle_used", "cycle_limit"}.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ACTOR_SEARCH, ACTOR_HASHTAG, TIER_BY_PLAN, Apify, args

run, opts = args('check.py <run_dir> [--smoke]')
api = Apify(run.dir)
me = api.req('GET', '/users/me')['data']
lim = api.req('GET', '/users/me/limits')['data']
plan = ((me.get('plan') or {}).get('id') or 'UNKNOWN').upper()
paid = plan not in ('FREE', 'UNKNOWN')
used, limit = lim['current']['monthlyUsageUsd'], lim['limits']['maxMonthlyUsageUsd']
cycle = lim.get('monthlyUsageCycle') or {}
engine = run.cfg['engine'] if run.cfg['engine'] != 'auto' else ('memo23' if paid else 'hashtag')
acc = dict(plan=plan, tier=TIER_BY_PLAN.get(plan, 'FREE'), paid=paid, engine=engine, cycle_used=round(used, 2),
           cycle_limit=limit, cycle_end=(cycle.get('endAt') or '')[:10])
run.save('account.json', acc)
print(f"plan {plan} (tier {acc['tier']}), spent this cycle ${used:.2f} of ${limit}, cycle ends {acc['cycle_end']}")
print(f"left on the account: ${limit - used:.2f}; budget of this run: ${run.cfg['budget_usd']}, already spent by this run: ${run.spent():.2f}")
print(f"search engine: {engine}" + ('' if paid else ' (free plan: memo23 runs only the first query with a few results, so the hashtag engine is used)'))
if not paid:
    print('free plan: author country ("about") is paid-only and will be skipped; transcripts run 5 links per run')
if limit - used < run.cfg['budget_usd']:
    print(f"WARNING: the account has less left (${limit - used:.2f}) than this run's budget. Lower budget_usd or top up.")

if '--smoke' in opts:
    if engine == 'memo23':
        d, it = api.run(ACTOR_SEARCH, {'queries': ['coffee'], 'maxResultsPerQuery': 5, 'contentType': 'reels_only',
                                       'searchCoverage': 'efficient'}, 0.05)
        log = api.log(d['id'])
        restricted = 'not paying' in log or 'restricted to 1 query' in log
    else:
        d, it = api.run(ACTOR_HASHTAG, {'hashtags': ['coffee'], 'resultsType': 'reels', 'resultsLimit': 5}, 0.05)
        restricted = False
    run.record('check', 'smoke', d.get('usageTotalUsd'))
    print(f"smoke test: {d['status']}, {len(it)} reels, ${d.get('usageTotalUsd') or 0:.3f}" + (' | RESTRICTED: account treated as free' if restricted else ''))
    if restricted and engine == 'memo23':
        acc['engine'] = 'hashtag'
        run.save('account.json', acc)
        print('switched engine to hashtag')
