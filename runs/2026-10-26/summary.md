# Prova del 26 ottobre 2026 (ricostruita)

La sessione di prova non ha potuto fare il push (il repo non era tra le sue sorgenti), quindi questo riepilogo è
ricostruito dal suo resoconto. I dati sono stati ricontrollati su Google Maps.

**Bozze create: 0.** Nessuna email inviata, nessuna attività contattata.

## Giri fatti (9 coppie, cursore 0 → 9)
idraulico Bassano del Grappa, centro estetico Valdagno, studio dentistico Sandrigo, autoscuola Marostica,
imbianchino Arzignano, serramenti Montecchio Maggiore, veterinario Thiene, palestra Bassano del Grappa,
tappezziere Lonigo.

## Candidati scartati
- **InKlima** (Bassano, alive 85%): buon lead, ma il sito è dietro il captcha di SiteGround. Senza testi e foto
  reali la pagina non si fa, e la protezione non va aggirata. Segnato `retry`: torna fra i candidati tra 30 giorni.
- **Autoscuola Agenzia Scaligera** (Marostica): sito dietro captcha SiteGround e recensioni piene di liti.
- **SATI 1967** (Bassano): alive 45%, ultime recensioni del 2021; anche questo sito è dietro captcha.
- **Flavia Estetica** (Valdagno): alive 45%, ultime recensioni del 2022.
- **Mrs.Sporty Bassano**: franchising, nessun sito proprio.
- **FirstFit Bassano**: catena; sito con punteggio 4, sotto la soglia.

## Problemi trovati e correzioni
- Push negato (403): le attività programmate ora girano in una sessione che ha il repo tra le sorgenti.
- `python3` di default (3.11) senza Playwright: nuovo `scripts/setup_session.sh` lo installa o indica il Python giusto.
- Captcha non segnalato: `score_sites.py` e `scrape_site.py` ora lo riconoscono; `find_leads.py` segna questi
  lead `retry` da solo.
- Franchising: `find_leads.py` scarta le catene (elenco `chains` in `leads/targets.json`, stesso sito per più sedi,
  pagina di una sede su un sito di rete).
- `candidates.json` sovrascritto a ogni giro: ora i giri della stessa notte si sommano.
