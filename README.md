# Lead Rebuilder

Ogni notte trova 2-3 attività di Vicenza e provincia che su Google Maps sono attive ma hanno un sito vecchio,
ne ridisegna **solo la home page** con le regole di design di tasteskill v2, e al mattino trovi in Gmail
**una bozza per ciascuna**, con allegati la card PRIMA/DOPO e una GIF della pagina nuova. Le bozze le rivedi e
le invii tu: niente parte da solo.

Basato su [claude-website-rebuilder](https://github.com/pantheonmarketing/claude-website-rebuilder) (MIT,
Jonny West) e [taste-skill](https://github.com/Leonxlnx/taste-skill) v2 (MIT, Leonxlnx), copiata in
`vendor/taste-skill` (versione in `vendor/taste-skill/VERSION`).

## Come funziona una notte
1. `scripts/find_leads.py` prende i prossimi settori e comuni da `leads/targets.json`, cerca su Google Maps,
   scarta le attività già viste (`leads/done.jsonl`), dà un punteggio ai siti e controlla le recensioni.
2. Per ogni lead scelto: raccoglie contenuti e foto dal sito vecchio, prende orari e recensioni da Google,
   disegna e costruisce la home con la taste-skill, la verifica a 1440, 768 e 390 px.
3. Prepara la card PRIMA/DOPO (`pitch_card.py`), le GIF dello scroll (`make_gif.py`) e il testo della mail
   (`templates/email_it.txt`).
4. Crea la bozza in Gmail con gli allegati (`gmail_draft.py`) e salva tutto in `runs/<data>/`.

Le istruzioni complete sono in `skills/website-rebuilder/SKILL.md` e `NIGHTLY.md`.

## Configurazione (una volta sola)

Tutte le chiavi vanno nelle impostazioni dell'ambiente cloud (menu dell'ambiente nella barra del titolo della
sessione → **Edit** → campo **Environment variables**, una riga NOME=valore per chiave). Non nei Network secrets
(quelli chiedono un dominio e servono ad altro). Mai nel repo, mai in chat.

### Il modo veloce: lo script
Apri [Google Cloud Shell](https://shell.cloud.google.com), carica `setup/google_setup.sh` (menu ⋮ → Carica) e
lancia `bash google_setup.sh`. Crea un progetto tuo, attiva le API, crea la chiave Maps, ti guida nell'unico passo a
mano (il client OAuth) e alla fine stampa i 4 valori da mettere nelle variabili d'ambiente. Si può rilanciare: riparte dal
progetto creato la prima volta. I passi qui sotto sono la stessa cosa fatta a mano.

### 1. Google Cloud
1. Vai su [console.cloud.google.com](https://console.cloud.google.com), crea un progetto (es. "lead-rebuilder")
   e collega un account di fatturazione (Places API lo richiede; c'è una quota gratuita mensile).
2. **API e servizi → Libreria**: attiva **Places API (New)** e **Gmail API**.

### 2. Chiave Google Maps → `GOOGLE_MAPS_API_KEY`
**Credenziali → Crea credenziali → Chiave API**. Poi "Limita chiave" → limita a **Places API (New)**.

### 3. Gmail (per creare le bozze con allegati) → `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET`, `GMAIL_REFRESH_TOKEN`
1. **Schermata consenso OAuth**: tipo utente **Interno** (disponibile con Google Workspace; così il token non
   scade dopo 7 giorni). Nome app a piacere, salva.
2. **Credenziali → Crea credenziali → ID client OAuth → Applicazione web**. In "URI di reindirizzamento
   autorizzati" aggiungi `https://developers.google.com/oauthplayground`. Copia ID client e segreto.
3. Apri [OAuth Playground](https://developers.google.com/oauthplayground), clicca l'ingranaggio in alto a destra
   → spunta **Use your own OAuth credentials** → incolla ID e segreto.
4. In "Step 1" scrivi lo scope `https://www.googleapis.com/auth/gmail.compose` → **Authorize APIs** → accedi con
   l'account da cui vuoi mandare le mail.
5. "Step 2" → **Exchange authorization code for tokens** → copia il **Refresh token**.

Lo scope `gmail.compose` permette di creare bozze; lo script `gmail_draft.py` usa solo la creazione di bozze.

### 4. Firma
Copia `config/signature.example.txt` in `config/signature.txt` con i tuoi dati: viene aggiunta in fondo a ogni
bozza.

### 5. Settori e comuni
Modifica `leads/targets.json` quando vuoi. Per riprendere un'attività scartata, togli la sua riga da
`leads/done.jsonl`.

## Uso a mano
In una sessione di Claude Code nel repo: "Usa la skill website-rebuilder su https://sito-vecchio.it".

## File
| Percorso | Cosa |
|---|---|
| `skills/website-rebuilder/SKILL.md` | La skill: trova, verifica, raccoglie, disegna, prepara la mail |
| `NIGHTLY.md` | Cosa fa la sessione notturna, passo per passo |
| `scripts/places.py` | Google Maps: ricerca, recensioni, orari, punteggio "attività viva" |
| `scripts/find_leads.py` | Sceglie i lead della notte e tiene il registro di quelli già fatti |
| `scripts/scrape_site.py` | Testi, link, immagini ed email dal sito vecchio |
| `scripts/score_sites.py`, `alive_check.py` | Quanto è vecchio un sito; segnali di attività |
| `scripts/shoot.py` | Screenshot desktop e mobile, controllo overflow ed errori |
| `scripts/pitch_card.py` | Card PRIMA/DOPO (`--lang it`) |
| `scripts/make_gif.py` | GIF dello scroll della pagina nuova |
| `scripts/gmail_draft.py` | Bozza Gmail con allegati (solo bozze) |
| `templates/email_it.txt` | Modello della mail |
| `vendor/taste-skill/` | tasteskill v2 (regole di design, ispettore, archivi immagini) |
| `leads/` | Settori e comuni, cursore, registro dei lead |
| `runs/<data>/` | Risultati di ogni notte |
