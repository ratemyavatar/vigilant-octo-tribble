#!/usr/bin/env bash
# Start the ROBLOX site (+ RCC backend) in one shot.
# Works on a Codespace, a Linux VPS, or any machine with python3.
# If tools/legacy/RCCService.exe exists it runs the real renderer under
# Wine/Xvfb; otherwise it falls back to the SOAP-compatible mock.
set -e
cd "$(dirname "$0")"

# --- render backend ------------------------------------------------------
if [ -f tools/legacy/RCCService.exe ]; then
    echo "[start] real RCCService.exe found -> wine mode"
    python3 - <<'EOF'
import json
c = json.load(open("config.json"))
c["rcc_enabled"] = True
c["rcc_mode"] = "wine"
json.dump(c, open("config.json", "w"), indent=2)
EOF
    if command -v wine >/dev/null 2>&1; then
        # Xvfb gives Wine a display; RCC keeps running in the background.
        (xvfb-run -a wine tools/legacy/RCCService.exe -console -verbose \
            > data/rcc.log 2>&1 &)
        echo "[start] RCCService launched under Wine (log: data/rcc.log)"
    else
        echo "[start] wine not installed! Run the devcontainer postCreate, or:"
        echo "  sudo dpkg --add-architecture i386 && sudo apt-get update"
        echo "  sudo apt-get install -y wine wine32 xvfb"
        exit 1
    fi
else
    echo "[start] no tools/legacy/RCCService.exe -> mock renderer"
    python3 - <<'EOF'
import json
c = json.load(open("config.json"))
c["rcc_enabled"] = True
c["rcc_mode"] = "mock"
json.dump(c, open("config.json", "w"), indent=2)
EOF
    (python3 tools/rcc_mock.py 64989 > data/rcc.log 2>&1 &)
    echo "[start] mock RCC on :64989 (log: data/rcc.log)"
fi

# --- site -----------------------------------------------------------------
sleep 1
echo "[start] site on :8080  (status: /rcc)"
exec python3 server.py
