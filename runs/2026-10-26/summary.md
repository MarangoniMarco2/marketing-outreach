# Notte del 2026-10-26
**Bozze create: 1.** Nessuna email inviata, nessuna attività contattata.
## Bozze
- **Studio dentistico Perin dott. Michele**, Bassano del Grappa: 4.6 su 22 recensioni, ultima 2026-08-08. A: studioperinmichele@libero.it.
  Allegati: card.jpg 0.2 MB, scroll-mobile.gif 3.4 MB, scroll-desktop.gif 1.6 MB (bozza 7.1 MB).
  Da controllare: scanner Cerec Omnicam ancora in uso (fonte: vecchia news); garanzia scritta sui lavori ancora offerta; chiusura del venerdì 15:30 (Maps) o 16:30 (vecchio sito), nella pagina c'è 15:30; foto della reception e del "relax" del 2017 circa, da confermare con lo staff attuale. Mail di circa 200 parole, leggermente oltre il target. Dettagli in `studio-perin/report.md`.
- **Studio Dentistico Pavin**, Bassano del Grappa: NON ricostruito. Era già in bozza da un run precedente di oggi (commit 58bb423, bozza Gmail a contatti@pavin.it già esistente), quindi nessuna seconda bozza. Dettagli in `studio-pavin/report.md`.
## Ricerca
fisioterapista Arzignano, marmista Sandrigo, autoscuola Breganze, carrozzeria Breganze. Il file dei candidati di oggi ne conteneva già 4 validi da controlli precedenti. Scartati: Bulato Antonio: 2.2 stelle, recensioni su lavori lasciati a metà; Centro Gaspari: sito già responsive, recensioni divise; autoscuolamarzi.wixsite.com: nessuna scheda Maps (retry); medicriab.it, fisiopoint.org, salutebenessere.vi.it: sito non abbastanza vecchio; misureriabilitativemoderne.it: HTTP 999 (blocco bot).
## Problemi
- La ricerca ha proposto un lead già "drafted" in leads/done.jsonl (Pavin): `find_leads.py show` dovrebbe escludere i lead già fatti. Miglioramento da fare nello script (non modificato stanotte).
- Perin: nessun video adatto nelle collezioni aperte (WARN); ritratti del team esclusi perché non verificabili.

# Giro di prova del 2026-10-26 (pomeriggio)
**Bozze create: 0.** Nessuna email inviata, nessuna attività contattata.
## Ricerca
12 coppie: impresa edile Montecchio Maggiore, palestra Thiene, lattoniere Altavilla Vicentina, ottico Lonigo, disinfestazione Rosà, ottico Valdagno, palestra Noventa Vicentina, tappezziere Noventa Vicentina, impresa edile Rosà, imbianchino Sandrigo, falegnameria Valdagno, autofficina Noventa Vicentina. Ripiego `pick`: gommista Valdagno, termoidraulica Sandrigo, autoscuola Dueville, centro estetico Cassola.
Scartati: Rossato & Figli (Valdagno): 3.7 su 6 recensioni, due 1 stella recenti su riparazioni non riuscite; Idro-Comm (Sandrigo): alive 45%, sito già responsive; Arredopiu (Noventa Vicentina): nessuna scheda Maps (retry); circa 20 siti scartati da `check` perché abbastanza moderni o non raggiungibili.
## Problemi
- 5 siti in errore 502 tramite proxy, mai valutati (tra cui otticacainelli.it e lazzariluciano.com, forse vecchi): da riprovare in un altro giro.
- Il percorso di output predefinito di `find_leads.py` puntava a runs/2026-10-27 (data UTC/locale?): l'agente ha passato `--out` a mano. Da correggere nello script.
- La zona attuale dà pochi siti vecchi: valutare di cambiare zona o categorie.
