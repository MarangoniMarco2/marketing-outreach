"""The last mile for one lead, in two calls instead of ten.

Usage:
  python3 scripts/finish_lead.py <slug> shots [--accent "#hex"] [--date YYYY-MM-DD]
      Serves site/ on a free local port and makes: the AFTER screenshots with the overflow and console checks
      (shots/), the BEFORE/AFTER card (card.jpg, Italian labels) and the two scroll GIFs. Prints problems and sizes.
      Then look at card.jpg and shots/mobile-index.png before writing the draft.
  python3 scripts/finish_lead.py <slug> draft --to "<email or empty>" [--date YYYY-MM-DD] [--dry-run]
      Splits email.txt (first line "OGGETTO: ...") into subject and body, creates the Gmail draft with card.jpg and
      scroll-mobile.gif (plus scroll-desktop.gif when the email stays under about 7.5 MB), records the lead as "drafted" in
      leads/done.jsonl and adds the draft to report.md. Without Gmail secrets it writes email.eml instead.
Reads lead.json (written by prepare_lead.py) for the name, the old website and the place id. Never sends anything.
"""
import functools, http.server, json, os, re, subprocess, sys, threading
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.dirname(os.path.abspath(__file__))


def run(*args):
    r = subprocess.run([sys.executable, *args], capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip()
    return r.returncode, out


def serve(site):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=site))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}'


def mb(p):
    return os.path.getsize(p) / 1e6 if os.path.exists(p) else 0


def shots(d, lead, accent):
    srv, url = serve(os.path.join(d, 'site'))
    try:
        code, out = run(f'{S}/shoot.py', url, 'index', os.path.join(d, 'shots'), '--no-video')
        print(out)
        if code or 'FIX' in out or any('console errors:' in l and not l.rstrip().endswith('none') for l in out.splitlines()):
            print('!! fix the overflow or console errors above before the draft')
        card = [f'{S}/pitch_card.py', lead['old_url'], url + '/', lead['name'], os.path.join(d, 'card.jpg'), '--lang', 'it']
        if accent: card += ['--accent', accent]
        print(run(*card)[1].splitlines()[-1])
        for flag, name in [([], 'scroll-desktop.gif'), (['--mobile'], 'scroll-mobile.gif')]:
            print(run(f'{S}/make_gif.py', url + '/', os.path.join(d, name), *flag)[1].splitlines()[-1])
    finally:
        srv.shutdown()
    print(f'look at: {os.path.relpath(d, ROOT)}/card.jpg and shots/mobile-index.png')


def draft(d, lead, to, dry=False):
    lines = open(os.path.join(d, 'email.txt'), encoding='utf-8').read().strip().splitlines()
    if not lines or not lines[0].upper().startswith('OGGETTO:'): sys.exit('email.txt must start with "OGGETTO: ..."')
    subject = lines[0].split(':', 1)[1].strip()
    body = os.path.join(d, 'email-body.txt')
    open(body, 'w', encoding='utf-8').write('\n'.join(lines[1:]).strip() + '\n')
    att = [os.path.join(d, 'card.jpg'), os.path.join(d, 'scroll-mobile.gif')]
    # attachments grow by a third once encoded: 5.5 MB of files is about a 7.5 MB email
    if sum(map(mb, att)) + mb(os.path.join(d, 'scroll-desktop.gif')) < 5.5: att.append(os.path.join(d, 'scroll-desktop.gif'))
    att = [a for a in att if os.path.exists(a)]
    args = [f'{S}/gmail_draft.py', '--to', to, '--subject', subject, '--body', body, '--attach', *att]
    gmail = all(os.environ.get(k) for k in ('GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET', 'GMAIL_REFRESH_TOKEN'))
    if not gmail or dry: args += ['--dry-run', os.path.join(d, 'email.eml')]
    code, out = run(*args)
    print(out)
    if code: sys.exit('draft not created')
    m = re.search(r'draft created: (\S+)', out)
    did = m.group(1) if m else 'dry-run (email.eml)'
    from find_leads import record
    record(lead.get('place_id') or '-', lead['name'], lead['old_url'], 'drafted',
           f'bozza {did} a {to or "nessun destinatario"}')
    sizes = ', '.join(f'{os.path.basename(a)} ({mb(a):.1f} MB)' for a in att)
    with open(os.path.join(d, 'report.md'), 'a', encoding='utf-8') as f:
        f.write(f'\n## Bozza\n- A: {to or "nessun destinatario (email non trovata)"}. Oggetto: "{subject}".\n'
                f'- Allegati: {sizes}. Draft id {did}.\n')
    print(f'recorded as drafted; attachments: {sizes}')


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2 or a[1] not in ('shots', 'draft'): sys.exit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    get = lambda k: a[a.index(k) + 1] if k in a else None
    d = os.path.join(ROOT, 'runs', get('--date') or date.today().isoformat(), a[0])
    lead = json.load(open(os.path.join(d, 'lead.json'), encoding='utf-8'))
    if a[1] == 'shots':
        shots(d, lead, get('--accent'))
    else:
        if '--to' not in a: sys.exit('draft needs --to "<email>" (or --to "" when no address was found)')
        draft(d, lead, get('--to'), '--dry-run' in a)
