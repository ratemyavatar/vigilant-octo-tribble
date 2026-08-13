#!/usr/bin/env bash
# Runs on the GitHub runner (ubuntu-22.04) to bundle everything the sandbox
# needs for a real RCC render farm:
#   - Xvfb + xkbcomp + xkeyboard-config + lib deps (display)
#   - Mesa GL + dri drivers (llvmpipe software GL) + OSMesa (render)
#   - portable wine wow64 (already have it, but keep it reproducible)
# Then pushes the tarballs onto the arena branch for the sandbox to fetch.
set -e
cd "$(dirname "$0")/.."

BUNDLE_DIR=/tmp/rcc-bundle
rm -rf "$BUNDLE_DIR" && mkdir -p "$BUNDLE_DIR"

echo "[1/5] apt packages"
sudo apt-get update -qq
sudo apt-get install -y -qq xvfb xkb-data xkbcomp \
    libgl1 libglx-mesa0 libgl1-mesa-dri libosmesa6 \
    libx11-6 libxkbfile1 libxkbcommon0 libxcb1 libxcb-keysyms1 \
    libxcb-xkb1 libxcb-randr0 libxcb-shape0 libxcb-xfixes0 \
    libxau6 libxdmcp6 libxfont2 libfontenc1 libfreetype6 \
    libpng16-16 libbz2-1.0 liblzma5 libzstd1 libbsd0 libmd0 \
    libxshmfence1 libxxf86vm1 libglvnd0 libegl1 >/dev/null

echo "[2/5] copy display stack"
mkdir -p "$BUNDLE_DIR/display/bin" "$BUNDLE_DIR/display/lib"
cp -L /usr/bin/Xvfb "$BUNDLE_DIR/display/bin/"
cp -L /usr/bin/xkbcomp "$BUNDLE_DIR/display/bin/"
cp -rL /usr/share/X11/xkb "$BUNDLE_DIR/display/xkb"
for exe in Xvfb xkbcomp; do
    for lib in $(ldd /usr/bin/$exe | awk '{print $3}' | grep '^/'); do
        cp -L --parents "$lib" "$BUNDLE_DIR/display/"
    done
done

echo "[3/5] copy mesa GL stack"
mkdir -p "$BUNDLE_DIR/display/lib/x86_64-linux-gnu/dri"
cp -L /usr/lib/x86_64-linux-gnu/dri/swrast_dri.so "$BUNDLE_DIR/display/lib/x86_64-linux-gnu/dri/" 2>/dev/null || true
cp -L /usr/lib/x86_64-linux-gnu/dri/kms_swrast_dri.so "$BUNDLE_DIR/display/lib/x86_64-linux-gnu/dri/" 2>/dev/null || true
for lib in \
    /usr/lib/x86_64-linux-gnu/libGL.so.1.7.0 \
    /usr/lib/x86_64-linux-gnu/libGLX_mesa.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libGLdispatch.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libGLX.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libOSMesa.so.8.0.0 \
    /usr/lib/x86_64-linux-gnu/libEGL_mesa.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libglapi.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libxatracker.so.2.5.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-dri2.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-dri3.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-glx.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-present.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-sync.so.1.0.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-xfixes.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libxcb.so.1.1.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-keysyms.so.1.0.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-randr.so.0.1.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-shape.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libxcb-xkb.so.1.0.0 \
    /usr/lib/x86_64-linux-gnu/libxkbfile.so.1.0.2 \
    /usr/lib/x86_64-linux-gnu/libxkbcommon.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libxkbcommon-x11.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libX11.so.6.4.0 \
    /usr/lib/x86_64-linux-gnu/libXau.so.6.0.0 \
    /usr/lib/x86_64-linux-gnu/libXdmcp.so.6.0.0 \
    /usr/lib/x86_64-linux-gnu/libXext.so.6.4.0 \
    /usr/lib/x86_64-linux-gnu/libXfont2.so.2.0.0 \
    /usr/lib/x86_64-linux-gnu/libX11-xcb.so.1.0.0 \
    /usr/lib/x86_64-linux-gnu/libXxf86vm.so.1.0.0 \
    /usr/lib/x86_64-linux-gnu/libxshmfence.so.1.0.0 \
    /usr/lib/x86_64-linux-gnu/libunwind.so.8.0.1 \
    /usr/lib/x86_64-linux-gnu/libunwind-x86_64.so.8.0.1 \
    /usr/lib/x86_64-linux-gnu/liblzma.so.5.2.5 \
    /usr/lib/x86_64-linux-gnu/libzstd.so.1.4.8 \
    /usr/lib/x86_64-linux-gnu/libfontenc.so.1.0.0 \
    /usr/lib/x86_64-linux-gnu/libfreetype.so.6.18.3 \
    /usr/lib/x86_64-linux-gnu/libpng16.so.16.37.0 \
    /usr/lib/x86_64-linux-gnu/libbrotlicommon.so.1.0.9 \
    /usr/lib/x86_64-linux-gnu/libbrotlidec.so.1.0.9 \
    /usr/lib/x86_64-linux-gnu/libpixman-1.so.0.40.0 \
    /usr/lib/x86_64-linux-gnu/libbsd.so.0.11.5 \
    /usr/lib/x86_64-linux-gnu/libmd.so.0.0.5 \
    /usr/lib/x86_64-linux-gnu/libcap.so.2.44 \
    /usr/lib/x86_64-linux-gnu/libcap-ng.so.0.0.0 \
    /usr/lib/x86_64-linux-gnu/libaudit.so.1.0.0 \
    /usr/lib/x86_64-linux-gnu/libgcrypt.so.20.3.4 \
    /usr/lib/x86_64-linux-gnu/libgpg-error.so.0.32.1 \
    /usr/lib/x86_64-linux-gnu/libsystemd.so.0.30.0 \
    /usr/lib/x86_64-linux-gnu/libselinux.so.1 \
    /usr/lib/x86_64-linux-gnu/libpcre2-8.so.0.10.4 \
    /usr/lib/x86_64-linux-gnu/libpcre.so.3.13.3 \
    /usr/lib/x86_64-linux-gnu/libjpeg.so.8.2.2 \
    /usr/lib/x86_64-linux-gnu/libtiff.so.5.7.0 \
    /usr/lib/x86_64-linux-gnu/libz.so.1.2.11 \
    /usr/lib/x86_64-linux-gnu/libexpat.so.1.8.7 \
    /usr/lib/x86_64-linux-gnu/libuuid.so.1.3.0 \
    /usr/lib/x86_64-linux-gnu/libglvnd.so.0.0.0 ; do
    if [ -f "$lib" ]; then
        cp -L "$lib" "$BUNDLE_DIR/display/lib/x86_64-linux-gnu/"
    fi
done

echo "[4/5] wine wow64 (idempotent)"
if [ ! -f /tmp/wine.tar.xz ]; then
    curl -L --retry 5 -o /tmp/wine.tar.xz \
        https://github.com/Kron4ek/Wine-Builds/releases/download/11.15/wine-11.15-amd64-wow64.tar.xz
fi

echo "[5/5] bundle + push onto the arena branch"
tar -C "$BUNDLE_DIR" -cJf /tmp/display-runtime.tar.xz .
mkdir -p tools/legacy
cp /tmp/wine.tar.xz tools/legacy/wine.tar.xz
cp /tmp/display-runtime.tar.xz tools/legacy/display-runtime.tar.xz
git config user.email "actions@github.com"
git config user.name "wine-mirror"
git add -f tools/legacy/wine.tar.xz tools/legacy/display-runtime.tar.xz
git commit -m "transient: display runtime + wine mirror"
git push origin HEAD:arena/019ff872-vigilant-octo-tribble
echo "DONE"
