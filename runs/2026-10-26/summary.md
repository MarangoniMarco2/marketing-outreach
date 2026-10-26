# Notte del 26 ottobre 2026 (prova completa)

**Bozze create: 1.** Nessuna email inviata, nessuna attività contattata.

## Bozza
**Studio Dentistico Dott.ssa Giovanna Nadia Pavin**, Bassano del Grappa (viale XI Febbraio 42/44)
- Google: 4,6 su 13 recensioni; la più recente del 4 luglio 2026, Nicoletta M., 5 stelle: "Frequento questo
  studio da più di 30 anni, la dottoressa Nadia è sempre stata accogliente e attenta al sorriso mio e della mia
  famiglia."
- Destinatario: contatti@pavin.it (dal sito).
- Allegati: card PRIMA/DOPO (card.jpg) e GIF dello scroll da telefono (scroll-mobile.gif). Bozza 5,0 MB.
- Perché: tutto il sito è una sola immagine GIF con la scritta "sito in costruzione": Google non legge i testi,
  dal telefono è minuscolo, il numero non si chiama con un tocco.
- La pagina nuova: direzione "Colour chapters" nei loro colori (blu del logo e ocra), il loro slogan
  "È questione di batticuore", le 21 cure in 5 schede con "Chiedi" che prepara la mail, "aperti adesso"
  dagli orari Google, tre recensioni Google citate parola per parola, foto di Bassano da Wikimedia Commons.
- **Da controllare prima di inviare (CONFIRM):** partita IVA mancante nel footer; le etichette
  "Tutti / Bambini / Adulti" accanto alle cure sono mie; nessuna foto vera dello studio (solo foto di Bassano).
- Dettagli in `studio-pavin/report.md`.

## Giri fatti (12 coppie, cursore 9 → 21)
Tre `pick --pairs 4`: dopo i primi due c'era un solo candidato con alive ≥ 55% e site_score ≥ 5, quindi
terzo giro fino al limite di 12 coppie. Solo Pavin ha superato la soglia.

## Candidati scartati
- **Studio dentistico Perin** (Bassano, 4,6, alive 85%): sito vecchio (WordPress 4.5) ma già responsive, con
  foto vere e buoni testi: il prima/dopo non convincerebbe. `skipped`.
- **Centro Chirurgico Odontoiatrico Gaspari** (Torri di Quartesolo, 4,1): una recensione descrive il dottore
  come brusco e un'altra attacca chi recensisce male; sito con foto stock. `skipped`.
- **Bulato Antonio** serramenti (Camisano Vicentino, 2,2): recensioni recenti di clienti molto scontenti. `excluded`.
- Lo script ha segnato `retry` da solo 8 siti dietro protezione anti-bot (4 studi dentistici di Bassano,
  Tendaggi Ruber, Carrozzeria San Nicola, Centro Medico Met, Poliambulatorio SS. Trinità) e scartato le catene
  (DentalPro, Bludental, Clinica Dentale, Centro di medicina, F.lli Capitanio).

## Problemi e miglioramenti da fare (non toccati stanotte)
- `inspect.mjs` non parte da root: Chrome chiede `--no-sandbox`. Stanotte ho usato `CHROME_PATH` verso un piccolo
  wrapper nella scratchpad che aggiunge `--no-sandbox`. Conviene che `setup_session.sh` crei questo wrapper (o
  che `cdp.mjs` aggiunga `--no-sandbox` quando gira come root).
- Molti siti segnati `retry` per anti-bot in una notte (8 in una notte): vale la pena controllare che il rilevamento in
  `score_sites.py` non dia falsi positivi (per esempio banner cookie o pagine con reCAPTCHA solo nei moduli).
- L'effetto "tendina" (`.shutter[data-reveal]`) sulle foto grandi a volte non si apre in tempo nelle schermate a
  pagina intera: l'ho tolto dalle foto. Utile una nota nella skill.
- Pochi lead buoni a 12 coppie: forse alzare il limite o allargare i settori in `leads/targets.json`.

---

# Prima prova del 26 ottobre 2026 (ricostruita)

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
