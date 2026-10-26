"""Pull the real content off a prospect's old site: text, internal links, image URLs.
Optionally downloads the images so you can pick usable ones.

Usage:
  python scrape_site.py https://oldsite.com [page2-path page3-path ...] [--download out_dir]
Example:
  python scrape_site.py https://old-site.example.com/ about/ contact/ --download raw
"""
import html, os, re, sys, urllib.error, urllib.request, urllib.parse
from score_sites import blocked

UA = {'User-Agent': 'Mozilla/5.0'}


def wall(url):
    # an anti-bot wall hides the real content: stop here, never try to get around it
    print(f'BLOCKED anti-bot: {url} is behind a captcha/anti-bot page. Do not bypass it: '
          'mark the lead with status "retry" and move on.', file=sys.stderr)
    sys.exit(3)


def get(url):
    try:
        b = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30).read()
    except urllib.error.HTTPError as e:
        if e.code in (403, 429, 503) or blocked(e.read(60000).decode('utf-8', 'replace')): wall(url)
        raise
    try:
        h = b.decode('utf-8')
    except UnicodeDecodeError:  # many old Italian sites are latin-1: keep the accents
        h = b.decode('cp1252', 'replace')
    if blocked(h): wall(url)
    return h


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
        emails |= {e.lower() for e in re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+\w', html.unescape(h))
                   if not re.search(r'\.(png|jpe?g|gif|webp|svg)$', e, re.I)}
    print(f'\nIMAGES ({len(imgs)}):\n' + '\n'.join(sorted(imgs)))
    # PEC addresses are for certified mail, never for outreach
    print('\nEMAILS: ' + (', '.join(sorted(e for e in emails if 'pec' not in e)) or 'none found') +
          ('' if not any('pec' in e for e in emails) else '   (PEC skipped: ' + ', '.join(e for e in emails if 'pec' in e) + ')'))
    if out:
        os.makedirs(out, exist_ok=True)
        for i, u in enumerate(sorted(imgs)):
            try:
                data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read()
                if len(data) > 15000:
                    open(os.path.join(out, f'{i:02d}-' + os.path.basename(urllib.parse.urlparse(u).path)[-40:]), 'wb').write(data)
            except Exception:
                pass
        print(f'\nDownloaded to {out}/ (files under 15KB skipped)')
