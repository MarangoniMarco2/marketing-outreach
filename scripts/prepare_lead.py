"""Everything a build needs about one lead, in one call: Google Maps data, the old site's text, links, emails and
pictures, a contact sheet of the pictures and the BEFORE screenshots.

Usage:
  python3 scripts/prepare_lead.py <place_id> <old_url> <slug> [--date YYYY-MM-DD]
Writes runs/<date>/<slug>/:
  lead.json         Google Maps: name, address, phones, rating, reviews (up to 5, verbatim), hours, alive %
  old-site.txt      text of the home page and up to 6 inner pages from its menu, then links and emails
  raw/              the old site's pictures over 15 KB; raw/contact-sheet.jpg shows them all in one image
  before/           home-desktop.jpg and home-mobile.jpg (first screen), the BEFORE of the pitch
Prints a short summary, not the page text. Exit 3: the home page is behind a captcha or anti-bot wall
(mark the lead "retry" and never try to get around it); an inner page behind one is just skipped.
<date> defaults to tonight's date in Italy (find_leads.run_date).
"""
import html, json, os, re, sys, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import places
from find_leads import run_date, site_key, slug
from scrape_site import UA, Wall, ctx, emails_in, fetch, text_of, wall

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# menu pages worth reading, best first
KEYS = [r'chi-?siamo|azienda|storia|about|lo-?studio|la-?nostra', r'serviz|lavoraz|prestaz|trattament|cure|prodott|attivit|cosa-?facciamo',
        r'team|staff|persone|medici|dottor', r'contatt|dove|orari|sede', r'lavori|realizzaz|gallery|galleria|foto|portfolio',
        r'certific|garanzi|qualit|marchi|partner']
# whole words of the path or query: /cartongesso and /carta-da-parati are not a cart
SKIP = re.compile(r'\.(pdf|jpe?g|png|gif|webp|svg|zip|docx?|xlsx?|mp4)$|(?<![a-z0-9])(privacy|cookies?|login|cart|carrello|'
                  r'wp-admin|feed)(?![a-z0-9])', re.I)


def inner_pages(home_url, h, n=10):
    """The site's own pages linked from the home page, the menu pages worth reading first. The query stays and the
    link text counts: old Joomla menus are index.php?option=...&id=..., with the words only in the text."""
    full = lambda href: urllib.parse.urldefrag(urllib.parse.urljoin(home_url, html.unescape(href).strip()))[0]
    words = {}
    for href, t in re.findall(r'<a\s[^>]*?href=["\']([^"\']+)["\'][^>]*>([\s\S]{0,400}?)</a>', h, re.I):
        words[full(href)] = words.get(full(href), '') + ' ' + slug(text_of(t))
    links = []
    for href in re.findall(r'href=["\']([^"\']+)', h, re.I):
        u = full(href); p = urllib.parse.urlparse(u)
        if p.scheme in ('http', 'https') and site_key(u) == site_key(home_url) and not (SKIP.search(p.path) or SKIP.search(p.query)) \
                and (p.path.strip('/') or p.query) and u.rstrip('/') != home_url.rstrip('/') and u not in links:
            links.append(u)
    ranked = []
    for k in KEYS:
        ranked += [u for u in links if re.search(k, urllib.parse.unquote(u) + words.get(u, ''), re.I) and u not in ranked]
    return ranked[:n], links


def pictures(page_url, h):
    found = re.findall(r'(?:src|data-src|data-lazy-src|href)=["\']([^"\']+\.(?:jpe?g|png|webp))', h, re.I)
    found += re.findall(r'url\(["\']?([^"\')]+\.(?:jpe?g|png|webp))', h, re.I)
    for s in re.findall(r'srcset=["\']([^"\']+)', h, re.I):
        found += [x.split()[0] for x in s.split(',') if x.strip()]
    return [urllib.parse.urljoin(page_url, u) for u in found]


def contact_sheet(files, out):
    from PIL import Image, ImageDraw
    cols, w, pad = 6, 230, 8
    thumbs = []
    for f in files:
        try:
            im = Image.open(f); size = im.size; im = im.convert('RGB'); im.thumbnail((w, w))
            thumbs.append((os.path.basename(f)[:2], size, im))
        except Exception:
            pass
    if not thumbs: return 0
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * (w + pad) + pad, rows * (w + 24 + pad) + pad), 'white')
    d = ImageDraw.Draw(sheet)
    for i, (idx, size, im) in enumerate(thumbs):
        x, y = pad + (i % cols) * (w + pad), pad + (i // cols) * (w + 24 + pad)
        sheet.paste(im, (x + (w - im.width) // 2, y + (w - im.height) // 2))
        d.text((x, y + w + 4), f'{idx}  {size[0]}x{size[1]}', fill='black')
    sheet.save(out, quality=80)
    return len(thumbs)


def before_shots(url, out):
    from playwright.sync_api import sync_playwright
    os.makedirs(out, exist_ok=True)
    with sync_playwright() as p:
        kw = {'executable_path': os.environ['CHROME_PATH']} if os.environ.get('CHROME_PATH') else {}
        b = p.chromium.launch(**kw)
        for name, vp, mob in [('desktop', {'width': 1440, 'height': 900}, False), ('mobile', {'width': 390, 'height': 844}, True)]:
            ctx = b.new_context(viewport=vp, is_mobile=mob, ignore_https_errors=True)
            pg = ctx.new_page()
            try:
                pg.goto(url, wait_until='load', timeout=45000); pg.wait_for_timeout(2500)
                pg.screenshot(path=os.path.join(out, f'home-{name}.jpg'), quality=75)
            except Exception as e:
                print(f'  before {name}: {str(e)[:80]}')
            ctx.close()
        b.close()


def main(place_id, url, lead_slug, day):
    d = os.path.join(ROOT, 'runs', day, lead_slug)
    raw = os.path.join(d, 'raw'); os.makedirs(raw, exist_ok=True)
    try:
        home, final = fetch(url)  # links and pictures are relative to the address after redirects
    except Wall:
        wall(url)  # exits 3: only the home page decides that the site is walled
    lead = places.detail(place_id)
    lead['old_url'] = url
    json.dump(lead, open(os.path.join(d, 'lead.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    pages, links = inner_pages(final, home)
    texts, pics, emails = [(final, home)], pictures(final, home), set()
    seen = {text_of(home).strip()}
    for u in pages:
        if len(texts) > 6: break
        try:
            h, fu = fetch(u)  # a wall here (a reCAPTCHA on the contact page) only skips that page
            t = text_of(h).strip()
            if t in seen: continue  # same page under another address ("-off", "?lang=")
            seen.add(t); texts.append((fu, h)); pics += pictures(fu, h)
        except Exception as e:
            print(f'  skipped {u}: {str(e)[:60]}')
    for _, h in texts:
        emails |= emails_in(h)
    alltext = ' '.join(text_of(h) for _, h in texts)
    vat = sorted(set(re.findall(r'(?:P\.?\s?IVA|partita iva|C\.?F\.?)\D{0,12}(\d{11})', alltext, re.I)))
    phones = {}
    for ph in re.findall(r'(?:\+39[\s.]?)?0\d{1,3}[\s./-]?\d{5,8}|3\d{2}[\s./-]?\d{6,7}', alltext):
        digits = re.sub(r'\D', '', ph).removeprefix('39') if ph.startswith('+') else re.sub(r'\D', '', ph)
        if digits not in vat: phones.setdefault(digits, ph.strip())
    phones = sorted(phones.values())
    with open(os.path.join(d, 'old-site.txt'), 'w', encoding='utf-8') as f:
        for u, h in texts:
            f.write(f'===== {u}\n{text_of(h).strip()[:5000]}\n\n')
        f.write('LINKS:\n' + '\n'.join(urllib.parse.unquote(l) for l in links[:80]) + '\n\n')
        f.write('EMAILS: ' + (', '.join(sorted(e for e in emails if 'pec' not in e)) or 'none found') + '\n')
        f.write('PEC (never for outreach): ' + (', '.join(sorted(e for e in emails if 'pec' in e)) or 'none') + '\n')
        f.write('PHONES ON THE SITE: ' + (', '.join(phones) or 'none') + '\n')
        f.write('VAT / CF: ' + (', '.join(vat) or 'not found') + '\n')

    kept = []
    for i, u in enumerate(dict.fromkeys(pics)):
        if len(kept) >= 40: break
        try:
            data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=20, context=ctx).read()
        except Exception:
            continue
        if len(data) > 15000:
            name = os.path.join(raw, f'{len(kept):02d}-' + os.path.basename(urllib.parse.urlparse(u).path)[-40:])
            open(name, 'wb').write(data); kept.append(name)
    n = contact_sheet(kept, os.path.join(raw, 'contact-sheet.jpg'))
    before_shots(url, os.path.join(d, 'before'))

    rel = os.path.relpath(d, ROOT)
    print(f"{lead['name']} | {lead.get('rating')} ({lead.get('reviews')} rec.), newest review {lead.get('newest_review')}, alive {lead.get('alive_pct')}%")
    print(f'pages read: {len(texts)} ({", ".join(urllib.parse.urlparse(u).path or "/" for u, _ in texts)})')
    print(f'pictures kept: {len(kept)} (contact sheet: {n})   emails: {", ".join(sorted(e for e in emails if "pec" not in e)) or "none"}')
    print(f'next: read {rel}/lead.json and {rel}/old-site.txt, look at {rel}/raw/contact-sheet.jpg and {rel}/before/home-mobile.jpg')


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 3: sys.exit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    main(a[0], a[1], a[2], a[a.index('--date') + 1] if '--date' in a else run_date())
