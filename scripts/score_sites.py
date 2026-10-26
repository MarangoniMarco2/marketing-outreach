"""Score business websites for how outdated they look. Higher score = better rebuild prospect.

Usage:
  python score_sites.py https://site1.com https://site2.com ...
  python score_sites.py -f urls.txt        (one URL per line)
"""
import re, ssl, sys, urllib.error, urllib.request, concurrent.futures as cf

ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
BUILDERS = r'lnwshop|readyplanet|wix|weebly|tarad|jimdo'
# anti-bot walls (SiteGround, Cloudflare, DataDome): the content is not reachable, never try to bypass them.
# Not "challenge-platform": Cloudflare adds /cdn-cgi/challenge-platform/scripts/jsd/main.js to normal pages too
ANTIBOT = r'sgcaptcha|cf_chl_opt|cf-chl-|<title>\s*Just a moment|Attention Required! \| Cloudflare|captcha-delivery'
# a reCAPTCHA/hCaptcha is often just on the contact form: it is a wall only when the page has almost no text
CAPTCHA = r'g-recaptcha|hcaptcha'


def blocked_http(code, body):
    """An HTTP error page that is a bot wall: only when the page itself is a captcha or challenge.
    A bare 403 or 429 is often a firewall or rate limit that lets the site through the next time (seen on
    studiomedicobassanese.com), and a 503 is a site that is down: those are errors, not walls."""
    return blocked(body)


def blocked(h):
    if len(h) >= 60000: return False
    if re.search(ANTIBOT, h, re.I): return True
    text = re.sub(r'\s+', ' ', re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>', ' ', h))
    return bool(re.search(CAPTCHA, h, re.I)) and len(text) < 400


def score(url):
    try:
        r = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20, context=ctx)
        h = r.read(600000).decode('utf-8', 'replace'); final = r.geturl()
    except urllib.error.HTTPError as e:
        body = e.read(60000).decode('utf-8', 'replace')
        return (-1, url, 'BLOCKED anti-bot' if blocked_http(e.code, body) else f'ERROR HTTP {e.code}')
    except Exception as e:
        return (-1, url, 'ERROR ' + str(e)[:60])
    if blocked(h): return (-1, final, 'BLOCKED anti-bot')
    s, f = 0, []
    if not re.search(r'name=["\']?viewport', h, re.I): s += 3; f.append('no-viewport')
    t = len(re.findall(r'<table', h, re.I))
    if t > 3: s += 2; f.append(f'tables:{t}')
    # the last year of a range: "© 2005-2025" is a site updated in 2025
    yrs = [max(map(int, re.findall(r'(?:19|20)\d\d', y))) for y in re.findall(
        r'(?:©|&copy;|copyright)\D{0,15}((?:19|20)\d\d(?:\s*(?:-|–|—|&[nm]dash;|&#821[12];)\s*(?:19|20)\d\d)?)', h, re.I)]
    if yrs and max(yrs) < 2022: s += 2; f.append(f'©{max(yrs)}')
    jq = re.search(r'jquery[-.]?(\d)\.(\d+)', h, re.I)
    if jq and int(jq.group(1)) < 2: s += 1; f.append('old-jquery')
    if final.startswith('http:'): s += 2; f.append('no-https')
    if re.search(r'<font|<marquee|<center>|\.swf|bgcolor=', h, re.I): s += 2; f.append('font/marquee')
    if yrs and max(yrs) < 2018: s += 1  # very old on top
    g = re.search(r'name="generator" content="([^"]+)', h, re.I)
    if g: f.append('gen:' + g.group(1)[:25])
    # a CMS that has not been updated for years usually comes with a theme of the same age
    old_cms = re.search(r'WordPress ([1-4])\.|Joomla! (1\.\d|2\.5)|Drupal [4-7]\b', g.group(1) if g else '', re.I)
    if old_cms: s += 2; f.append('old-cms')
    b = re.search(BUILDERS, h, re.I)
    if b: f.append('builder:' + b.group(0))
    f.append('FORM' if re.search(r'<form[^>]*>[\s\S]{0,4000}?<textarea', h, re.I) else 'noform')
    return (s, final, ' '.join(f))


if __name__ == '__main__':
    args = sys.argv[1:]
    urls = open(args[1], encoding='utf-8').read().split() if args[:1] == ['-f'] else args
    if not urls: sys.exit(__doc__)
    with cf.ThreadPoolExecutor(10) as ex:
        for s, u, f in sorted(ex.map(score, urls), reverse=True):
            print(s, u, f)
