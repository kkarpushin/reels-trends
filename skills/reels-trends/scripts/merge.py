"""Step 2: merge raw search results -> dedupe, date window, niche relevance, exclusions, caption language, topic.

usage: python3 merge.py <run_dir>
Output: work/merged.json (sorted by plays). Prints what was dropped and the language/topic mix, so you can fix
relevance_regex, exclude_regex, topics or add queries before paying for profiles.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glob, json, os, re
from collections import Counter
from common import args, ts, window

run, _ = args('merge.py <run_dir>')
cfg = run.cfg
_, _, LO, HI = window(cfg)
REL = re.compile(cfg['relevance_regex'], re.I) if cfg.get('relevance_regex') else None
EXC = re.compile(cfg['exclude_regex'], re.I) if cfg.get('exclude_regex') else None
TOPICS = [(n, re.compile(rx, re.I)) for n, rx in cfg.get('topics', [])]
FALLBACK = cfg.get('fallback_topic') or ('Общее' if cfg['report_language'] == 'ru' else 'General')

try:
    from lingua import Language as L, LanguageDetectorBuilder
    LANGS = {L.ENGLISH: 'EN', L.SPANISH: 'ES', L.PORTUGUESE: 'PT', L.RUSSIAN: 'RU', L.UKRAINIAN: 'UA', L.TURKISH: 'TR', L.GERMAN: 'DE',
             L.FRENCH: 'FR', L.ITALIAN: 'IT', L.POLISH: 'PL', L.DUTCH: 'NL', L.INDONESIAN: 'ID', L.MALAY: 'ID', L.THAI: 'TH', L.VIETNAMESE: 'VI',
             L.JAPANESE: 'JA', L.KOREAN: 'KO', L.CHINESE: 'ZH', L.ARABIC: 'AR', L.PERSIAN: 'FA', L.HINDI: 'HI', L.TAGALOG: 'TL', L.ROMANIAN: 'RO',
             L.CZECH: 'CS', L.GREEK: 'EL', L.HEBREW: 'HE', L.KAZAKH: 'KK', L.GEORGIAN: 'KA', L.ARMENIAN: 'HY', L.AZERBAIJANI: 'AZ', L.URDU: 'UR',
             L.BENGALI: 'BN', L.HUNGARIAN: 'HU', L.SWEDISH: 'SV', L.BULGARIAN: 'BG', L.SERBIAN: 'SR', L.CROATIAN: 'HR', L.LITHUANIAN: 'LT',
             L.LATVIAN: 'LV', L.ESTONIAN: 'ET', L.FINNISH: 'FI', L.DANISH: 'DA', L.BOKMAL: 'NO', L.CATALAN: 'CA'}
    DET = LanguageDetectorBuilder.from_languages(*LANGS).with_minimum_relative_distance(0.05).build()
except ImportError:
    DET = None
    print('NOTE: lingua is not installed (pip install lingua-language-detector); language = language of the search query')


def clean(s):
    s = re.sub(r'https?://\S+|[#@][\w.]+', '', s or '')
    return re.sub(r'[^\w\s]', '', s, flags=re.U)


def lang_of(r):
    q = sorted(r['qseg'])
    txt = clean(r['cap'])
    if DET is None or len(re.sub(r'[\W\d_]', '', txt)) < 12:
        # caption is only hashtags or emoji: hashtags like #massage say nothing about the language, use the query's
        return (q[0] if len(q) == 1 and q != ['EN'] else 'xx'), 'query'
    l = DET.detect_language_of(txt)
    return (LANGS.get(l, 'xx') if l else 'xx'), 'caption'


def topic_of(text):
    return next((n for n, rx in TOPICS if rx.search(text or '')), FALLBACK)


rows = {}
def add(r):
    o = rows.get(r['code'])
    if o:
        o['queries'] |= r['queries']; o['qseg'] |= r['qseg']; o['plays'] = max(o['plays'], r['plays'])
    else:
        rows[r['code']] = r

for f in sorted(glob.glob(run.p('raw', '*.json'))):
    name = os.path.basename(f)
    eng, seg = name.split('__')[0], name.split('__')[1]
    for x in json.load(open(f, encoding='utf-8')):
        if not isinstance(x, dict) or not x.get('shortCode'):
            continue
        if eng == 'memo23':
            add(dict(code=x['shortCode'], url=x.get('url') or f"https://www.instagram.com/reel/{x['shortCode']}/", t=ts(x.get('takenAt')),
                     plays=x.get('playCount') or 0, likes=x.get('likeCount') or 0, comments=x.get('commentCount') or 0, shares=x.get('shareCount'),
                     user=x.get('username') or '', name=x.get('userFullName') or '', cap=x.get('caption') or '', tags=x.get('hashtags') or [],
                     music=' · '.join(filter(None, [x.get('musicArtist'), x.get('musicTitle')])), dur=x.get('videoDuration'),
                     thumb=x.get('thumbnailUrl'), video=x.get('videoUrl'), loc=x.get('locationName'), alt=x.get('accessibilityCaption') or '',
                     queries={x.get('query') or ''}, qseg={seg}))
        else:
            if x.get('type') not in (None, 'Video') and x.get('productType') != 'clips':
                continue
            mi = x.get('musicInfo') if isinstance(x.get('musicInfo'), dict) else {}
            src = (x.get('inputUrl') or '').rstrip('/').split('/')[-1]
            add(dict(code=x['shortCode'], url=x.get('url') or f"https://www.instagram.com/reel/{x['shortCode']}/", t=ts(x.get('timestamp')),
                     plays=x.get('videoPlayCount') or x.get('igPlayCount') or x.get('videoViewCount') or 0, likes=max(x.get('likesCount') or 0, 0),
                     comments=x.get('commentsCount') or 0, shares=x.get('sharesCount'), user=x.get('ownerUsername') or '',
                     name=x.get('ownerFullName') or '', cap=x.get('caption') or '', tags=x.get('hashtags') or [],
                     music=' · '.join(filter(None, [mi.get('artist_name'), mi.get('song_name')])), dur=x.get('videoDuration'),
                     thumb=x.get('displayUrl'), video=x.get('videoUrl'), loc=x.get('locationName'), alt=x.get('alt') or '',
                     queries={src}, qseg={seg}))

st = Counter(unique_found=len(rows))
out = []
for r in rows.values():
    if not r['t'] or not (LO <= r['t'] < HI):
        st['outside_dates'] += 1; continue
    hay = ' '.join([r['cap'], ' '.join(r['tags']), r['user'], r['name'], r['loc'] or '', r['alt']])
    if REL and not REL.search(hay):
        st['not_in_niche'] += 1; continue
    if EXC and EXC.search(hay):
        st['excluded'] += 1; continue
    r['lang'], r['lang_src'] = lang_of(r)
    r['topic'] = topic_of(r['cap'] + ' ' + ' '.join(r['tags']) + ' ' + r['user'] + ' ' + r['name'])
    r['t'] = r['t'].isoformat()
    r['queries'], r['qseg'] = sorted(r['queries']), sorted(r['qseg'])
    out.append(r)
out.sort(key=lambda r: -r['plays'])
run.save('merged.json', out)
st['kept'] = len(out)
print(dict(st), 'authors', len({r['user'] for r in out}))
print('by language', Counter(r['lang'] for r in out).most_common())
print('by topic', Counter(r['topic'] for r in out).most_common())
print('language from', dict(Counter(r['lang_src'] for r in out)))
