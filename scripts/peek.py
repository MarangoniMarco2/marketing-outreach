"""One image with the first screen of several websites, desktop and phone side by side, to compare candidates at a
glance (one image to look at instead of a dozen).

Usage:
  python3 scripts/peek.py <out.jpg> <url> [<url> ...]      (up to 8 sites)
"""
import io, os, sys
from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright


def main(out, urls):
    rows = []
    with sync_playwright() as p:
        kw = {'executable_path': os.environ['CHROME_PATH']} if os.environ.get('CHROME_PATH') else {}
        b = p.chromium.launch(**kw)
        for url in urls[:8]:
            shots = []
            for vp, mob in [({'width': 1280, 'height': 800}, False), ({'width': 390, 'height': 844}, True)]:
                ctx = b.new_context(viewport=vp, is_mobile=mob, ignore_https_errors=True)
                pg = ctx.new_page()
                try:
                    pg.goto(url, wait_until='load', timeout=30000); pg.wait_for_timeout(1500)
                    shots.append(Image.open(io.BytesIO(pg.screenshot(type='jpeg', quality=70))).convert('RGB'))
                except Exception:
                    shots.append(Image.new('RGB', (vp['width'], vp['height']), (230, 230, 230)))
                ctx.close()
            d, m = shots
            d.thumbnail((560, 350)); m.thumbnail((162, 350))
            rows.append((url, d, m))
        b.close()
    h = 24 + 350 + 12
    sheet = Image.new('RGB', (560 + 162 + 36, h * len(rows) + 12), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (url, d, m) in enumerate(rows):
        y = 12 + i * h
        draw.text((12, y), f'{i + 1}. {url[:90]}', fill='black')
        sheet.paste(d, (12, y + 20)); sheet.paste(m, (12 + 560 + 12, y + 20))
    sheet.save(out, quality=80)
    print(f'saved {out} ({len(rows)} sites)')


if __name__ == '__main__':
    if len(sys.argv) < 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2:])
