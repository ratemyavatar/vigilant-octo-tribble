"""Site admin console, adapted from Economy Simulator admin.

Hardcoded owner: 2amposts has every command and cannot be banned.
"""
from __future__ import annotations

import html as htmlmod
import json
import re
import time
from datetime import datetime

import database as db

HARD_ADMINS = frozenset({"2amposts"})

ALL_PERMS = [
    "GetUsersList",
    "GetUserJoinCount",
    "GetUsersOnline",
    "GetUsersInGame",
    "BanUser",
    "UnbanUser",
    "DeleteUser",
    "GiveUserRobux",
    "GiveUserItem",
    "RemoveUserItem",
    "CreateUser",
    "CreateAsset",
    "SetAssetProduct",
    "GetAdminLogs",
    "SetAlert",
    "MessageUser",
    "DestroyAllSessionsForUser",
    "LockAccount",
    "ResetUsername",
    "ResetDescription",
    "GetGroupManageInfo",
    "ManagePromo",
    "DeletePlace",
    "ManageStaff",
    "NullifyPassword",
]

BAN_REASONS = [
    ("TOS Violation", "This account has been closed due to violating the terms of service."),
    ("Bad Username", "Your username is inappropriate."),
    ("Spam", "Do not repeatedly post spam chat or content."),
    ("Inappropriate Behaviour", "Your account has been deleted for inappropriate behavior or content."),
    ("Hate Speech", "Hate speech is not permitted."),
    ("Real-Life Information", "Do not ask for or give out personal information."),
    ("Scamming", "Scamming is a violation of the Terms of Service."),
    ("Account Theft", "Your account has been deleted for theft of an account and/or its assets."),
]


def esc(s) -> str:
    return htmlmod.escape("" if s is None else str(s))


def is_hard_admin(user) -> bool:
    if not user:
        return False
    return (user.get("username") or "").strip().lower() in HARD_ADMINS


def is_admin(user) -> bool:
    if not user:
        return False
    if is_hard_admin(user):
        return True
    return bool(user.get("is_staff"))


def has_permission(user, perm: str) -> bool:
    if is_hard_admin(user):
        return True
    if not is_admin(user):
        return False
    return True


def protected_user(target) -> bool:
    return is_hard_admin(target)


def log_action(actor, action, target="", detail=""):
    con = db.connect()
    con.execute(
        "INSERT INTO admin_logs (actor_id, action, target, detail, created_at) VALUES (?,?,?,?,?)",
        (
            (actor or {}).get("id") or 0,
            action,
            str(target or ""),
            str(detail or "")[:2000],
            int(time.time()),
        ),
    )
    con.commit()
    con.close()


def list_logs(limit=80):
    con = db.connect()
    rows = con.execute(
        """
        SELECT l.*, u.username AS actor_name
        FROM admin_logs l
        LEFT JOIN users u ON u.id = l.actor_id
        ORDER BY l.id DESC LIMIT ?
        """,
        (int(limit),),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_alert():
    con = db.connect()
    row = con.execute("SELECT v FROM site_kv WHERE k='alert'").fetchone()
    con.close()
    if not row or not row["v"]:
        return {"text": "", "url": ""}
    try:
        data = json.loads(row["v"])
        if isinstance(data, dict):
            return {"text": data.get("text") or "", "url": data.get("url") or ""}
    except Exception:
        pass
    return {"text": "", "url": ""}


def set_alert(text, url=""):
    payload = json.dumps({"text": (text or "").strip(), "url": (url or "").strip()})
    con = db.connect()
    con.execute("INSERT OR REPLACE INTO site_kv (k, v) VALUES ('alert', ?)", (payload,))
    con.commit()
    con.close()


def refresh_user(user):
    """Clear expired bans and never leave the hardcoded owner banned/locked."""
    if not user:
        return user
    changed = False
    if is_hard_admin(user) and (user.get("banned") or user.get("account_locked")):
        changed = True
    elif user.get("banned"):
        until = int(user.get("ban_until") or 0)
        if until and until <= int(time.time()):
            changed = True
    if changed:
        user["banned"] = 0
        user["account_locked"] = 0
        user["ban_reason"] = ""
        user["ban_internal"] = ""
        user["ban_until"] = 0
        try:
            con = db.connect()
            con.execute(
                "UPDATE users SET banned=0, account_locked=0, ban_reason='', ban_internal='', ban_until=0 WHERE id=?",
                (user["id"],),
            )
            con.commit()
            con.close()
        except Exception:
            pass
    return user


def is_blocked(user) -> bool:
    if not user:
        return False
    if is_hard_admin(user):
        return False
    if user.get("account_locked"):
        return True
    if user.get("banned"):
        until = int(user.get("ban_until") or 0)
        if until and until < int(time.time()):
            return False
        return True
    return False


def block_reason(user) -> str:
    if not user:
        return "This account cannot be used."
    if user.get("account_locked"):
        return "This account has been locked."
    return (user.get("ban_reason") or "This account has been terminated.").strip()


def can_set_username(actor, new_name) -> bool:
    new_name = (new_name or "").strip()
    if not new_name:
        return False
    if new_name.lower() in HARD_ADMINS and not is_hard_admin(actor):
        return False
    if is_hard_admin(actor) and new_name.lower() not in HARD_ADMINS:
        return False
    return True


def blocked_page(user):
    reason = esc(block_reason(user))
    return _html(
        """<!DOCTYPE html>
<html class="adm-html">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Account Deleted</title>
<link rel="stylesheet" href="/static/admin.css">
<style>
body{background:#191b1d;color:#fff;font-family:Arial,Helvetica,sans-serif;padding:40px}
h1{color:#fff}p{color:#bdbebe}a{color:#00a2ff}
</style>
</head>
<body class="adm-body">
<div class="adm-main" style="max-width:640px;margin:40px auto">
  <h1>Account Deleted</h1>
  <p>%s</p>
  <p><a href="/logout">Back to login</a></p>
</div>
</body>
</html>"""
        % reason,
        403,
    )


def inject_site_alert(html: str) -> str:
    try:
        alert = get_alert()
    except Exception:
        return html
    text = (alert.get("text") or "").strip()
    if not text:
        return html
    url = (alert.get("url") or "").strip()
    if url:
        body = '<a href="%s">%s</a>' % (esc(url), esc(text))
    else:
        body = esc(text)
    banner = '<div class="site-alert" role="status">%s</div>' % body
    new, n = re.subn(
        r'(<div class="container-main"[^>]*>)',
        r"\1" + banner,
        html,
        count=1,
        flags=re.I,
    )
    if n:
        return new
    new, n = re.subn(
        r"(<div class=container-main[^>]*>)",
        r"\1" + banner,
        html,
        count=1,
        flags=re.I,
    )
    if n:
        return new
    return html


def fmt_time(ts):
    try:
        return datetime.utcfromtimestamp(int(ts or 0)).strftime("%m/%d/%Y %H:%M")
    except Exception:
        return "—"


def user_status(u):
    if not u:
        return "Unknown"
    if u.get("account_locked"):
        return "Locked"
    if u.get("banned"):
        until = int(u.get("ban_until") or 0)
        if until and until <= int(time.time()):
            return "Ok"
        return "Banned"
    return "Ok"


def _json(obj, status=200):
    return status, "application/json; charset=utf-8", json.dumps(obj).encode("utf-8")


def _html(s, status=200):
    return status, "text/html; charset=utf-8", s.encode("utf-8")


def chrome(user, title, inner, active="dash"):
    nav = [
        ("dash", "/admin", "Dashboard"),
        ("players", "/admin/players", "Players"),
        ("groups", "/admin/groups", "Groups"),
        ("places", "/admin/places", "Places"),
        ("catalog", "/admin/catalog", "Catalog"),
        ("create", "/admin/user/create", "Create Player"),
        ("promo", "/admin/promo", "Promo Codes"),
        ("logs", "/admin/logs", "Logs"),
    ]
    links = []
    for key, href, label in nav:
        cls = "adm-link active" if key == active else "adm-link"
        links.append('<a class="%s" href="%s">%s</a>' % (cls, href, esc(label)))
    alert = get_alert()
    banner = ""
    if alert.get("text"):
        banner = '<div class="adm-banner">%s</div>' % esc(alert["text"])
    return """<!DOCTYPE html>
<html class="adm-html">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s - Management</title>
<link rel="icon" href="/static/ecs/logo_R.svg">
<link rel="stylesheet" href="/static/admin.css">
</head>
<body class="adm-body">
<header class="adm-top">
  <a class="adm-brand" href="/admin">Management</a>
  <span class="adm-who">signed in as %s</span>
  <a class="adm-back" href="/home-loggedin.html">Back to ROBLOX</a>
</header>
%s
<div class="adm-shell">
  <nav class="adm-side">
    <p class="adm-side-head">Console</p>
    %s
  </nav>
  <main class="adm-main">
    %s
  </main>
</div>
</body>
</html>""" % (
        esc(title),
        esc(user.get("username") or ""),
        banner,
        "\n    ".join(links),
        inner,
    )


def dash_page(user):
    users = db.list_users(500)
    now = int(time.time())
    hour = sum(1 for u in users if now - int(u.get("created_at") or 0) < 3600)
    day = sum(1 for u in users if now - int(u.get("created_at") or 0) < 86400)
    online = 0
    try:
        con = db.connect()
        row = con.execute(
            "SELECT COUNT(DISTINCT user_id) AS c FROM sessions WHERE expires_at>?",
            (now,),
        ).fetchone()
        con.close()
        online = int(row["c"] or 0) if row else 0
    except Exception:
        online = 0
    places = db.list_places()
    assets = db.list_assets()
    jobs = 0
    try:
        con = db.connect()
        row = con.execute("SELECT COUNT(*) AS c FROM jobs").fetchone()
        con.close()
        jobs = int(row["c"] or 0) if row else 0
    except Exception:
        pass
    alert = get_alert()
    inner = """
    <h1>Dashboard</h1>
    <div class="adm-cards">
      <div class="adm-stat"><p class="adm-stat-k">%s / %s</p><p class="adm-stat-v">Signups, past hour / day</p></div>
      <div class="adm-stat"><p class="adm-stat-k">%s</p><p class="adm-stat-v">Sessions online</p></div>
      <div class="adm-stat"><p class="adm-stat-k">%s</p><p class="adm-stat-v">Players</p></div>
      <div class="adm-stat"><p class="adm-stat-k">%s</p><p class="adm-stat-v">Places</p></div>
      <div class="adm-stat"><p class="adm-stat-k">%s</p><p class="adm-stat-v">Catalog items</p></div>
      <div class="adm-stat"><p class="adm-stat-k">%s</p><p class="adm-stat-v">Game jobs</p></div>
    </div>
    <div class="adm-card">
      <h2>Site-wide alert</h2>
      <p class="adm-muted">Empty the text and submit to clear it. Shows on every page.</p>
      <form method="post" action="/admin/alert">
        <label class="adm-label">Alert text</label>
        <input class="adm-input" name="text" value="%s" placeholder="Alert text">
        <label class="adm-label">Optional link</label>
        <input class="adm-input" name="url" value="%s" placeholder="/games-loggedin.html">
        <button class="adm-btn" type="submit">Save alert</button>
      </form>
    </div>
    """ % (
        hour,
        day,
        online,
        len(users),
        len(places),
        len(assets),
        jobs,
        esc(alert.get("text") or ""),
        esc(alert.get("url") or ""),
    )
    return chrome(user, "Dashboard", inner, "dash")


def players_page(user, q):
    query = (q.get("q") or "").strip()
    sort = q.get("sort") or "id"
    rows = db.search_users(query) if query else db.list_users(200)
    if sort == "name":
        rows = sorted(rows, key=lambda u: (u.get("username") or "").lower())
    elif sort == "robux":
        rows = sorted(rows, key=lambda u: int(u.get("robux") or 0), reverse=True)
    bits = []
    for u in rows:
        st = user_status(u)
        badge = "ok" if st == "Ok" else "bad"
        admin_b = '<span class="adm-badge warn">Owner</span>' if is_hard_admin(u) else ""
        if u.get("is_staff") and not is_hard_admin(u):
            admin_b += ' <span class="adm-badge">Staff</span>'
        bits.append(
            "<tr>"
            '<td><a href="/admin/user?id=%s">%s</a></td>'
            '<td><a href="/admin/user?id=%s">%s</a> %s</td>'
            "<td>%s</td>"
            '<td><span class="adm-badge %s">%s</span></td>'
            "<td>R$ %s</td>"
            "</tr>"
            % (
                u["id"],
                u["id"],
                u["id"],
                esc(u.get("username")),
                admin_b,
                esc(fmt_time(u.get("created_at"))),
                badge,
                esc(st),
                int(u.get("robux") or 0),
            )
        )
    inner = """
    <h1>Players</h1>
    <form class="adm-filter" method="get" action="/admin/players">
      <input class="adm-input" name="q" value="%s" placeholder="Search username">
      <select class="adm-input" name="sort">
        <option value="id">Newest</option>
        <option value="name"%s>Name</option>
        <option value="robux"%s>Robux</option>
      </select>
      <button class="adm-btn" type="submit">Search</button>
    </form>
    <div class="adm-card">
      <table class="adm-table">
        <thead><tr><th>#</th><th>Name</th><th>Created</th><th>Status</th><th>Robux</th></tr></thead>
        <tbody>%s</tbody>
      </table>
    </div>
    """ % (
        esc(query),
        " selected" if sort == "name" else "",
        " selected" if sort == "robux" else "",
        "".join(bits) or '<tr><td colspan="5">No players.</td></tr>',
    )
    return chrome(user, "Players", inner, "players")


def user_page(user, q):
    try:
        uid = int(q.get("id") or 0)
    except Exception:
        uid = 0
    target = db.get_user(uid) if uid else None
    if not target:
        return chrome(user, "User", "<h1>User not found</h1>", "players")
    st = user_status(target)
    places = db.places_by_creator(uid)
    inv = db.list_inventory(uid)
    friends = db.list_friends(uid)
    prot = protected_user(target)
    ban_box = ""
    if st == "Banned":
        ban_box = (
            '<div class="adm-warn">Banned. Reason: %s<br>Internal: %s</div>'
            % (esc(target.get("ban_reason") or "—"), esc(target.get("ban_internal") or "—"))
        )
    if prot:
        ban_box += '<div class="adm-info">Hardcoded owner. This account cannot be banned or deleted.</div>'
    actions = []
    if not prot:
        if st == "Banned" or target.get("account_locked"):
            actions.append(
                '<form method="post" action="/admin/unban"><input type="hidden" name="userId" value="%s">'
                '<button class="adm-btn" type="submit">Unban / Unlock</button></form>' % uid
            )
        else:
            actions.append('<a class="adm-btn danger" href="/admin/ban?id=%s">Ban</a>' % uid)
        actions.append(
            '<form method="post" action="/admin/lock"><input type="hidden" name="userId" value="%s">'
            '<button class="adm-btn ghost" type="submit">Lock account</button></form>' % uid
        )
        actions.append(
            '<form method="post" action="/admin/sessions"><input type="hidden" name="userId" value="%s">'
            '<button class="adm-btn ghost" type="submit">Reset sessions</button></form>' % uid
        )
        actions.append(
            '<form method="post" action="/admin/reset-desc"><input type="hidden" name="userId" value="%s">'
            '<button class="adm-btn ghost" type="submit">Reset description</button></form>' % uid
        )
    place_bits = "".join(
        '<li><a href="/game-loggedin.html?id=%s">%s</a></li>' % (p["id"], esc(p.get("name")))
        for p in places
    ) or "<li>None</li>"
    inv_bits = "".join(
        "<li>#%s %s</li>" % (a["id"], esc(a.get("name"))) for a in inv
    ) or "<li>Empty</li>"
    pw_card = ""
    if not prot:
        pw_card = (
            '<div class="adm-card"><h2>Set password</h2>'
            '<form method="post" action="/admin/password">'
            '<input type="hidden" name="userId" value="%s">'
            '<input class="adm-input" name="password" type="password" placeholder="New password" required>'
            '<button class="adm-btn ghost" type="submit">Save password</button></form></div>' % uid
        )
    staff_card = ""
    if is_hard_admin(user) and not prot:
        if target.get("is_staff"):
            staff_card = (
                '<div class="adm-card"><h2>Staff</h2><p class="adm-muted">This player can open Management.</p>'
                '<form method="post" action="/admin/staff">'
                '<input type="hidden" name="userId" value="%s">'
                '<input type="hidden" name="on" value="0">'
                '<button class="adm-btn ghost" type="submit">Remove staff</button></form></div>' % uid
            )
        else:
            staff_card = (
                '<div class="adm-card"><h2>Staff</h2><p class="adm-muted">Grant every Management command except owner protection.</p>'
                '<form method="post" action="/admin/staff">'
                '<input type="hidden" name="userId" value="%s">'
                '<input type="hidden" name="on" value="1">'
                '<button class="adm-btn" type="submit">Make staff</button></form></div>' % uid
            )
    inner = """
    <h1>%s</h1>
    %s
    <div class="adm-split">
      <div class="adm-card">
        <img class="adm-avatar" src="/thumbs/avatar.ashx?userId=%s" alt="">
        <p><span class="adm-badge %s">%s</span></p>
        <p class="adm-muted">Joined %s</p>
        <p>Robux <strong>R$ %s</strong></p>
        <p>Friends %s · Places %s · Items %s</p>
        <p><a href="/profile-loggedin.html?id=%s">View profile</a></p>
        <p class="adm-muted">About</p>
        <p>%s</p>
      </div>
      <div>
        <div class="adm-card">
          <h2>Account actions</h2>
          <div class="adm-actions">%s</div>
        </div>
        <div class="adm-card">
          <h2>Give Robux</h2>
          <form method="post" action="/admin/robux">
            <input type="hidden" name="userId" value="%s">
            <input class="adm-input" name="amount" type="number" value="100">
            <button class="adm-btn" type="submit">Add Robux</button>
          </form>
        </div>
        <div class="adm-card">
          <h2>Send message</h2>
          <form method="post" action="/admin/message">
            <input type="hidden" name="userId" value="%s">
            <input class="adm-input" name="subject" placeholder="Subject">
            <textarea class="adm-input" name="body" rows="3" placeholder="Message"></textarea>
            <button class="adm-btn" type="submit">Send</button>
          </form>
        </div>
        <div class="adm-card">
          <h2>Grant catalog item</h2>
          <form method="post" action="/admin/grant">
            <input type="hidden" name="userId" value="%s">
            <input class="adm-input" name="assetId" placeholder="Asset ID">
            <button class="adm-btn" type="submit">Grant</button>
          </form>
        </div>
        %s
        %s
      </div>
    </div>
    <div class="adm-split">
      <div class="adm-card"><h2>Places</h2><ul>%s</ul></div>
      <div class="adm-card"><h2>Inventory</h2><ul>%s</ul></div>
    </div>
    """ % (
        esc(target.get("username")),
        ban_box,
        uid,
        "ok" if st == "Ok" else "bad",
        esc(st),
        esc(fmt_time(target.get("created_at"))),
        int(target.get("robux") or 0),
        len(friends),
        len(places),
        len(inv),
        uid,
        esc(target.get("blurb") or "No description."),
        "".join(actions) or "<p class=\"adm-muted\">No actions on this account.</p>",
        uid,
        uid,
        uid,
        pw_card,
        staff_card,
        place_bits,
        inv_bits,
    )
    return chrome(user, target.get("username") or "User", inner, "players")


def ban_page(user, q):
    try:
        uid = int(q.get("id") or 0)
    except Exception:
        uid = 0
    target = db.get_user(uid) if uid else None
    if not target:
        return chrome(user, "Ban", "<h1>User not found</h1>", "players")
    if protected_user(target):
        return chrome(user, "Ban", "<h1>Cannot ban the hardcoded owner.</h1>", "players")
    fills = "".join(
        '<button type="button" class="adm-chip" data-fill="%s">%s</button>'
        % (esc(text), esc(name))
        for name, text in BAN_REASONS
    )
    inner = """
    <h1>Ban %s</h1>
    <div class="adm-card">
      <form method="post" action="/admin/ban">
        <input type="hidden" name="userId" value="%s">
        <label class="adm-label">Reason (shown to user)</label>
        <textarea class="adm-input" id="ban-reason" name="reason" rows="4" required></textarea>
        <label class="adm-label">Internal reason (staff only)</label>
        <textarea class="adm-input" name="internal" rows="2" required></textarea>
        <label class="adm-label">Length</label>
        <select class="adm-input" name="length">
          <option value="permanent">Permanent</option>
          <option value="1d">1 Day</option>
          <option value="7d">1 Week</option>
          <option value="warn">Warning (1 second)</option>
        </select>
        <p class="adm-muted">Quick fill</p>
        <div class="adm-chips">%s</div>
        <button class="adm-btn danger" type="submit">Submit ban</button>
      </form>
    </div>
    <script>
    (function(){
      var ta=document.getElementById('ban-reason');
      var chips=document.querySelectorAll('.adm-chip');
      for (var i=0;i<chips.length;i++){
        chips[i].addEventListener('click', function(){ ta.value=this.getAttribute('data-fill')||''; });
      }
    })();
    </script>
    """ % (
        esc(target.get("username")),
        uid,
        fills,
    )
    return chrome(user, "Ban", inner, "players")


def logs_page(user):
    rows = list_logs(120)
    bits = []
    for r in rows:
        bits.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (
                esc(fmt_time(r.get("created_at"))),
                esc(r.get("actor_name") or r.get("actor_id")),
                esc(r.get("action")),
                esc(r.get("target")),
                esc(r.get("detail")),
            )
        )
    inner = """
    <h1>Logs</h1>
    <div class="adm-card">
      <table class="adm-table">
        <thead><tr><th>When</th><th>Staff</th><th>Action</th><th>Target</th><th>Detail</th></tr></thead>
        <tbody>%s</tbody>
      </table>
    </div>
    """ % (
        "".join(bits) or '<tr><td colspan="5">No logs yet.</td></tr>'
    )
    return chrome(user, "Logs", inner, "logs")


def groups_page(user):
    groups = db.list_groups_detailed()
    bits = []
    for g in groups:
        bits.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"
            '<td><form method="post" action="/admin/group/delete" class="inline">'
            '<input type="hidden" name="groupId" value="%s">'
            '<button class="adm-btn ghost" type="submit">Delete</button></form></td></tr>'
            % (
                g["id"],
                esc(g.get("name")),
                esc(g.get("owner_name") or ""),
                int(g.get("member_count") or 0),
                g["id"],
            )
        )
    inner = """
    <h1>Groups</h1>
    <div class="adm-card">
      <table class="adm-table">
        <thead><tr><th>#</th><th>Name</th><th>Owner</th><th>Members</th><th></th></tr></thead>
        <tbody>%s</tbody>
      </table>
    </div>
    """ % (
        "".join(bits) or '<tr><td colspan="5">No groups.</td></tr>'
    )
    return chrome(user, "Groups", inner, "groups")


def places_page(user):
    places = db.list_places()
    bits = []
    for p in places:
        cr = db.get_user(p.get("creator_id") or 0)
        bits.append(
            "<tr><td>%s</td><td><a href=\"/game-loggedin.html?id=%s\">%s</a></td><td>%s</td><td>%s</td>"
            '<td><form method="post" action="/admin/place/delete" class="inline">'
            '<input type="hidden" name="placeId" value="%s">'
            '<button class="adm-btn ghost" type="submit">Delete</button></form></td></tr>'
            % (
                p["id"],
                p["id"],
                esc(p.get("name")),
                esc((cr or {}).get("username") or "ROBLOX"),
                int(p.get("visits") or 0),
                p["id"],
            )
        )
    inner = """
    <h1>Places</h1>
    <div class="adm-card">
      <table class="adm-table">
        <thead><tr><th>#</th><th>Name</th><th>Creator</th><th>Visits</th><th></th></tr></thead>
        <tbody>%s</tbody>
      </table>
    </div>
    """ % (
        "".join(bits) or '<tr><td colspan="5">No places.</td></tr>'
    )
    return chrome(user, "Places", inner, "places")


def catalog_page(user):
    assets = db.list_assets()
    bits = []
    for a in assets:
        cr = db.get_user(a.get("creator_id") or 0)
        bits.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>R$ %s</td>"
            '<td><form method="post" action="/admin/asset/delete" class="inline">'
            '<input type="hidden" name="assetId" value="%s">'
            '<button class="adm-btn ghost" type="submit">Delete</button></form></td></tr>'
            % (
                a["id"],
                esc(a.get("name")),
                esc(a.get("asset_type")),
                esc((cr or {}).get("username") or ""),
                int(a.get("price") or 0),
                a["id"],
            )
        )
    inner = """
    <h1>Catalog</h1>
    <div class="adm-card">
      <h2>Create item</h2>
      <form method="post" action="/admin/asset/create">
        <input class="adm-input" name="name" placeholder="Name" required>
        <select class="adm-input" name="asset_type">
          <option>Hat</option><option>Hair</option><option>Face</option>
          <option>Shirt</option><option>Pants</option><option>Gear</option><option>Accessory</option>
        </select>
        <input class="adm-input" name="price" type="number" value="0">
        <input class="adm-input" name="description" placeholder="Description">
        <button class="adm-btn" type="submit">Create</button>
      </form>
    </div>
    <div class="adm-card">
      <table class="adm-table">
        <thead><tr><th>#</th><th>Name</th><th>Type</th><th>Creator</th><th>Price</th><th></th></tr></thead>
        <tbody>%s</tbody>
      </table>
    </div>
    """ % (
        "".join(bits) or '<tr><td colspan="6">Catalog empty.</td></tr>'
    )
    return chrome(user, "Catalog", inner, "catalog")


def create_user_page(user):
    inner = """
    <h1>Create Player</h1>
    <div class="adm-card">
      <form method="post" action="/admin/user/create">
        <label class="adm-label">Username</label>
        <input class="adm-input" name="username" required>
        <label class="adm-label">Password</label>
        <input class="adm-input" name="password" type="password" required>
        <button class="adm-btn" type="submit">Create</button>
      </form>
    </div>
    """
    return chrome(user, "Create Player", inner, "create")


def promo_page(user):
    con = db.connect()
    rows = con.execute("SELECT * FROM promo_codes ORDER BY code").fetchall()
    con.close()
    bits = []
    for r in rows:
        used = "used" if r["redeemed_by"] else "open"
        bits.append(
            "<tr><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (esc(r["code"]), esc(r["reward"] or ""), used)
        )
    inner = """
    <h1>Promo Codes</h1>
    <div class="adm-card">
      <form method="post" action="/admin/promo">
        <input class="adm-input" name="code" placeholder="CODE" required>
        <input class="adm-input" name="reward" placeholder="robux:100" value="robux:100">
        <button class="adm-btn" type="submit">Add code</button>
      </form>
    </div>
    <div class="adm-card">
      <table class="adm-table">
        <thead><tr><th>Code</th><th>Reward</th><th>Status</th></tr></thead>
        <tbody>%s</tbody>
      </table>
    </div>
    """ % (
        "".join(bits) or '<tr><td colspan="3">No codes.</td></tr>'
    )
    return chrome(user, "Promo Codes", inner, "promo")


def deny_page():
    return _html(
        """<!DOCTYPE html>
<html class="adm-html">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Forbidden</title>
<link rel="stylesheet" href="/static/admin.css">
<style>
body{background:#191b1d;color:#fff;font-family:Arial,Helvetica,sans-serif;padding:40px}
h1{color:#fff}p{color:#bdbebe}a{color:#00a2ff}
</style>
</head>
<body class="adm-body">
<div class="adm-main" style="max-width:640px;margin:40px auto">
<h1>Forbidden</h1>
<p>You do not have access to Management.</p>
<p><a href="/home-loggedin.html">Back to ROBLOX</a></p>
</div>
</body>
</html>""",
        403,
    )


def handle(method, path, low, q, user, req):
    if not (low == "/admin" or low.startswith("/admin/") or low.startswith("/admin.html")):
        return None
    if not user:
        req.redirect("/signup.html")
        return False
    user = refresh_user(user)
    if is_blocked(user):
        return blocked_page(user)
    if not is_admin(user):
        return deny_page()

    if method == "POST":
        form = req.parse_form()
        dest = _post(user, low, form)
        if dest:
            req.redirect(dest)
            return False

    m = re.match(r"^/admin/manage-user/(\d+)", low)
    if m:
        q = dict(q)
        q["id"] = m.group(1)
        return _html(user_page(user, q))
    m = re.match(r"^/admin/ban-user/(\d+)", low)
    if m:
        q = dict(q)
        q["id"] = m.group(1)
        return _html(ban_page(user, q))

    if low in ("/admin", "/admin/", "/admin.html"):
        return _html(dash_page(user))
    if low.startswith("/admin/players"):
        return _html(players_page(user, q))
    if low.startswith("/admin/user/create"):
        return _html(create_user_page(user))
    if low.startswith("/admin/user"):
        return _html(user_page(user, q))
    if low.startswith("/admin/ban"):
        return _html(ban_page(user, q))
    if low.startswith("/admin/logs"):
        return _html(logs_page(user))
    if low.startswith("/admin/groups"):
        return _html(groups_page(user))
    if low.startswith("/admin/places"):
        return _html(places_page(user))
    if low.startswith("/admin/catalog"):
        return _html(catalog_page(user))
    if low.startswith("/admin/promo"):
        return _html(promo_page(user))
    return _html(dash_page(user))


def _post(actor, low, form):
    if low.startswith("/admin/alert"):
        set_alert(form.get("text") or "", form.get("url") or "")
        log_action(actor, "SetAlert", "", form.get("text") or "(cleared)")
        return "/admin"
    if low.startswith("/admin/ban") and form.get("userId"):
        uid = int(form.get("userId") or 0)
        target = db.get_user(uid)
        if not target or protected_user(target):
            return "/admin/user?id=%s" % uid
        length = form.get("length") or "permanent"
        until = 0
        now = int(time.time())
        if length == "1d":
            until = now + 86400
        elif length == "7d":
            until = now + 86400 * 7
        elif length == "warn":
            until = now + 1
        con = db.connect()
        con.execute(
            "UPDATE users SET banned=1, ban_reason=?, ban_internal=?, ban_until=? WHERE id=?",
            (form.get("reason") or "", form.get("internal") or "", until, uid),
        )
        con.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
        con.commit()
        con.close()
        log_action(actor, "BanUser", target.get("username"), form.get("reason") or "")
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/unban"):
        uid = int(form.get("userId") or 0)
        con = db.connect()
        con.execute(
            "UPDATE users SET banned=0, ban_reason='', ban_internal='', ban_until=0, account_locked=0 WHERE id=?",
            (uid,),
        )
        con.commit()
        con.close()
        log_action(actor, "UnbanUser", uid)
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/lock"):
        uid = int(form.get("userId") or 0)
        target = db.get_user(uid)
        if target and not protected_user(target):
            con = db.connect()
            con.execute("UPDATE users SET account_locked=1 WHERE id=?", (uid,))
            con.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
            con.commit()
            con.close()
            log_action(actor, "LockAccount", target.get("username"))
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/sessions"):
        uid = int(form.get("userId") or 0)
        db.delete_other_sessions(uid, "")
        log_action(actor, "ResetSessions", uid)
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/reset-desc"):
        uid = int(form.get("userId") or 0)
        target = db.get_user(uid)
        if target and not protected_user(target):
            db.update_user(uid, blurb="", status="")
            log_action(actor, "ResetDescription", target.get("username"))
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/robux"):
        uid = int(form.get("userId") or 0)
        try:
            amt = int(form.get("amount") or 0)
        except Exception:
            amt = 0
        if amt:
            con = db.connect()
            con.execute("UPDATE users SET robux = IFNULL(robux,0) + ? WHERE id=?", (amt, uid))
            con.commit()
            con.close()
            log_action(actor, "GiveUserRobux", uid, str(amt))
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/message"):
        uid = int(form.get("userId") or 0)
        db.send_message(actor["id"], uid, form.get("body") or "", form.get("subject") or "Staff message")
        log_action(actor, "MessageUser", uid)
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/grant"):
        uid = int(form.get("userId") or 0)
        try:
            aid = int(form.get("assetId") or 0)
        except Exception:
            aid = 0
        if aid:
            db.grant_asset(uid, aid)
            log_action(actor, "GiveUserItem", uid, str(aid))
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/user/create"):
        created = db.create_user(form.get("username") or "", form.get("password") or "")
        if created:
            log_action(actor, "CreateUser", created.get("username"))
            return "/admin/user?id=%s" % created["id"]
        return "/admin/user/create"
    if low.startswith("/admin/group/delete"):
        gid = int(form.get("groupId") or 0)
        con = db.connect()
        con.execute("DELETE FROM group_members WHERE group_id=?", (gid,))
        con.execute("DELETE FROM groups WHERE id=?", (gid,))
        con.commit()
        con.close()
        log_action(actor, "DeleteGroup", gid)
        return "/admin/groups"
    if low.startswith("/admin/place/delete"):
        pid = int(form.get("placeId") or 0)
        con = db.connect()
        con.execute("DELETE FROM places WHERE id=?", (pid,))
        con.commit()
        con.close()
        log_action(actor, "DeletePlace", pid)
        return "/admin/places"
    if low.startswith("/admin/asset/delete"):
        aid = int(form.get("assetId") or 0)
        con = db.connect()
        con.execute("DELETE FROM wearing WHERE asset_id=?", (aid,))
        con.execute("DELETE FROM inventory WHERE asset_id=?", (aid,))
        con.execute("DELETE FROM assets WHERE id=?", (aid,))
        con.commit()
        con.close()
        log_action(actor, "DeleteAsset", aid)
        return "/admin/catalog"
    if low.startswith("/admin/asset/create"):
        aid = db.create_asset(
            actor["id"],
            form.get("name") or "Item",
            form.get("asset_type") or "Hat",
            form.get("description") or "",
            "",
            "",
            form.get("price") or 0,
        )
        log_action(actor, "CreateAsset", aid, form.get("name") or "")
        return "/admin/catalog"
    if low.startswith("/admin/promo"):
        code = (form.get("code") or "").strip()
        reward = (form.get("reward") or "robux:0").strip()
        if code:
            con = db.connect()
            try:
                con.execute(
                    "INSERT OR REPLACE INTO promo_codes (code, reward, redeemed_by) VALUES (?,?,NULL)",
                    (code, reward),
                )
                con.commit()
            finally:
                con.close()
            log_action(actor, "CreatePromo", code, reward)
        return "/admin/promo"
    if low.startswith("/admin/password"):
        uid = int(form.get("userId") or 0)
        target = db.get_user(uid)
        newpw = form.get("password") or ""
        if target and newpw and not protected_user(target):
            con = db.connect()
            con.execute("UPDATE users SET password_hash=? WHERE id=?", (db._hash(newpw), uid))
            con.commit()
            con.close()
            log_action(actor, "NullifyPassword", target.get("username"))
        return "/admin/user?id=%s" % uid
    if low.startswith("/admin/staff"):
        uid = int(form.get("userId") or 0)
        target = db.get_user(uid)
        if is_hard_admin(actor) and target and not protected_user(target):
            flag = 1 if str(form.get("on") or "") == "1" else 0
            con = db.connect()
            con.execute(
                "UPDATE users SET is_staff=?, staff_role=? WHERE id=?",
                (flag, "Staff" if flag else "", uid),
            )
            con.commit()
            con.close()
            log_action(actor, "ManageStaff", target.get("username"), "on" if flag else "off")
        return "/admin/user?id=%s" % uid
    return "/admin"
