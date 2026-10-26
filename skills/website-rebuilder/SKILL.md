---
name: website-rebuilder
description: Find local businesses (Vicenza area by default) that are alive on Google Maps but have an ugly, outdated website, and rebuild their HOME PAGE ONLY as a premium page designed with tasteskill v2 (vendor/taste-skill), using their real content, photos and Google reviews. Produces desktop and phone screenshots, a BEFORE/AFTER pitch card, scroll GIFs and a Gmail draft with everything attached (never sends). Use when the user says "find an old/ugly website", "rebuild this site", "run the website rebuilder on <url>", "make a sample site for <business>", or for the nightly lead run (NIGHTLY.md).
version: 2.0
---

# Website Rebuilder v2 (home page + outreach)

The idea: find a business that is busy (Google Maps) but whose website is clearly old, design the one page that
matters (the home page) so it looks like a top studio made it, and use the before/after as the opener of an email
the user reviews and sends. Never quote a price. Never send an email: only drafts.

Run everything from the repo root. Paths below are relative to it.

## Session setup (every run)

```bash
bash scripts/setup_session.sh
```
It makes sure `python3` has Playwright 1.63.0 and Pillow (installing them if needed; that version matches the
preinstalled Chromium, never run "playwright install"), checks Node 22+ and ffmpeg, points `/usr/bin/chromium` at
Playwright's Chromium for taste-skill, and lists which secrets are set (names only). `FAIL` lines must be fixed
before going on. If it says `WARN ... use /usr/bin/python3.X`, write that path instead of `python3` in every
command of the run.
Environment variables set with `export` do not survive between commands, so the commands below never rely on
them. If HTTPS calls fail on certificates in a cloud session, prefix that one command with
`SSL_CERT_FILE=/root/.ccr/ca-bundle.crt`.
Secrets come from the environment: `GOOGLE_MAPS_API_KEY` (step 1) and `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`,
`GMAIL_REFRESH_TOKEN` (step 6). If one is missing, say so plainly and do the parts that do not need it.

## Lean context (every run)
Every turn re-reads everything already in the conversation, so what you read stays on the bill until the end:
- Read only what the step needs: this file, `vendor/taste-skill/SKILL.md` and the references it sends you to
  when you design. Never `cat` the scripts, the README or old summaries: the commands below are all you need,
  and each script prints its usage when run without arguments.
- Look at the few images the steps name (contact sheet, BEFORE on the phone, card, AFTER on the phone, the
  inspect screenshots), not every file.
- Keep command output short (`| tail`, `| head`, `grep`); the scripts already print summaries.
- One command per step where there is one (`prepare_lead.py`, `finish_lead.py`), not their parts by hand.
- Write a file whole when you create it (one Write for `index.html`, one for the CSS), and batch fixes into one
  edit per file per round instead of many small edits.

Output for one business goes in `runs/<date>/<slug>/`:
`site/` (index.html + assets), `before/` and `shots/` (screenshots), `card.jpg`, `scroll-desktop.gif`,
`scroll-mobile.gif`, `email.txt`, `report.md`.
`<date>` (YYYY-MM-DD) is the run's date, today in Italy (`TZ=Europe/Rome date +%F`); in a nightly run the
coordinator gives it. Pass it as `--date` to `prepare_lead.py` and `finish_lead.py`, so a build that goes past
midnight stays in one folder.

## Step 1: Find prospects (web search first, Google Maps to check)

The web search finds sites that are really there to rebuild (own domain, real text and photos); Google Maps then
says whether the business behind them is alive.

```bash
python3 scripts/find_leads.py next --pairs 4
```
It moves the cursor in `leads/state.json` and prints the next niche/town pairs from `leads/targets.json` with
search ideas. For each pair, run two or three web searches in Italian (`autofficina Thiene`,
`autofficina Thiene contatti`, `autofficina vicino a Thiene`), with `blocked_domains` for the big directories
(paginegialle.it, paginebianche.it, facebook.com, instagram.com, prontopro.it, miodottore.it, infobel.com,
starofservice.it, reteimprese.it). Old-site tricks from the original skill: search the footer text of an old
template or builder plus the trade and town ("realizzato da", "powered by", "© 2012"), and note phone numbers
that come back on several sites (one owner, several sites).

Collect the businesses' own websites (not directories, lead-gen "pronto intervento" pages or insurers' networks)
and pass them all to:
```bash
python3 scripts/find_leads.py check --query "autofficina Thiene" https://a.it/ https://b.it/ ...
```
For each site it prints why it was dropped (directory, already seen, modern enough, captcha, not on Maps, closed,
few reviews, chain) or `OK` with the Maps name, site score, alive % and newest review. The good ones go into
`runs/<date>/candidates.json` with reviews and hours (several `check` calls add up). Captcha-walled sites and
sites with no Maps listing are marked `retry`, permanently closed ones `excluded`.

Fallback (web search not available, or still nothing after 12 pairs): `python3 scripts/find_leads.py pick
--pairs 4` searches Google Maps directly for the next pairs and fills the same candidates file.

A single business given by the user skips this step: use `python3 scripts/places.py search "<name> <town>"` and
`details <place_id>` to get the same data.

Then **look**: `python3 scripts/find_leads.py show` lists the candidates with their reviews in a few lines each,
and `python3 scripts/peek.py runs/<date>/peek.jpg <url> <url> ...` puts the old home pages of the best ones
(desktop and phone) in one image. The score finds candidates, your eyes choose. Drop a candidate (and `mark` it
as `skipped` with the reason) when the site is actually fine, the business looks closed, or something feels off.

### Is the business alive?
`alive_pct` from `places.py`: reviews in the last 6 months = 85%+ (good lead); only older activity = 55-70% (only
if nothing better tonight); below 55% = skip. Also read the reviews themselves. Skip when they describe the owner
as rude or dishonest, the business as closed or moved, or show an unhappy pattern: those owners will not answer
well and the reviews would end up on their new page. Red flags as before: several unrelated businesses on one
phone number, a newer second website, a copy of the site on another domain.

## Step 2: Harvest real content (one command)

```bash
python3 scripts/prepare_lead.py <place_id> <old_url> <slug> --date <date>
```
It writes `runs/<date>/<slug>/`: `lead.json` (Google Maps: rating, up to five reviews verbatim with author and
date, hours, phones, alive %), `old-site.txt` (text of the home page and up to six menu pages, then links, emails,
phones, VAT), `raw/` with the old site's pictures and `raw/contact-sheet.jpg` showing them all, and the BEFORE
screenshots in `before/` (the old site can change). It prints a four-line summary.
Exit code 3 = the home page is behind a captcha: do not try to get around it (no other user agents, no browser
tricks, no cached copies). `mark` the lead `retry` with the reason and take the next candidate. An inner page
behind a captcha (often the contact form) is just skipped.

Read `lead.json` and `old-site.txt`, look at `raw/contact-sheet.jpg` and `before/home-mobile.jpg`: that is the
whole inventory. Collect: name, legal name and VAT, phones, email, address(es), hours (Google Maps hours win over
the site's), years in business, history, team, services, certifications and networks, guarantees, unique claims,
clients they name. Invent nothing a customer would rely on. The outreach address comes from `EMAILS:` (never a
PEC). No address found = the draft is created without a recipient and the report says so.

Photos: use their real photos of work, place and people (crop out baked-in logos and labels). Do NOT use promo
posters, banners with text, other brands' material, or stock photos from the old site (a supercar on a body
shop's site is stock: say so in the email if it is a weakness). Open a single file from `raw/` only when you
need to judge it closely.

## Step 3: Design and build the home page with tasteskill v2

Read `vendor/taste-skill/SKILL.md` and follow **its run, steps 1 to 10, for one page**, with these adaptations.
Where this file and the taste-skill house rules disagree on design, **the taste-skill house rules win** (no
eyebrows, no 01/02/03 numbering, no icon-topped card rows, no gradients, no shadows at rest, no glass or blur, no
pill badges, no tiny tracked capitals, two typefaces at most, square or fully round buttons).

Commands: the taste-skill scripts must run inside the lead's folder (`.taste-skill/` lands there). Other leads
may be built at the same time in the same session, so never rely on the current directory: start each command
with `cd` to the lead's absolute folder, and call the scripts with exactly this relative path (the form
`.claude/settings.json` allows; no variables or `env` around them).
```bash
cd /home/user/marketing-outreach/runs/<date>/<slug> && node ../../../vendor/taste-skill/scripts/draw.mjs --sector <closest sector> --brief "<one line>" --sections <roles> --have photography --options 3
cd /home/user/marketing-outreach/runs/<date>/<slug> && node ../../../vendor/taste-skill/scripts/draw.mjs <same args> --direction <id>
cd /home/user/marketing-outreach/runs/<date>/<slug> && node ../../../vendor/taste-skill/scripts/assets.mjs "<query from the inventory>"
cd /home/user/marketing-outreach/runs/<date>/<slug> && node ../../../vendor/taste-skill/scripts/lint.mjs site/ && node ../../../vendor/taste-skill/scripts/inspect.mjs site/index.html
```
The last line is one gate round: lint and inspect together, in one command.
Python scripts: `cd /home/user/marketing-outreach && python3 scripts/...`. If the repo is somewhere else, use
that path instead.

Adaptations for this job:
- **One page only:** `site/index.html` with its CSS, JS and `img/`. No inner pages. Every section the visitor
  came for (services, the proof, where and when, contact) lives on this page with its own heading and anchor in
  the navigation. A booking or quote request is a `mailto:` with a written subject, or `tel:`; no fake form
  backend.
- **Sector:** trades and workshops are usually `other` or `physical-product`; clinics `health`; salons, gyms and
  shops `consumer-app` is wrong, use `other` or `hospitality`. Pick the closest and say why in the report.
- **The brand:** if their logo or sign has clear colours, pass `--keep palette` and map them to the roles; keep
  their name as the wordmark (set in the dealt typeface, no fake logo).
- **The idea (taste step 4)** comes from the inventory: the year they opened, the street and town, the sign on
  the building, the trade's own artefact (a job card, a service booklet, a tyre label, a quote). Apply the
  competitor test with the shop down the road.
- **The live thing:** something real and small: "Siete aperti adesso?" from the real hours, a quote request that
  builds the email text from the visitor's choices, the route from the motorway exit, the next free slot type.
- **Proof:** only real proof. Google reviews from `places.py` may be quoted word for word with the author's first
  name and initial, the stars and the month, and the line "Recensione Google"; never edit them, never invent
  any. No reviews worth quoting = show the rating and count as text, or no proof section.
- **Pictures:** their own photos first, then open-collection pictures of the town or trade (credited in the
  footer), then drawn. At least four real pictures (taste floor). No AI image tool unless one is really available.
- **Copy:** Italian, simple (a 6th-grade reader), the business's own words where possible, no em or en dashes in
  customer-facing copy. Every phone number is a `tel:` link and the top bar carries one call action.
- **Unconfirmed facts** (old client lists, team size, partner companies that may have merged): keep them out of
  the page, or mark with `<!-- CONFIRM: ... -->` and list them in the report.
- `<meta name="robots" content="noindex, nofollow">` on the page.
- **Screenshots and GIFs** are made with full-page captures and a fast scroll: a reveal effect that hides a big
  picture until it scrolls into view (a "shutter" or clip that opens late) can leave it blank in them. Keep
  pictures visible by default and animate only small things.
- **Time budget (nightly):** two look-and-fix rounds at most (taste step 8), then the motion layer, then gate
  again. The gate must end with 0 FAIL at 1440, 768 and 390.

## Step 4: Screens, pitch card and GIFs (one command)

```bash
python3 scripts/finish_lead.py <slug> shots --accent "#hex" --date <date>
```
It serves `site/` on a free local port, takes the AFTER screenshots with the overflow and console checks
(`shots/`), the BEFORE/AFTER card (`card.jpg`, Italian labels) and the two scroll GIFs, and prints problems and
sizes. A step that failed is printed with its error and the command ends with a non-zero exit code. Fix anything
it flags and run it again. Then look at `card.jpg` and `shots/mobile-index.png` (two images, not every file).
Each GIF should be under about 4 MB. The old site may show a popup or cookie banner in the BEFORE: leave it, it
is part of the pitch, unless it covers everything. Accessory screens are fine when they help the pitch; save
them in `shots/` with clear names.

## Step 5: The email text

Write `email.txt` from `templates/email_it.txt` (first line `OGGETTO: ...`). Name one or two concrete, verified
problems of the old site (visible in `before/`) and two or three real strengths you put on the new page. No price,
no claims about a phone call that did not happen, about 180 words, the opt-out line at the end.

## Step 6: Gmail draft (never send) and record (one command)

```bash
python3 scripts/finish_lead.py <slug> draft --to "<email or empty>" --date <date>
```
It splits `email.txt` into subject and body, creates the Gmail draft with `card.jpg` and `scroll-mobile.gif` (plus
the desktop GIF when the email stays under about 7.5 MB), records the lead as `drafted` in `leads/done.jsonl` and
adds the draft id and attachments to `report.md`. It only creates drafts. It refuses to run without `card.jpg` and
`scroll-mobile.gif` (run `shots` first), and refuses a second draft when `report.md` already has one: add
`--replace <draft id>` to rewrite that draft. Without Gmail secrets (or with `--dry-run`) it writes `email.eml`
instead, records nothing and says so.

## Report (report.md, and a short summary to the user)
- Business, Google data (rating, count, newest review, alive %), why it was chosen.
- Direction dealt (name, seed), redraws and why, the idea sentence, the live thing, last critique scores.
- What is real, what is drawn or found (with credits), every `CONFIRM`, anything not wired.
- Recipient (or "no email found"), attachments and their sizes, draft id.

## Good manners
- Only drafts; the user reviews and sends. Commercial email to a business without consent is regulated in Italy
  (art. 130 Codice Privacy): keep it personal, one message, with the opt-out line.
- Only show a business's old website publicly with their permission. Previews stay `noindex`.
- Google review text is shown with its author and the Google attribution, unedited.
