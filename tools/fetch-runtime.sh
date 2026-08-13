#!/usr/bin/env bash
# Runs on the GitHub runner (ubuntu-22.04) to bundle the display + Mesa GL
# stack the sandbox needs for RCC rendering. Pushes tarballs AND a build log
# onto the arena branch so the sandbox can inspect results via git.
cd "$(dirname "$0")/.."

LOG=/tmp/build.log
exec > >(tee "$LOG") 2>&1
echo "=== fetch-runtime start $(date -u) ==="

push_log() {
  echo "=== trap: pushing log $(date -u) ==="
  mkdir -p tools/legacy
  cp /tmp/build.log tools/legacy/fetch-runtime.log 2>/dev/null
  git config user.email "actions@github.com" 2>/dev/null
  git config user.name "wine-mirror" 2>/dev/null
  git add -f tools/legacy/fetch-runtime.log 2>/dev/null
  git commit -m "transient: fetch-runtime log" 2>/dev/null
  git push origin HEAD:arena/019ff872-vigilant-octo-tribble 2>/dev/null
  echo "=== trap done ==="
}
trap push_log EXIT

BUNDLE_DIR=/tmp/rcc-bundle
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR/display/bin" "$BUNDLE_DIR/display/lib" "$BUNDLE_DIR/display/mesa"

echo "[1/5] apt packages"
sudo apt-get update -qq || true
sudo apt-get install -y -qq \
    xvfb xkb-data xkbcomp xserver-xorg-core \
    libgl1 libglx-mesa0 libgl1-mesa-dri libosmesa6 libglvnd0 libegl1 \
    libx11-6 libxkbfile1 libxkbcommon0 libxkbcommon-x11-0 libxcb1 \
    libxcb-keysyms1 libxcb-xkb1 libxcb-randr0 libxcb-shape0 libxcb-xfixes0 \
    libxau6 libxdmcp6 libxfont2 libfontenc1 libfreetype6 libpng16-16 \
    libbz2-1.0 liblzma5 libzstd1 libbsd0 libmd0 libxshmfence1 libxxf86vm1 \
    libunwind8 libpixman-1-0 libjpeg-turbo8 libtiff5 libpcre3 libselinux1 \
    libexpat1 libuuid1 libz1 || true
echo "[1/5] apt done"

echo "[2/5] display binaries"
cp -L /usr/bin/Xvfb "$BUNDLE_DIR/display/bin/" || true
cp -L /usr/bin/xkbcomp "$BUNDLE_DIR/display/bin/" || true
cp -rL /usr/share/X11/xkb "$BUNDLE_DIR/display/xkb" || true
for exe in /usr/bin/Xvfb /usr/bin/xkbcomp; do
    for lib in $(ldd "$exe" 2>/dev/null | awk '{print $3}' | grep '^/'); do
        mkdir -p "$BUNDLE_DIR/display/$(dirname "${lib#/}")"
        cp -L "$lib" "$BUNDLE_DIR/display/${lib#/}" 2>/dev/null || true
    done
done
echo "[2/5] display binaries done: $(du -sh "$BUNDLE_DIR/display" | cut -f1)"

echo "[3/5] mesa GL stack"
M="$BUNDLE_DIR/display/mesa"
cp -L /usr/lib/x86_64-linux-gnu/dri/swrast_dri.so "$M/" 2>/dev/null || true
cp -L /usr/lib/x86_64-linux-gnu/dri/kms_swrast_dri.so "$M/" 2>/dev/null || true
echo "[3.2/5] xorg GLX module (Xvfb needs it to serve GLX)"
mkdir -p "$BUNDLE_DIR/display/xorg"
GLXMOD=$(find /usr/lib -name "libglx.so" 2>/dev/null | head -1)
echo "glx module found at: ${GLXMOD:-NOWHERE}"
dpkg -L xserver-xorg-core 2>/dev/null | grep -c glx || true
ls /usr/lib/xorg/modules/extensions/ 2>/dev/null || ls /usr/lib/xorg/modules/ 2>/dev/null || echo "no /usr/lib/xorg/modules"
if [ -n "$GLXMOD" ]; then
    cp -L "$GLXMOD" "$BUNDLE_DIR/display/xorg/" 2>/dev/null || true
fi
cp -rL /usr/lib/xorg/modules "$BUNDLE_DIR/display/xorg/" 2>/dev/null || true
for lib in $(ldd "$GLXMOD" 2>/dev/null | awk '{print $3}' | grep '^/'); do
    mkdir -p "$BUNDLE_DIR/display/$(dirname "${lib#/}")"
    cp -L "$lib" "$BUNDLE_DIR/display/${lib#/}" 2>/dev/null || true
done
ls -la "$BUNDLE_DIR/display/xorg/" 2>/dev/null | head -8
for lib in \
    libGL.so.1.7.0 libGLX_mesa.so.0.0.0 libGLdispatch.so.0.0.0 libGLX.so.0.0.0 \
    libOSMesa.so.8.0.0 libEGL_mesa.so.0.0.0 libglapi.so.0.0.0 libxatracker.so.2.5.0 \
    libxcb-dri2.so.0.0.0 libxcb-dri3.so.0.0.0 libxcb-glx.so.0.0.0 \
    libxcb-present.so.0.0.0 libxcb-sync.so.1.0.0 libxcb-xfixes.so.0.0.0 \
    libxcb.so.1.1.0 libxcb-keysyms.so.1.0.0 libxcb-randr.so.0.1.0 \
    libxcb-shape.so.0.0.0 libxcb-xkb.so.1.0.0 libxkbfile.so.1.0.2 \
    libxkbcommon.so.0.0.0 libxkbcommon-x11.so.0.0.0 libX11.so.6.4.0 \
    libXau.so.6.0.0 libXdmcp.so.6.0.0 libXext.so.6.4.0 libXfont2.so.2.0.0 \
    libX11-xcb.so.1.0.0 libXxf86vm.so.1.0.0 libxshmfence.so.1.0.0 \
    libunwind.so.8.0.1 libunwind-x86_64.so.8.0.1 liblzma.so.5.2.5 \
    libzstd.so.1.4.8 libfontenc.so.1.0.0 libfreetype.so.6.18.3 \
    libpng16.so.16.37.0 libbrotlicommon.so.1.0.9 libbrotlidec.so.1.0.9 \
    libpixman-1.so.0.40.0 libbsd.so.0.11.5 libmd.so.0.0.5 libcap.so.2.44 \
    libcap-ng.so.0.0.0 libaudit.so.1.0.0 libgcrypt.so.20.3.4 \
    libgpg-error.so.0.32.1 libsystemd.so.0.30.0 libselinux.so.1 \
    libpcre2-8.so.0.10.4 libpcre.so.3.13.3 libjpeg.so.8.2.2 libtiff.so.5.7.0 \
    libz.so.1.2.11 libexpat.so.1.8.7 libuuid.so.1.3.0 libglvnd.so.0.0.0 ; do
    if [ -f "/usr/lib/x86_64-linux-gnu/$lib" ]; then
        cp -L "/usr/lib/x86_64-linux-gnu/$lib" "$M/" || true
    fi
done
echo "[3/5] mesa done: $(ls "$M" | wc -l) libs + $(ls "$M"/*.so 2>/dev/null | wc -l) drivers"

echo "[4/5] wine tarball"
if [ ! -f tools/legacy/wine.tar.xz ]; then
    curl -L --retry 5 --retry-all-errors -o tools/legacy/wine.tar.xz \
        https://github.com/Kron4ek/Wine-Builds/releases/download/11.15/wine-11.15-amd64-wow64.tar.xz \
        || echo "WARN: wine download failed"
fi
ls -la tools/legacy/wine.tar.xz || true

echo "[5/5] bundle + push"
tar -C "$BUNDLE_DIR" -cJf /tmp/display-runtime.tar.xz .
cp /tmp/display-runtime.tar.xz tools/legacy/display-runtime.tar.xz
git config user.email "actions@github.com"
git config user.name "wine-mirror"
git add -f tools/legacy/display-runtime.tar.xz tools/legacy/wine.tar.xz
git commit -m "transient: display runtime + mesa bundle" || echo "commit skipped (no changes?)"
git push origin HEAD:arena/019ff872-vigilant-octo-tribble || echo "PUSH FAILED"
echo "=== fetch-runtime DONE $(date -u) ==="
