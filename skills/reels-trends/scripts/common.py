"""Shared helpers for the reels-trends pipeline: run folder, config with defaults, Apify client, spend ledger.

Every script takes the run folder as its first argument: python3 <script> <run_dir> [options].
The run folder holds config.json (written for the niche), work/ (raw and intermediate data) and report/.
"""
import copy, datetime as dt, json, os, statistics, sys, time, urllib.error, urllib.request

ACTOR_SEARCH = 'memo23~instagram-reels-search-scraper'   # keyword + hashtag-feed search with a date filter (paid Apify plans)
ACTOR_HASHTAG = 'apify~instagram-hashtag-scraper'        # hashtag / keyword feeds, works on the free plan, no date filter
ACTOR_PROFILE = 'apify~instagram-profile-scraper'        # followers, latest posts (author median), "about" country (paid plans)
ACTOR_TRANSCRIPT = 'apple_yang~instagram-transcripts-scraper'

DEFAULTS = {
    'niche': '',
    'report_language': 'ru',
    'date_from': None,
    'date_to': None,
    'budget_usd': 10,
    'engine': 'auto',                       # auto | memo23 | hashtag
    'search': {'coverage': 'comprehensive', 'queries_per_run': 2, 'default_max_per_query': 60,
               'deadline_sec': 1500, 'hashtag_results': 60, 'keyword_results': 40},
    'segments': {},                         # {"EN": {"min_views": 10000, "queries": [["massage", 120], ...], "hashtags": ["massage", ...]}}
    'relevance_regex': '',                  # empty = keep everything the search returned
    'exclude_regex': r'onlyfans|fansly|\bxxx\b|escort',
    'topics': [],                           # [["Topic name", "regex"], ...], first match wins
    'fallback_topic': None,
    'profiles': {'floor_by_lang': {'default': 10000}, 'max_authors': 1500, 'chunk': 120},
    'leaders': {'top_x': 100, 'x_min_plays': 20000, 'top_plays': 30, 'per_author': 3, 'lang_quota': {},
                'lang_quota_default': 7, 'lang_min_plays': {}, 'lang_min_plays_default': 5000, 'lang_min_reels': 15},
    'x_floor': 1000,                        # author median below this is raised to it, so tiny accounts do not get absurd multipliers
    'transcripts': True,
    'frames': True,
    'country_for_leaders': True,
    'focus_topics': [],                     # topics to break down by language in stats
    'labels': {},                           # optional overrides of the label taxonomy: {"formats": [...], "creators": [...], "speech": [...]}
}


def deep_merge(base, extra):
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


class Run:
    def __init__(self, path):
        self.dir = os.path.abspath(path)
        cfg_path = os.path.join(self.dir, 'config.json')
        if not os.path.exists(cfg_path):
            sys.exit(f'config.json not found in {self.dir}. Write it first (see references/config.md).')
        self.cfg = deep_merge(DEFAULTS, json.load(open(cfg_path, encoding='utf-8')))
        self.work = os.path.join(self.dir, 'work')
        self.report = os.path.join(self.dir, 'report')
        os.makedirs(self.work, exist_ok=True)
        os.makedirs(self.report, exist_ok=True)

    def p(self, *parts):
        return os.path.join(self.work, *parts)

    def load(self, name, default=None):
        f = self.p(name)
        if not os.path.exists(f):
            if default is not None:
                return default
            sys.exit(f'{name} not found in work/. Run the previous step first.')
        return json.load(open(f, encoding='utf-8'))

    def save(self, name, data):
        tmp = self.p(name + '.tmp')
        json.dump(data, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
        os.replace(tmp, self.p(name))

    # ---- spend ledger: every paid run is recorded; scripts refuse to start runs above the remaining budget
    def spent(self):
        f = self.p('spend.jsonl')
        if not os.path.exists(f):
            return 0.0
        return sum(json.loads(l).get('usd', 0) for l in open(f, encoding='utf-8') if l.strip())

    def record(self, stage, tag, usd):
        with open(self.p('spend.jsonl'), 'a', encoding='utf-8') as fh:
            fh.write(json.dumps({'stage': stage, 'tag': tag, 'usd': round(usd or 0, 4), 'at': dt.datetime.utcnow().isoformat(timespec='seconds')}) + '\n')

    def remaining(self):
        return float(self.cfg['budget_usd']) - self.spent()

    def account(self):
        return self.load('account.json', default={'plan': 'UNKNOWN', 'paid': False, 'tier': 'FREE'})


# ---- Apify token: env APIFY_TOKEN, file named by APIFY_TOKEN_FILE, ~/.config/reels-trends/apify_token, or APIFY_TOKEN=... in <run>/.env
def token(run_dir=None):
    if os.environ.get('APIFY_TOKEN'):
        return os.environ['APIFY_TOKEN'].strip()
    cands = [os.environ.get('APIFY_TOKEN_FILE'), os.path.expanduser('~/.config/reels-trends/apify_token')]
    if run_dir:
        cands.append(os.path.join(run_dir, '.env'))
    for f in cands:
        if f and os.path.exists(f):
            for line in open(f, encoding='utf-8'):
                line = line.strip()
                if line.startswith('APIFY_TOKEN='):
                    return line.split('=', 1)[1].strip().strip('"\'')
                if line and '=' not in line and not line.startswith('#'):
                    return line
    sys.exit('No Apify token. Set APIFY_TOKEN, or save it to ~/.config/reels-trends/apify_token '
             '(one line), or put APIFY_TOKEN=... into <run_dir>/.env. Token: https://console.apify.com/settings/integrations')


class Apify:
    B = 'https://api.apify.com/v2'

    def __init__(self, run_dir=None):
        self.t = token(run_dir)

    def req(self, method, url, body=None, timeout=120, raw=False):
        r = urllib.request.Request(url if url.startswith('http') else self.B + url, method=method,
                                   data=json.dumps(body).encode() if body is not None else None,
                                   headers={'Authorization': f'Bearer {self.t}', 'Content-Type': 'application/json'})
        for attempt in range(4):
            try:
                resp = urllib.request.urlopen(r, timeout=timeout).read()
                return resp.decode('utf-8', 'replace') if raw else json.loads(resp)
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    sys.exit(f'Apify rejected the token ({e.code}). Check APIFY_TOKEN.')
                if attempt == 3:
                    raise
            except Exception:
                if attempt == 3:
                    raise
            time.sleep(5 * (attempt + 1))

    def start(self, actor, inp, cap, memory=None):
        q = f'maxTotalChargeUsd={max(round(cap, 2), 0.01)}' + (f'&memory={memory}' if memory else '')
        return self.req('POST', f'/acts/{actor}/runs?{q}', inp)['data']

    def wait(self, rid, deadline=None):
        aborted = False
        while True:
            time.sleep(10)
            d = self.req('GET', f'/actor-runs/{rid}')['data']
            if d['status'] not in ('READY', 'RUNNING', 'ABORTING'):
                return d
            if deadline and time.time() > deadline and not aborted:
                self.req('POST', f'/actor-runs/{rid}/abort')   # data collected so far stays in the dataset
                aborted = True

    def items(self, ds):
        out, off = [], 0
        while True:
            chunk = self.req('GET', f'/datasets/{ds}/items?clean=1&format=json&offset={off}&limit=1000')
            out += chunk
            off += len(chunk)
            if len(chunk) < 1000:
                return out

    def log(self, rid):
        return self.req('GET', f'/logs/{rid}', raw=True)

    def run(self, actor, inp, cap, deadline=None, memory=None):
        d = self.wait(self.start(actor, inp, cap, memory)['id'], deadline)
        return d, self.items(d['defaultDatasetId'])

    def price(self, actor, tier='FREE', events=None):
        """Per-result price for the account tier from the actor's live pricing. `events` limits which charge events are summed
        (e.g. profile scraper: ['profile'] or ['profile', 'about-account']); default = every per-result event."""
        fallback = {ACTOR_SEARCH: 0.0015, ACTOR_HASHTAG: 0.0026, ACTOR_PROFILE: 0.0026, ACTOR_TRANSCRIPT: 0.0055}
        try:
            pi = (self.req('GET', f'/acts/{actor}')['data'].get('pricingInfos') or [{}])[-1]
            evs = ((pi.get('pricingPerEvent') or {}).get('actorChargeEvents') or {})
            total = 0.0
            for name, ev in evs.items():
                if ev.get('isOneTimeEvent') or (events and name not in events):
                    continue
                tiers = ev.get('eventTieredPricingUsd') or {}
                total += (tiers.get(tier) or tiers.get('FREE') or {}).get('tieredEventPriceUsd') or ev.get('eventPriceUsd') or 0
            return total or fallback.get(actor, 0.003)
        except Exception:
            return fallback.get(actor, 0.003)


TIER_BY_PLAN = {'FREE': 'FREE', 'STARTER': 'BRONZE', 'SCALE': 'SILVER', 'BUSINESS': 'GOLD'}


def ts(x):
    if x in (None, ''):
        return None
    if isinstance(x, (int, float)):
        return dt.datetime.fromtimestamp(x, dt.timezone.utc)
    try:
        d = dt.datetime.fromisoformat(str(x).replace('Z', '+00:00'))
        return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
    except Exception:
        return None


def med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else None


def rnd(x, n=1):
    return None if x is None else round(x, n)


def window(cfg):
    """Inclusive [date_from, date_to] as UTC datetimes; default = last 30 days."""
    today = dt.datetime.now(dt.timezone.utc).date()
    d_to = dt.date.fromisoformat(cfg['date_to']) if cfg.get('date_to') else today
    d_from = dt.date.fromisoformat(cfg['date_from']) if cfg.get('date_from') else d_to - dt.timedelta(days=30)
    lo = dt.datetime.combine(d_from, dt.time.min, dt.timezone.utc)
    hi = dt.datetime.combine(d_to + dt.timedelta(days=1), dt.time.min, dt.timezone.utc)
    return d_from, d_to, lo, hi


def args(usage):
    if len(sys.argv) < 2 or sys.argv[1].startswith('-'):
        sys.exit('usage: ' + usage)
    return Run(sys.argv[1]), sys.argv[2:]
