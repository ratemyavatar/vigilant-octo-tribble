#!/usr/bin/env bash
# Rebuild the full real-RCC stack in a fresh sandbox (no apt needed).
# What it does:
#   1. pulls wine wow64 + display/mesa runtime tarballs from the git branch
#   2. builds the glvnd EGL dispatcher (with X11 support) from source
#   3. sets up Xvfb (:97, +iglx) with software GL (llvmpipe)
#   4. fetches the Pekora RCC kit + fmod + core scripts from GitHub
#   5. trust-patches RCCService.exe
#   6. launches RCCService under wine (SOAP :64989)
# Requirements: python3, gcc, make, pip, git, curl, gh (auth)
set -e
cd "$(dirname "$0")/.."
export TOOLS="$(pwd)/tools"

echo "[1/6] extract runtimes from branch tarballs"
mkdir -p /tmp/wine /tmp/display
if [ ! -x /tmp/wine/bin/wine ]; then
    git show HEAD:tools/legacy/wine.tar.xz > /tmp/wine.tar.xz 2>/dev/null || true
    [ -f /tmp/wine.tar.xz ] || echo "WARN: wine.tar.xz not on branch - run the fetch-runtime workflow first"
    [ -f /tmp/wine.tar.xz ] && tar -xJf /tmp/wine.tar.xz -C /tmp/wine --strip-components=1
fi
if [ ! -d /tmp/display/display/mesa ]; then
    git show HEAD:tools/legacy/display-runtime.tar.xz > /tmp/display-runtime.tar.xz 2>/dev/null || true
    [ -f /tmp/display-runtime.tar.xz ] && tar -xJf /tmp/display-runtime.tar.xz -C /tmp/display
fi
MESA=/tmp/display/display/mesa
[ -d "$MESA" ] || { echo "missing mesa runtime"; exit 1; }

echo "[2/6] mesa dir fixups (symlinks, drop foreign glibc)"
cd "$MESA"
rm -f libc.so.6* libm.so.6* libpthread.so.0 libdl.so.2 librt.so.1 libstdc++* libgcc_s* ld-linux* 2>/dev/null || true
for f in lib*.so.*; do
    case "$f" in *.*.*.*|*.*.*) soname=$(echo "$f" | grep -oE '^lib[^.]+\.so\.[0-9]+') ;; *) continue ;; esac
    [ -n "$soname" ] && [ ! -e "$soname" ] && ln -sf "$f" "$soname"
done
sudo mkdir -p /usr/lib/x86_64-linux-gnu/dri
sudo cp -f swrast_dri.so kms_swrast_dri.so /usr/lib/x86_64-linux-gnu/dri/ 2>/dev/null || true

echo "[3/6] build glvnd EGL dispatcher with X11 (needed by wine's wgl)"
if [ ! -f "$MESA/libEGL.so.1.1.0" ] || ! strings "$MESA/libEGL.so.1.1.0" | grep -q EGL_EXT_platform_x11; then
    pip install --break-system-packages -q meson ninja py7zr 2>/dev/null || true
    cd /tmp
    [ -d libglvnd-1.7.0 ] || { curl -sL -o libglvnd.tar.gz https://codeload.github.com/NVIDIA/libglvnd/tar.gz/refs/tags/v1.7.0 && tar xzf libglvnd.tar.gz; }
    [ -d libX11-master ] || { curl -sL -o libX11.tar.gz https://codeload.github.com/mirror/libX11/tar.gz/refs/heads/master && tar xzf libX11.tar.gz; }
    mkdir -p /tmp/x11-include/X11 /tmp/x11-lib /tmp/bin
    cp libX11-master/include/X11/*.h /tmp/x11-include/X11/
    cat > /tmp/x11-include/X11/X.h <<'EOF'
#ifndef _X11_X_H_
#define _X11_X_H_
typedef unsigned long XID;
typedef XID Window; typedef XID Drawable; typedef XID Pixmap; typedef XID Colormap;
typedef unsigned long Mask; typedef unsigned long Atom; typedef unsigned long VisualID;
#define Bool int
#define Status int
#define True 1
#define False 0
#define None 0L
#define CopyFromParent 0L
#define InputOutput 1
#define InputOnly 2
#define Success 0
#define BadValue 2
#define BadWindow 3
#define BadMatch 8
#define BadDrawable 9
#define NoEventMask 0L
#define KeyPressMask (1L<<0)
#define KeyReleaseMask (1L<<1)
#define ButtonPressMask (1L<<2)
#define ButtonReleaseMask (1L<<3)
#define PointerMotionMask (1L<<6)
#define ExposureMask (1L<<15)
#define CWX (1<<0)
#define CWY (1<<1)
#define CWWidth (1<<2)
#define CWHeight (1<<3)
#define CWBorderWidth (1<<4)
#define LSBFirst 0
#define MSBFirst 1
typedef unsigned char KeyCode;
#endif
EOF
    cat > /tmp/x11-include/X11/Xfuncproto.h <<'EOF'
#ifndef _X11_XFUNCPROTO_H_
#define _X11_XFUNCPROTO_H_
#ifdef __cplusplus
#define _XFUNCPROTOBEGIN extern "C" {
#define _XFUNCPROTOEND }
#else
#define _XFUNCPROTOBEGIN
#define _XFUNCPROTOEND
#endif
#define _Xconst const
#define _X_SENTINEL(x)
#define _X_ATTRIBUTE_PRINTF(x,y)
#define _X_DEPRECATED
#define _X_NORETURN
#define _X_UNUSED
#define _X_EXPORT
#define _X_HIDDEN
#define _X_INTERNAL
#define _X_COLD
#define _X_HOT
#define _X_PURE
#define _X_NOTUSED
#define _X_ALIGNED(n)
#define _X_NONNULL(args)
#define _X_RESTRICT_KYWD restrict
#define _X_DEPRECATED_MSG(msg)
#endif
EOF
    cat > /tmp/x11-include/X11/Xosdefs.h <<'EOF'
#ifndef _X11_XOSDEFS_H_
#define _X11_XOSDEFS_H_
#define X_NOT_POSIX
#define X_NOT_STDC_ENV
#define NeedFunctionPrototypes 1
#define NeedVarargsPrototypes 1
#endif
EOF
    cat > /tmp/x11-include/X11/Xutil.h <<'EOF'
#ifndef _X11_XUTIL_H_
#define _X11_XUTIL_H_
#include <X11/Xlib.h>
typedef struct {
    Visual *visual;
    VisualID visualid;
    int screen;
    int depth;
    int class_;
    unsigned long red_mask, green_mask, blue_mask;
    int colormap_size;
    int bits_per_rgb;
} XVisualInfo;
extern XVisualInfo *XGetVisualInfo(Display*, long, XVisualInfo*, int*);
extern void XFree(void*);
#define VisualNoMask 0x0
#define VisualIDMask 0x1
#define VisualScreenMask 0x2
#define VisualDepthMask 0x4
#define VisualClassMask 0x8
#define VisualRedMaskMask 0x10
#define VisualGreenMaskMask 0x20
#define VisualBlueMaskMask 0x40
#define VisualColormapSizeMask 0x80
#define VisualBitsPerRGBMask 0x100
#define VisualAllMask 0x1FF
#endif
EOF
    cat > /tmp/x11.pc <<'EOF'
prefix=/tmp/x11-prefix
exec_prefix=${prefix}
includedir=/tmp/x11-include
libdir=/tmp/x11-lib
Name: X11
Description: X11 library headers
Version: 1.8.7
Cflags: -I${includedir}
Libs: -L${libdir} -lX11
EOF
    cat > /tmp/xext.pc <<'EOF'
prefix=/tmp/x11-prefix
includedir=/tmp/x11-include
libdir=/tmp/x11-lib
Name: Xext
Description: X11 extensions library
Version: 1.3.5
Cflags: -I${includedir}
Libs: -L${libdir} -lXext
EOF
    cat > /tmp/glproto.pc <<'EOF'
prefix=/tmp/x11-prefix
includedir=/tmp/x11-include
Name: glproto
Description: GL extension headers
Version: 1.4.17
Cflags: -I${includedir}
EOF
    cp "$TOOLS/pkg-config-shim.py" /tmp/bin/pkg-config 2>/dev/null && chmod +x /tmp/bin/pkg-config
    ln -sf "$MESA/libX11.so.6" /tmp/x11-lib/libX11.so
    ln -sf "$MESA/libXext.so.6" /tmp/x11-lib/libXext.so
    cd /tmp/libglvnd-1.7.0
    rm -rf build-x11
    PATH=/tmp/bin:$PATH PKG_CONFIG_PATH=/tmp meson setup build-x11 -Dglx=disabled -Dx11=enabled -Degl=true -Dheaders=false -Dhgl=false -Dasm=disabled
    PATH=/tmp/bin:$PATH PKG_CONFIG_PATH=/tmp ninja -C build-x11 src/EGL/libEGL.so.1.1.0 src/GLdispatch/libGLdispatch.so.0.0.0
    cp build-x11/src/EGL/libEGL.so.1.1.0 "$MESA/"
    cp build-x11/src/GLdispatch/libGLdispatch.so.0.0.0 "$MESA/"
fi
cd "$MESA"
ln -sf libEGL.so.1.1.0 libEGL.so.1
ln -sf libGLdispatch.so.0.0.0 libGLdispatch.so.0

echo "[4/6] glvnd vendor configs"
for d in /usr/local/etc/glvnd/egl_vendor.d /etc/glvnd/egl_vendor.d /usr/share/glvnd/egl_vendor.d; do
    sudo mkdir -p "$d"
    sudo tee "$d/50_mesa.json" > /dev/null <<EOF
{
  "file_format_version" : "1.0.0",
  "ICD" : {
    "library_path" : "$MESA/libEGL_mesa.so.0"
  }
}
EOF
done

echo "[5/6] xkb data for Xvfb"
sudo cp /tmp/display/display/bin/xkbcomp /usr/bin/xkbcomp 2>/dev/null || true
sudo chmod +x /usr/bin/xkbcomp 2>/dev/null || true
sudo rm -rf /usr/share/X11/xkb
sudo cp -r /tmp/display/display/xkb /usr/share/X11/xkb

echo "[6/6] launch Xvfb + RCC (SOAP 64989)"
pkill -x Xvfb 2>/dev/null || true
(LD_LIBRARY_PATH="$MESA" /tmp/display/display/bin/Xvfb :97 -screen 0 1024x768x24 +extension GLX +iglx > /tmp/xvfb.log 2>&1 &)
sleep 4
export WINEPREFIX=/tmp/rcc-prefix
mkdir -p /tmp/rcc-prefix
export WINE=/tmp/wine/bin/wine
export WINEDLLOVERRIDES="mscoree,mshtml=;opengl32=b"
export DISPLAY=:97
export LD_LIBRARY_PATH="$MESA"
export LIBGL_ALWAYS_SOFTWARE=1
export LP_NUM_THREADS=1
"$WINE" wineboot -u >/dev/null 2>&1 || true
if [ ! -f /tmp/pekora-rcc/RCCService.trustpatched285.exe ]; then
    echo "WARN: /tmp/pekora-rcc not set up - run tools/fetch-rcc-kit.sh first"
fi
echo "Ready. Start RCC with:"
echo "  cd /tmp/pekora-rcc && /tmp/wine/bin/wine RCCService.trustpatched285.exe -Console -port:64989"
