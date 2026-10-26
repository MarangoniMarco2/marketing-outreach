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
python3 -c "import playwright, PIL" || pip install "playwright==1.63.0" pillow   # match the preinstalled browser; never run "playwright install"
node --version   # taste-skill needs Node 22+
# taste-skill looks for Chrome in the usual places (or CHROME_PATH); in cloud sessions link Playwright's Chromium once
[ -e /usr/bin/chromium ] || ln -s "$(ls -d /opt/pw-browsers/chromium-*/chrome-linux64/chrome | head -1)" /usr/bin/chromium
```
Environment variables set with `export` do not survive between commands, so the commands below never rely on
them. If HTTPS calls fail on certificates in a cloud session, prefix that one command with
`SSL_CERT_FILE=/root/.ccr/ca-bundle.crt`.
Secrets come from the environment: `GOOGLE_MAPS_API_KEY` (step 1) and `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`,
`GMAIL_REFRESH_TOKEN` (step 7). If one is missing, say so plainly and do the parts that do not need it.

Output for one business goes in `runs/<YYYY-MM-DD>/<slug>/`:
`site/` (index.html + assets), `before/` and `shots/` (screenshots), `card.jpg`, `scroll-desktop.gif`,
`scroll-mobile.gif`, `email.txt`, `report.md`.

## Step 1: Find prospects (Google Maps first)

```bash
python3 scripts/find_leads.py pick --pairs 3
```
It takes the next niche/town pairs from `leads/targets.json`, searches Google Maps, keeps businesses that are
OPERATIONAL, have a real website (not Facebook or a directory) and at least 5 reviews, skips anything already in
`leads/done.jsonl`, scores each website for how outdated it is (`score_sites.py`) and fetches details (reviews,
hours) for the worst ones. It prints `site_score`, `alive %` and the newest review date, and saves
`runs/<date>/candidates.json`.

A single business given by the user skips this step: use `python3 scripts/places.py search "<name> <town>"` and
`details <place_id>` to get the same data.

Then **look**: screenshot the top candidates (desktop and phone) and pick with your eyes. The score finds
candidates, your eyes choose. Drop a candidate (and `mark` it as `skipped` with the reason) when the site is
actually fine, the business looks closed, or something feels off.

### Is the business alive?
`alive_pct` from `places.py`: reviews in the last 6 months = 85%+ (good lead); only older activity = 55-70% (only
if nothing better tonight); below 55% = skip. Also read the reviews themselves. Skip when they describe the owner
as rude or dishonest, the business as closed or moved, or show an unhappy pattern: those owners will not answer
well and the reviews would end up on their new page. Red flags as before: several unrelated businesses on one
phone number, a newer second website, a copy of the site on another domain.

## Step 2: Harvest real content

```bash
python3 scripts/scrape_site.py https://oldsite.it <inner pages from LINKS> --download runs/<date>/<slug>/raw
```
Collect: name, legal name and VAT, phones, email, address(es), hours (Google Maps hours win over the site's),
years in business, history, team, services, certifications and networks, guarantees, unique claims, clients they
name. Invent nothing a customer would rely on. Note the outreach address from `EMAILS:` (never a PEC). No
address found = the draft is created without a recipient and the report says so.

From `places.py details`: the up-to-five Google reviews with author and date, rating and count, hours.

Photos: make a contact sheet of `raw/` and look at it. Use their real photos of work, place and people (crop out
baked-in logos and labels). Do NOT use promo posters, banners with text, other brands' material, or stock photos
from the old site (a supercar on a body shop's site is stock: say so in the email if it is a weakness).

Record the BEFORE now: screenshot the old home page on desktop and phone into `before/` (the old site can change).

## Step 3: Design and build the home page with tasteskill v2

Read `vendor/taste-skill/SKILL.md` and follow **its run, steps 1 to 10, for one page**, with these adaptations.
Where this file and the taste-skill house rules disagree on design, **the taste-skill house rules win** (no
eyebrows, no 01/02/03 numbering, no icon-topped card rows, no gradients, no shadows at rest, no glass or blur, no
pill badges, no tiny tracked capitals, two typefaces at most, square or fully round buttons).

Commands: first `cd runs/<date>/<slug>` (the working directory persists), so `.taste-skill/` lands there, then
call the scripts with exactly this path. `.claude/settings.json` allows these five scripts in exactly this form
(and from the repo root as `node vendor/taste-skill/scripts/...`); do not wrap them in variables, `env` or `&&`
chains, or the night run will stop at a permission prompt nobody answers.
```bash
node ../../../vendor/taste-skill/scripts/draw.mjs --sector <closest sector> --brief "<one line>" --sections <roles> --have photography --options 3
node ../../../vendor/taste-skill/scripts/draw.mjs <same args> --direction <id>
node ../../../vendor/taste-skill/scripts/assets.mjs "<query from the inventory>"   # open-collection pictures, credited
node ../../../vendor/taste-skill/scripts/lint.mjs site/
node ../../../vendor/taste-skill/scripts/inspect.mjs site/index.html
```
`cd` back to the repo root before running the Python scripts.

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
- **Time budget (nightly):** two look-and-fix rounds at most (taste step 8), then the motion layer, then gate
  again. The gate must end with 0 FAIL at 1440, 768 and 390.

## Step 4: Screens for the email

```bash
python3 -m http.server 4812 --directory runs/<date>/<slug>/site &
python3 scripts/shoot.py http://localhost:4812 index runs/<date>/<slug>/shots
```
Look at every screenshot. Accessory screens are fine when they help the pitch (for example the services section
or the contact block cropped at phone width); save them in `shots/` with clear names.

## Step 5: Pitch card and GIFs

```bash
python3 scripts/pitch_card.py <old-url> http://localhost:4812/ "<Business name>" runs/<date>/<slug>/card.jpg --lang it --accent "#hex"
python3 scripts/make_gif.py http://localhost:4812/ runs/<date>/<slug>/scroll-desktop.gif
python3 scripts/make_gif.py http://localhost:4812/ runs/<date>/<slug>/scroll-mobile.gif --mobile
```
Open the card and look at it. Each GIF should be under about 4 MB (lower `--width` or `--screens` if not).
The old site may show a popup or cookie banner in the BEFORE: leave it, it is part of the pitch, unless it
covers everything.

## Step 6: The email text

Write `email.txt` from `templates/email_it.txt` (first line `OGGETTO: ...`). Name one or two concrete, verified
problems of the old site (visible in `before/`) and two or three real strengths you put on the new page. No price,
no claims about a phone call that did not happen, about 180 words, the opt-out line at the end.

## Step 7: Gmail draft (never send)

```bash
python3 scripts/gmail_draft.py --to "<email or empty>" --subject "<subject>" --body runs/<date>/<slug>/email-body.txt \
  --attach runs/<date>/<slug>/card.jpg runs/<date>/<slug>/scroll-mobile.gif
```
`email-body.txt` is `email.txt` without the OGGETTO line. Attach the card and one GIF (the phone one usually
shows the difference best); add the desktop GIF only if the total stays under about 8 MB. The script only creates
drafts. Without Gmail secrets, run it with `--dry-run runs/<date>/<slug>/email.eml` and say so.

Then record the business:
```bash
python3 scripts/find_leads.py mark <place_id> --name "<name>" --website <url> --status drafted --note "<one line>"
```

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
