#!/usr/bin/env python3
"""Mock RCCService SOAP endpoint for local testing (no proprietary binaries).

Implements just enough of the RCCService SOAP API (HelloWorld, OpenJobEx,
CloseJob, GetAllJobsEx) for rcc.py to talk to, and mimics the real render
flow: when a render.lua job arrives it generates a placeholder PNG and POSTs
it to the site's /thumbs/... URL exactly the way the real RCCService does
after ThumbnailGenerator:Click.

This is NOT a renderer. Swap it for a real RCCService.exe (under Wine or on
another machine) and the site works unchanged — rcc.py speaks the same SOAP.

Run: python3 tools/rcc_mock.py [port]   (default 64989)
"""
import base64
import json
import re
import struct
import sys
import time
import urllib.request
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

LISTEN = "0.0.0.0"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 64989


# ---------------------------------------------------------------- tiny PNG --
def _chunk(tag: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + tag
        + data
        + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    )


def _make_png(width: int, height: int, rows: list) -> bytes:
    raw = b"".join(b"\x00" + row for row in rows)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(raw, 6))
        + _chunk(b"IEND", b"")
    )


def _hsl(h: float, s: float, l: float) -> tuple:
    def hue(p, q, t):
        t = ((t % 1.0) + 1.0) % 1.0
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r, g, b = hue(p, q, h + 1 / 3), hue(p, q, h), hue(p, q, h - 1 / 3)
    return int(r * 255), int(g * 255), int(b * 255)


def _headshot_png(seed: int) -> bytes:
    """Fake 420x420 'headshot': gradient background + bust, hue keyed by id."""
    w = h = 420
    hue = (seed * 47) % 360 / 360.0
    bg_top = _hsl(hue, 0.45, 0.88)
    bg_bot = _hsl(hue, 0.55, 0.42)
    skin = _hsl((hue + 0.12) % 1.0, 0.52, 0.66)
    skin_dark = _hsl((hue + 0.12) % 1.0, 0.52, 0.52)
    rows = []
    for y in range(h):
        t = y / (h - 1)
        row = bytearray()
        for x in range(w):
            # head circle
            ddx, ddy = x - 210, y - 158
            in_head = ddx * ddx + ddy * ddy <= 88 * 88
            # shoulders ellipse
            sx, sy = (x - 210) / 158.0, (y - 430) / 210.0
            in_shoulders = (not in_head) and (sx * sx + sy * sy <= 1.0) and y >= 300
            if in_head:
                rgb = skin if (x + y) % 7 else skin_dark  # cheap shading dither
            elif in_shoulders:
                rgb = _hsl(hue, 0.35, 0.55)
            else:
                r = int(bg_top[0] + (bg_bot[0] - bg_top[0]) * t)
                g = int(bg_top[1] + (bg_bot[1] - bg_top[1]) * t)
                b = int(bg_top[2] + (bg_bot[2] - bg_top[2]) * t)
                rgb = (r, g, b)
            row += bytes(rgb)
        rows.append(bytes(row))
    return _make_png(w, h, rows)


# ---------------------------------------------------------------- SOAP ----
def _unescape_xml(s: str) -> str:
    return (
        s.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
    )


def _envelope(verb: str, result: str) -> bytes:
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'xmlns:xsd="http://www.w3.org/2001/XMLSchema" '
        'xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">'
        "<soap:Body>"
        + '<%sResponse xmlns="http://roblox.com/">' % verb
        + "<result>%s</result>" % result
        + "</%sResponse>" % verb
        + "</soap:Body></soap:Envelope>"
    )
    return xml.encode("utf-8")


def _render_from_lua(lua: str) -> None:
    """Mimic RCC running render.lua: find the postback URL and send a PNG."""
    m = re.search(r'https?://[^"\'\s]+/thumbs/(?:headshot|asset)\.ashx\?[^"\'\s]*', lua)
    if not m:
        print("  [mock] no /thumbs/ postback URL in script, skipping render")
        return
    url = m.group(0)
    uid = re.search(r"userId=(\d+)", url)
    aid = re.search(r"(?:^|[?&])id=(\d+)", url)
    seed = int(uid.group(1)) if uid else (int(aid.group(1)) if aid else int(time.time()))
    kind = "headshot" if "headshot" in url else "asset"
    png = _headshot_png(seed)
    payload = json.dumps(
        {
            "thumbnail": base64.b64encode(png).decode("ascii"),
            "id": seed,
            "userId": seed,
            "kind": kind,
        }
    ).encode("utf-8")
    print("  [mock] rendering -> POST %s (%d bytes)" % (url, len(png)))
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("  [mock] postback status %s" % resp.status)


class Handler(BaseHTTPRequestHandler):
    server_version = "RCCMock/0.1"

    def log_message(self, fmt, *args):  # keep stdout readable
        pass

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(
            b"RCCService mock listening (HelloWorld/OpenJobEx/CloseJob/GetAllJobsEx)\n"
            b"This is NOT the real RCCService.exe renderer.\n"
        )

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length).decode("utf-8", "replace")
        verb = re.search(r"<soap:Body>\s*<(\w+)", body)
        verb = verb.group(1) if verb else "Unknown"
        print("[mock] SOAP %s from %s" % (verb, self.client_address[0]))

        result = "false"
        if verb == "HelloWorld":
            result = "Hello, world!"
        elif verb == "OpenJobEx":
            job = re.search(r"<id>([^<]*)</id>", body)
            job_id = job.group(1) if job else "?"
            lua = ""
            idx = body.rfind("<script>")
            if idx >= 0:
                end = body.find("</script>", idx)
                lua = _unescape_xml(body[idx + 8 : end])
            print("  [mock] job %s (%d chars of lua)" % (job_id, len(lua)))
            if lua:
                try:
                    _render_from_lua(lua)
                except Exception as e:
                    print("  [mock] render simulation failed:", e)
            result = job_id
        elif verb == "CloseJob":
            result = "true"
        elif verb == "GetAllJobsEx":
            result = "<jobs></jobs>"

        data = _envelope(verb, result)
        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def main():
    httpd = ThreadingHTTPServer((LISTEN, PORT), Handler)
    print("RCC mock listening on %s:%d (fake renderer, for testing)" % (LISTEN, PORT))
    httpd.serve_forever()


if __name__ == "__main__":
    main()
