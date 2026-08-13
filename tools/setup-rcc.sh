#!/usr/bin/env bash
# Assemble the RCC runtime folder from:
#   1. the public RCC kit (OPENGL32.dll shim, OSMESA32.dll, content, shaders,
#      VC++ runtimes) from github.com/tp-link-extender/RCCService
#   2. your own RCCService binary (Legacy.tar on main / tools/legacy/)
#   3. the portable wine build (tools/legacy/wine.tar.xz) if present
# Then launch RCCService under wine (or use system wine) listening for SOAP
# on 64989. Xvfb runtime bundle (tools/legacy/xvfb-runtime.tar.xz) is used as
# a fallback display if wine's null graphics driver is not enough.
set -e
cd "$(dirname "$0")/.."

RUNTIME="${RCC_RUNTIME:-/tmp/rcc-runtime}"
LEGACY="tools/legacy"
KIT_URL="https://codeload.github.com/tp-link-extender/RCCService/tar.gz/refs/heads/main"
KIT_TAR="/tmp/rcc-kit.tar.gz"
KIT_DIR="/tmp/rcc-kit"
WINE_DIR="/tmp/wine"
WINE_TAR=""
SOAP_PORT="${RCC_SOAP_PORT:-64989}"

log() { echo "[rcc] $*"; }

mkdir -p "$LEGACY"

# ---------------------------------------------------------------- kit ----
if [ ! -d "$KIT_DIR" ]; then
    log "downloading RCC kit ($KIT_URL)"
    curl -sL -o "$KIT_TAR" "$KIT_URL"
    tar xzf "$KIT_TAR" -C /tmp
    mv /tmp/RCCService-main/RCCService "$KIT_DIR"
fi
mkdir -p "$RUNTIME"
cp -rn "$KIT_DIR"/. "$RUNTIME"/

# -------------------------------------------------------- user's exe ----
if [ ! -f "$LEGACY/0.285.0.49012.exe" ] && [ -f Legacy.tar ]; then
    log "extracting Legacy.tar -> tools/legacy/"
    tar -xf Legacy.tar -C "$LEGACY"
fi
if [ -f "$LEGACY/0.285.0.49012.exe" ]; then
    cp -f "$LEGACY/0.285.0.49012.exe" "$RUNTIME/"
    [ -f "$LEGACY/OSMESA32.dll" ] && cp -f "$LEGACY/OSMESA32.dll" "$RUNTIME/"
else
    log "WARNING: no 0.285.0.49012.exe found (put Legacy.tar at repo root or in tools/legacy/)"
fi

# fmod.dll import alias + site settings
cp -f "$RUNTIME/fmodex.dll" "$RUNTIME/fmod.dll" 2>/dev/null || true
cat > "$RUNTIME/AppSettings.xml" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<Settings>
	<ContentFolder>content</ContentFolder>
	<BaseUrl>http://127.0.0.1:8080</BaseUrl>
</Settings>
EOF

# --------------------------------------------------------------- wine ----
WINE_BIN=""
if [ -f "$LEGACY/wine.tar.xz" ] && [ ! -x "$WINE_DIR/bin/wine" ]; then
    log "extracting portable wine build"
    rm -rf "$WINE_DIR" && mkdir -p "$WINE_DIR"
    tar -xJf "$LEGACY/wine.tar.xz" -C "$WINE_DIR" --strip-components=1
fi
if [ -x "$WINE_DIR/bin/wine" ]; then
    WINE_BIN="$WINE_DIR/bin/wine"
    export PATH="$WINE_DIR/bin:$PATH"
    log "using portable wine at $WINE_DIR"
elif command -v wine >/dev/null 2>&1; then
    WINE_BIN="$(command -v wine)"
    log "using system wine ($WINE_BIN)"
else
    log "no wine found! install wine, or run the fetch-runtime workflow /"
    log "drop a portable wine build at tools/legacy/wine.tar.xz"
    exit 1
fi

# ------------------------------------------------------------- prefix ----
PREFIX="${WINEPREFIX:-/tmp/rcc-wineprefix}"
export WINEPREFIX="$PREFIX"
export WINEDLLOVERRIDES="mscoree,mshtml=;opengl32=n;msvcr90=n;msvcp110=n;msvcr110=n"
if [ ! -d "$PREFIX/drive_c" ]; then
    log "initializing wine prefix (headless, null graphics driver)"
    DISPLAY= wineboot --init -u 2>/dev/null || true
    "$WINE_BIN" reg add "HKCU\\Software\\Wine\\Drivers" /v Graphics /d null /f 2>/dev/null || true
fi

# optional Xvfb fallback bundle
if [ -f "$LEGACY/xvfb-runtime.tar.xz" ] && [ ! -x /tmp/xvfb/usr/bin/Xvfb ]; then
    log "extracting xvfb runtime bundle"
    mkdir -p /tmp/xvfb && tar -xJf "$LEGACY/xvfb-runtime.tar.xz" -C /tmp/xvfb
fi

# ------------------------------------------------------------- launch ----
cd "$RUNTIME"
if ! curl -s -o /dev/null "http://127.0.0.1:$SOAP_PORT/" 2>/dev/null; then
    if [ -x /tmp/xvfb/usr/bin/Xvfb ]; then
        log "starting Xvfb (fallback display)"
        /tmp/xvfb/usr/bin/Xvfb :97 -screen 0 1024x768x24 >/tmp/xvfb.log 2>&1 &
        export DISPLAY=:97
    else
        unset DISPLAY
    fi
    log "launching RCCService 0.285 under wine (SOAP port $SOAP_PORT)"
    nohup "$WINE_BIN" 0.285.0.49012.exe -Console > /tmp/rcc.log 2>&1 &
    echo $! > /tmp/rcc.pid
    # wait for the SOAP listener
    for i in $(seq 1 60); do
        sleep 1
        if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$SOAP_PORT/" 2>/dev/null; then
            log "RCC SOAP listener is up on :$SOAP_PORT (log: /tmp/rcc.log)"
            break
        fi
    done
else
    log "RCC already listening on :$SOAP_PORT"
fi

log "done. Now set rcc_soap=http://127.0.0.1:$SOAP_PORT, rcc_mode=wine,"
log "rcc_enabled=true in config.json and (re)start python3 server.py."
