#!/usr/bin/env bash
# Get a cloud session ready for the website rebuilder. Safe to run more than once; prints one line per check.
# Playwright must be exactly 1.63.0: it matches the Chromium preinstalled in /opt/pw-browsers.
# Never run "playwright install" (it would download a browser the other tools do not find).
want=1.63.0
fail=0

has_pw() { "$1" -c "import PIL; from importlib.metadata import version as v; raise SystemExit(v('playwright') != '$want')" 2>/dev/null; }

if ! has_pw python3; then
  python3 -m pip --version >/dev/null 2>&1 || python3 -m ensurepip --upgrade >/dev/null 2>&1
  python3 -m pip install -q "playwright==$want" pillow 2>/dev/null ||
    python3 -m pip install -q --break-system-packages "playwright==$want" pillow
fi
if has_pw python3; then
  echo "OK   python3 $(python3 -c 'import platform; print(platform.python_version())'): playwright $want, pillow"
else
  alt=$(for p in /usr/bin/python3.*; do [[ $p =~ python3\.[0-9]+$ ]] && has_pw "$p" && echo "$p" && break; done)
  if [ -n "$alt" ]; then
    echo "WARN python3 has no playwright $want: use $alt instead of python3 in every command of this run"
  else
    echo "FAIL no Python with playwright $want and pillow (pip install did not work)"; fail=1
  fi
fi

major=$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)
if [ "$major" -ge 22 ]; then echo "OK   node $(node --version)"; else echo "FAIL node 22+ needed by taste-skill (found: $(node --version 2>&1))"; fail=1; fi

# taste-skill looks for Chrome in the usual places: point /usr/bin/chromium at Playwright's Chromium
chrome=$(ls -d /opt/pw-browsers/chromium-*/chrome-linux64/chrome 2>/dev/null | head -1)
[ -e /usr/bin/chromium ] || { [ -n "$chrome" ] && ln -s "$chrome" /usr/bin/chromium; }
if [ -e /usr/bin/chromium ]; then echo "OK   chromium for taste-skill"; else echo "FAIL no Chromium found for taste-skill"; fail=1; fi

if command -v ffmpeg >/dev/null; then echo "OK   ffmpeg"; else echo "FAIL ffmpeg missing (make_gif.py needs it)"; fail=1; fi

# names only, never the values
for v in GOOGLE_MAPS_API_KEY GMAIL_CLIENT_ID GMAIL_CLIENT_SECRET GMAIL_REFRESH_TOKEN; do
  if [ -n "${!v}" ]; then echo "OK   $v is set"; else echo "MISS $v"; fi
done
[ -f config/signature.txt ] && echo "OK   config/signature.txt" || echo "MISS config/signature.txt (drafts go out without signature)"
exit $fail
