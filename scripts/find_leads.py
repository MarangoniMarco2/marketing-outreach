"""Nightly prospecting: rotate niche x town, find old websites with a web search, keep the businesses that Google
Maps shows alive.

Usage:
  python find_leads.py next [--pairs 4]
      Takes the next niche/town pairs from leads/targets.json (cursor in leads/state.json) and prints them with
      web search ideas. Search the web yourself, then pass the businesses' own websites to "check".
  python find_leads.py check --query "autofficina Thiene" URL [URL ...] [--out runs/<date>/candidates.json]
      For websites found with the web search: drops directories, social pages and businesses already in
      leads/done.jsonl, scores each site, finds the business on Google Maps by its website, keeps it if it is
      OPERATIONAL with enough reviews and not a chain, fetches reviews and hours (alive %) and adds it to the
      night's candidates file. Captcha-walled sites and sites missing from Maps are marked "retry".
  python find_leads.py show [--out runs/<date>/candidates.json]
      Tonight's candidates in a few lines each: site score and flags, alive %, rating, and the Google reviews
      (stars, month, first 160 characters) to spot red flags. Read this instead of candidates.json.
  python find_leads.py maps --query "autofficina Thiene" [--query "..."] [--out runs/<date>/candidates.json]
      The Google Maps half of the double search, for the pairs `next` printed (the cursor does not move):
      Maps lists businesses whose old sites never reach the first page of a web search.
  python find_leads.py pick [--pairs 3] [--out runs/<date>/candidates.json]
      Fallback when web search is not available: searches Google Maps directly for the next pairs,
      drops businesses already in leads/done.jsonl and chains/franchises, scores their websites and checks they
      are alive. Adds to the night's candidates file (a second pick does not overwrite the first). Sites behind a
      captcha/anti-bot wall are marked "retry" automatically: never try to get around the wall.
  python find_leads.py mark <place_id> --name "..." --website URL --status drafted|skipped|excluded|retry [--note "..."]
      Records a business in leads/done.jsonl so it is not picked again ("retry": not for RETRY_DAYS days).
Needs GOOGLE_MAPS_API_KEY (see places.py).
"""
import hashlib, html, itertools, json, os, re, sys, unicodedata, urllib.parse, urllib.request
import concurrent.futures as cf
from collections import Counter
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import places
from score_sites import ctx, score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS = os.path.join(ROOT, 'leads')
# not a business's own site, by the registrable name of the host (paginegialle in www.paginegialle.it), never as text
# anywhere in the address: vicenzaclimbing.it is not bing
NOT_A_SITE = {'facebook', 'instagram', 'paginegialle', 'paginebianche', 'virgilio', 'google', 'tripadvisor', 'miodottore',
              'treatwell',
              # directories, marketplaces, news and public sites that show up in a web search
              'prontopro', 'infobel', 'cylex', 'cylex-italia', 'misterimprese', 'guidamonaci', 'kompass', 'europages', 'yelp', 'youdriver', 'prontoimprese', 'aposto', 'saugo', 'vittoriaassicurazioni',
              'habitissimo', 'instapro', 'starofservice', 'tuttocitta', 'hotfrog', 'trovaaziende', 'reteimprese',
              'registroimprese', 'ufficiocamerale', 'informazione-aziende', 'companyreports',
              'linkedin', 'youtube', 'youtu', 'tiktok', 'subito', 'idealista', 'immobiliare', 'wikipedia',
              'amazon', 'groupon', 'doctolib', 'dentisti-italia', 'top-doctors', 'topdoctors', 'quandoo', 'thefork',
              'ilgiornaledivicenza', 'vicenzatoday', 'mappe', 'yellowpages', 'trovalost', 'infoisinfo', 'micuro', 'idraulico24', 'termoidraulici', 'sosmastro',
              'dovemivesto', 'oraridiapertura', 'orari-apertura', 'bing', 'apple'}
NOT_A_SITE_HOSTS = ('gov.it', 'wa.me', 'linktr.ee', 'business.site', 'g.page', 'goo.gl')  # these and their subdomains; also comune.*
# free hosts where each site is a folder of a shared host name: digilander.libero.it/rossi and
# digilander.libero.it/bianchi are two businesses (on altervista, jimdo, webnode, blogspot... the subdomain is the site)
SHARED_HOSTS = r'(^|\.)(digilander\.libero\.it|digilander\.iol\.it|web\.tiscali\.it|web\.tiscalinet\.it|xoomer\.virgilio\.it|' \
               r'xoomer\.alice\.it|space\.virgilio\.it|members\.xoom\.it|utenti\.lycos\.it|sites\.google\.com|wixsite\.com)$'
RETRY_DAYS = 30


def run_date():
    """Tonight's date, in Italy: a night starts at 01:17 Rome time, which is 23:17 UTC in summer, so the UTC date
    would change in the middle of the night and the steps would look in two different runs/<date>/ folders."""
    try:
        return datetime.now(ZoneInfo('Europe/Rome')).date().isoformat()
    except ZoneInfoNotFoundError:  # no time zone data (Windows without tzdata): the computer's own date
        return date.today().isoformat()


def parse(url):
    url = (url or '').strip()
    return urllib.parse.urlparse(url if '://' in url else 'http://' + url)  # websites are often written "pavin.it"


def domain(url):
    h = parse(url).hostname or ''
    return h[4:] if h.startswith('www.') else h


def site_key(url):
    """A site's identity, wherever two sites are compared: the host without www./m., plus the site's folder on a
    shared host (digilander.libero.it/rossi; sites.google.com/view/rossi)."""
    h = re.sub(r'^m\.', '', domain(url))
    seg = [x.lower() for x in parse(url).path.split('/') if x]
    if seg and re.search(SHARED_HOSTS, h):
        return h + '/' + '/'.join(seg[:2 if h == 'sites.google.com' and seg[0] in ('view', 'site') else 1])
    return h


def not_a_site(url):
    """Directories, social pages and public sites. A site in its own folder of a shared host is a site, also on
    sites.google.com or xoomer.virgilio.it."""
    h = re.sub(r'^m\.', '', domain(url))
    if '/' in site_key(url): return False
    labels = h.split('.')
    return not h or (len(labels) > 1 and labels[-2] in NOT_A_SITE) or h.startswith('comune.') \
        or any(h == x or h.endswith('.' + x) for x in NOT_A_SITE_HOSTS)


def same_site(a, b):
    """Two website addresses of the same business (www., m. and .it/.com variants of one name count as one)."""
    a, b = site_key(a), site_key(b)
    if not a or not b: return False
    if a == b: return True
    la, lb = a.split('.')[0], b.split('.')[0]
    builder = re.search(r'webnode|jimdo|wix|altervista|blogspot|wordpress\.com', a + b)
    return la == lb and len(la) >= 6 and a.count('.') == b.count('.') == 1 and not builder


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def load_done():
    ids, doms = set(), set()
    path = os.path.join(LEADS, 'done.jsonl')
    since = (date.fromisoformat(run_date()) - timedelta(days=RETRY_DAYS)).isoformat()
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            if line.strip():
                d = json.loads(line)
                if d.get('status') == 'retry' and d.get('date', '') < since: continue  # time to try again
                ids.add(d.get('place_id')); doms.add(site_key(d.get('website')))
    ids.discard(None); doms.discard('')
    return ids, doms


def targets():
    return json.load(open(os.path.join(LEADS, 'targets.json'), encoding='utf-8'))


def is_chain(c, name, host):
    """The chain's name as whole words in the business name ("Point S" is not "Car Point Snc", "Avanzi" is not
    "Ottica Avanzini"), or as a label of the website's host: point-s.it, midas-thiene.it, thiene-midas.it."""
    if re.search(r'(?<!\w)' + r'[\s-]+'.join(map(re.escape, c.split())) + r'(?!\w)', name, re.I): return True
    s = slug(c); k = s.replace('-', '')
    return any(l.replace('-', '') == k or any(l.startswith(f + '-') or l.endswith('-' + f) for f in (s, k))
               for l in host.split('.')[:-1])


def chain_reason(p, shared, t):
    """Why this looks like a chain or franchise (no owner to pitch, the site is the brand's), or None."""
    hit = next((c for c in t.get('chains', []) if is_chain(c, p['name'], domain(p['website']))), None)
    if hit: return f'catena ({hit})'
    if shared[site_key(p['website'])] >= 3: return 'stesso sito per 3+ sedi'
    # a branch page: /club/bassano-del-grappa/ is, /autofficina-thiene/ is not (a folder on a shared host is the site)
    segs = [slug(re.sub(r'\.\w+$', '', x)) for x in parse(p['website']).path.split('/') if x]
    segs = segs[site_key(p['website']).count('/'):]
    if len(segs) >= 2 and any(slug(town) in segs for town in t['towns']): return 'pagina di una sede su un sito di rete'
    return None


def pairs(n):
    t = targets()
    # every niche x town once, in a fixed shuffled order so consecutive nights change both
    allp = sorted(itertools.product(t['niches'], t['towns']), key=lambda p: hashlib.md5('|'.join(p).encode()).hexdigest())
    sp = os.path.join(LEADS, 'state.json')
    cur = json.load(open(sp)).get('cursor', 0) if os.path.exists(sp) else 0
    out = [allp[(cur + i) % len(allp)] for i in range(n)]
    json.dump({'cursor': (cur + n) % len(allp), 'total_pairs': len(allp)}, open(sp, 'w'))
    return out


def show_next(n_pairs):
    for niche, town in pairs(n_pairs):
        print(f'\n{niche} | {town}\n  web: "{niche} {town}"   "{niche} {town} contatti"   "{niche} vicino a {town}"'
              f'\n  then: python3 scripts/find_leads.py check --query "{niche} {town}" <url> <url> ...'
              f'\n  and:  python3 scripts/find_leads.py maps --query "{niche} {town}"')


def site_name(url):
    """The name the site gives itself (og:site_name or the first part of <title>), to look it up on Maps."""
    try:
        h = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=20,
                                   context=ctx).read(300000).decode('utf-8', 'replace')
    except Exception:
        return ''
    m = re.search(r'property=["\']og:site_name["\'] content=["\']([^"\']+)', h, re.I) or re.search(r'<title[^>]*>([^<]+)', h, re.I)
    t = re.sub(r'\s+', ' ', html.unescape(m.group(1))).strip() if m else ''
    return re.split(r'\s[|\-–—:·»]\s|\s[|–—»]', t)[0].strip()[:60]


def on_maps(url, final, town):
    """The Google Maps listing whose website is this site, or None."""
    key = site_key(final or url)
    label = key.rsplit('/', 1)[1] if '/' in key else key.split('.')[0]  # the folder's name on a shared host
    name = site_name(final or url)
    tried = set()
    for q in (f'{name} {town}' if name else '', f'{label} {town}', key):
        q = q.strip()
        if not q or q in tried: continue
        tried.add(q)
        for r in places.search(q, 10):
            if r['website'] and (same_site(r['website'], url) or same_site(r['website'], final)): return r
    return None


def check(query, urls, out_path, min_reviews=5, min_score=3):  # lower bar than pick: few URLs, and your eyes choose
    places.key()
    ids, doms = load_done()
    t = targets()
    town = max((x for x in t['towns'] if x.lower() in query.lower()), key=len, default='')
    found = load_found(out_path)
    ids |= {p['place_id'] for p in found}; doms |= {site_key(p['website']) for p in found}
    todo, seen = [], set()
    for u in urls:
        u = u.strip().rstrip('.,;)')
        if not u.startswith('http'): u = 'http://' + u
        d = site_key(u)
        if not d or d in seen: continue
        seen.add(d)
        if not_a_site(u): print(f'--  {d}: directory/social, not a business site'); continue
        if d in doms: print(f'--  {d}: already in done.jsonl or in tonight\'s candidates'); continue
        pu = urllib.parse.urlparse(u)
        # score the home page, not the inner page the search happened to land on: the host's root, or the site's
        # folder on a shared host (digilander.libero.it/rossi/, not the root of digilander.libero.it)
        folder = [x for x in pu.path.split('/') if x][:d.count('/')]
        todo.append(urllib.parse.urlunparse(pu._replace(path='/' + ''.join(x + '/' for x in folder), params='', query='', fragment='')))
    with cf.ThreadPoolExecutor(8) as ex:
        scores = list(ex.map(score, todo))
    added = 0
    for url, (s, final, flags) in zip(todo, scores):
        d = site_key(url)
        if flags.startswith('BLOCKED'):
            record(None, d, url, 'retry', f'sito dietro captcha/anti-bot, riprovare dopo {RETRY_DAYS} giorni')
            print(f'--  {d}: behind a captcha/anti-bot wall, marked retry'); continue
        if flags.startswith('ERROR'): print(f'--  {d}: {flags}'); continue
        if s < min_score: print(f'--  {d}: site score {s}, not outdated enough ({flags})'); continue
        p = on_maps(url, final, town)
        if not p:
            record(None, d, url, 'retry', f'non trovata su Google Maps (punteggio sito {s}); verificare a mano')
            print(f'--  {d}: score {s} but no Google Maps listing with this website, marked retry'); continue
        why = (p['place_id'] in ids and 'already seen') or (p['status'] != 'OPERATIONAL' and f'Maps: {p["status"]}') \
            or (p['reviews'] < min_reviews and f'only {p["reviews"]} reviews') or chain_reason(p, Counter(), t)
        if why:
            if p['status'] == 'CLOSED_PERMANENTLY': record(p['place_id'], p['name'], url, 'excluded', 'chiusa su Google Maps')
            print(f'--  {d}: {p["name"]}: {why}'); continue
        det = places.detail(p['place_id'])
        found.append({**p, **{k: det.get(k) for k in ('hours', 'review_list', 'newest_review', 'newest_review_days', 'alive_pct', 'phone_intl')},
                      'site_score': s, 'final_url': final, 'flags': flags, 'query': query, 'source': 'web'})
        ids.add(p['place_id']); doms.add(d); added += 1
        print(f'OK  {d}: {p["name"]}, score {s}, alive {det.get("alive_pct")}% ({p["reviews"]} rec., ultima {det.get("newest_review")}) {flags}')
    save(found, out_path)
    print(f'{query}: {added} new candidates, {len(found)} in {out_path}')


def load_found(out_path):
    """Tonight's candidates, minus anything recorded in done.jsonl since (drafted, skipped, excluded, retry)."""
    found = json.load(open(out_path, encoding='utf-8')) if os.path.exists(out_path) else []
    ids, doms = load_done()
    return [p for p in found if p['place_id'] not in ids and site_key(p['website']) not in doms]


def show(out_path):
    found = load_found(out_path)
    for i, p in enumerate(found, 1):
        print(f"{i}. {p['name']} | {p['address']}\n   place_id {p['place_id']}  {p['final_url']}\n"
              f"   site {p['site_score']} ({p['flags']}) | alive {p['alive_pct']}% | {p.get('rating')} ({p['reviews']} rec.), "
              f"newest {p.get('newest_review')} | {p.get('phone_intl') or ''}")
        for r in p.get('review_list') or []:
            print(f"   {r.get('rating')}* {(r.get('date') or '')[:7]} {(r.get('text') or '').replace(chr(10), ' ')[:160]}")
    print(f'{len(found)} candidates in {out_path}')


def save(found, out_path):
    found.sort(key=lambda p: (-((p.get('alive_pct') or 0) >= 55), -p['site_score'], -(p.get('alive_pct') or 0)))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(found, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def pick(n_pairs, out_path, min_reviews=5, min_score=3, details_per_pair=4, queries=None):
    """Google Maps first: the next n_pairs from the cursor, or the given queries (the pairs of `next`, cursor untouched)."""
    places.key()  # fail before moving the cursor
    ids, doms = load_done()
    t = targets()
    # earlier picks of the same night stay: add to them instead of overwriting
    found = load_found(out_path)
    ids |= {p['place_id'] for p in found}
    for q in queries or [f'{niche} {town}' for niche, town in pairs(n_pairs)]:
        res = places.search(q)
        shared = Counter(site_key(p['website']) for p in res if p['website'])
        hits, chains = [], 0
        for p in res:
            if not (p['website'] and p['status'] == 'OPERATIONAL' and p['reviews'] >= min_reviews
                    and p['place_id'] not in ids and site_key(p['website']) not in doms
                    and not not_a_site(p['website'])):
                continue
            why = chain_reason(p, shared, t)
            if why:
                chains += 1; print(f'  chain: {p["name"]} ({why})', file=sys.stderr); continue
            hits.append(p); ids.add(p['place_id']); doms.add(site_key(p['website']))
        scored, walls = [], 0
        for p in hits:
            s, final, flags = score(p['website'])
            if flags.startswith('BLOCKED'):
                walls += 1
                record(p['place_id'], p['name'], p['website'], 'retry',
                       f'sito dietro captcha/anti-bot ({p["reviews"]} rec.), riprovare dopo {RETRY_DAYS} giorni')
            elif s >= min_score:
                scored.append({**p, 'site_score': s, 'final_url': final, 'flags': flags, 'query': q})
        scored.sort(key=lambda p: -p['site_score'])
        for p in scored[:details_per_pair]:
            d = places.detail(p['place_id'])
            p.update({k: d.get(k) for k in ('hours', 'review_list', 'newest_review', 'newest_review_days', 'alive_pct', 'phone_intl')})
            found.append(p)
        print(f'{q}: {len(hits)} with a website, {len(scored)} outdated, {chains} chains, {walls} behind anti-bot (marked retry)',
              file=sys.stderr)
    save(found, out_path)
    for p in found:
        print(f"{p['site_score']:>2}  alive {p.get('alive_pct') or 0:>3}%  {p['name']}  {p['final_url']}  "
              f"({p['reviews']} rec., ultima {p['newest_review']})  {p['flags']}")
    print(f'saved {len(found)} candidates to {out_path}')


def record(place_id, name, website, status, note):
    entry = {'date': run_date(), 'place_id': place_id if place_id != '-' else None,
             'name': name, 'website': website, 'status': status, 'note': note}
    with open(os.path.join(LEADS, 'done.jsonl'), 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print('marked', name, status, file=sys.stderr)


def mark(place_id, a):
    get = lambda k: a[a.index(k) + 1] if k in a else None
    record(place_id, get('--name'), get('--website'), get('--status'), get('--note'))


if __name__ == '__main__':
    a = sys.argv[1:]
    sys.stdout.reconfigure(encoding='utf-8')
    out = a[a.index('--out') + 1] if '--out' in a else os.path.join(ROOT, 'runs', run_date(), 'candidates.json')
    if a[:1] == ['show']:
        show(out)
    elif a[:1] == ['next']:
        show_next(int(a[a.index('--pairs') + 1]) if '--pairs' in a else 4)
    elif a[:1] == ['check'] and '--query' in a:
        opts = {i + 1 for i, x in enumerate(a) if x in ('--query', '--out')} | {i for i, x in enumerate(a) if x in ('--query', '--out')}
        check(a[a.index('--query') + 1], [x for i, x in enumerate(a[1:], 1) if i not in opts], out)
    elif a[:1] == ['maps'] and '--query' in a:
        pick(0, out, queries=[a[i + 1] for i, x in enumerate(a) if x == '--query'])
    elif a[:1] == ['pick']:
        pick(int(a[a.index('--pairs') + 1]) if '--pairs' in a else 3, out)
    elif a[:1] == ['mark'] and len(a) > 1:
        mark(a[1], a)
    else:
        sys.exit(__doc__)
