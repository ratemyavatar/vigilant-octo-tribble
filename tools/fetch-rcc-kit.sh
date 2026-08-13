#!/usr/bin/env bash
# Fetch + assemble the RCC kit (proprietary renderer + content + patches).
# Uses only github.com (codeload + api.github.com with gh auth), no apt.
# Result: /tmp/pekora-rcc/ ready to run under wine.
set -e
TOKEN="${GH_TOKEN:-$(gh auth token 2>/dev/null || true)}"
cd /tmp

echo "[1/4] Pekora RCC kit (exe + content + scripts)"
[ -f pekora-rcc.7z ] || curl -sL -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github.raw" \
    -o pekora-rcc.7z "https://api.github.com/repos/tooblewtf/pekora/contents/RCCService/RCCService.7z"
rm -rf pekora-rcc
python3 -c "import py7zr" 2>/dev/null || pip install --break-system-packages -q py7zr
python3 - <<'EOF'
import py7zr
with py7zr.SevenZipFile('/tmp/pekora-rcc.7z') as z:
    z.extractall('/tmp/pekora-rcc')
EOF

echo "[2/4] fmod.dll (C++ API build the exe imports)"
curl -sL -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github.raw" \
    -o pekora-rcc/fmod.dll \
    "https://api.github.com/repos/ThugShaker3D/Karma-2016-Client/contents/CoreScriptConverter2/tool/win32/fmod.dll"

echo "[3/4] core scripts (Karma 2016 client dump)"
mkdir -p pekora-rcc/content/scripts
curl -s "https://api.github.com/repos/ThugShaker3D/Karma-2016-Client/git/trees/main?recursive=1" \
    -H "Authorization: Bearer $TOKEN" | python3 -c "
import json, sys
d = json.load(sys.stdin)
for t in d.get('tree', []):
    p = t.get('path', '')
    if t.get('type') == 'blob' and p.startswith('content/scripts/'):
        print(p)
" > /tmp/scriptlist.txt
cat /tmp/scriptlist.txt | xargs -P 6 -I{} sh -c '
    mkdir -p "/tmp/pekora-rcc/$(dirname "{}")"
    curl -sL -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github.raw" \
        -o "/tmp/pekora-rcc/{}" "https://api.github.com/repos/ThugShaker3D/Karma-2016-Client/contents/{}"
'

echo "[4/4] rewrite URLs + trust-patch the exe"
grep -rlE "www\.(roblox|projex|pekora)\.zip|roblox\.com" pekora-rcc/content/ 2>/dev/null | while read f; do
    sed -i -E 's|https?://www\.roblox\.com|http://127.0.0.1:8080|g;
               s|https?://www\.projex\.zip|http://127.0.0.1:8080|g;
               s|https?://www\.pekora\.zip|http://127.0.0.1:8080|g' "$f"
done
cat > pekora-rcc/AppSettings.xml <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Settings>
	<ContentFolder>content</ContentFolder>
	<BaseUrl>http://127.0.0.1:8080</BaseUrl>
</Settings>
EOF
# The shipped RCCService.exe needs the real fmod + works with wine's null GL.
python3 "$(dirname "$0")/patch-trust.py" pekora-rcc/RCCService.exe \
    pekora-rcc/RCCService.trustpatched285.exe || true
# Also patch the smaller (BatchJobEx) variant that ships alongside.
cp pekora-rcc/RCCService.trustpatched285.exe pekora-rcc/RCCService.trustpatched.exe 2>/dev/null || true
echo "Kit ready in /tmp/pekora-rcc"
echo "Run:  cd /tmp/pekora-rcc && /tmp/wine/bin/wine RCCService.trustpatched285.exe -Console -port:64989"
