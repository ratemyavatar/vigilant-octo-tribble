#!/usr/bin/env python3
"""Site + Roblox client/RCC API.

Run:  python3 server.py
RCC:  set rcc_enabled and rcc_soap in config.json after you install RCCService.exe
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import time
import uuid
import mimetypes
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, unquote

import database as db
import api
import live
import rcc
import rbxapi

ROOT = Path(__file__).resolve().parent
PAGES = ROOT / "pages"
PARTIALS = ROOT / "partials"
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"

with open(ROOT / "config.json", encoding="utf-8") as f:
    CONFIG = json.load(f)

PUBLIC = CONFIG.get("public_url", "http://127.0.0.1:8080").rstrip("/")
NAV_OUT = (PARTIALS / "nav_out.html").read_text(encoding="utf-8", errors="replace")
NAV_IN = (PARTIALS / "nav_in.html").read_text(encoding="utf-8", errors="replace")

# logged-out pages keep these filenames even when a -loggedin twin exists
AUTH_PAGES = {"login.html", "signup.html", "index.html", "landing.html"}


def next_game_port():
    start = int(CONFIG.get("game_port_start", 53640))
    con = db.connect()
    row = con.execute("SELECT MAX(port) AS p FROM jobs").fetchone()
    con.close()
    if row and row["p"]:
        return int(row["p"]) + 1
    return start


def fill_lua(name: str, mapping: dict) -> str:
    text = (SCRIPTS / name).read_text(encoding="utf-8")
    for k, v in mapping.items():
        text = text.replace("{{" + k + "}}", str(v))
    return text


RENDERS = DATA / "renders"


def rewrite_thumbs(html: str, user: dict | None) -> str:
    """Point snapshot CDN thumbs at on-site /thumbs/ routes."""
    html = re.sub(
        r'https?://tr\.rbxcdn\.com/([a-f0-9]+)/\d+/\d+/AvatarHeadshot/\w+',
        r'/thumbs/headshot.ashx?hash=\1',
        html,
        flags=re.I,
    )
    html = re.sub(
        r'https?://tr\.rbxcdn\.com/([a-f0-9]+)/\d+/\d+/Image/\w+',
        r'/thumbs/asset.ashx?hash=\1',
        html,
        flags=re.I,
    )
    html = re.sub(
        r'https?://t[0-7]\.rbxcdn\.com/([a-f0-9]+)',
        r'/thumbs/asset.ashx?hash=\1',
        html,
        flags=re.I,
    )
    uid = user["id"] if user else 0
    html = re.sub(
        r'(<img[^>]*id=home-avatar-thumb[^>]*)src=""',
        r'\1src="/thumbs/headshot.ashx?userId=%s"' % uid,
        html,
    )
    html = re.sub(
        r'(<img[^>]*src="")([^>]*id=home-avatar-thumb)',
        r'<img alt=avatar src="/thumbs/headshot.ashx?userId=%s" id=home-avatar-thumb' % uid,
        html,
    )
    return html


def rewrite_offsite(html: str, logged_in: bool) -> str:
    """Keep in-site nav from leaving for roblox.com."""
    s = "-loggedin.html" if logged_in else ".html"
    pairs = [
        (r"https?://(?:www\.|web\.)?roblox\.com/info/privacy[^\"'\\s>]*", "privacy" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/info/terms[^\"'\\s>]*", "terms" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/info/help[^\"'\\s>]*", "help" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/help[^\"'\\s>]*", "help" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/search/users[^\"'\\s>]*", "search" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/search/groups[^\"'\\s>]*", "groups" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/discover[^\"'\\s>]*", "discover" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/catalog[^\"'\\s>]*", "catalog" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/develop[^\"'\\s>]*", "create" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/premium/membership[^\"'\\s>]*", "premium" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/upgrades/robux[^\"'\\s>]*", "robux" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/my/groups[^\"'\\s>]*", "groups" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/My/Groups[^\"'\\s>]*", "groups" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/groups[^\"'\\s>]*", "groups" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/my/character[^\"'\\s>]*", "avatar" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/my/avatar[^\"'\\s>]*", "avatar" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/my/account[^\"'\\s>]*", "settings" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/my/messages[^\"'\\s>]*", "messages" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/users/friends[^\"'\\s>]*", "friends" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/users/[^\"'\\s>]*/profile[^\"'\\s>]*", "profile" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/newlogin[^\"'\\s>]*", "login.html"),
        (r"https?://(?:www\.|web\.)?roblox\.com/login[^\"'\\s>]*", "login.html"),
        (r"https?://(?:www\.|web\.)?roblox\.com/home[^\"'\\s>]*", "home" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/games/\d+[^\"'\\s>]*", "game" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/games[^\"'\\s>]*", "games" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/giftcards[^\"'\\s>]*", "giftcards" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/places/create[^\"'\\s>]*", "create" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/My/Money\.aspx[^\"'\\s>]*", "trades" + s),
        (r"https?://forum\.roblox\.com[^\"'\\s>]*", "blog" + s),
        (r"https?://wiki\.roblox\.com[^\"'\\s>]*", "help" + s),
        (r"https?://create\.roblox\.com[^\"'\\s>]*", "create" + s),
        (r"https?://developer\.roblox\.com[^\"'\\s>]*", "help" + s),
        (r"https?://corp\.roblox\.com[^\"'\\s>]*", "about" + s),
        (r"https?://en\.help\.roblox\.com[^\"'\\s>]*", "help" + s),
        (r"https?://blog\.roblox\.com[^\"'\\s>]*", "blog" + s),
        (r"https?://(?:www\.|web\.)?roblox\.com/?", "home" + s),
    ]
    for pat, dest in pairs:
        html = re.sub(pat, dest, html, flags=re.I)
    return html


def render_png(kind: str, key: str) -> bytes:
    """On-site render file, or placeholder if RCC is down / file missing."""
    kind = kind.lower()
    if kind in ("headshot", "avatar"):
        folder, placeholder = "headshots", RENDERS / "placeholder-headshot.png"
    elif kind in ("place", "game"):
        folder, placeholder = "places", RENDERS / "placeholder-place.png"
    else:
        folder, placeholder = "assets", RENDERS / "placeholder-place.png"
    key = re.sub(r"[^a-zA-Z0-9_-]", "", str(key or "")) or "0"
    target = RENDERS / folder / (key + ".png")
    if target.is_file() and target.stat().st_size > 0:
        return target.read_bytes()
    # RCC down or never rendered — on-site placeholder
    extra = ROOT / "static" / "placeholder.png"
    if extra.is_file():
        return extra.read_bytes()
    if placeholder.is_file():
        return placeholder.read_bytes()
    return _placeholder_png()


def inject_nav(html: str, user: dict | None) -> str:
    nav_in = (PARTIALS / "nav_in.html").read_text(encoding="utf-8", errors="replace")
    nav_out = (PARTIALS / "nav_out.html").read_text(encoding="utf-8", errors="replace")
    sprite = (PARTIALS / "icons_sprite.html").read_text(encoding="utf-8", errors="replace")
    if user:
        nav = (
            nav_in.replace("{{USERNAME}}", user["username"])
            .replace("{{ROBUX}}", str(user.get("robux") or 0))
            .replace("{{USER_ID}}", str(user["id"]))
        )
    else:
        nav = nav_out
    nav = sprite + "\n" + nav
    # replace existing wrap/header through container-main
    patterns = [
        (r'<div id="wrap"[\s\S]*?<div class="container-main"', nav + '\n    <div class="container-main"'),
        (r'<div id=wrap[\s\S]*?<div class=container-main', nav + '\n    <div class=container-main'),
        (r'<div id="header"[\s\S]*?<div class="container-main"', nav + '\n    <div class="container-main"'),
        (r'<div id=header[\s\S]*?<div class=container-main', nav + '\n    <div class=container-main'),
    ]
    for pat, repl in patterns:
        if re.search(pat, html, re.I):
            return re.sub(pat, repl, html, count=1, flags=re.I)
    # no header found — insert after <body>
    html = re.sub(r'(<body[^>]*>)', r'\1\n' + nav + '\n', html, count=1, flags=re.I)
    return html


def pick_page(name: str, user: dict | None) -> Path:
    name = name.lstrip("/").split("?")[0]
    if not name or name == "/":
        name = "home-loggedin.html" if user else "signup.html"
    if not name.endswith(".html"):
        name = name + ".html"
    if name in ("game-shindo.html", "game-shindo-loggedin.html"):
        name = "game-loggedin.html" if user else "game.html"
    landing = {"login.html", "index.html", "landing.html", "signup.html", "home.html"}
    if name in landing and not user:
        name = "signup.html"
    if name in landing and user:
        name = "home-loggedin.html"
    if user and name not in AUTH_PAGES:
        twin = name[:-5] + "-loggedin.html" if not name.endswith("-loggedin.html") else name
        if (PAGES / twin).exists():
            return PAGES / twin
    return PAGES / name


def json_bytes(obj, status=200):
    return status, "application/json; charset=utf-8", json.dumps(obj).encode("utf-8")


def text_bytes(s, ctype="text/plain; charset=utf-8", status=200):
    return status, ctype, s.encode("utf-8")


def lua_bytes(s, status=200):
    return status, "text/plain; charset=utf-8", s.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "RobloxSite/1.0"

    def log_message(self, fmt, *args):
        try:
            msg = fmt % args
        except Exception:
            msg = " ".join(str(a) for a in (fmt,) + args)
        print("%s - %s" % (self.address_string(), msg), flush=True)

    def _cookies(self):
        raw = self.headers.get("Cookie", "")
        c = cookies.SimpleCookie()
        if raw:
            try:
                c.load(raw)
            except Exception:
                pass
        return c

    def current_user(self):
        c = self._cookies()
        sid = None
        for key in (".ROBLOSECURITY", "ROBLOSECURITY", "session"):
            if key in c:
                sid = c[key].value
                break
        return db.session_user(sid)

    def read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def parse_form(self):
        body = self.read_body().decode("utf-8", "replace")
        ctype = self.headers.get("Content-Type", "")
        if "application/json" in ctype:
            try:
                return json.loads(body or "{}")
            except Exception:
                return {}
        return {k: v[0] if v else "" for k, v in parse_qs(body, keep_blank_values=True).items()}

    def send_raw(self, status, ctype, data, extra_headers=None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def redirect(self, loc, set_cookie=None, clear_cookie=False):
        self.send_response(302)
        self.send_header("Location", loc)
        if set_cookie:
            self.send_header(
                "Set-Cookie",
                ".ROBLOSECURITY=%s; Path=/; HttpOnly; Max-Age=%s" % (set_cookie, 60 * 60 * 24 * 14),
            )
        if clear_cookie:
            self.send_header("Set-Cookie", ".ROBLOSECURITY=; Path=/; Max-Age=0")
        self.end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Cookie, Roblox-Session-Id, Roblox-Game-Id")
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        self.route("GET")

    def do_POST(self):
        self.route("POST")

    def route(self, method):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        qs = parse_qs(parsed.query)
        q = {k: v[0] if v else "" for k, v in qs.items()}
        low = path.lower()

        try:
            handled = self.api(method, path, low, q)
            if handled is False:
                return
            if handled is not None:
                status, ctype, data = handled[:3]
                extra = handled[3] if len(handled) > 3 else None
                self.send_raw(status, ctype, data, extra)
                return
            self.serve_page(path)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_raw(500, "text/plain", str(e).encode())

    # ----- Roblox client + site API -----
    def api(self, method, path, low, q):
        user = self.current_user()

        api_hit = api.handle(method, path, low, q, user, self)
        if api_hit is not None:
            return api_hit
        rbx_hit = rbxapi.handle(method, path, low, q, user, self)
        if rbx_hit is not None:
            return rbx_hit

        if low in ("/login", "/login/") and method == "POST":
            form = self.parse_form()
            u = db.verify_user(form.get("username", ""), form.get("password", ""))
            if not u:
                return text_bytes("Invalid username or password", status=401)
            sid = db.create_session(u["id"])
            self.redirect("/home-loggedin.html", set_cookie=sid)
            return False

        if low in ("/signup", "/signup/") and method == "POST":
            form = self.parse_form()
            bday = "/".join(
                filter(
                    None,
                    [
                        form.get("BirthMonth") or form.get("month"),
                        form.get("BirthDay") or form.get("day"),
                        form.get("BirthYear") or form.get("year"),
                    ],
                )
            )
            u = db.create_user(
                form.get("username", ""),
                form.get("password", ""),
                bday,
                form.get("gender", ""),
            )
            if not u:
                return text_bytes("Username taken or invalid", status=400)
            sid = db.create_session(u["id"])
            self.redirect("/home-loggedin.html", set_cookie=sid)
            return False

        if low in ("/logout", "/login/logout.ashx"):
            c = self._cookies()
            if ".ROBLOSECURITY" in c:
                db.delete_session(c[".ROBLOSECURITY"].value)
            self.redirect("/login.html", clear_cookie=True)
            return False

        if low in ("/places/create", "/places/create/") and method == "POST":
            if not user:
                self.redirect("/login.html")
                return False
            form = self.parse_form()
            pid = db.create_place(
                user["id"],
                form.get("Name") or "Untitled",
                form.get("Description") or "",
                form.get("Genre") or "All",
                form.get("TemplateID") or "",
                form.get("NumberOfPlayersMax") or 10,
            )
            self.redirect("/games-loggedin.html?id=%s" % pid)
            return False

        if low in ("/catalog/upload",) and method == "POST":
            if not user:
                return json_bytes({"error": "login"}, 401)
            form = self.parse_form()
            aid = db.create_asset(
                user["id"],
                form.get("name") or "Item",
                form.get("asset_type") or "Hat",
                form.get("description") or "",
                "",
                "",
                form.get("price") or 0,
            )
            if CONFIG.get("rcc_enabled"):
                try:
                    lua = fill_lua(
                        "render.lua",
                        {"BASE_URL": PUBLIC, "ASSET_ID": aid, "USER_ID": 0},
                    )
                    rcc.open_job(CONFIG["rcc_soap"], "Render", lua, timeout=int(CONFIG.get("rcc_timeout", 15)))
                except Exception as e:
                    print("render job", e)
            accept = (self.headers.get("Accept") or "").lower()
            if "application/json" in accept:
                return json_bytes({"id": aid})
            self.redirect("/catalog-loggedin.html")
            return False

        if low in ("/friends/add", "/friends/add/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            other = form.get("userId") or form.get("userid") or ""
            if not str(other).isdigit():
                named = db.get_user_by_name(form.get("username") or "")
                other = named["id"] if named else 0
            db.request_friend(user["id"], other)
            self.redirect("/friends-loggedin.html")
            return False

        if low in ("/play", "/play/"):
            accept = (self.headers.get("Accept") or "").lower()
            want_json = (
                q.get("json") == "1"
                or "application/json" in accept
                or (self.headers.get("X-Requested-With") or "") == "XMLHttpRequest"
            )
            if not user:
                if want_json:
                    return json_bytes({"error": "login"}, 401)
                self.redirect("/signup.html")
                return False
            try:
                pid = int(q.get("placeId") or q.get("placeid") or q.get("id") or 0)
            except Exception:
                pid = 0
            if not pid:
                pid = int(CONFIG.get("default_place_id") or 1)
            job = self._open_game_job(pid)
            db.record_play(user["id"], pid)
            place = db.get_place(pid) or {}
            launcher = PUBLIC + "/game/PlaceLauncher.ashx?placeId=%s" % pid
            ticket = uuid.uuid4().hex
            proto = (
                "roblox-player:1+launchmode:play+gameinfo:%s+placelauncherurl:%s+launchtime:%s"
                % (ticket, launcher, int(time.time() * 1000))
            )
            if want_json:
                return json_bytes(
                    {
                        "ok": True,
                        "uri": proto,
                        "placeId": pid,
                        "placeName": place.get("name") or "Experience",
                        "jobId": (job or {}).get("id") or "",
                        "placeLauncherUrl": launcher,
                    }
                )
            self.redirect("/game-loggedin.html?id=%s&launch=1" % pid)
            return False

        if low in ("/settings/update", "/settings/update/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            tab = form.get("tab") or ""
            profile = {}
            for k in ("username", "status", "blurb", "birthday", "gender"):
                if k in form:
                    profile[k] = form.get(k)
            if profile:
                db.update_user(user["id"], **profile)
            updates = {}
            if tab == "security":
                updates["two_step"] = form.get("two_step") == "1"
            elif tab == "notifications":
                for k in ("notify_messages", "notify_friends", "notify_trades", "notify_updates"):
                    updates[k] = form.get(k) == "1"
            elif tab == "parental-controls":
                updates["account_restrictions"] = form.get("account_restrictions") == "1"
                if form.get("content_maturity"):
                    updates["content_maturity"] = form.get("content_maturity")
                if form.get("monthly_spend"):
                    updates["monthly_spend"] = form.get("monthly_spend")
                if form.get("clear_pin") == "1":
                    db.set_pin(user["id"], "")
                elif form.get("new_pin"):
                    db.set_pin(user["id"], form.get("new_pin"))
            elif tab == "privacy":
                for k in (
                    "who_message",
                    "who_chat_app",
                    "who_chat_game",
                    "who_join",
                    "who_inventory",
                    "who_trade",
                    "who_friends",
                ):
                    if form.get(k):
                        updates[k] = form.get(k)
            else:
                if "display_name" in form:
                    updates["display_name"] = form.get("display_name") or ""
                if "email" in form:
                    updates["email"] = form.get("email") or ""
                if form.get("language"):
                    updates["language"] = form.get("language")
            if updates:
                db.save_user_settings(user["id"], updates)
            dest = "/settings-loggedin.html"
            if tab:
                dest += "#" + tab
            elif "status" in form and "username" not in form:
                dest = "/home-loggedin.html"
            self.redirect(dest)
            return False

        if low in ("/settings/password", "/settings/password/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            ok = db.update_password(user["id"], form.get("current_password"), form.get("new_password"))
            if not ok:
                return text_bytes("Current password is wrong or new password is empty", status=400)
            self.redirect("/settings-loggedin.html#security")
            return False

        if low in ("/settings/sessions/logout", "/settings/sessions/logout/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            c = self._cookies()
            sid = c[".ROBLOSECURITY"].value if ".ROBLOSECURITY" in c else ""
            db.delete_other_sessions(user["id"], sid)
            self.redirect("/settings-loggedin.html#security")
            return False

        if low in ("/messages/send", "/messages/send/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            to_id = form.get("toId") or form.get("to") or ""
            if not str(to_id).isdigit():
                named = db.get_user_by_name(form.get("username") or form.get("to") or "")
                to_id = named["id"] if named else 0
            db.send_message(user["id"], to_id, form.get("body") or "", form.get("subject") or "")
            self.redirect("/messages-loggedin.html")
            return False

        if low in ("/groups/create", "/groups/create/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.create_group(user["id"], form.get("name") or "", form.get("description") or "")
            self.redirect("/groups-loggedin.html")
            return False

        if low in ("/promo/redeem", "/promo/redeem/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.redeem_promo(user["id"], form.get("code") or "")
            self.redirect("/promocodes-loggedin.html")
            return False

        if low in ("/catalog/buy", "/catalog/buy/") and method == "POST":
            if not user:
                return json_bytes({"error": "login"}, 401)
            form = self.parse_form()
            aid = form.get("id") or form.get("assetId") or q.get("id") or 0
            ok, reason = db.buy_asset(user["id"], aid)
            accept = (self.headers.get("Accept") or "").lower()
            if "application/json" in accept:
                return json_bytes({"ok": ok, "reason": reason}, 200 if ok else 400)
            self.redirect("/catalog-loggedin.html")
            return False

        if low in ("/friends/accept", "/friends/accept/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            other = form.get("userId") or form.get("id") or 0
            db.accept_friend(user["id"], other)
            self.redirect("/friends-loggedin.html#requests-pane")
            return False

        if low in ("/friends/decline", "/friends/decline/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            other = form.get("userId") or form.get("id") or 0
            db.decline_friend(user["id"], other)
            self.redirect("/friends-loggedin.html#requests-pane")
            return False

        if low in ("/avatar/outfit/create", "/avatar/outfit/create/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.create_outfit(user["id"], form.get("name") or "Outfit")
            self.redirect("/avatar-loggedin.html?tab=outfits")
            return False

        if low in ("/avatar/outfit/wear", "/avatar/outfit/wear/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.wear_outfit(user["id"], form.get("id") or 0)
            self.redirect("/avatar-loggedin.html?tab=outfits")
            return False

        if low in ("/avatar/outfit/delete", "/avatar/outfit/delete/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.delete_outfit(user["id"], form.get("id") or 0)
            self.redirect("/avatar-loggedin.html?tab=outfits")
            return False

        if low in ("/avatar/colors", "/avatar/colors/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            color = form.get("color") or ""
            part = form.get("part") or "all"
            allowed = {
                "head": "head_color",
                "torso": "torso_color",
                "left_arm": "left_arm_color",
                "right_arm": "right_arm_color",
                "left_leg": "left_leg_color",
                "right_leg": "right_leg_color",
            }
            updates = {}
            if color.startswith("#") and len(color) == 7:
                if part == "all":
                    for k in allowed.values():
                        updates[k] = color
                elif part in allowed:
                    updates[allowed[part]] = color
            if updates:
                db.save_user_settings(user["id"], updates)
            self.redirect("/avatar-loggedin.html")
            return False

        if low in ("/avatar/type", "/avatar/type/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            kind = (form.get("avatar_type") or "R6").upper()
            if kind not in ("R6", "R15"):
                kind = "R6"
            db.save_user_settings(user["id"], {"avatar_type": kind})
            self.redirect("/avatar-loggedin.html")
            return False

        if low in ("/avatar/wear", "/avatar/wear/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.wear_asset(user["id"], form.get("id") or 0)
            self.redirect("/avatar-loggedin.html")
            return False

        if low in ("/avatar/unwear", "/avatar/unwear/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.unwear_asset(user["id"], form.get("id") or 0)
            self.redirect("/avatar-loggedin.html")
            return False

        if low in ("/places/favorite", "/places/favorite/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            pid = form.get("placeId") or form.get("id") or 0
            db.toggle_favorite(user["id"], pid)
            self.redirect("/game-loggedin.html?id=%s" % pid)
            return False

        if low in ("/groups/join", "/groups/join/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            gid = form.get("groupId") or form.get("id") or 0
            db.join_group(gid, user["id"])
            self.redirect("/groups-loggedin.html?id=%s" % gid)
            return False

        if low in ("/trades/send", "/trades/send/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            named = db.get_user_by_name(form.get("username") or "")
            to_id = named["id"] if named else 0
            tid = db.create_trade(user["id"], to_id)
            if tid:
                for raw in (form.get("offer") or "").split(","):
                    raw = raw.strip()
                    if raw.isdigit():
                        db.add_trade_item(tid, user["id"], int(raw))
            self.redirect("/trades-loggedin.html")
            return False

        if low in ("/trades/accept", "/trades/accept/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.set_trade_status(form.get("id") or 0, user["id"], "completed")
            self.redirect("/trades-loggedin.html")
            return False

        if low in ("/trades/decline", "/trades/decline/") and method == "POST":
            if not user:
                self.redirect("/signup.html")
                return False
            form = self.parse_form()
            db.set_trade_status(form.get("id") or 0, user["id"], "declined")
            self.redirect("/trades-loggedin.html")
            return False

        # auth ticket
        if low.endswith("/login/negotiate.ashx") or low.endswith("/authentication/negotiate"):
            suggest = q.get("suggest") or (user["username"] if user else "Guest")
            ticket = uuid.uuid4().hex
            return text_bytes(ticket)

        if low.endswith("/login/requestauth.ashx"):
            return text_bytes(user["username"] if user else "Guest")

        if low.endswith("/game/getcurrentuser.ashx") or low.endswith("/game/getcurrentuser.ashx"):
            return text_bytes(str(user["id"]) if user else "0")

        if "/game/players/" in low:
            return json_bytes({"ChatFilter": "whitelist"})

        if "keepalivepinger" in low:
            return text_bytes("OK")

        if "clientpresence" in low:
            return text_bytes("OK")

        if "validate-machine" in low or "validatemachine" in low:
            return json_bytes({"success": True})

        if "validate-place-join" in low:
            return text_bytes("true")

        if "chatfilter" in low or "filtertext" in low:
            text = q.get("text") or q.get("textFilter") or ""
            if method == "POST":
                form = self.parse_form()
                text = form.get("text") or form.get("textFilter") or text
            return json_bytes({"success": True, "data": {"white": text, "black": text}})

        if "handlesocialrequest" in low:
            return text_bytes("true")

        if low.startswith("/error/") or low.endswith(".ashx") and "error" in low:
            self.read_body()
            return text_bytes("OK")

        if "clientappsettings" in low or "clientsharedsettings" in low:
            return json_bytes(
                {
                    "WebsiteUrl": PUBLIC,
                    "BaseUrl": PUBLIC,
                    "DefaultSiteUrl": PUBLIC,
                    "ContentFolderUrl": PUBLIC + "/content/",
                    "FFlagUseNewGamesPage": False,
                }
            )

        if "avatar-fetch" in low:
            uid = q.get("userId") or q.get("userid") or (str(user["id"]) if user else "1")
            return json_bytes(
                {
                    "resolvedAvatarType": "R6",
                    "equippedGearVersionIds": [],
                    "backpackGearVersionIds": [],
                    "assetAndAssetTypeIds": [],
                    "animationAssetIds": {},
                    "bodyColorsUrl": PUBLIC + "/asset/BodyColors.ashx?userId=" + str(uid),
                    "scales": {"height": 1, "width": 1, "head": 1, "depth": 1},
                }
            )

        if "characterfetch" in low or "character-fetch" in low:
            uid = q.get("userId") or (str(user["id"]) if user else "1")
            return text_bytes(
                PUBLIC + "/asset/BodyColors.ashx?userId=" + str(uid) + ";"
            )

        if low.endswith("/asset/bodycolors.ashx"):
            return text_bytes(
                '<?xml version="1.0" encoding="utf-8"?>'
                '<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">'
                "<Item class=\"BodyColors\"><Properties></Properties></Item></roblox>",
                "text/xml",
            )

        if low in ("/asset/", "/asset", "/asset/index") or low.startswith("/asset/"):
            aid = q.get("id") or q.get("assetversionid") or ""
            if aid.isdigit():
                place = db.get_place(int(aid))
                if place and place.get("file_path"):
                    fp = ROOT / place["file_path"]
                    if fp.exists():
                        data = fp.read_bytes()
                        return 200, "application/octet-stream", data
                asset = db.get_asset(int(aid))
                if asset and asset.get("file_path"):
                    fp = ROOT / asset["file_path"]
                    if fp.exists():
                        return 200, "application/octet-stream", fp.read_bytes()
            return 404, "text/plain", b"asset not found"

        if low.startswith("/thumbs/") or low.startswith("/renders/"):
            kind = "asset"
            if "headshot" in low or "avatar" in low:
                kind = "headshot"
            elif "place" in low or "game" in low:
                kind = "place"
            key = (
                q.get("userId")
                or q.get("userid")
                or q.get("assetId")
                or q.get("assetid")
                or q.get("id")
                or q.get("hash")
                or "0"
            )
            if method == "POST":
                body = self.read_body()
                folder = "headshots" if kind == "headshot" else ("places" if kind == "place" else "assets")
                dest = RENDERS / folder
                dest.mkdir(parents=True, exist_ok=True)
                safe = re.sub(r"[^a-zA-Z0-9_-]", "", str(key)) or "0"
                (dest / (safe + ".png")).write_bytes(body)
                return json_bytes({"ok": True, "url": "/thumbs/%s.ashx?id=%s" % (kind, safe)})
            return 200, "image/png", render_png(kind, key)

        if "marketplace/productinfo" in low or "marketplace/productdetails" in low:
            aid = int(q.get("assetId") or q.get("productId") or 0)
            asset = db.get_asset(aid) if aid else None
            place = db.get_place(aid) if aid else None
            name = (asset or place or {}).get("name") or "Product"
            return json_bytes(
                {
                    "TargetId": aid,
                    "ProductType": "Place" if place else "User Product",
                    "AssetId": aid,
                    "ProductId": aid,
                    "Name": name,
                    "Description": (asset or place or {}).get("description") or "",
                    "IsForSale": True,
                    "PriceInRobux": (asset or {}).get("price") or 0,
                }
            )

        if "currency/balance" in low:
            return json_bytes({"robux": user.get("robux", 0) if user else 0})

        if "ownership/hasasset" in low:
            return text_bytes("false")

        if "get-friendship-count" in low:
            n = len(db.list_friends(user["id"])) if user else 0
            return json_bytes({"success": True, "count": n})

        if low.endswith("/my/settings/json"):
            if not user:
                return json_bytes({"error": "Not logged in"}, 401)
            return json_bytes(
                {
                    "UserId": user["id"],
                    "Name": user["username"],
                    "DisplayName": user["username"],
                    "IsUnder13": False,
                    "RobuxBalance": user.get("robux") or 0,
                }
            )

        if low in ("/v1/users/authenticated", "/v2/users/authenticated"):
            if not user:
                return json_bytes({"errors": [{"message": "Unauthorized"}]}, 401)
            return json_bytes({"id": user["id"], "name": user["username"], "displayName": user["username"]})

        if low.startswith("/v1/users/") or low.startswith("/v2/users/"):
            parts = [p for p in low.split("/") if p]
            try:
                uid = int(parts[2])
            except Exception:
                uid = user["id"] if user else 0
            u = db.get_user(uid)
            if not u:
                return json_bytes({"errors": [{"message": "NotFound"}]}, 404)
            return json_bytes({"id": u["id"], "name": u["username"], "displayName": u["username"]})

        if "universes/get-universe-containing-place" in low:
            return json_bytes({"UniverseId": int(q.get("placeid") or 1)})

        if "loadplaceinfo" in low:
            pid = int(q.get("PlaceId") or q.get("placeId") or 1)
            place = db.get_place(pid) or {"id": pid, "creator_id": 1, "name": "Place"}
            return json_bytes(
                {
                    "CreatorId": place.get("creator_id") or 1,
                    "CreatorType": "User",
                    "PlaceVersion": 1,
                    "GameId": pid,
                    "MachineId": "1",
                }
            )

        if "device/initialize" in low:
            return json_bytes({"browserTrackerId": int(time.time()), "appDeviceIdentifier": None})

        if "getscriptstate" in low:
            return text_bytes("0 0 0 0")

        # Place launcher + join
        if "placelauncher" in low:
            pid = int(q.get("placeId") or q.get("placeid") or CONFIG.get("default_place_id") or 1)
            request = q.get("request") or q.get("Request") or "RequestGame"
            job = db.latest_job_for_place(pid)
            if request.lower() in ("requestgame", "requestgamejob", "requestfollowuser") or method == "POST":
                if not job or job.get("status") != 2:
                    job = self._open_game_job(pid)
                return json_bytes(
                    {
                        "jobId": job["id"] if job else "",
                        "status": 2 if job else 3,
                        "statusData": None,
                        "joinScriptUrl": PUBLIC + "/game/join.ashx?job=" + (job["id"] if job else ""),
                        "authenticationUrl": PUBLIC + "/Login/Negotiate.ashx",
                        "authenticationTicket": uuid.uuid4().hex,
                        "message": None,
                    }
                )
            return json_bytes({"jobId": job["id"] if job else "", "status": 2 if job else 0})

        if low.endswith("/game/join.ashx") or low.endswith("/game/join.ashx/"):
            job_id = q.get("job") or q.get("jobId") or q.get("jobid")
            job = db.get_job(job_id) if job_id else None
            if not job:
                pid = int(q.get("placeId") or q.get("placeid") or 1)
                job = self._open_game_job(pid)
            place = db.get_place(job["place_id"]) if job else None
            lua = fill_lua(
                "join.lua",
                {
                    "PLACE_ID": job["place_id"] if job else 1,
                    "CREATOR_ID": (place or {}).get("creator_id") or 1,
                    "USER_ID": user["id"] if user else 0,
                    "HOST": job["host"] if job else "127.0.0.1",
                    "PORT": job["port"] if job else 53640,
                },
            )
            return lua_bytes(lua)

        if low in ("/game/gameserver.ashx", "/game/gameserver.ashx/"):
            pid = int(q.get("placeId") or 1)
            job = self._open_game_job(pid)
            return json_bytes(job or {"error": "rcc unavailable"}, 200 if job else 503)

        if low == "/rcc/hello":
            ok = False
            if CONFIG.get("rcc_enabled"):
                ok = rcc.hello(CONFIG["rcc_soap"], timeout=3)
            return json_bytes({"rcc_enabled": bool(CONFIG.get("rcc_enabled")), "reachable": ok, "soap": CONFIG.get("rcc_soap")})

        if low == "/api/places":
            return json_bytes(db.list_places())

        if low == "/api/catalog":
            return json_bytes(db.list_assets())

        if low == "/api/me":
            if not user:
                return json_bytes({"guest": True})
            return json_bytes({"id": user["id"], "username": user["username"], "robux": user.get("robux") or 0})

        return None

    def _open_game_job(self, place_id: int):
        place = db.get_place(place_id) or {"id": place_id, "max_players": 10, "creator_id": 1}
        host = urlparse(PUBLIC).hostname or "127.0.0.1"
        port = next_game_port()
        job_id = str(uuid.uuid4())
        if CONFIG.get("rcc_enabled"):
            lua = fill_lua(
                "gameserver.lua",
                {
                    "PLACE_ID": place_id,
                    "PORT": port,
                    "BASE_URL": PUBLIC,
                    "MAX_PLAYERS": place.get("max_players") or 10,
                },
            )
            try:
                job_id = rcc.open_job(
                    CONFIG["rcc_soap"],
                    "GameServer",
                    lua,
                    timeout=int(CONFIG.get("rcc_timeout", 15)),
                )
            except Exception as e:
                print("RCC OpenJob failed:", e)
                # still record a job so join scripts can be tested
        db.create_job(job_id, place_id, host, port, status=2)
        return db.get_job(job_id)

    def serve_page(self, path):
        user = self.current_user()
        # static data files
        rel = path.lstrip("/")
        if rel.startswith("static/") or rel.startswith("data/"):
            fp = (ROOT / rel).resolve()
            if str(fp).startswith(str(ROOT)) and fp.is_file():
                ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
                self.send_raw(200, ctype, fp.read_bytes())
                return
        page = pick_page(path, user)
        if not page.exists() or not page.is_file():
            # try without -loggedin fallback
            alt = PAGES / Path(path.lstrip("/")).name
            if alt.exists():
                page = alt
            else:
                self.send_raw(404, "text/plain", b"Not found")
                return
        data = page.read_bytes()
        ctype = mimetypes.guess_type(str(page))[0] or "application/octet-stream"
        if page.suffix.lower() == ".html":
            html = data.decode("utf-8", "replace")
            if 'href="/static/site.css"' not in html:
                html = html.replace(
                    "</head>",
                    '<link rel="stylesheet" href="/static/site.css"></head>',
                    1,
                )
            html = inject_nav(html, user)
            html = rewrite_thumbs(html, user)
            html = rewrite_offsite(html, user is not None)
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query)
            q = {k: v[0] if v else "" for k, v in qs.items()}
            html = live.prepare(html, page.name, user, q)
            # wire forms
            html = html.replace(
                '<form class="login-form" name="loginForm">',
                '<form class="login-form" name="loginForm" method="post" action="/login">',
            )
            if "signup" in page.name or page.name in ("login.html", "index.html", "landing.html"):
                html = html.replace('id="MondDropdown"', 'id="MondDropdown" name="BirthMonth"')
                html = html.replace('id="DayDropdown"', 'id="DayDropdown" name="BirthDay"')
                html = html.replace('id="YearDropdown"', 'id="YearDropdown" name="BirthYear"')
            html = html.replace(
                'id="login-button" class="btn-full-width login-button btn-secondary-md"',
                'id="login-button" type="submit" class="btn-full-width login-button btn-secondary-md"',
            )
            html = html.replace('type="button" id="login-button"', 'type="submit" id="login-button"')
            html = html.replace(
                '<form id="placeForm" method="POST" action="https://www.roblox.com/places/create">',
                '<form id="placeForm" method="POST" action="/places/create">',
            )
            html = html.replace(
                '<form id="placeForm" method="POST" action="create.html">',
                '<form id="placeForm" method="POST" action="/places/create">',
            )
            html = html.replace(
                '<form id="placeForm" method="POST" action="create-loggedin.html">',
                '<form id="placeForm" method="POST" action="/places/create">',
            )
            if user:
                html = html.replace("{{USERNAME}}", user["username"])
                html = html.replace("{{PROFILE_ID}}", str(user["id"]))
            else:
                html = html.replace("{{USERNAME}}", "")
                html = html.replace("{{PROFILE_ID}}", "0")
            data = html.encode("utf-8")
            ctype = "text/html; charset=utf-8"
        self.send_raw(200, ctype, data)


def _placeholder_png():
    # 1x1 png
    import base64

    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+X2ZkAAAAASUVORK5CYII="
    )


def main():
    db.init()
    DATA.mkdir(exist_ok=True)
    host = CONFIG.get("host", "0.0.0.0")
    port = int(CONFIG.get("port", 8080))
    print("Serving %s on %s:%s" % (PUBLIC, host, port))
    print("RCC enabled=%s soap=%s" % (CONFIG.get("rcc_enabled"), CONFIG.get("rcc_soap")))
    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
