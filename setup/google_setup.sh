#!/usr/bin/env bash
# Lead Rebuilder: configura Google Cloud in un colpo solo.
#   - crea un progetto tuo (o riusa quello creato la volta prima)
#   - collega la fatturazione, attiva Places API (New) e Gmail API
#   - crea la chiave Google Maps limitata a Places
#   - imposta la schermata di consenso come "Interna" (Google Workspace)
#   - ti guida nella creazione del client OAuth (unico passo a mano) e ottiene il refresh token Gmail
#   - prova Places e Gmail (crea e cancella subito una bozza di prova)
#   - stampa i 4 valori da incollare nei Network secrets dell'ambiente Claude
#
# Da eseguire in Google Cloud Shell: https://shell.cloud.google.com
#   bash google_setup.sh
# Per usare un progetto esistente in cui sei Proprietario:  PROJECT=id-del-progetto bash google_setup.sh
set -uo pipefail

say()  { printf '\n\033[1;33m==> %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m    OK\033[0m %s\n' "$*"; }
warn() { printf '\033[1;35m    ATTENZIONE\033[0m %s\n' "$*"; }
die()  { printf '\n\033[1;31mERRORE:\033[0m %s\n\n' "$*"; exit 1; }

STATE="$HOME/.lead-rebuilder-project"
EMAIL=$(gcloud config get-value account 2>/dev/null)
[ -n "$EMAIL" ] || die "Nessun account Google attivo: apri questo script da Google Cloud Shell (https://shell.cloud.google.com)."
say "Account Google: $EMAIL"

# ---------- 1. Progetto ----------
ORG=$(gcloud organizations list --format='value(name)' 2>/dev/null | head -1); ORG=${ORG#organizations/}
if [ -z "${PROJECT:-}" ] && [ -f "$STATE" ]; then PROJECT=$(cat "$STATE"); fi
PROJECT=${PROJECT:-lead-rebuilder-$(date +%m%d%H%M)}
if gcloud projects describe "$PROJECT" >/dev/null 2>&1; then
  ok "uso il progetto $PROJECT"
else
  say "Creo il progetto $PROJECT${ORG:+ (organizzazione $ORG)}"
  gcloud projects create "$PROJECT" --name="Lead Rebuilder" ${ORG:+--organization=$ORG} || die "Il tuo account non puo creare progetti Google Cloud.
  - Se sei l'amministratore di Google Workspace: apri https://console.cloud.google.com/iam-admin/iam?organizationId=$ORG
    e dai al tuo utente i ruoli 'Autore progetto' (Project Creator) e 'Utente account di fatturazione', poi rilancia lo script.
  - Altrimenti chiedili all'amministratore, oppure rilancia con un progetto in cui sei Proprietario:
    PROJECT=id-del-progetto bash google_setup.sh"
fi
echo "$PROJECT" > "$STATE"
gcloud config set project "$PROJECT" >/dev/null 2>&1

# ---------- 2. Fatturazione ----------
say "Fatturazione"
if [ "$(gcloud billing projects describe "$PROJECT" --format='value(billingEnabled)' 2>/dev/null)" = "True" ]; then
  ok "gia collegata"
else
  mapfile -t ACCS < <(gcloud billing accounts list --filter='open=true' --format='value(name,displayName)' 2>/dev/null)
  [ ${#ACCS[@]} -gt 0 ] || die "Non trovo account di fatturazione utilizzabili.
  Creane uno qui (serve una carta; Places API ha una quota gratuita mensile): https://console.cloud.google.com/billing/create
  poi rilancia lo script."
  if [ ${#ACCS[@]} -eq 1 ]; then CHOICE=1; else
    i=1; for a in "${ACCS[@]}"; do echo "  $i) $a"; i=$((i+1)); done
    read -rp "  Quale account di fatturazione uso? (numero) " CHOICE
  fi
  ACC=$(echo "${ACCS[$((CHOICE-1))]}" | awk '{print $1}'); ACC=${ACC#billingAccounts/}
  gcloud billing projects link "$PROJECT" --billing-account="$ACC" >/dev/null || die "Non riesco a collegare la fatturazione $ACC: ti serve il ruolo 'Utente account di fatturazione' su quell'account."
  ok "collegata ($ACC)"
fi

# ---------- 3. API ----------
say "Attivo Places API (New) e Gmail API (puo richiedere un minuto)"
gcloud services enable places.googleapis.com gmail.googleapis.com apikeys.googleapis.com iap.googleapis.com --project "$PROJECT" \
  || die "Non riesco ad attivare le API: controlla di essere Proprietario o Editor del progetto $PROJECT."
ok "API attive"

# ---------- 4. Chiave Google Maps ----------
say "Chiave Google Maps"
KEY_LABEL="Lead Rebuilder Places"
KEY_NAME=$(gcloud services api-keys list --project "$PROJECT" --filter="displayName='$KEY_LABEL'" --format='value(name)' 2>/dev/null | head -1)
if [ -z "$KEY_NAME" ]; then
  gcloud services api-keys create --project "$PROJECT" --display-name="$KEY_LABEL" \
    --api-target=service=places.googleapis.com >/dev/null 2>&1 || die "Non riesco a creare la chiave API."
  KEY_NAME=$(gcloud services api-keys list --project "$PROJECT" --filter="displayName='$KEY_LABEL'" --format='value(name)' | head -1)
fi
MAPS_KEY=$(gcloud services api-keys get-key-string "$KEY_NAME" --format='value(keyString)')
[ -n "$MAPS_KEY" ] || die "Chiave creata ma non riesco a leggerla."
ok "chiave pronta (limitata a Places API)"

# ---------- 5. Schermata di consenso ----------
say "Schermata di consenso OAuth"
if [ -n "$ORG" ]; then
  if [ -n "$(gcloud iap oauth-brands list --project "$PROJECT" --format='value(name)' 2>/dev/null)" ]; then
    ok "gia presente"
  elif gcloud iap oauth-brands create --project "$PROJECT" --application_title="Lead Rebuilder" --support_email="$EMAIL" >/dev/null 2>&1; then
    ok "creata come Interna (il token non scade)"
  else
    warn "non sono riuscito a crearla da qui. Aprila e impostala a mano come 'Interno':"
    echo "    https://console.cloud.google.com/apis/credentials/consent?project=$PROJECT"
    read -rp "    Premi Invio quando hai salvato... " _
  fi
else
  warn "il tuo account non e in un'organizzazione Google Workspace: la schermata si puo fare solo 'Esterna'."
  echo "    1) Aprila: https://console.cloud.google.com/apis/credentials/consent?project=$PROJECT"
  echo "    2) Tipo utente 'Esterno', nome app 'Lead Rebuilder', la tua email, salva."
  echo "    3) Poi clicca 'Pubblica app' (altrimenti il token scade dopo 7 giorni)."
  read -rp "    Premi Invio quando hai finito... " _
fi

# ---------- 6. Client OAuth (unico passo a mano) ----------
# Google shows a client secret only once, so keep it in Cloud Shell (private home, mode 600) for re-runs.
OAUTH_FILE="$HOME/.lead-rebuilder-oauth"
CLIENT_ID=""; CLIENT_SECRET=""
if [ -f "$OAUTH_FILE" ]; then
  . "$OAUTH_FILE"
  say "Client OAuth: uso quello salvato la volta scorsa (${CLIENT_ID:0:12}...)"
  read -rp "    Va bene? [S/n] " REUSE
  case "$REUSE" in n|N) CLIENT_ID=""; CLIENT_SECRET="";; esac
fi
if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
  say "Client OAuth: questo passo va fatto a mano (Google non lo permette da script)"
  cat <<EOF
    1) Apri:  https://console.cloud.google.com/apis/credentials/oauthclient?project=$PROJECT
    2) Tipo di applicazione: "App desktop"     Nome: "Lead Rebuilder"     poi "Crea"
       (se il client esiste gia: aprilo e clicca "Aggiungi secret" per averne uno nuovo)
    3) Copia "ID client" e "Client secret" e incollali qui sotto.
EOF
  read -rp  "    ID client: " CLIENT_ID
  read -rsp "    Client secret (non si vede mentre incolli): " CLIENT_SECRET; echo
  CLIENT_ID=$(echo "$CLIENT_ID" | tr -d '[:space:]'); CLIENT_SECRET=$(echo "$CLIENT_SECRET" | tr -d '[:space:]')
  [ -n "$CLIENT_ID" ] && [ -n "$CLIENT_SECRET" ] || die "ID client o secret vuoti."
  ( umask 077; printf 'CLIENT_ID=%q\nCLIENT_SECRET=%q\n' "$CLIENT_ID" "$CLIENT_SECRET" > "$OAUTH_FILE" )
  ok "salvato in $OAUTH_FILE (solo nella tua Cloud Shell)"
fi

# ---------- 7. Refresh token Gmail + prova ----------
say "Autorizzazione Gmail (permesso: solo creare bozze)"
PY=$(mktemp)
cat > "$PY" <<'PYEOF'
import base64, hashlib, json, os, secrets, sys, urllib.error, urllib.parse, urllib.request
cid, sec = os.environ['CLIENT_ID'], os.environ['CLIENT_SECRET']
redirect = 'http://localhost:8080'
def err(s): sys.stderr.write(s); sys.stderr.flush()  # flush: the prompt must show before the paste
def call(req, fatal=True):
    try:
        return json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400]
        if fatal:
            err(f'\n    Errore Google {e.code}: {body}\n'); sys.exit(1)
        return {'_error': body}

tok = None
for attempt in range(1, 4):
    verifier = secrets.token_urlsafe(64)  # PKCE, recommended by Google for desktop clients
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).decode().rstrip('=')
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode({
        'client_id': cid, 'redirect_uri': redirect, 'response_type': 'code', 'access_type': 'offline',
        'prompt': 'consent', 'scope': 'https://www.googleapis.com/auth/gmail.compose',
        'code_challenge': challenge, 'code_challenge_method': 'S256'})
    err(f'\n    Tentativo {attempt} di 3. Fai questi passaggi di seguito, il codice vale pochi minuti.\n')
    err('\n    1) Apri questo link NUOVO nel browser, scegli il tuo account e consenti:\n\n' + url + '\n\n')
    err('    2) Alla fine il browser mostra "Impossibile raggiungere il sito": e normale.\n')
    err('       Copia TUTTO l\'indirizzo dalla barra del browser (inizia con http://localhost:8080/?) e incollalo qui.\n\n')
    err('    Indirizzo: ')
    # drop bracketed-paste markers some terminals add around pasted text
    pasted = sys.stdin.readline().replace('\x1b[200~', '').replace('\x1b[201~', '').strip()
    code = urllib.parse.parse_qs(urllib.parse.urlparse(pasted).query).get('code', [pasted])[0]
    tok = call(urllib.request.Request('https://oauth2.googleapis.com/token', urllib.parse.urlencode({
        'code': code, 'client_id': cid, 'client_secret': sec, 'redirect_uri': redirect,
        'grant_type': 'authorization_code', 'code_verifier': verifier}).encode()), fatal=False)
    if 'refresh_token' in tok: break
    reason = tok.get('_error', 'manca il refresh token')
    if 'invalid_client' in reason:
        err('\n    ID client o Client secret non validi. Rilancia lo script e rispondi "n" per inserirli di nuovo.\n'); sys.exit(1)
    err(f'\n    Non riuscito ({reason.strip()[:160]}). Ripetiamo con un link nuovo: non riusare il vecchio indirizzo.\n')
else:
    err('\n    Tre tentativi falliti. Controlla di usare lo stesso account Google e rilancia lo script.\n'); sys.exit(1)
auth = {'Authorization': 'Bearer ' + tok['access_token'], 'Content-Type': 'application/json'}
raw = base64.urlsafe_b64encode('Subject: Prova Lead Rebuilder\r\n\r\nBozza di prova, viene cancellata subito.'.encode()).decode()
d = call(urllib.request.Request('https://gmail.googleapis.com/gmail/v1/users/me/drafts',
                                json.dumps({'message': {'raw': raw}}).encode(), auth))
try:  # DELETE answers with an empty body
    urllib.request.urlopen(urllib.request.Request(f"https://gmail.googleapis.com/gmail/v1/users/me/drafts/{d['id']}",
                                                  method='DELETE', headers=auth), timeout=60)
except urllib.error.HTTPError as e:
    err(f'    (la bozza di prova non si e cancellata da sola, eliminala a mano: {e.code})\n')
err('    OK bozza di prova creata e cancellata: Gmail funziona.\n')
print(tok['refresh_token'])
PYEOF
REFRESH=$(CLIENT_ID="$CLIENT_ID" CLIENT_SECRET="$CLIENT_SECRET" python3 "$PY") || { rm -f "$PY"; die "Autorizzazione Gmail non riuscita (vedi sopra). Puoi rilanciare lo script: riparte da qui."; }
rm -f "$PY"

# ---------- 8. Prova Google Maps ----------
say "Prova Google Maps (una chiave nuova puo metterci un minuto ad attivarsi)"
for i in 1 2 3 4 5 6 7 8; do
  RES=$(curl -s -X POST https://places.googleapis.com/v1/places:searchText \
    -H "Content-Type: application/json" -H "X-Goog-Api-Key: $MAPS_KEY" -H "X-Goog-FieldMask: places.displayName" \
    -d '{"textQuery":"autofficina Vicenza","languageCode":"it"}' |
    python3 -c 'import json,sys; d=json.load(sys.stdin); print("ERR " + d["error"].get("message","")[:120] if "error" in d else len(d.get("places",[])))')
  case "$RES" in ERR*) sleep 15;; *) break;; esac
done
case "$RES" in ERR*) warn "Places non risponde ancora ($RES). Di solito si sistema da sola entro pochi minuti.";;
                *) ok "Google Maps funziona: trovate $RES autofficine a Vicenza";; esac

# ---------- 9. Risultato ----------
cat <<EOF

=====================================================================
 FATTO. Copia questi 4 valori nei Network secrets dell'ambiente Claude
 (barra del titolo della sessione -> menu dell'ambiente -> Edit).
 Nome a sinistra dell'uguale, valore a destra. Non incollarli in chat.
=====================================================================
GOOGLE_MAPS_API_KEY=$MAPS_KEY
GMAIL_CLIENT_ID=$CLIENT_ID
GMAIL_CLIENT_SECRET=$CLIENT_SECRET
GMAIL_REFRESH_TOKEN=$REFRESH
=====================================================================
 Progetto Google Cloud: $PROJECT
 Quando hai copiato tutto, scrivi  clear  per pulire lo schermo.
EOF
