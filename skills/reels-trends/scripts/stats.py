"""Step 8: aggregate everything the report needs into work/stats.json and print a compact summary to write findings from.

usage: python3 stats.py <run_dir> [--quiet]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, re
from collections import Counter, defaultdict
from common import args, med, rnd
import labels

run, opts = args('stats.py <run_dir> [--quiet]')
cfg = run.cfg
ru = cfg['report_language'] == 'ru'
rows = run.load('scored.json')
L = run.load('leaders.json')
byc = {r['code']: r for r in rows}
cls = labels.load(run)
P = run.load('profiles.json', default={})
LR = [byc[r['code']] for r in L if r['code'] in byc]
LV = [r for r in LR if cls.get(r['code'], {}).get('relevant', True) and not cls.get(r['code'], {}).get('flag')]
FX = [r for r in LR if cls.get(r['code'], {}).get('relevant', True) and cls.get(r['code'], {}).get('flag')]
C = lambda r: cls.get(r['code'], {})


def group(items, key, top_examples=4):
    G = defaultdict(list)
    for r in items:
        k = key(r)
        for kk in (k if isinstance(k, list) else [k]):
            if kk:
                G[kk].append(r)
    res = [dict(name=k, n=len(g), authors=len({r['user'] for r in g}), medPlays=med([r['plays'] for r in g]), medX=rnd(med([r['x'] for r in g])),
                nx=sum(1 for r in g if r['x']), hits100k=sum(1 for r in g if r['plays'] >= 100000), hits1m=sum(1 for r in g if r['plays'] >= 1000000),
                examples=[r['code'] for r in sorted(g, key=lambda r: -(r['x'] or 0))[:top_examples]]) for k, g in G.items()]
    return sorted(res, key=lambda d: -d['n'])


def bucket(v, edges):
    for lo, hi, n in edges:
        if v is not None and lo <= v < hi:
            return n


def country(r):
    return (P.get(r['user'].lower()) or {}).get('country') or C(r).get('country')


K = 'тыс.' if ru else 'K'; M = 'млн' if ru else 'M'; S = 'с' if ru else 's'
out = dict(
    total=dict(reels=len(rows), authors=len({r['user'] for r in rows}), plays=sum(r['plays'] for r in rows), with_x=sum(1 for r in rows if r['x']),
               medPlays=med([r['plays'] for r in rows]), medX=rnd(med([r['x'] for r in rows])), langs=len({r['lang'] for r in rows if r['lang'] != 'xx'}),
               leaders=len(L), leaders_clean=len(LV), leaders_flagged=len(FX), labelled=sum(1 for r in L if r['code'] in cls),
               spent=round(run.spent(), 2)),
    by_lang=group(rows, lambda r: r['lang']),
    by_topic=group(rows, lambda r: r['topic']),
    leaders_by_format=group(LV, lambda r: C(r).get('format')),
    leaders_by_topic=group(LV, lambda r: C(r).get('topic')),
    leaders_by_creator=group(LV, lambda r: C(r).get('creator')),
    leaders_by_speech=group(LV, lambda r: C(r).get('speech')),
    leaders_by_lang=group(LV, lambda r: r['lang']),
    leaders_by_country=group(LV, country),
    by_duration=group(rows, lambda r: bucket(r['dur'], [(0, 10, f'0–10 {S}'), (10, 20, f'10–20 {S}'), (20, 30, f'20–30 {S}'), (30, 60, f'30–60 {S}'), (60, 1e9, f'60+ {S}')])),
    by_followers=group(rows, lambda r: bucket(r.get('followers'), [(0, 1000, f'0–1 {K}'), (1000, 10000, f'1–10 {K}'), (10000, 100000, f'10–100 {K}'),
                                                                  (100000, 1000000, f'100 {K}–1 {M}'), (1000000, 1e12, f'1 {M}+')])),
)
orig = lambda r: (not r['music']) or bool(re.search(r'original|оригинал|áudio original|audio original|son original|originalton|suono originale', r['music'], re.I))
out['original_audio_share'] = round(sum(1 for r in rows if orig(r)) / max(1, len(rows)), 3)
A = defaultdict(list)
for r in rows:
    if not orig(r):
        A[r['music']].append(r)
out['audio'] = sorted([dict(name=k, n=len(v), plays=sum(r['plays'] for r in v)) for k, v in A.items() if len(v) >= 2], key=lambda d: (-d['n'], -d['plays']))[:25]
H = defaultdict(list)
for r in rows:
    for t in {t.lower() for t in r['tags']}:
        H[t].append(r)
out['hashtags'] = sorted([dict(tag=k, n=len(v), med=med([r['plays'] for r in v]), medX=rnd(med([r['x'] for r in v]))) for k, v in H.items()], key=lambda d: -d['n'])[:40]
CTA = {
    'save': r"\bsave (this|it|for)|сохрани|збережи|guarda (este|esto|para)|salva (esse|este|para)|kaydet|simpan|保存|저장",
    'send': r"send (this|it) to|tag (someone|a friend|your)|envía(selo)? a|manda (pra|para|a)|envia (pra|para)|отправь|скинь|перешли|надішли|marca a|marque|invia a|wyślij",
    'comment_word': r"(comment|comenta|comente|commenta|kommentier|напиши|пиши|коммент|коментуй|напишіть|yorum|tulis|type|drop|escribe|escreva)\W{0,25}[«\"“'‘]?[A-ZА-ЯЁІЇЄҐÁÉÍÓÚÑÇ0-9]{3,}",
    'book': r"book|reserv|agend|запис|бронир|link in bio|ссылк|посилан|\bdm\b|whatsapp|директ|direct|citas|turnos",
    'question_first_line': None,
}
cta = {}
for k, rx in CTA.items():
    f = (lambda r: '?' in re.split(r'[\n.!]', r['cap'].strip())[0][:150]) if rx is None else (lambda r, rx=re.compile(rx, re.I | re.U): bool(rx.search(r['cap'])))
    a = [r for r in rows if f(r)]; b = [r for r in rows if not f(r)]
    cta[k] = dict(n=len(a), medPlays=med([r['plays'] for r in a]), medX=rnd(med([r['x'] for r in a])), restMedPlays=med([r['plays'] for r in b]), restMedX=rnd(med([r['x'] for r in b])))
out['caption_mechanics'] = cta
out['focus'] = {t: group([r for r in rows if r['topic'] == t], lambda r: r['lang']) for t in cfg.get('focus_topics', [])}
out['flagged'] = dict(n=len(FX), authors=sorted({r['user'] for r in FX}), plays=sum(r['plays'] for r in FX), medPlays=med([r['plays'] for r in FX]),
                      medX=rnd(med([r['x'] for r in FX])), reasons=Counter(C(r).get('flag') for r in FX).most_common(),
                      countries=Counter(country(r) for r in FX).most_common(), codes=[r['code'] for r in sorted(FX, key=lambda r: -r['plays'])])
out['leaders_clean'] = dict(n=len(LV), medPlays=med([r['plays'] for r in LV]), medX=rnd(med([r['x'] for r in LV])),
                            medDur=med([r['dur'] for r in LV]), small_accounts=sum(1 for r in LV if (r.get('followers') or 0) < 10000))
out['top_by_plays'] = [dict(code=r['code'], user=r['user'], plays=r['plays'], x=r['x'], lang=r['lang'], topic=r['topic'], fmt=C(r).get('format'))
                       for r in sorted(rows, key=lambda r: -r['plays'])[:30]]
run.save('stats.json', out)

if '--quiet' not in opts:
    t = out['total']
    print(json.dumps(t, ensure_ascii=False))
    def show(name, items, top=30):
        print('==', name)
        for d in items[:top]:
            print(f"  {d['name']} | n {d['n']} | med plays {d['medPlays']} | med x {d['medX']} | 100k+ {d['hits100k']} | 1M+ {d['hits1m']} | ex {' '.join(d['examples'][:3])}")
    for k in ['by_topic', 'by_lang', 'by_duration', 'by_followers', 'leaders_by_format', 'leaders_by_speech', 'leaders_by_creator', 'leaders_by_country']:
        show(k, out[k])
    for k, g in out['focus'].items():
        show('focus: ' + k, g)
    print('caption mechanics', json.dumps(cta, ensure_ascii=False))
    print('original audio share', out['original_audio_share'])
    print('flagged', json.dumps({k: v for k, v in out['flagged'].items() if k != 'codes'}, ensure_ascii=False))
    print('clean leaders', out['leaders_clean'])
