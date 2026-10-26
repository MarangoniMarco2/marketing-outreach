"""Animated GIF of the new home page scrolling, to attach to the outreach email.

Usage:
  python make_gif.py <url> <out.gif> [--mobile] [--screens 4] [--width 640] [--fps 10] [--colors 96]
Records the page with Playwright (holds on the first screen, then scrolls about N screens),
converts it with ffmpeg (two-pass palette) and prints the file size. Set CHROME_PATH to use an existing Chromium.
Keep each GIF under about 4 MB so the email stays light.
"""
import os, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright


def record(url, mobile, screens, tmp):
    vp = {'width': 390, 'height': 844} if mobile else {'width': 1280, 'height': 800}
    with sync_playwright() as p:
        kw = {'executable_path': os.environ['CHROME_PATH']} if os.environ.get('CHROME_PATH') else {}
        b = p.chromium.launch(**kw)
        ctx = b.new_context(viewport=vp, is_mobile=mobile, record_video_dir=tmp, record_video_size=vp)
        t0 = time.monotonic()
        pg = ctx.new_page(); pg.goto(url, wait_until='networkidle'); pg.wait_for_timeout(1200)
        start = time.monotonic() - t0  # cut the blank loading frames
        pg.wait_for_timeout(1500)  # hold on the hero
        dist = min(pg.evaluate('document.documentElement.scrollHeight - innerHeight'), int(vp['height'] * screens))
        # scroll inside the page on animation frames: stepping from Python is slow and uneven.
        # behavior 'instant' because pages with scroll-behavior:smooth would restart a smooth scroll every frame
        pg.evaluate('''([d, ms]) => new Promise(done => {
            const t0 = performance.now();
            const step = t => { const p = Math.min(1, (t - t0) / ms);
                                scrollTo({ top: d * p * p * (3 - 2 * p), behavior: 'instant' });
                                p < 1 ? requestAnimationFrame(step) : done(); };
            requestAnimationFrame(step); })''', [dist, int(1000 * (1.1 * screens + 1))])
        pg.wait_for_timeout(1000)
        length = time.monotonic() - t0 - start
        path = pg.video.path(); ctx.close(); b.close()
    return path, start, length


def to_gif(src, out, start, length, width, fps, colors):
    vf = (f'fps={fps},scale={width}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors={colors}:stats_mode=diff[p];'
          '[b][p]paletteuse=dither=none:diff_mode=rectangle')  # no dither: far smaller files when scrolling
    subprocess.run([os.environ.get('FFMPEG', 'ffmpeg'), '-v', 'error', '-y', '-ss', f'{start:.2f}', '-t', f'{length:.2f}',
                    '-i', src, '-vf', vf, '-loop', '0', out], check=True)


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2: sys.exit(__doc__)
    url, out = a[:2]
    mobile = '--mobile' in a
    screens = float(a[a.index('--screens') + 1]) if '--screens' in a else (6 if mobile else 4)
    width = int(a[a.index('--width') + 1]) if '--width' in a else (300 if mobile else 640)
    fps = int(a[a.index('--fps') + 1]) if '--fps' in a else 10
    colors = int(a[a.index('--colors') + 1]) if '--colors' in a else 96
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src, start, length = record(url, mobile, screens, tmp)
        to_gif(src, out, start, length, width, fps, colors)
    mb = os.path.getsize(out) / 1e6
    print(f'saved {out} ({mb:.1f} MB, {length:.1f} s)' + ('   <-- over 4 MB: lower --width, --fps or --screens' if mb > 4 else ''))
