"""Labels = agent output (work/cls/*.json) + your review (work/overrides.json). Used by stats.py and build.py.

overrides.json: {"patch": {"<code>": {"relevant": false, "format": "..."}}, "flagged": {"<code>": "sexualised"}, "unflag": ["<code>"]}
Flagged reels stay in the data but are left out of the format tables and ideas and are hidden in the report grid by default.

usage (check only): python3 labels.py <run_dir>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glob, json, os


def load(run):
    cls = {}
    for f in sorted(glob.glob(run.p('cls', '*.json'))):
        try:
            for c in json.load(open(f, encoding='utf-8')):
                cls[c['code']] = c
        except Exception as e:
            print(f'WARNING: cannot read {f}: {e}')
    ov = run.load('overrides.json', default={})
    for code, patch in ov.get('patch', {}).items():
        if code in cls:
            cls[code].update(patch)
    for code, reason in ov.get('flagged', {}).items():
        if code in cls:
            cls[code]['flag'] = reason
    for code in ov.get('unflag', []):
        if code in cls:
            cls[code]['flag'] = None
    for c in cls.values():
        c.setdefault('relevant', True)
        c.setdefault('flag', None)
    return cls


if __name__ == '__main__':
    from collections import Counter
    from common import args
    run, _ = args('labels.py <run_dir>')
    cls = load(run)
    L = run.load('leaders.json')
    missing = [r['code'] for r in L if r['code'] not in cls]
    print(f'labelled {len(cls)} of {len(L)} leaders; missing {len(missing)}: {" ".join(missing[:20])}')
    print('relevant', dict(Counter(c['relevant'] for c in cls.values())), '| flags', dict(Counter(c['flag'] for c in cls.values() if c['flag'])))
    print('formats', Counter(c.get('format') for c in cls.values() if c['relevant'] and not c['flag']).most_common())
