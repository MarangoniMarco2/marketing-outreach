# Nightly run

What the scheduled session does every night. It works alone: nobody is watching, so it never asks questions,
never sends an email and never contacts a business. Its only outputs are Gmail drafts and commits to this repo.

1. **Setup.** `cd` into the repo, `git pull origin main`, then the "Session setup" block of
   `skills/website-rebuilder/SKILL.md`. Check the secrets by name only (never print their values):
   `GOOGLE_MAPS_API_KEY`, `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`.
   - No Google Maps key: stop here and write `runs/<date>/summary.md` saying the key is missing.
   - No Gmail secrets: do the work, create `.eml` files with `--dry-run`, and say so in the summary.
   - If `config/signature.txt` does not exist, say so in the summary (drafts go out without signature).
2. **Find.** `python3 scripts/find_leads.py pick --pairs 3`. If fewer than two candidates have
   `alive_pct >= 55` and a `site_score >= 5`, run `pick --pairs 3` once more (at most 9 pairs per night).
3. **Choose 2 or 3.** Screenshot the best candidates' old home pages (desktop and phone) and look at them.
   Prefer `alive_pct >= 85`. `mark` every candidate you looked at and rejected (`skipped`, with the reason) so it
   is not picked again. Never more than 3 per night.
4. **Build each one,** steps 2 to 7 of `skills/website-rebuilder/SKILL.md`, one business at a time, start to
   finish (draft created and business marked `drafted`) before starting the next. Two complete leads beat three
   half-built ones: if the night is running long, stop after the current one.
5. **Summary.** Write `runs/<date>/summary.md` in Italian: for each draft, the business, town, Google rating and
   newest review, the recipient (or "email non trovata"), the attachments, the CONFIRM items, and anything that
   went wrong. List the rejected candidates with one line each.
6. **Save.** `git add leads runs && git commit -m "Notte <date>: <n> bozze"` and `git push origin main`
   (this repo's main branch is the pipeline's memory: `leads/done.jsonl` and `leads/state.json` must persist).
   Retry the push with backoff on network errors.
7. **Finish** with a short Italian message: how many drafts, for whom, and what needs the user's attention
   before sending.

Rules for the night:
- Drafts only. Do not use any tool that sends mail. Do not post, call or message anyone.
- Do not change the skill, the scripts or `vendor/` during a nightly run; note improvements in the summary instead.
- Spend the time on design quality, not on more leads.
