"""Step 9: build the report from work/stats.json, labels and <run_dir>/content.json (findings, notes and ideas written for this run).

usage: python3 build.py <run_dir>
Writes report/index.html (open in a browser), report/artifact.html (body-only page for publishing as a Claude artifact)
and report/reels.json (every reel with scores and labels).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datetime as dt, json, os, re, statistics
from common import args
import labels

run, _ = args('build.py <run_dir>')
cfg = run.cfg
ru = cfg['report_language'] == 'ru'
HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
cpath = os.path.join(run.dir, 'content.json')
if not os.path.exists(cpath):
    raise SystemExit('content.json not found in the run folder. Write it from stats (see references/content.md).')
K = json.load(open(cpath, encoding='utf-8'))
S = run.load('stats.json'); rows = run.load('scored.json'); L = run.load('leaders.json')
P = run.load('profiles.json', default={}); TH = run.load('covers.json', default={}); TR = run.load('transcripts.json', default={})
cls = labels.load(run)
CTRY = json.load(open(os.path.join(HERE, 'countries.json'), encoding='utf-8'))
byc = {r['code']: r for r in rows}

UI = {
    'ru': dict(locale='ru-RU', dec=',', k='тыс', m='млн', na='н/д', period='период', reels='рилсов', authors='авторов', langs='языков',
               plays='просмотров суммарно', main='Главное', formats='Форматы', topics='Темы', geo='География', top='Топ рилсов',
               hooks='Первые секунды лидеров', audio='Звук', tags='Хэштеги', method='Как считали', th_format='Формат', th_n='Рилсов',
               th_med='Медиана просмотров', th_x='Медиана ×', th_bar='Сила формата', th_topic='Тема', th_works='Что работает',
               th_lang='Язык подписи', th_authors='Авторов', th_leaders='Лидеров', th_lang_note='Что там залетает',
               countries='Страны авторов-лидеров', howto='Как читать', r='рилс.', median='медиана', sort='сортировка',
               by_x='× к медиане автора', by_plays='просмотры', lang='язык', all_langs='все языки', format='формат',
               all_formats='все форматы', topic='тема', all_topics='все темы', followers='подп.', followers_na='подп. н/д', sec='с',
               empty='Под этот фильтр рилсов нет.', hook='Хук', example='пример', views='просмотров',
               no_audio='Повторяющихся треков не нашлось', flagged='скрытые ролики'),
    'en': dict(locale='en-US', dec='.', k='K', m='M', na='n/a', period='period', reels='reels', authors='authors', langs='languages',
               plays='total views', main='Key findings', formats='Formats', topics='Topics', geo='Geography', top='Top reels',
               hooks='First seconds of the leaders', audio='Sound', tags='Hashtags', method='Method', th_format='Format', th_n='Reels',
               th_med='Median views', th_x='Median ×', th_bar='Format strength', th_topic='Topic', th_works='What works',
               th_lang='Caption language', th_authors='Authors', th_leaders='Leaders', th_lang_note='What flies there',
               countries='Countries of leader accounts', howto='How to read', r='reels', median='median', sort='sort',
               by_x='× vs author median', by_plays='views', lang='language', all_langs='all languages', format='format',
               all_formats='all formats', topic='topic', all_topics='all topics', followers='followers', followers_na='followers n/a', sec='s',
               empty='No reels for this filter.', hook='Hook', example='example', views='views',
               no_audio='No repeated tracks', flagged='hidden reels'),
}
LN = {
    'ru': {'EN': 'английский', 'ES': 'испанский', 'PT': 'португальский', 'RU': 'русский', 'UA': 'украинский', 'TR': 'турецкий', 'DE': 'немецкий',
           'FR': 'французский', 'IT': 'итальянский', 'PL': 'польский', 'NL': 'нидерландский', 'ID': 'индонезийский и малайский', 'TH': 'тайский',
           'VI': 'вьетнамский', 'JA': 'японский', 'KO': 'корейский', 'ZH': 'китайский', 'AR': 'арабский', 'FA': 'персидский', 'HI': 'хинди',
           'TL': 'тагальский', 'RO': 'румынский', 'CS': 'чешский', 'EL': 'греческий', 'HE': 'иврит', 'KK': 'казахский', 'KA': 'грузинский',
           'HY': 'армянский', 'AZ': 'азербайджанский', 'UR': 'урду', 'BN': 'бенгальский', 'HU': 'венгерский', 'SV': 'шведский', 'BG': 'болгарский',
           'SR': 'сербский', 'HR': 'хорватский', 'LT': 'литовский', 'LV': 'латышский', 'ET': 'эстонский', 'FI': 'финский', 'DA': 'датский',
           'NO': 'норвежский', 'CA': 'каталанский', 'xx': 'не определён'},
    'en': {'EN': 'English', 'ES': 'Spanish', 'PT': 'Portuguese', 'RU': 'Russian', 'UA': 'Ukrainian', 'TR': 'Turkish', 'DE': 'German', 'FR': 'French',
           'IT': 'Italian', 'PL': 'Polish', 'NL': 'Dutch', 'ID': 'Indonesian and Malay', 'TH': 'Thai', 'VI': 'Vietnamese', 'JA': 'Japanese',
           'KO': 'Korean', 'ZH': 'Chinese', 'AR': 'Arabic', 'FA': 'Persian', 'HI': 'Hindi', 'TL': 'Tagalog', 'RO': 'Romanian', 'CS': 'Czech',
           'EL': 'Greek', 'HE': 'Hebrew', 'KK': 'Kazakh', 'KA': 'Georgian', 'HY': 'Armenian', 'AZ': 'Azerbaijani', 'UR': 'Urdu', 'BN': 'Bengali',
           'HU': 'Hungarian', 'SV': 'Swedish', 'BG': 'Bulgarian', 'SR': 'Serbian', 'HR': 'Croatian', 'LT': 'Lithuanian', 'LV': 'Latvian',
           'ET': 'Estonian', 'FI': 'Finnish', 'DA': 'Danish', 'NO': 'Norwegian', 'CA': 'Catalan', 'xx': 'undetected'},
}
lang = 'ru' if ru else 'en'


def country(r):
    return (P.get(r['user'].lower()) or {}).get('country') or cls.get(r['code'], {}).get('country')


def cname(c):
    return (CTRY[c][1] if ru else c) if c in CTRY else c


def clip(s, n):
    s = re.sub(r'\s+', ' ', s or '').strip()
    return s if len(s) <= n else s[:n - 1].rstrip() + '…'


LR = [byc[r['code']] for r in L if r['code'] in byc]
leaders = [r for r in LR if cls.get(r['code'], {}).get('relevant', True)]
clean = [r for r in leaders if not cls[r['code']].get('flag')] if cls else leaders
lead_by_lang = {}
for r in clean:
    lead_by_lang[r['lang']] = lead_by_lang.get(r['lang'], 0) + 1
reels = []
for r in leaders:
    c = cls.get(r['code'], {}); cc = country(r); flag = c.get('flag')
    hook = c.get('hook_tr') or ''
    if not re.sub(r'[#@][\w.]+|[^\w]', '', hook):
        hook = ''  # hashtags or emoji only: not a hook
    what = c.get('what') or clip(r['cap'], 110)
    reels.append(dict(code=r['code'], url=r['url'], user=r['user'], followers=r.get('followers'), plays=r['plays'], x=r['x'], dur=r['dur'],
                      lang=r['lang'], cc=CTRY[cc][0] if cc in CTRY else None, date=dt.datetime.fromisoformat(r['t']).strftime('%d.%m'),
                      format=c.get('format'), topic=c.get('topic') or r['topic'], hook=clip(hook, 120) if hook else clip(what, 130),
                      orig=clip(what, 130) if hook else None, thumb=None if flag == 'sexualised' else TH.get(r['code']),
                      f=(K.get('meta', {}).get('flaggedLabel') or flag) if flag else None))
fdesc = K.get('formats', {})
formats = [dict(f, desc=fdesc.get(f['name'], '')) for f in S['leaders_by_format']]
formats = [f for f in formats if f['name'] not in ('Другое', 'Other')]
formats.sort(key=lambda f: -(f['medX'] or 0))
topics = [dict(t, note=K.get('topics', {}).get(t['name'], '')) for t in S['by_topic']]
topics.sort(key=lambda t: -(t['medX'] or 0))
lmin = K.get('langMin', 30)
langs = [dict(code=l['name'], n=l['n'], authors=l['authors'], medPlays=l['medPlays'], medX=l['medX'], leaders=lead_by_lang.get(l['name'], 0),
              note=K.get('langs', {}).get(l['name'], '')) for l in S['by_lang'] if l['n'] >= lmin and l['name'] != 'xx']
cn = {}
for r in clean:
    c = country(r)
    if c:
        cn.setdefault(c, []).append(r)
countries = sorted([dict(name=cname(k), n=len(v), medX=round(statistics.median([r['x'] for r in v if r['x']]), 1) if any(r['x'] for r in v) else None)
                    for k, v in cn.items() if len(v) >= 2], key=lambda d: (-d['n'], -(d['medX'] or 0)))
hooks = []
for code in K.get('hooks', []):
    r = byc.get(code); c = cls.get(code, {})
    if r:
        hooks.append(dict(code=code, user=r['user'], plays=r['plays'], x=r['x'], lang=r['lang'], tr=c.get('hook_tr'), orig=c.get('hook_orig')))
meta = dict(K.get('meta', {}))
meta.update(reels=S['total']['reels'], authors=S['total']['authors'], langs=S['total']['langs'], totalPlays=S['total']['plays'])
meta.setdefault('spent', f"{run.spent():.2f}")
meta.setdefault('method', [])
D = dict(meta=meta, findings=K.get('findings', []), formats=formats, topics=topics, langs=langs, countries=countries, reels=reels,
         ideas=K.get('ideas', []), hooks=hooks, audio=S['audio'][:12], hashtags=S['hashtags'][:16], ui=UI[lang], langNames=LN[lang])
data = json.dumps(D, ensure_ascii=False).replace('</', '<\\/')
title = meta.get('title') or (f"Reels: {cfg.get('niche') or 'research'}")
page = open(os.path.join(SKILL, 'assets', 'report.html'), encoding='utf-8').read().replace('__DATA__', data).replace('__TITLE__', title.replace('<', ''))
open(os.path.join(run.report, 'artifact.html'), 'w', encoding='utf-8').write(page)
head, body = page.split('<div class="wrap" id="app"></div>', 1)
open(os.path.join(run.report, 'index.html'), 'w', encoding='utf-8').write(
    f'<!doctype html>\n<html lang="{lang}">\n<head>\n{head}</head>\n<body>\n<div class="wrap" id="app"></div>{body}</body>\n</html>\n')
full = []
for r in rows:
    c = cls.get(r['code'], {})
    item = {k: r.get(k) for k in ('code', 'url', 't', 'plays', 'likes', 'comments', 'shares', 'user', 'name', 'cap', 'tags', 'music', 'dur', 'loc',
                                  'queries', 'lang', 'topic', 'followers', 'med', 'x', 'bio', 'cat', 'country')}
    if c:
        item.update(leader=True, label=c, transcript=TR.get(r['code']))
    full.append(item)
json.dump({'reels': full}, open(os.path.join(run.report, 'reels.json'), 'w', encoding='utf-8'), ensure_ascii=False)
mb = os.path.getsize(os.path.join(run.report, 'index.html')) / 1e6
print(f"report: {os.path.join(run.report, 'index.html')} ({mb:.1f} MB), grid {len(reels)} reels ({sum(1 for r in reels if r['f'])} hidden), "
      f"formats {len(formats)}, topics {len(topics)}, languages {len(langs)}, countries {len(countries)}")
missing = [k for k in ('h1', 'lede', 'period', 'eyebrow') if not meta.get(k)]
if missing:
    print('WARNING: content.json meta is missing', missing)
