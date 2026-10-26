# Nightly run

The scheduled session starts each night with a clean context, does the lead search itself (short), and hands each
chosen lead to its own build agent. Every turn re-reads the whole conversation, so one long conversation gets more
expensive with every step: split this way, each lead pays only for its own steps, and the leads are built in
parallel. Every extra agent also costs its own start (instructions and tools), so no agent for small jobs.

Nobody is watching: never ask questions, never send an email, never contact a business. The only outputs are
Gmail drafts and commits to this repo.

## You, the coordinator: few, short turns
If the scheduled prompt still speaks of a separate search agent, this file wins: do the search yourself.

1. `cd` to the repo (normally `/home/user/marketing-outreach`; it must be among the session's sources, a fresh
   clone cannot push), then `git checkout -q main && git pull -q origin main && bash scripts/setup_session.sh`.
   Do not read other files yourself: the agents read what they need.
   - The night's `<date>` is today in Italy: `TZ=Europe/Rome date +%F` (what the scripts use by default). The
     night starts on the previous day in UTC, so use this one everywhere below and give it to every build agent.
   - A `FAIL` line or no `GOOGLE_MAPS_API_KEY`: write `runs/<date>/summary.md` with the reason, commit, push, stop.
   - A `WARN ... use /usr/bin/python3.X` line: tell every agent to use that path instead of `python3`.
   - No Gmail secrets: the drafts become `.eml` files by themselves (`finish_lead.py`) and the leads are not
     recorded as drafted; say so in the summary.
2. **Search yourself**: read only the sections "Lean context" and "Step 1" of `skills/website-rebuilder/SKILL.md`
   and do Step 1: `find_leads.py next --pairs 4`, two or three web searches per pair, one `check` per pair with
   the businesses' own websites; repeat `next` until at least two candidates have alive_pct >= 55 and
   site_score >= 4, at most 12 pairs; still nothing, `pick --pairs 4` once. Then `find_leads.py show` and one
   `peek.py` image of the best old sites, and choose at most 3 leads: alive (prefer alive_pct >= 85), clearly old
   site, real content to work with, no red flags in the reviews. `mark` every candidate you looked at and
   rejected (skipped, excluded or retry, with the reason). Never try to get around a captcha.
3. No leads: go to 5. Otherwise start **one build agent per lead, all in the same message** (Agent tool,
   general-purpose) so they run in parallel (at most 3), each with the prompt below, the night's date and that
   lead's line `{"place_id": "...", "name": "...", "town": "...", "url": "...", "slug": "short-kebab-name"}`.
   Wait for all.
4. If a build agent failed or stopped early, do not redo its work yourself: list it in the summary.
5. Write `runs/<date>/summary.md` in Italian (template below), then
   `git add leads runs && git commit -qm "Notte <date>: <n> bozze" && git push -q origin main`.
   Network error: retry with backoff. Rejected because `main` moved: `git pull --rebase -q origin main`, push
   again. A 403 from the git proxy: do not retry or look for other ways to publish; say the push was refused.
6. Send a push notification with 2-3 lines (how many drafts, for whom, what to check before sending) and end with
   the same lines in Italian.

### Build agent prompt
> Build one lead for tonight's Lead Rebuilder run. Repo: /home/user/marketing-outreach. Date: <date>.
> Lead: <the JSON line>. Read skills/website-rebuilder/SKILL.md (skip Step 1) and do steps 2 to 6 for this lead,
> then write report.md. Pass `--date <date>` to every prepare_lead.py and finish_lead.py command (the night
> crosses midnight in UTC). Other leads are being built at the same time in this session: start every command
> with `cd` to an absolute path, work only in runs/<date>/<slug>/, and do not commit or push. If the site turns
> out blocked or unusable, `mark` the lead (retry or skipped, with the reason) and stop. Answer with at most 8 lines:
> name | town | Google rating (count), newest review | recipient or "email non trovata" | attachments and size |
> CONFIRM items | problems, or "BLOCCATO: <reason>".

### summary.md template
```
# Notte del <date>
**Bozze create: <n>.** Nessuna email inviata, nessuna attività contattata.
## Bozze
- **<name>**, <town>: <rating> su <count> recensioni, ultima <date>. A: <email | email non trovata>.
  Allegati: <...>. Da controllare: <CONFIRM>. Dettagli in `<slug>/report.md`.
## Ricerca
<pairs searched>; scartati: <name: reason; ...>
## Problemi
<anything that went wrong, improvements to make; or "nessuno">
```

Rules for the night:
- Drafts only. Do not use any tool that sends mail. Do not post, call or message anyone.
- Do not change the skill, the scripts or `vendor/` during a nightly run; note improvements in the summary instead.
- Spend the time on design quality, not on more leads. Never more than 3 leads.
