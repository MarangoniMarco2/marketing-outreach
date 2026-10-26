# Studio Dentistico Dott.ssa Giovanna Nadia Pavin (Bassano del Grappa)

## Dati Google
- Viale XI Febbraio 42/44, 36061 Bassano del Grappa. Tel. 0424 522262. Email dal sito: contatti@pavin.it
- Voto 4,6 su 13 recensioni. Ultima recensione: 4 luglio 2026 (Nicoletta M., 5 stelle). Alive 85%.
- Orari Google: lun-ven 8:30-19:30, sabato e domenica chiuso.
- Perché: il sito è un'unica GIF 888x909 con una mappa cliccabile e la scritta "sito in costruzione"; niente
  viewport, niente HTTPS, nessun testo leggibile da Google, numero non cliccabile. site_score 5.

## Design (tasteskill v2)
- Settore `health` (studio dentistico). `--keep palette`: blu notte #004263 e ocra #a49159 del loro logo e
  del riquadro del vecchio sito, più due azzurri presi dal loro sfondo.
- Direzione: **Colour chapters** (`colour-chapters`), seed 1735848449. Nessun redraw.
- Hero "Swatch column beside the view", intro "Statement tiles", cure "Day tabs, banded agenda" (le schede
  sono le 5 aree di cura invece dei giorni), recensioni "Quotation spread edge to edge", contatti "Address in
  display rows".
- Idea: sulla pagina, **lo slogan del loro vecchio sito, "È questione di batticuore"** (la paura che si
  scioglie, la gioia) diventa **il titolo e il filo dei capitoli di colore** nei colori del loro marchio.
- La cosa viva: "Aperti adesso / Chiusi, riapriamo ..." calcolato dagli orari Google (ora di Roma), e per
  ogni cura un pulsante "Chiedi" che apre una mail a contatti@pavin.it con oggetto e testo già scritti;
  il pulsante grande segue l'area scelta.
- Gate finale: lint 0 FAIL 0 WARN; inspect 0 FAIL a 1440, 768 e 390. WARN rimasti, difesi:
  10 dimensioni di testo (il footer con il nome a tutta larghezza e le righe dei contatti sono da blueprint),
  nessun video (cercato "Bassano del Grappa": nessuna clip adatta; c'è il lento movimento sulle foto),
  measure 96 caratteri (righe brevi della citazione distribuite a tutta larghezza), didascalia della foto
  grande a sinistra (è una didascalia).
- Critica ultimo giro (critique.md, sintetica): idea 7, composizione 7, tipografia 7, colore 8, immagini 6
  (nessuna foto loro), contenuto 7. Corretti al secondo giro: accento della "È" tagliato, linea dello scrim
  sulla foto, foto che non comparivano (effetto tendina tolto), citazione con parole attaccate, orari nei
  contatti. Ancora debole: niente foto dello studio vero.

## Cosa è vero, cosa è trovato
- Testi: l'introduzione è il loro testo del vecchio sito (trascritto dall'immagine), appena accorciato.
  Elenco delle 21 cure dal vecchio sito; le note di una riga sotto ogni cura sono spiegazioni generiche mie.
- Recensioni Google citate parola per parola: Vincenzo V. (ott 2022), Nicoletta M. (lug 2026), Maura P. (set 2024).
- Foto (tutte Wikimedia Commons, accreditate nel footer, nessuna presentata come dello studio):
  "Ponte Vecchio (Bassano del Grappa) 01" di Superchilum, CC BY-SA 4.0;
  "Ponte degli Alpini Bassano del Grappa 2007" di Patrick Denker, CC BY 2.0;
  "Bassano del Grappa Brenta 2" di Zairon, CC BY-SA 4.0;
  "Bassano del Grappa Abendstimmung" di Museshare, CC BY-SA 3.0;
  "Bassano del Grappa Vista Aerea" di Paolo Fiorese, CC BY-SA 4.0.
- Nessuna foto del sito vecchio usata: l'unica è il volto azzurrato dentro la GIF (sembra stock).

## CONFIRM
- Partita IVA da aggiungere nel footer (non trovata sul sito).
- Etichette "Tutti / Bambini / Adulti" accanto a ogni cura: scelte da me, da confermare.
- "21 cure": conteggio delle voci del vecchio sito (le voci sono 21).

## Bozza
- A: contatti@pavin.it. Oggetto: "Studio Pavin: un'anteprima del vostro nuovo sito".
- Allegati: card.jpg (260 KB), scroll-mobile.gif (3,4 MB). Totale bozza 5,0 MB. Draft id r-4427733477024737728.
- scroll-desktop.gif (3,7 MB) non allegata, resta in locale (non va nel repo).
