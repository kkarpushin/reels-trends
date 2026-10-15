"""Step 6c: for every leader download the video once, cut 4 frames (0.6 s, 30%, 55%, 85%) into one strip for visual labelling
(work/frames/<code>.jpg) and make a small cover (work/covers.json, base64) for the report grid. Videos are deleted right away.

usage: python3 media.py <run_dir>
Needs Pillow; frames also need ffmpeg/ffprobe on PATH (without them only covers are made and labelling uses covers).
Instagram CDN links expire within days, so run this soon after search.py.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import base64, concurrent.futures as cf, io, json, os, shutil, subprocess, urllib.request
from common import args

try:
    from PIL import Image
except ImportError:
    raise SystemExit('Pillow is missing: pip install pillow')

run, _ = args('media.py <run_dir>')
rows = {r['code']: r for r in run.load('scored.json')}
L = [rows[r['code']] for r in run.load('leaders.json') if r['code'] in rows]
FD, VD = run.p('frames'), run.p('vid')
os.makedirs(FD, exist_ok=True); os.makedirs(VD, exist_ok=True)
HAVE_FF = bool(shutil.which('ffmpeg') and shutil.which('ffprobe')) and run.cfg['frames']
if not HAVE_FF:
    print('NOTE: ffmpeg/ffprobe not found (or frames off): only covers will be made')
UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'}

def fetch(url, timeout=60):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout).read()

def cover(r):
    try:
        im = Image.open(io.BytesIO(fetch(r['thumb'], 30))).convert('RGB'); im.thumbnail((240, 426))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=68, optimize=True)
        return r['code'], 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()
    except Exception:
        return r['code'], None

def strip(r):
    out = os.path.join(FD, r['code'] + '.jpg')
    if os.path.exists(out) or not HAVE_FF or not r.get('video'):
        return os.path.exists(out)
    vp = os.path.join(VD, r['code'] + '.mp4')
    try:
        open(vp, 'wb').write(fetch(r['video'], 120))
        dur = r.get('dur') or float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', vp],
                                                   capture_output=True, text=True).stdout.strip() or 10)
        ims = []
        for t in [0.6, dur * 0.30, dur * 0.55, dur * 0.85]:
            p = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{min(t, max(dur - 0.2, 0)):.2f}', '-i', vp, '-frames:v', '1', '-vf', 'scale=270:-2',
                                '-f', 'image2pipe', '-vcodec', 'mjpeg', '-'], capture_output=True)
            if p.stdout:
                ims.append(Image.open(io.BytesIO(p.stdout)).convert('RGB'))
        if not ims:
            return False
        h = max(i.height for i in ims); w = sum(i.width for i in ims) + 6 * (len(ims) - 1)
        s = Image.new('RGB', (w, h), (255, 255, 255)); x = 0
        for i in ims:
            s.paste(i, (x, 0)); x += i.width + 6
        s.save(out, 'JPEG', quality=72)
        return True
    except Exception as e:
        print('frames failed', r['code'], str(e)[:80], flush=True)
        return False
    finally:
        if os.path.exists(vp):
            os.remove(vp)

covers = run.load('covers.json', default={})
with cf.ThreadPoolExecutor(12) as ex:
    for code, c in ex.map(cover, [r for r in L if r['code'] not in covers and r.get('thumb')]):
        if c:
            covers[code] = c
    ok = list(ex.map(strip, L))
run.save('covers.json', covers)
print(f'covers {sum(1 for r in L if r["code"] in covers)} of {len(L)}, frame strips {sum(ok)} of {len(L)}')
