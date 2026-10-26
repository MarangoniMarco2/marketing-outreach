"""Create a Gmail draft with attachments (the connector cannot attach files, this script can).

Usage:
  python gmail_draft.py --to info@example.com --subject "..." --body body.txt --attach card.jpg scroll.gif [--dry-run out.eml]
                        [--replace <draft id>]   (rewrite that draft instead of creating a new one)
The body file is plain text; config/signature.txt is appended when it exists.
Needs GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET and GMAIL_REFRESH_TOKEN (scope gmail.compose, see README).
It only ever creates drafts: nothing is sent.
--to may be empty ("") when no address was found: the draft is created without a recipient.
"""
import base64, json, mimetypes, os, sys, urllib.parse, urllib.request
from email.message import EmailMessage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def token():
    need = ['GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET', 'GMAIL_REFRESH_TOKEN']
    missing = [k for k in need if not os.environ.get(k)]
    if missing: sys.exit('Missing environment secrets: ' + ', '.join(missing) + ' (see README).')
    data = urllib.parse.urlencode({'client_id': os.environ[need[0]], 'client_secret': os.environ[need[1]],
                                   'refresh_token': os.environ[need[2]], 'grant_type': 'refresh_token'}).encode()
    try:
        return json.load(urllib.request.urlopen('https://oauth2.googleapis.com/token', data, timeout=30))['access_token']
    except urllib.error.HTTPError as e:
        sys.exit(f'Gmail token error {e.code}: {e.read().decode()[:300]}')


def build(to, subject, body, files):
    m = EmailMessage()
    if to: m['To'] = to
    m['Subject'] = subject
    sig = os.path.join(ROOT, 'config', 'signature.txt')
    if os.path.exists(sig): body = body.rstrip() + '\n\n' + open(sig, encoding='utf-8').read().strip() + '\n'
    m.set_content(body)
    for f in files:
        ctype = mimetypes.guess_type(f)[0] or 'application/octet-stream'
        main, sub = ctype.split('/', 1)
        m.add_attachment(open(f, 'rb').read(), maintype=main, subtype=sub, filename=os.path.basename(f))
    return m


if __name__ == '__main__':
    a = sys.argv[1:]
    get = lambda k: a[a.index(k) + 1] if k in a else None
    if not get('--subject') or not get('--body'): sys.exit(__doc__)
    files = []
    if '--attach' in a:
        for x in a[a.index('--attach') + 1:]:
            if x.startswith('--'): break
            files.append(x)
    msg = build(get('--to') or '', get('--subject'), open(get('--body'), encoding='utf-8').read(), files)
    size = len(msg.as_bytes()) / 1e6
    if size > 20: sys.exit(f'Email is {size:.1f} MB: shrink the attachments (Gmail limit 25 MB).')
    if '--dry-run' in a:
        open(get('--dry-run'), 'wb').write(msg.as_bytes()); print(f'dry run: wrote {get("--dry-run")} ({size:.1f} MB)'); sys.exit()
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    old = get('--replace')  # rewrite an existing draft in place instead of adding a second one
    url = 'https://gmail.googleapis.com/gmail/v1/users/me/drafts' + (f'/{old}' if old else '')
    body = {'id': old, 'message': {'raw': raw}} if old else {'message': {'raw': raw}}
    req = urllib.request.Request(url, json.dumps(body).encode(), {'Authorization': 'Bearer ' + token(), 'Content-Type': 'application/json'},
                                 method='PUT' if old else 'POST')
    try:
        d = json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f'Gmail API error {e.code}: {e.read().decode()[:300]}')
    print(f"draft {'updated' if old else 'created'}: {d['id']} ({size:.1f} MB) https://mail.google.com/mail/#drafts")
