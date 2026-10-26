"""Pull the real content off a prospect's old site: text, internal links, image URLs.
Optionally downloads the images so you can pick usable ones.

Usage:
  python scrape_site.py https://oldsite.com [page2-path page3-path ...] [--download out_dir]
Example:
  python scrape_site.py https://old-site.example.com/ about/ contact/ --download raw
"""
import html, os, re, sys, urllib.error, urllib.request, urllib.parse
from score_sites import blocked, blocked_http, ctx  # ctx: old sites often have expired or mismatched certificates

UA = {'User-Agent': 'Mozilla/5.0'}
# a real TLD (letters): "bootstrap@5.3.2" in a CDN address is not an email
EMAIL = re.compile(r'[\w.+-]+@(?:[\w-]+\.)+[a-z]{2,}\b', re.I)


def wall(url):
    # an anti-bot wall hides the real content: stop here, never try to get around it
    print(f'BLOCKED anti-bot: {url} is behind a captcha/anti-bot page. Do not bypass it: '
          'mark the lead with status "retry" and move on.', file=sys.stderr)
    sys.exit(3)


class Wall(Exception):
    pass


def fetch(url):
    """The page and its address after redirects (relative links and pictures are relative to that one).
    Raises Wall on an anti-bot page."""
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30, context=ctx)
        b, final = r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        if blocked_http(e.code, e.read(60000).decode('utf-8', 'replace')): raise Wall('anti-bot wall')
        raise
    try:
        h = b.decode('utf-8')
    except UnicodeDecodeError:  # many old Italian sites are latin-1: keep the accents
        h = b.decode('cp1252', 'replace')
    if blocked(h): raise Wall('anti-bot wall')
    return h, final


def get(url):
    try:
        return fetch(url)[0]
    except Wall:
        wall(url)


def emails_in(h):
    """Email addresses in a page, also when written as entities (info&#64;dominio.it)."""
    return {e.lower() for e in EMAIL.findall(html.unescape(h)) if not re.search(r'\.(png|jpe?g|gif|webp|svg|js|css)$', e, re.I)}


def text_of(h):
    t = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', '', h)
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', t)))


if __name__ == '__main__':
    args = sys.argv[1:]
    if not args: sys.exit(__doc__)
    out = None
    if '--download' in args:
        i = args.index('--download'); out = args[i + 1]; args = args[:i] + args[i + 2:]
    base, pages = args[0], [''] + args[1:]
    host = urllib.parse.urlparse(base).netloc
    imgs, emails = set(), set()
    sys.stdout.reconfigure(encoding='utf-8')
    for p in pages:
        url = urllib.parse.urljoin(base, p)
        h = get(url)
        print(f'\n===== {url}\n{text_of(h)[:4000]}')
        if p == '':
            # relative links too (old sites use "contatti.htm" without a leading slash)
            links = sorted(set(l for l in re.findall(r'href="([^"#?]+)"', h) if host in l or not re.match(r'^[a-z]+:', l)))
            print('\nLINKS:\n' + '\n'.join(urllib.parse.unquote(l) for l in links[:80]))
        imgs |= set(urllib.parse.urljoin(url, s) for s in re.findall(r'(?:src|data-src|href)="([^"]+\.(?:jpe?g|png|webp))"', h, re.I))
        emails |= emails_in(h)
    print(f'\nIMAGES ({len(imgs)}):\n' + '\n'.join(sorted(imgs)))
    # PEC addresses are for certified mail, never for outreach
    print('\nEMAILS: ' + (', '.join(sorted(e for e in emails if 'pec' not in e)) or 'none found') +
          ('' if not any('pec' in e for e in emails) else '   (PEC skipped: ' + ', '.join(e for e in emails if 'pec' in e) + ')'))
    if out:
        os.makedirs(out, exist_ok=True)
        for i, u in enumerate(sorted(imgs)):
            try:
                data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30, context=ctx).read()
                if len(data) > 15000:
                    open(os.path.join(out, f'{i:02d}-' + os.path.basename(urllib.parse.urlparse(u).path)[-40:]), 'wb').write(data)
            except Exception:
                pass
        print(f'\nDownloaded to {out}/ (files under 15KB skipped)')
