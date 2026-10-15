"""Step 7: write labelling batches (work/batches/bNN.json) and the rendered labelling instructions (work/label_prompt.md).
Then label every batch with a sub-agent (or yourself): results go to work/cls/bNN.json.

usage: python3 batches.py <run_dir> [--size 20]
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import json, os, re
from common import args
from taxonomy import LANG_NAMES, taxonomy

run, opts = args('batches.py <run_dir> [--size 20]')
cfg = run.cfg
N = int(opts[opts.index('--size') + 1]) if '--size' in opts else 20
rows = {r['code']: r for r in run.load('scored.json')}
L = [rows[r['code']] for r in run.load('leaders.json') if r['code'] in rows]
TR = run.load('transcripts.json', default={})
covers = run.load('covers.json', default={})
os.makedirs(run.p('batches'), exist_ok=True); os.makedirs(run.p('cls'), exist_ok=True)

def c(s, n):
    s = re.sub(r'\s+', ' ', s or '').strip(); return s[:n]

L.sort(key=lambda r: (r['lang'], -(r['x'] or 0)))  # one language per batch where possible: easier to read and translate
names = []
for i in range(0, len(L), N):
    name = f'b{i // N:02d}'
    items = []
    for r in L[i:i + N]:
        fr = run.p('frames', r['code'] + '.jpg')
        cov = None
        if not os.path.exists(fr) and r['code'] in covers:   # no frames: give the agent the cover as a file
            import base64
            cov = run.p('frames', r['code'] + '_cover.jpg')
            os.makedirs(run.p('frames'), exist_ok=True)
            open(cov, 'wb').write(base64.b64decode(covers[r['code']].split(',', 1)[1]))
        items.append(dict(code=r['code'], caption_lang=r['lang'], author='@' + r['user'], author_name=r['name'], author_followers=r.get('followers'),
                          author_bio=c(r.get('bio'), 200), author_category=r.get('cat'), plays=r['plays'], x_vs_author_median=r.get('x'),
                          duration_s=round(r['dur']) if r.get('dur') else None, posted=r['t'][:10], music=r['music'], location=r.get('loc'),
                          caption=c(r['cap'], 650), transcript=c(TR.get(r['code']), 1000),
                          frames=fr if os.path.exists(fr) else None, cover=cov, url=f"https://www.instagram.com/reel/{r['code']}/"))
    json.dump(items, open(run.p('batches', name + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    names.append(name)

formats, creators, speech = taxonomy(cfg)
topics = [t[0] for t in cfg.get('topics', [])] + [cfg.get('fallback_topic') or ('Общее' if cfg['report_language'] == 'ru' else 'General')]
skill = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tpl = open(os.path.join(skill, 'assets', 'label_prompt.md'), encoding='utf-8').read()
prompt = (tpl.replace('{NICHE}', cfg.get('niche') or '').replace('{DATE_FROM}', str(cfg.get('date_from') or ''))
          .replace('{DATE_TO}', str(cfg.get('date_to') or ''))
          .replace('{FORMATS}', '\n'.join(f'  - "{n}" ({h})' for n, h in formats))
          .replace('{TOPICS}', ', '.join(f'"{t}"' for t in topics))
          .replace('{CREATORS}', ', '.join(f'"{x}"' for x in creators))
          .replace('{SPEECH}', ', '.join(f'"{x}"' for x in speech))
          .replace('{LANG}', LANG_NAMES.get(cfg['report_language'], cfg['report_language'])))
open(run.p('label_prompt.md'), 'w', encoding='utf-8').write(prompt)
done = [n for n in names if os.path.exists(run.p('cls', n + '.json'))]
print(f"{len(L)} leaders in {len(names)} batches of up to {N}; frames for {sum(1 for r in L if os.path.exists(run.p('frames', r['code'] + '.jpg')))}")
print(f"instructions: {run.p('label_prompt.md')}")
print('todo:', ' '.join(n for n in names if n not in done) or 'nothing, all batches labelled')
for n in names:
    if n not in done:
        print(f"  {n}: BATCH={run.p('batches', n + '.json')} OUT={run.p('cls', n + '.json')}")
