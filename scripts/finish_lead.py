"""The last mile for one lead, in two calls instead of ten.

Usage:
  python3 scripts/finish_lead.py <slug> shots [--accent "#hex"] [--date YYYY-MM-DD]
      Serves site/ on a free local port and makes: the AFTER screenshots with the overflow and console checks
      (shots/), the BEFORE/AFTER card (card.jpg, Italian labels) and the two scroll GIFs. Prints problems and sizes,
      and exits non-zero when a step failed. Then look at card.jpg and shots/mobile-index.png before writing the draft.
  python3 scripts/finish_lead.py <slug> draft --to "<email or empty>" [--date YYYY-MM-DD] [--dry-run] [--replace <draft id>]
      Splits email.txt (first line "OGGETTO: ...") into subject and body, creates the Gmail draft with card.jpg and
      scroll-mobile.gif (plus scroll-desktop.gif when the email stays under about 7.5 MB), records the lead as "drafted" in
      leads/done.jsonl and adds the draft to report.md. Refuses without card.jpg and scroll-mobile.gif, and refuses a
      second draft when report.md already has one (--replace <its id> rewrites it). With --dry-run or without Gmail
      secrets it only writes email.eml: nothing is recorded.
Reads lead.json (written by prepare_lead.py) for the name, the old website and the place id. Never sends anything.
<date> defaults to tonight's date in Italy (find_leads.run_date).
"""
import functools, http.server, json, os, re, subprocess, sys, threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from find_leads import record, run_date
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
    failed = []

    def step(name, *args):  # prints the last line, or the last lines (the error) when the step failed
        code, out = run(*args)
        lines = out.splitlines() or [f'{name}: no output']
        print('\n'.join(lines[-8:] if code else lines[-1:]))
        if code: failed.append(f'{name} (exit {code})')

    try:
        code, out = run(f'{S}/shoot.py', url, 'index', os.path.join(d, 'shots'), '--no-video')
        print(out)
        if code: failed.append(f'screenshots (exit {code})')
        if code or 'FIX' in out or any('console errors:' in l and not l.rstrip().endswith('none') for l in out.splitlines()):
            print('!! fix the overflow or console errors above before the draft')
        card = [f'{S}/pitch_card.py', lead['old_url'], url + '/', lead['name'], os.path.join(d, 'card.jpg'), '--lang', 'it']
        if accent: card += ['--accent', accent]
        step('card.jpg', *card)
        for flag, name in [([], 'scroll-desktop.gif'), (['--mobile'], 'scroll-mobile.gif')]:
            step(name, f'{S}/make_gif.py', url + '/', os.path.join(d, name), *flag)
    finally:
        srv.shutdown()
    if failed: sys.exit('!! failed: ' + ', '.join(failed) + '. Fix it and run shots again before the draft.')
    print(f'look at: {os.path.relpath(d, ROOT)}/card.jpg and shots/mobile-index.png')


def draft(d, lead, to, dry=False, replace=None):
    att = [os.path.join(d, 'card.jpg'), os.path.join(d, 'scroll-mobile.gif')]
    missing = [os.path.basename(a) for a in att if not os.path.exists(a)]
    if missing: sys.exit(f'{" and ".join(missing)} missing: run "finish_lead.py <slug> shots" first (no draft without them)')
    gmail = all(os.environ.get(k) for k in ('GMAIL_CLIENT_ID', 'GMAIL_CLIENT_SECRET', 'GMAIL_REFRESH_TOKEN'))
    rp = os.path.join(d, 'report.md')
    report = open(rp, encoding='utf-8').read() if os.path.exists(rp) else ''
    old = re.search(r'Draft id (r-?\d+)', report)
    if gmail and not dry and old and not replace:
        sys.exit(f'report.md already has draft {old.group(1)}: add --replace {old.group(1)} to rewrite it, never a second draft')
    lines = open(os.path.join(d, 'email.txt'), encoding='utf-8').read().strip().splitlines()
    if not lines or not lines[0].upper().startswith('OGGETTO:'): sys.exit('email.txt must start with "OGGETTO: ..."')
    subject = lines[0].split(':', 1)[1].strip()
    body = os.path.join(d, 'email-body.txt')
    open(body, 'w', encoding='utf-8').write('\n'.join(lines[1:]).strip() + '\n')
    # attachments grow by a third once encoded: 5.5 MB of files is about a 7.5 MB email
    desk = os.path.join(d, 'scroll-desktop.gif')
    if os.path.exists(desk) and sum(map(mb, att)) + mb(desk) < 5.5: att.append(desk)
    args = [f'{S}/gmail_draft.py', '--to', to, '--subject', subject, '--body', body, '--attach', *att]
    if not gmail or dry: args += ['--dry-run', os.path.join(d, 'email.eml')]
    elif replace: args += ['--replace', replace]
    code, out = run(*args)
    print(out)
    if code: sys.exit('draft not created')
    if not gmail or dry:
        print(f'NO GMAIL DRAFT ({"dry run" if dry else "no Gmail secrets"}): only {os.path.relpath(d, ROOT)}/email.eml was written. '
              'Nothing recorded in leads/done.jsonl or report.md.')
        return
    m = re.search(r'draft (created|updated): (\S+)', out)
    if not m: sys.exit('Gmail did not confirm the draft: nothing recorded')
    did = m.group(2)
    sizes = ', '.join(f'{os.path.basename(a)} ({mb(a):.1f} MB)' for a in att)
    section = (f'\n## Bozza\n- A: {to or "nessun destinatario (email non trovata)"}. Oggetto: "{subject}".\n'
               f'- Allegati: {sizes}. Draft id {did}.\n')
    if m.group(1) == 'updated' and old:  # the same lead, already recorded: only the report's lines change
        report = re.sub(r'\n## Bozza\n(?:- .*\n?)*', lambda _: section, report, count=1) if '\n## Bozza\n' in report \
            else report.replace(old.group(1), did)
        open(rp, 'w', encoding='utf-8').write(report)
        print(f'draft {did} rewritten, report.md updated (not recorded again); attachments: {sizes}')
        return
    record(lead.get('place_id') or '-', lead['name'], lead['old_url'], 'drafted', f'bozza {did} a {to or "nessun destinatario"}')
    with open(rp, 'a', encoding='utf-8') as f:
        f.write(section)
    print(f'recorded as drafted; attachments: {sizes}')


if __name__ == '__main__':
    a = sys.argv[1:]
    if len(a) < 2 or a[1] not in ('shots', 'draft'): sys.exit(__doc__)
    sys.stdout.reconfigure(encoding='utf-8')
    get = lambda k: a[a.index(k) + 1] if k in a else None
    d = os.path.join(ROOT, 'runs', get('--date') or run_date(), a[0])
    lead = json.load(open(os.path.join(d, 'lead.json'), encoding='utf-8'))
    if a[1] == 'shots':
        shots(d, lead, get('--accent'))
    else:
        if '--to' not in a: sys.exit('draft needs --to "<email>" (or --to "" when no address was found)')
        draft(d, lead, get('--to'), '--dry-run' in a, get('--replace'))
