"""Nightly prospecting: rotate niche x town, find businesses on Google Maps, keep the alive ones with an old website.

Usage:
  python find_leads.py pick [--pairs 3] [--out runs/2026-10-27/candidates.json]
      Takes the next niche/town pairs from leads/targets.json (cursor in leads/state.json), searches Google Maps,
      drops businesses already in leads/done.jsonl and chains/franchises, scores their websites and checks they
      are alive. Adds to the night's candidates file (a second pick does not overwrite the first). Sites behind a
      captcha/anti-bot wall are marked "retry" automatically: never try to get around the wall.
  python find_leads.py mark <place_id> --name "..." --website URL --status drafted|skipped|excluded|retry [--note "..."]
      Records a business in leads/done.jsonl so it is not picked again ("retry": not for RETRY_DAYS days).
Needs GOOGLE_MAPS_API_KEY (see places.py).
"""
import hashlib, itertools, json, os, re, sys, unicodedata, urllib.parse
from collections import Counter
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import places
from score_sites import score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEADS = os.path.join(ROOT, 'leads')
NOT_A_SITE = ('facebook.', 'instagram.', 'paginegialle.', 'paginebianche.', 'virgilio.', 'google.', 'business.site',
              'linktr.ee', 'wa.me', 'tripadvisor.', 'miodottore.', 'treatwell.')
RETRY_DAYS = 30


def domain(url):
    h = urllib.parse.urlparse(url or '').hostname or ''
    return h[4:] if h.startswith('www.') else h


def slug(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def load_done():
    ids, doms = set(), set()
    path = os.path.join(LEADS, 'done.jsonl')
    since = (date.today() - timedelta(days=RETRY_DAYS)).isoformat()
    if os.path.exists(path):
        for line in open(path, encoding='utf-8'):
            if line.strip():
                d = json.loads(line)
                if d.get('status') == 'retry' and d.get('date', '') < since: continue  # time to try again
                ids.add(d.get('place_id')); doms.add(domain(d.get('website')))
    ids.discard(None); doms.discard('')
    return ids, doms


def targets():
    return json.load(open(os.path.join(LEADS, 'targets.json'), encoding='utf-8'))


def chain_reason(p, shared, t):
    """Why this looks like a chain or franchise (no owner to pitch, the site is the brand's), or None."""
    name, site = p['name'].lower(), p['website'].lower()
    hit = next((c for c in t.get('chains', []) if c.lower() in name or slug(c).replace('-', '') in site.replace('-', '')), None)
    if hit: return f'catena ({hit})'
    if shared[domain(p['website'])] >= 3: return 'stesso sito per 3+ sedi'
    path = '-' + slug(urllib.parse.urlparse(p['website']).path) + '-'  # whole words only ("malo" is not "malocclusione")
    if any(f'-{slug(town)}-' in path for town in t['towns']): return 'pagina di una sede su un sito di rete'
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


def pick(n_pairs, out_path, min_reviews=5, min_score=4, details_per_pair=4):
    places.key()  # fail before moving the cursor
    ids, doms = load_done()
    t = targets()
    # earlier picks of the same night stay: add to them instead of overwriting
    found = json.load(open(out_path, encoding='utf-8')) if os.path.exists(out_path) else []
    ids |= {p['place_id'] for p in found}
    for niche, town in pairs(n_pairs):
        q = f'{niche} {town}'
        res = places.search(q)
        shared = Counter(domain(p['website']) for p in res if p['website'])
        hits, chains = [], 0
        for p in res:
            if not (p['website'] and p['status'] == 'OPERATIONAL' and p['reviews'] >= min_reviews
                    and p['place_id'] not in ids and domain(p['website']) not in doms
                    and not any(x in p['website'] for x in NOT_A_SITE)):
                continue
            why = chain_reason(p, shared, t)
            if why:
                chains += 1; print(f'  chain: {p["name"]} ({why})', file=sys.stderr); continue
            hits.append(p); ids.add(p['place_id']); doms.add(domain(p['website']))
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
            p.update({k: d[k] for k in ('hours', 'review_list', 'newest_review', 'newest_review_days', 'alive_pct', 'phone_intl')})
            found.append(p)
        print(f'{q}: {len(hits)} with a website, {len(scored)} outdated, {chains} chains, {walls} behind anti-bot (marked retry)',
              file=sys.stderr)
    found.sort(key=lambda p: (-(p['alive_pct'] >= 55), -p['site_score'], -p['alive_pct']))
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(found, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for p in found:
        print(f"{p['site_score']:>2}  alive {p['alive_pct']:>3}%  {p['name']}  {p['final_url']}  "
              f"({p['reviews']} rec., ultima {p['newest_review']})  {p['flags']}")
    print(f'saved {len(found)} candidates to {out_path}')


def record(place_id, name, website, status, note):
    entry = {'date': date.today().isoformat(), 'place_id': place_id if place_id != '-' else None,
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
    if a[:1] == ['pick']:
        n = int(a[a.index('--pairs') + 1]) if '--pairs' in a else 3
        out = a[a.index('--out') + 1] if '--out' in a else os.path.join(ROOT, 'runs', date.today().isoformat(), 'candidates.json')
        pick(n, out)
    elif a[:1] == ['mark'] and len(a) > 1:
        mark(a[1], a)
    else:
        sys.exit(__doc__)
