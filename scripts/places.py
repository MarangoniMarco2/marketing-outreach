"""Google Maps (Places API, New) for prospecting and the 'is it alive?' check.

Needs the environment variable GOOGLE_MAPS_API_KEY (Places API (New) enabled on the key).

Usage:
  python places.py search "carrozzeria Thiene" [--max 20]   -> one JSON object per line
  python places.py details <place_id>                        -> one JSON object (reviews, hours, phone...)
Output fields are documented in summarize() and detail().
"""
import json, os, sys, urllib.request
from datetime import datetime, timezone

API = 'https://places.googleapis.com/v1'
SEARCH_FIELDS = ','.join('places.' + f for f in [
    'id', 'displayName', 'formattedAddress', 'websiteUri', 'businessStatus', 'rating', 'userRatingCount',
    'nationalPhoneNumber', 'primaryTypeDisplayName', 'googleMapsUri'])
DETAIL_FIELDS = ','.join([
    'id', 'displayName', 'formattedAddress', 'websiteUri', 'businessStatus', 'rating', 'userRatingCount',
    'nationalPhoneNumber', 'internationalPhoneNumber', 'regularOpeningHours', 'reviews', 'googleMapsUri',
    'primaryTypeDisplayName'])


def key():
    k = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not k: sys.exit('GOOGLE_MAPS_API_KEY is not set: add it to the environment secrets (see README).')
    return k


def call(url, body=None, fields=''):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, method='POST' if body else 'GET',
                                 headers={'X-Goog-Api-Key': key(), 'X-Goog-FieldMask': fields, 'Content-Type': 'application/json'})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))
    except urllib.error.HTTPError as e:
        sys.exit(f'Places API error {e.code}: {e.read().decode()[:300]}')


def summarize(p):
    return {'place_id': p.get('id'), 'name': p.get('displayName', {}).get('text'), 'address': p.get('formattedAddress'),
            'website': p.get('websiteUri'), 'status': p.get('businessStatus'), 'rating': p.get('rating'),
            'reviews': p.get('userRatingCount', 0), 'phone': p.get('nationalPhoneNumber'),
            'type': p.get('primaryTypeDisplayName', {}).get('text'), 'maps': p.get('googleMapsUri')}


def search(query, max_results=20):
    body = {'textQuery': query, 'languageCode': 'it', 'regionCode': 'IT', 'pageSize': min(max_results, 20)}
    return [summarize(p) for p in call(f'{API}/places:searchText', body, SEARCH_FIELDS).get('places', [])]


def detail(place_id):
    p = call(f'{API}/places/{place_id}?languageCode=it', fields=DETAIL_FIELDS)
    out = summarize(p)
    out['phone_intl'] = p.get('internationalPhoneNumber')
    out['hours'] = p.get('regularOpeningHours', {}).get('weekdayDescriptions', [])
    revs = []
    for r in p.get('reviews', []):  # Google returns at most 5, "most relevant" first
        revs.append({'rating': r.get('rating'), 'date': (r.get('publishTime') or '')[:10],
                     'author': r.get('authorAttribution', {}).get('displayName'),
                     'text': (r.get('originalText') or r.get('text') or {}).get('text', '')})
    out['review_list'] = revs
    dates = [r['date'] for r in revs if r['date']]
    out['newest_review'] = max(dates) if dates else None  # both None without reviews: the keys are always there
    out['newest_review_days'] = (datetime.now(timezone.utc) - datetime.fromisoformat(out['newest_review'])
                                 .replace(tzinfo=timezone.utc)).days if out['newest_review'] else None
    out['alive_pct'] = alive_score(out)
    return out


def alive_score(d):
    """Skill rule: reviews in the last 6 months = 85%+, only older activity = 55-70%, nothing = skip."""
    if d.get('status') and d['status'] != 'OPERATIONAL': return 0
    age, n = d.get('newest_review_days'), d.get('reviews') or 0
    if age is None: return 40 if n else 20
    if age <= 180: return 95 if n >= 30 else 85
    if age <= 365: return 65
    return 45


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2 or a[0] not in ('search', 'details'): sys.exit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    if a[0] == 'search':
        n = int(a[a.index('--max') + 1]) if '--max' in a else 20
        for p in search(a[1], n): print(json.dumps(p, ensure_ascii=False))
    else:
        print(json.dumps(detail(a[1]), ensure_ascii=False, indent=1))
