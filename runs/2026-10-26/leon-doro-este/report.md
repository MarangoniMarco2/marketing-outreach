# Leon d'Oro, Este (2026-10-26)

## Business and Google data
- Albergo Ristorante Leon d'Oro, Viale Fiume 20, 35042 Este (PD). Tel. 0429 602949, fax 0429 3072, prenotazioni@leondoroeste.it, P.IVA 04185510288.
- Google: 4.4 (531 recensioni), newest review 2026-09-06, alive 95%. Hours (Google): Mon-Sat 12:00-14:00, 19:30-21:30, Sunday closed.
- Why: busy, well reviewed, family run (4th generation, famiglia Rubini), old site is a fixed 800px table layout from the 2000s: on a phone it shows the desktop page shrunk, with unreadable text (before/home-mobile.jpg). Reviews are positive (one 4-star mentions rooms needing maintenance, no lift, no parking nearby: not quoted).
- Inventory: home, dove-dormire, dove-siamo (prepare_lead) plus camere, ristorante, bike hotel, ospedale and prenotazione pages read by a plain fetch for facts (no captcha anywhere).

## Design (tasteskill v2)
- Sector `hospitality` (albergo + ristorante). Direction dealt: **page-is-the-object** ("The page is the object"), seed 1310041444. Type Big Shoulders / Public Sans; palette "Newsprint and brass" proportions kept, colours taken from the subject: dark green ink/field (shutters and the green lettering of the old postcard), brass yellow accent (the yellow facade). No redraws. Dealt "Coast" photographs not used (wrong subject).
- Idea: on this page, the old postcard "Albergo - Ristorante Leon d'Oro" becomes the stationery the whole page is printed on: the hero card with the postcard tipped in, the scalloped menu sheet, the booking coupon, and the back of the postcard as the footer.
- Live thing: the booking coupon builds the email the old site asks for (name, phone, arrival, departure, adults, children, "arriviamo in bici") as a mailto to prenotazioni@; plus "Siete aperti adesso?" line from the real Google hours (Europe/Rome).
- Sections: hero card, Storia (letter sheet + Porta Vecchia), Cucina (pinned side + full menu sheet, no prices), Camere (amenities + Miriam D. review), In bici (full-bleed photo + 6 slips: E2 70 km, Transeuganea 60 km, Atestina Superbike, Team Este Bike, terme, città vicine), Recensioni (rating 4,4 / 531 + Alessandra D. review verbatim), Prenota (coupon), Dove siamo (footer postcard).
- Motion: pinned story (sticky kitchen column beside the scrolling menu), staggered text entrances, hover/press feedback, slow drift on the hero photo; reduced-motion fallback.
- Gate: lint 0 FAIL; inspect 0 FAIL at 1440/768/390. Remaining WARN: 14 font sizes, no video (no clip found on the open collections for Colli Euganei), margins 40/56 at 1440, ragged edges.
- Last critique (2 rounds): idea 7.5, composition 7, type 7, colour 7.5, imagery 6.5 (own photos are low-res, 420-960px), content 8, overall about 7.3. Weakest: small own photos (facade 420px), long phone page.

## Real, found, drawn
- Real (from their old site): old postcard of the albergo, facade photo, old photo of via Roma Este, "Este in fiore" piazza, sentiero sui Colli at sunset.
- Found: "Mura castello dei Carraresi 01" (hero) and "Torre civica di Porta Vecchia Este 01", both Nicola Quirico, CC BY-SA 4.0, via Wikimedia Commons; credited in the footer imprint.
- Nothing drawn or AI generated. Menu items, dishes, amenities, bike info, hours all taken from their site / Google. No prices on the page.

## CONFIRM
- Rights of the Este/Colli photos on the old site (via Roma, Este in fiore, sentiero): theirs or taken from the web?
- Menu shown as "una proposta tipo" from the old site: still current? Friday fish menu still on?
- Room amenities (aria condizionata, TV SAT, wi-fi, telefono) and mezza pensione / pensione completa still offered.
- Team Este Bike collaboration and meeting times (8:30 estate, 9:00 inverno) still valid.
- Left out on purpose: hospital page (old site says Este hospital 400 m and also the new Monselice hospital, contradictory), "parcheggio pubblico adiacente" (a review says no parking nearby), outdated Valdastico text, fax shown in footer only.
- Not wired: the coupon opens the visitor's email app (mailto), no form backend.


## Bozza
- A: prenotazioni@leondoroeste.it. Oggetto: "Leon d'Oro: un'anteprima del vostro nuovo sito".
- Allegati: card.jpg (0.3 MB), scroll-mobile.gif (3.2 MB). Draft id r-3414500685381727817.
