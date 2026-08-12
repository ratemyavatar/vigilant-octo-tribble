"""Strip snapshot Roblox data from dump HTML and fill the same classes from the DB."""
from __future__ import annotations

import html as htmlmod
import re
import time
from datetime import datetime

import database as db


def esc(s) -> str:
    return htmlmod.escape("" if s is None else str(s))


def _match_end(html: str, start: int, tag: str) -> int:
    open_re = re.compile(r"<" + re.escape(tag) + r"\b", re.I)
    close_re = re.compile(r"</" + re.escape(tag) + r"\s*>", re.I)
    pos = html.find(">", start) + 1
    if pos <= 0:
        return len(html)
    depth = 1
    while depth > 0 and pos < len(html):
        mo = open_re.search(html, pos)
        mc = close_re.search(html, pos)
        if mc is None:
            return len(html)
        if mo and mo.start() < mc.start():
            depth += 1
            pos = mo.end()
        else:
            depth -= 1
            pos = mc.end()
    return pos


def remove_elements_with_class(html: str, class_name: str) -> str:
    out = []
    i = 0
    token = class_name.lower()
    lower = html.lower()
    word = re.compile(r'(?:^|[\s"\'=])' + re.escape(class_name) + r'(?:[\s"\']|$)', re.I)
    while True:
        idx = lower.find(token, i)
        if idx < 0:
            out.append(html[i:])
            break
        start = html.rfind("<", i, idx)
        if start < 0:
            i = idx + len(token)
            continue
        if html[start + 1 : start + 2] == "/":
            i = idx + len(token)
            continue
        m = re.match(r"<([a-zA-Z0-9]+)", html[start:])
        if not m:
            i = idx + len(token)
            continue
        gt = html.find(">", start)
        if gt < 0:
            out.append(html[i:])
            break
        taghtml = html[start : gt + 1]
        if not word.search(taghtml):
            i = idx + len(token)
            continue
        tag = m.group(1)
        out.append(html[i:start])
        if taghtml.rstrip().endswith("/>") or tag.lower() in (
            "img",
            "input",
            "br",
            "hr",
            "meta",
            "link",
        ):
            i = gt + 1
        else:
            i = _match_end(html, start, tag)
        lower = html.lower()
    return "".join(out)


def empty_uls(html: str, class_tokens) -> str:
    for token in class_tokens:
        html = re.sub(
            r"(<ul\b[^>]*\b" + re.escape(token) + r"\b[^>]*>).*?(</ul>)",
            r"\1\2",
            html,
            flags=re.I | re.S,
        )
    return html


def replace_ul_inner(html: str, class_hint: str, inner: str, count: int = 0) -> str:
    return re.sub(
        r"(<ul\b[^>]*\b" + class_hint + r"\b[^>]*>)(.*?)(</ul>)",
        lambda m: m.group(1) + inner + m.group(3),
        html,
        count=count,
        flags=re.I | re.S,
    )


def sanitize(html: str) -> str:
    html = empty_uls(
        html,
        (
            "friend-list",
            "item-cards",
            "game-cards",
            "game-tile-list",
            "list-gallery",
            "request-list",
            "inbox-list",
            "sent-list",
            "group-list",
            "my-group-list",
            "trade-list",
            "server-list",
            "group-member-list",
        ),
    )
    for cls in (
        "large-game-tile",
        "GroupMember",
    ):
        html = remove_elements_with_class(html, cls)
    html = re.sub(
        r'(<ul[^>]*id=["\']FeaturedGamesContainer["\'][^>]*>).*?(</ul>)',
        r"\1\2",
        html,
        flags=re.I | re.S,
    )
    html = re.sub(
        r"(<div id=recently-visited-places-content>).*?(</div>)",
        r"\1\2",
        html,
        flags=re.I | re.S,
    )
    html = re.sub(
        r'(<div id="recently-visited-places-content">).*?(</div>)',
        r"\1\2",
        html,
        flags=re.I | re.S,
    )
    html = re.sub(r"Friends\s*\(\d+\)", "Friends (0)", html)
    html = re.sub(
        r"Amigos<span[^>]*>\(\d+\)</span>",
        'Friends<span class="friends-count">(0)</span>',
        html,
    )
    html = re.sub(r'data-friendscount="\d+"', 'data-friendscount="0"', html)
    html = re.sub(r'data-followerscount="\d+"', 'data-followerscount="0"', html)
    html = re.sub(r'data-followingscount="\d+"', 'data-followingscount="0"', html)
    html = re.sub(r'data-count=["\']?\d+', 'data-count="0"', html)
    html = re.sub(r"Hello,\s*Player!", "Hello, {{USERNAME}}!", html)
    html = re.sub(r'data-name="Player"', 'data-name="{{USERNAME}}"', html)
    html = re.sub(r'data-displayname="Player"', 'data-displayname="{{USERNAME}}"', html)
    html = re.sub(r'data-displayname="a_randomperson"', 'data-displayname="{{USERNAME}}"', html)
    html = re.sub(r"(notification-red[^>]*>)\s*\d+", r"\g<1>0", html)
    html = re.sub(r"(notification-blue[^>]*>)\s*\d+", r"\g<1>0", html)
    html = re.sub(r"(btr-nav-notif[^>]*>)\s*\d+", r"\g<1>0", html)
    html = re.sub(r"@Player", "@{{USERNAME}}", html)
    html = re.sub(r">Player<", ">{{USERNAME}}<", html)
    html = re.sub(r"Player:", "{{USERNAME}}:", html)
    html = re.sub(
        r"(<ul\b[^>]*\bblog-news\b[^>]*>).*?(</ul>)",
        r"\1\2",
        html,
        flags=re.I | re.S,
    )
    html = re.sub(r'data-name="Player"', 'data-name="{{USERNAME}}"', html)
    html = re.sub(r"notification-red nav-setting-highlight\">\d+", 'notification-red nav-setting-highlight">0', html)
    return html


def game_card(place: dict, suffix: str) -> str:
    pid = place["id"]
    name = esc(place.get("name") or "Untitled")
    href = "/game%s?id=%s" % (suffix, pid)
    thumb = "/thumbs/place.ashx?id=%s" % pid
    return (
        '<li class="list-item game-card game-tile" title="%s">'
        '<div class="game-card-container">'
        '<a class="game-card-link" href="%s">'
        '<div class="game-card-thumb-container">'
        '<span class="thumbnail-2d-container game-card-thumb">'
        '<img src="%s" alt="%s" title="%s">'
        "</span></div>"
        '<div class="game-card-name game-name-title" title="%s">%s</div>'
        '<div class="game-card-info">'
        '<span class="info-label icon-playing-counts-gray"><svg class="rbx-icon icon-sm"><use href="#icon-playing"></use></svg></span>'
        '<span class="info-label playing-counts-label">%s</span>'
        "</div></a></div></li>"
    ) % (name, href, thumb, name, name, name, name, int(place.get("visits") or 0))


def friend_card(user: dict, suffix: str) -> str:
    uid = user["id"]
    name = esc(user.get("username") or "")
    return (
        '<li id="friend_%s" class="list-item friend">'
        '<div class="avatar-container">'
        '<a href="/profile%s?id=%s" class="avatar avatar-card-fullbody friend-link" title="%s">'
        '<span class="avatar-card-link friend-avatar">'
        '<img alt="%s" class="avatar-card-image" src="/thumbs/headshot.ashx?userId=%s">'
        '</span><span class="text-overflow friend-name">%s</span></a></div></li>'
    ) % (uid, suffix, uid, name, name, uid, name)


def _type_icon(asset_type) -> str:
    m = {
        "Hat": "icon-hat",
        "Hair": "icon-hair",
        "Face": "icon-face",
        "Shirt": "icon-shirt",
        "T-Shirt": "icon-shirt",
        "Pants": "icon-pants",
        "Gear": "icon-gear",
        "Accessory": "icon-accessory",
    }
    return m.get(asset_type or "Hat", "icon-accessory")


def item_card(asset: dict, buy: bool = False, wear: bool = False, wearing: bool = False) -> str:
    aid = asset["id"]
    name = esc(asset.get("name") or "Item")
    price = int(asset.get("price") or 0)
    extra = ""
    if buy:
        extra = (
            '<form method="post" action="/catalog/buy" class="item-buy-form">'
            '<input type="hidden" name="id" value="%s">'
            '<button type="submit" class="btn-primary-xs">Buy</button></form>' % aid
        )
    elif wearing:
        extra = (
            '<form method="post" action="/avatar/unwear" class="item-buy-form">'
            '<input type="hidden" name="id" value="%s">'
            '<button type="submit" class="btn-secondary-xs">Remove</button></form>' % aid
        )
    elif wear:
        extra = (
            '<form method="post" action="/avatar/wear" class="item-buy-form">'
            '<input type="hidden" name="id" value="%s">'
            '<button type="submit" class="btn-secondary-xs">Wear</button></form>' % aid
        )
    return (
        '<li class="list-item item-card">'
        '<div class="item-card-container">'
        '<a href="#" class="item-card-link">'
        '<div class="item-card-thumb-container">'
        '<img class="item-card-thumb" src="/thumbs/asset.ashx?id=%s" alt="%s">'
        '<span class="item-type-badge"><svg class="rbx-icon icon-sm"><use href="#%s"></use></svg></span>'
        "</div>"
        '<div class="text-overflow item-card-name" title="%s">%s</div>'
        "</a>"
        '<div class="text-overflow item-card-price">'
        '<span class="icon-robux-16x16"></span><span class="text-robux">%s</span>'
        "</div>%s</div></li>"
    ) % (aid, name, _type_icon(asset.get("asset_type")), name, name, price, extra)


def people_card(user: dict, suffix: str) -> str:
    return friend_card(user, suffix)


def _suffix(logged_in: bool) -> str:
    return "-loggedin.html" if logged_in else ".html"


def fill_games(html: str, places: list, suffix: str) -> str:
    cards = "".join(game_card(p, suffix) for p in places)
    if not cards:
        html = re.sub(
            r"(No Search Results Found)",
            r"\1",
            html,
            count=1,
        )
        return html
    html = replace_ul_inner(html, "game-tile-list", cards, count=1)
    html = replace_ul_inner(html, "game-cards", cards, count=1)
    html = re.sub(
        r'(<div id=recently-visited-places-content>)</div>',
        r"\1<ul class=\"hlist games game-cards\">%s</ul></div>" % cards,
        html,
        count=1,
    )
    html = re.sub(
        r'(<div id="recently-visited-places-content">)</div>',
        r'\1<ul class="hlist games game-cards">%s</ul></div>' % cards,
        html,
        count=1,
    )
    if cards:
        html = html.replace(
            '<p class="list-content">No Search Results Found</p>',
            "",
            1,
        )
    return html


def fill_friends(html: str, friends: list, suffix: str) -> str:
    n = len(friends)
    html = re.sub(r"Friends\s*\(\d+\)", "Friends (%s)" % n, html)
    html = re.sub(
        r'(<span class="friends-count"[^>]*>)\(\d+\)',
        r"\g<1>(%s)" % n,
        html,
    )
    html = replace_ul_inner(html, "friend-list", "".join(friend_card(u, suffix) for u in friends))
    return html


def fill_catalog(html: str, assets: list, buy: bool = False) -> str:
    cards = "".join(item_card(a, buy=buy) for a in assets)
    html = replace_ul_inner(html, "item-cards", cards)
    if cards:
        html = html.replace('<p class="list-content">No Search Results Found</p>', "", 1)
    return html


def fill_game_detail(html: str, place: dict, suffix: str) -> str:
    name = esc(place.get("name") or "Untitled")
    desc = esc(place.get("description") or "")
    pid = place["id"]
    creator = db.get_user(place.get("creator_id") or 0)
    cname = esc(creator["username"]) if creator else "ROBLOX"
    cid = creator["id"] if creator else 0
    maxp = place.get("max_players") or 10
    genre = esc(place.get("genre") or "All")
    created = datetime.utcfromtimestamp(int(place.get("created_at") or time.time())).strftime("%m/%d/%Y")
    html = html.replace("{{GAME_NAME}}", name)
    html = html.replace("{{GAME_DESC}}", desc)
    html = html.replace("{{GAME_ID}}", str(pid))
    html = html.replace("{{CREATOR_NAME}}", cname)
    html = html.replace("{{CREATOR_ID}}", str(cid))
    html = html.replace("{{MAX_PLAYERS}}", str(maxp))
    html = html.replace("{{GENRE}}", genre)
    html = html.replace("{{CREATED}}", created)
    html = html.replace("{{VISITS}}", str(int(place.get("visits") or 0)))
    html = html.replace("{{PLAYING}}", "0")
    html = html.replace("/profile.html?id=", "/profile%s?id=" % suffix)
    return html



def request_card(user: dict) -> str:
    uid = user["id"]
    name = esc(user.get("username") or "")
    return (
        '<li class="list-item"><div class="list-body">'
        '<a href="/profile-loggedin.html?id=%s">%s</a> '
        '<form method="post" action="/friends/accept" class="inline-form">'
        '<input type="hidden" name="userId" value="%s">'
        '<button type="submit" class="btn-primary-xs">Accept</button></form> '
        '<form method="post" action="/friends/decline" class="inline-form">'
        '<input type="hidden" name="userId" value="%s">'
        '<button type="submit" class="btn-secondary-xs">Decline</button></form>'
        "</div></li>"
    ) % (uid, name, uid, uid)


def group_card(group: dict, joined=False) -> str:
    gid = group["id"]
    name = esc(group.get("name") or "Group")
    desc = esc(group.get("description") or "")
    members = int(group.get("member_count") or 0)
    owner = esc(group.get("owner_name") or "")
    join = ""
    if not joined:
        join = (
            '<form method="post" action="/groups/join" class="inline-form">'
            '<input type="hidden" name="groupId" value="%s">'
            '<button type="submit" class="btn-secondary-xs">Join</button></form>' % gid
        )
    return (
        '<li class="list-item group-card"><div class="list-body">'
        '<h2><a href="/groups.html?id=%s">%s</a></h2>'
        '<p class="list-content">%s</p>'
        '<p class="text-label">%s · Members %s</p>%s</div></li>'
    ) % (gid, name, desc, owner, members, join)


def trade_card(trade: dict, user_id: int) -> str:
    tid = trade["id"]
    other = trade["to_id"] if trade["from_id"] == user_id else trade["from_id"]
    other_u = db.get_user(other)
    name = esc((other_u or {}).get("username") or "User")
    status = esc(trade.get("status") or "open")
    items = db.list_trade_items(tid)
    names = ", ".join(esc(i.get("name") or "") for i in items) or "No items"
    actions = ""
    if status == "open" and trade["to_id"] == user_id:
        actions = (
            '<form method="post" action="/trades/accept" class="inline-form">'
            '<input type="hidden" name="id" value="%s">'
            '<button type="submit" class="btn-primary-xs">Accept</button></form> '
            '<form method="post" action="/trades/decline" class="inline-form">'
            '<input type="hidden" name="id" value="%s">'
            '<button type="submit" class="btn-secondary-xs">Decline</button></form>'
            % (tid, tid)
        )
    return (
        '<li class="list-item"><div class="list-body"><h2>Trade #%s with %s</h2>'
        '<p class="text-label">%s</p><p class="list-content">%s</p>%s</div></li>'
    ) % (tid, name, status, names, actions)


def message_item(m: dict, sent=False) -> str:
    who = esc(m.get("to_name") if sent else m.get("from_name") or "")
    label = "To" if sent else "From"
    return (
        '<li class="list-item"><div class="list-body"><h2>%s</h2>'
        '<p class="text-label">%s %s</p>'
        '<p class="list-content">%s</p></div></li>'
        % (
            esc(m.get("subject") or "(no subject)"),
            label,
            who,
            esc(m.get("body") or ""),
        )
    )


def fill_ul(html: str, class_hint: str, cards: str, count: int = 1) -> str:
    return replace_ul_inner(html, class_hint, cards, count=count)


def _opts(choices, current) -> str:
    out = []
    for c in choices:
        sel = " selected" if str(c) == str(current) else ""
        out.append('<option value="%s"%s>%s</option>' % (esc(c), sel, esc(c)))
    return "".join(out)


def _checked(val) -> str:
    return "checked" if val else ""



BRICKCOLORS = [
    ("#F5CD30", "Bright yellow"),
    ("#DA8541", "Bright orange"),
    ("#C4281C", "Bright red"),
    ("#0D69AC", "Bright blue"),
    ("#4B974B", "Bright green"),
    ("#6B327C", "Bright violet"),
    ("#D7C59A", "Light orange"),
    ("#CC8E69", "Nougat"),
    ("#A05F35", "Brown"),
    ("#694028", "Reddish brown"),
    ("#A3A2A5", "Medium stone grey"),
    ("#1B2A35", "Black"),
    ("#F8F8F8", "White"),
    ("#287F47", "Dark green"),
    ("#2154B9", "Deep blue"),
    ("#FF98DC", "Pink"),
]


def r6_figure(user: dict, wearing=None) -> str:
    s = db.get_user_settings(user)
    head = s.get("head_color") or "#F5CD30"
    torso = s.get("torso_color") or "#0D69AC"
    la = s.get("left_arm_color") or head
    ra = s.get("right_arm_color") or head
    ll = s.get("left_leg_color") or "#4B974B"
    rl = s.get("right_leg_color") or "#4B974B"
    types = {(a.get("asset_type") or "").lower() for a in (wearing or [])}
    hat = ""
    if any(x in types for x in ("hat", "hair", "accessory")):
        hat = '<rect x="46" y="8" width="44" height="10" fill="#2d2f31"/><rect x="40" y="16" width="56" height="6" fill="#232527"/>'
    shirt = ""
    if any(x in types for x in ("shirt", "t-shirt", "tshirt")):
        shirt = '<rect x="44" y="56" width="48" height="10" fill="rgba(255,255,255,0.18)"/>'
    return (
        '<svg class="r6-figure" viewBox="0 0 136 220" role="img" aria-label="Avatar">'
        '<rect class="r6-head" x="44" y="18" width="48" height="48" fill="%s"/>'
        '<rect x="56" y="34" width="6" height="6" fill="#111"/>'
        '<rect x="74" y="34" width="6" height="6" fill="#111"/>'
        '<rect x="58" y="48" width="20" height="4" fill="#111"/>'
        '%s'
        '<rect class="r6-torso" x="44" y="68" width="48" height="62" fill="%s"/>'
        '%s'
        '<rect class="r6-arm-l" x="26" y="68" width="18" height="62" fill="%s"/>'
        '<rect class="r6-arm-r" x="92" y="68" width="18" height="62" fill="%s"/>'
        '<rect class="r6-leg-l" x="44" y="130" width="24" height="70" fill="%s"/>'
        '<rect class="r6-leg-r" x="68" y="130" width="24" height="70" fill="%s"/>'
        "</svg>"
    ) % (head, hat, torso, shirt, la, ra, ll, rl)


def color_swatches() -> str:
    bits = []
    for hexv, name in BRICKCOLORS:
        bits.append(
            '<button type="submit" name="color" value="%s" class="color-dot" style="background:%s" title="%s" aria-label="%s"></button>'
            % (hexv, hexv, name, name)
        )
    return "".join(bits)


def fill_settings(html: str, user: dict) -> str:

    s = db.get_user_settings(user)
    privacy = ["Everyone", "Friends", "No one"]
    html = html.replace("{{DISPLAY_NAME}}", esc(s.get("display_name") or user.get("username") or ""))
    html = html.replace("{{EMAIL}}", esc(s.get("email") or ""))
    html = html.replace("{{BIRTHDAY}}", esc(user.get("birthday") or ""))
    html = html.replace("{{ROBUX}}", str(user.get("robux") or 0))
    html = html.replace("{{SESSION_COUNT}}", str(db.session_count(user["id"])))
    html = html.replace("{{PIN_STATUS}}", "PIN is on." if user.get("pin_hash") else "PIN is off.")
    html = html.replace("{{GENDER_OPTS}}", _opts(["Male", "Female", "Prefer not to say"], user.get("gender") or "Male"))
    html = html.replace("{{LANGUAGE_OPTS}}", _opts(["English", "Spanish", "Portuguese", "French", "German"], s.get("language") or "English"))
    html = html.replace("{{WHO_MESSAGE_OPTS}}", _opts(privacy, s.get("who_message")))
    html = html.replace("{{WHO_CHAT_APP_OPTS}}", _opts(privacy, s.get("who_chat_app")))
    html = html.replace("{{WHO_CHAT_GAME_OPTS}}", _opts(privacy, s.get("who_chat_game")))
    html = html.replace("{{WHO_JOIN_OPTS}}", _opts(privacy, s.get("who_join")))
    html = html.replace("{{WHO_INVENTORY_OPTS}}", _opts(privacy, s.get("who_inventory")))
    html = html.replace("{{WHO_TRADE_OPTS}}", _opts(privacy, s.get("who_trade")))
    html = html.replace("{{WHO_FRIENDS_OPTS}}", _opts(privacy, s.get("who_friends")))
    html = html.replace("{{MATURITY_OPTS}}", _opts(["Minimal", "Mild", "Moderate", "Restricted"], s.get("content_maturity")))
    html = html.replace("{{SPEND_OPTS}}", _opts(["None", "0", "10", "25", "50", "100"], s.get("monthly_spend")))
    html = html.replace("{{TWO_STEP_CHECKED}}", _checked(s.get("two_step")))
    html = html.replace("{{RESTRICTIONS_CHECKED}}", _checked(s.get("account_restrictions")))
    html = html.replace("{{NOTIFY_MESSAGES_CHECKED}}", _checked(s.get("notify_messages")))
    html = html.replace("{{NOTIFY_FRIENDS_CHECKED}}", _checked(s.get("notify_friends")))
    html = html.replace("{{NOTIFY_TRADES_CHECKED}}", _checked(s.get("notify_trades")))
    html = html.replace("{{NOTIFY_UPDATES_CHECKED}}", _checked(s.get("notify_updates")))
    html = html.replace("{{BLURB}}", esc(user.get("blurb") or ""))
    html = html.replace("{{STATUS}}", esc(user.get("status") or ""))
    html = html.replace('value="{{USERNAME}}"', 'value="%s"' % esc(user["username"]))
    html = html.replace("{{USERNAME}}", esc(user["username"]))
    return html


def fill_profile(html: str, viewed: dict, friends: list, places: list, suffix: str) -> str:
    name = esc(viewed.get("username") or "")
    uid = viewed["id"]
    s = db.get_user_settings(viewed)
    joined = datetime.utcfromtimestamp(int(viewed.get("created_at") or time.time())).strftime("%m/%d/%Y")
    blurb = esc(viewed.get("blurb") or "This user has no description.")
    status = esc(viewed.get("status") or "")
    html = html.replace("{{PROFILE_NAME}}", name)
    html = html.replace("{{PROFILE_ID}}", str(uid))
    html = html.replace("{{PROFILE_STATUS}}", status)
    html = html.replace("{{PROFILE_BLURB}}", blurb)
    html = html.replace("{{PROFILE_JOINED}}", joined)
    html = html.replace("{{FRIEND_COUNT}}", str(len(friends)))
    html = html.replace("{{PLACE_VISITS}}", str(db.user_place_visits(uid)))
    html = html.replace("{{DISPLAY_NAME}}", esc(s.get("display_name") or name))
    html = re.sub(
        r'(<h2 class="profile-name"[^>]*>)(.*?)(</h2>)',
        lambda m: m.group(1) + name + m.group(3),
        html,
        count=1,
        flags=re.S,
    )
    html = fill_friends(html, friends, suffix)
    html = fill_games(html, places, suffix)
    return html


def fill_search(html: str, keyword: str, users: list, places: list, suffix: str) -> str:
    cards = "".join(people_card(u, suffix) for u in users)
    games = "".join(game_card(p, suffix) for p in places)
    inner = ""
    if keyword:
        inner += '<p class="list-content">Search: %s</p>' % esc(keyword)
    if users:
        inner += '<div class="container-header"><h3>People</h3></div><ul class="hlist friend-list">%s</ul>' % cards
    if places:
        inner += '<div class="container-header"><h3>Experiences</h3></div><ul class="hlist games game-cards">%s</ul>' % games
    if not users and not places:
        inner += '<p class="list-content">No Search Results Found</p>'
    html = re.sub(
        r'(<p class="list-content">No Search Results Found</p>)',
        inner,
        html,
        count=1,
    )
    return html


SITE_JS = r"""
<script>
(function () {
  var gender = document.getElementById('gender-field');
  var buttons = document.querySelectorAll('.gender-row .gender-button');
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].addEventListener('click', function () {
      for (var j = 0; j < buttons.length; j++) buttons[j].classList.remove('selected');
      this.classList.add('selected');
      if (gender) gender.value = (this.id === 'FemaleButton') ? 'Female' : 'Male';
    });
  }
  var form = document.getElementById('placeForm');
  var finish = document.getElementById('finishButton');
  if (form && finish) {
    finish.addEventListener('click', function (e) {
      e.preventDefault();
      form.submit();
    });
  }
  var tpls = document.querySelectorAll('.template');
  for (var t = 0; t < tpls.length; t++) {
    tpls[t].addEventListener('click', function (e) {
      e.preventDefault();
      var id = this.getAttribute('placeid');
      var inp = document.getElementById('TemplateID');
      if (inp && id) inp.value = id;
      for (var k = 0; k < tpls.length; k++) tpls[k].classList.remove('selected');
      this.classList.add('selected');
    });
  }
  var tabLinks = document.querySelectorAll('[data-tab]');
  var panes = document.querySelectorAll('.settings-tab-pane');
  function showTab(id) {
    if (!id) return;
    for (var i = 0; i < panes.length; i++) panes[i].classList.toggle('active', panes[i].id === id);
    for (var j = 0; j < tabLinks.length; j++) {
      var on = tabLinks[j].getAttribute('data-tab') === id;
      tabLinks[j].classList.toggle('active', on);
      var li = tabLinks[j].closest('.rbx-tab');
      if (li) li.classList.toggle('active', on);
    }
    if (history.replaceState) history.replaceState(null, '', '#' + id);
  }
  for (var tb = 0; tb < tabLinks.length; tb++) {
    tabLinks[tb].addEventListener('click', function (e) {
      e.preventDefault();
      showTab(this.getAttribute('data-tab'));
    });
  }
  if (panes.length && location.hash) showTab(location.hash.replace('#', ''));

  var partBtns = document.querySelectorAll('.color-part');
  var partField = document.getElementById('color-part');
  for (var c = 0; c < partBtns.length; c++) {
    partBtns[c].addEventListener('click', function (e) {
      e.preventDefault();
      for (var k = 0; k < partBtns.length; k++) partBtns[k].classList.remove('selected');
      this.classList.add('selected');
      if (partField) partField.value = this.getAttribute('data-part') || 'all';
    });
  }


  function ensurePlayModal() {
    if (document.getElementById('rbx-play-modal')) return;
    var box = document.createElement('div');
    box.id = 'rbx-play-modal';
    box.className = 'modal-container';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.innerHTML = '<div class="modal-backdrop" id="rbx-play-backdrop"></div>'
      + '<div class="modal-window">'
      + '<div class="modal-header"><h3>Starting ROBLOX</h3>'
      + '<button type="button" class="modal-close" id="rbx-play-close" aria-label="Close">x</button></div>'
      + '<div class="modal-body"><p class="list-content" id="rbx-play-status">ROBLOX is now loading. Get ready!</p>'
      + '<p class="text-lead" id="rbx-play-name"></p></div>'
      + '<div class="modal-btns">'
      + '<a class="btn-secondary-md" href="/download.html">Download</a> '
      + '<button type="button" class="btn-primary-md" id="rbx-play-retry">Retry</button> '
      + '<button type="button" class="btn-secondary-md" id="rbx-play-cancel">Cancel</button>'
      + '</div></div>';
    document.body.appendChild(box);
  }
  var lastPlaceId = '';
  function closePlayModal() {
    var m = document.getElementById('rbx-play-modal');
    if (m) m.classList.remove('open');
  }
  function fireUri(uri) {
    var a = document.createElement('a');
    a.href = uri;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
  function launchPlace(placeId) {
    if (!placeId) return;
    lastPlaceId = String(placeId);
    ensurePlayModal();
    var modal = document.getElementById('rbx-play-modal');
    var status = document.getElementById('rbx-play-status');
    var nameEl = document.getElementById('rbx-play-name');
    if (modal) modal.classList.add('open');
    if (status) status.textContent = 'ROBLOX is now loading. Get ready!';
    if (nameEl) nameEl.textContent = 'Place ' + lastPlaceId;
    fetch('/play?placeId=' + encodeURIComponent(lastPlaceId) + '&json=1', {
      credentials: 'same-origin',
      headers: { 'Accept': 'application/json', 'X-Requested-With': 'XMLHttpRequest' }
    }).then(function (r) {
      if (r.status === 401) { window.location.href = '/signup.html'; return null; }
      return r.json();
    }).then(function (data) {
      if (!data) return;
      if (!data.ok || !data.uri) {
        if (status) status.textContent = data.error || 'Could not start the client.';
        return;
      }
      if (nameEl && data.placeName) nameEl.textContent = data.placeName;
      fireUri(data.uri);
      if (status) status.textContent = 'If the client did not open, install it from Download, then press Retry.';
    }).catch(function () {
      if (status) status.textContent = 'Could not start the client.';
    });
  }
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t) return;
    if (t.id === 'rbx-play-close' || t.id === 'rbx-play-cancel' || t.id === 'rbx-play-backdrop') {
      closePlayModal();
      return;
    }
    if (t.id === 'rbx-play-retry') {
      launchPlace(lastPlaceId);
      return;
    }
    var play = t.closest ? t.closest('.rbx-play-button, .VisitButtonPlayGLI a, a[href*="/play"]') : null;
    if (!play) return;
    var href = play.getAttribute('href') || '';
    var pid = play.getAttribute('data-placeid') || play.getAttribute('placeid') || '';
    var wrap = play.closest('[placeid]');
    if (!pid && wrap) pid = wrap.getAttribute('placeid');
    if (!pid && href.indexOf('placeId=') >= 0) {
      var m = href.match(/placeId=(\d+)/i);
      if (m) pid = m[1];
    }
    if (!pid && href.indexOf('/play') < 0 && !play.classList.contains('rbx-play-button')) return;
    e.preventDefault();
    launchPlace(pid);
  });
  var launchQ = /(?:\\?|&)launch=1(?:&|$)/.exec(location.search);
  if (launchQ) {
    var idm = location.search.match(/[?&]id=(\d+)/);
    if (idm) launchPlace(idm[1]);
  }

  var wrapEl = document.getElementById('wrap');
  var nav = document.getElementById('navigation');
  var menuBtn = document.getElementById('header-menu-icon');
  var overlay = document.getElementById('navigation-overlay');
  function isPhone() { return window.innerWidth < 768; }
  function setExpanded(open) {
    if (menuBtn) menuBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  function closeNav() {
    if (nav) nav.classList.remove('nav-show');
    if (wrapEl) wrapEl.classList.remove('nav-open');
    setExpanded(false);
  }
  function toggleNav(e) {
    if (e) e.preventDefault();
    if (!wrapEl || !nav) return;
    if (isPhone() || wrapEl.classList.contains('logged-out')) {
      var open = !nav.classList.contains('nav-show');
      nav.classList.toggle('nav-show', open);
      wrapEl.classList.toggle('nav-open', open);
      setExpanded(open);
    } else {
      wrapEl.classList.toggle('nav-collapsed');
      setExpanded(!wrapEl.classList.contains('nav-collapsed'));
    }
  }
  if (menuBtn) {
    menuBtn.addEventListener('click', toggleNav);
    menuBtn.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') toggleNav(e);
    });
  }
  if (overlay) overlay.addEventListener('click', closeNav);

  var setBtn = document.getElementById('nav-settings');
  var setMenu = document.getElementById('settings-popover');
  if (setBtn && setMenu) {
    setBtn.addEventListener('click', function (e) {
      e.preventDefault();
      var open = !setMenu.classList.contains('open');
      setMenu.classList.toggle('open', open);
      setBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  var loginToggle = document.getElementById('navbar-login-toggle');
  var loginBar = document.querySelector('.navbar-login-bar');
  if (loginToggle && loginBar) {
    loginToggle.addEventListener('click', function (e) {
      e.preventDefault();
      loginBar.classList.toggle('open');
    });
  }

  document.addEventListener('click', function (e) {
    var t = e.target;
    if (setMenu && setBtn && !setMenu.contains(t) && !setBtn.contains(t)) {
      setMenu.classList.remove('open');
      setBtn.setAttribute('aria-expanded', 'false');
    }
    if (loginBar && loginToggle && !loginBar.contains(t) && !loginToggle.contains(t)) {
      loginBar.classList.remove('open');
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
      closeNav();
      if (setMenu) setMenu.classList.remove('open');
      if (loginBar) loginBar.classList.remove('open');
      closePlayModal();
    }
  });
})();
</script>
"""



def prepare(html: str, page_name: str, user: dict | None, qs: dict) -> str:
    logged_in = user is not None
    suffix = _suffix(logged_in)
    html = sanitize(html)
    name = (page_name or "").lower()

    keyword = qs.get("keyword") or qs.get("search") or qs.get("q") or ""
    genre = qs.get("genre") or "All"
    sort = qs.get("sort") or "new"
    category = qs.get("category") or qs.get("asset_type") or "All"

    places = db.list_places_filtered(genre=genre if "discover" in name or name.startswith("games") else None, keyword=keyword if "discover" in name or name.startswith("games") else None, sort="visits" if sort == "visits" else "new")
    if not ("discover" in name or name.startswith("games")):
        places = db.list_places()
    assets = db.list_assets_filtered(asset_type=category if "catalog" in name else None, keyword=keyword if "catalog" in name else None, sort=sort if "catalog" in name else "new")
    friends = db.list_friends(user["id"]) if user else []

    html = html.replace("{{SEARCH_KEYWORD}}", esc(keyword))
    html = html.replace("{{GENRE_OPTS}}", _opts(["All","Adventure","Building","Comedy","Fighting","FPS","Horror","Medieval","Military","Naval","RPG","Sci-Fi","Sports","Town and City","Western"], genre))
    html = html.replace("{{SORT_OPTS}}", _opts(["new", "visits", "name"], sort))
    html = html.replace("{{CATEGORY_OPTS}}", _opts(["All","Hat","Hair","Face","Shirt","Pants","Gear","Accessory"], category))
    html = html.replace("{{CATALOG_SORT_OPTS}}", _opts(["new", "price", "price_desc"], sort))

    if any(x in name for x in ("discover", "games")) and "game." not in name and not name.startswith("game-"):
        html = fill_games(html, places, suffix)
    if name.startswith("game") and "games" not in name:
        pass
    elif "home" in name:
        html = fill_games(html, places, suffix)

    if "home" in name and user:
        html = html.replace("Hello!", "Hello, {{USERNAME}}!")
        html = html.replace("{{PROFILE_ID}}", str(user["id"]))
        html = html.replace("{{STATUS}}", esc(user.get("status") or ""))
        html = fill_friends(html, friends, suffix)
        recent = db.list_recent(user["id"])
        favs = db.list_favorites(user["id"])
        mine = db.places_by_creator(user["id"])
        html = replace_ul_inner(html, "game-cards", "".join(game_card(p, suffix) for p in recent), count=1)
        html = replace_ul_inner(html, "game-cards", "".join(game_card(p, suffix) for p in favs), count=1)
        html = replace_ul_inner(html, "game-tile-list", "".join(game_card(p, suffix) for p in places), count=1)
        html = replace_ul_inner(html, "game-cards", "".join(game_card(p, suffix) for p in mine), count=1)
    if "friend" in name:
        html = fill_friends(html, friends, suffix)
        reqs = db.list_friend_requests(user["id"]) if user else []
        html = replace_ul_inner(html, "request-list", "".join(request_card(u) for u in reqs))
        if reqs:
            html = html.replace('<p class="list-content request-empty">No pending requests.</p>', "")
    if "catalog" in name:
        html = fill_catalog(html, assets, buy=True)
    if "inventory" in name:
        owned = db.list_inventory(user["id"]) if user else []
        if category not in ("", "All") and owned:
            owned = [a for a in owned if (a.get("asset_type") or "") == category]
        wearing = db.list_wearing(user["id"]) if user else []
        wear_ids = {a["id"] for a in wearing}
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a, wearing=True) for a in wearing), count=1)
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a, wear=a["id"] not in wear_ids, wearing=a["id"] in wear_ids) for a in owned), count=1)
        if owned:
            html = html.replace('<p class="list-content">No Search Results Found</p>', "", 1)
    if "trade" in name:
        owned = db.list_inventory(user["id"]) if user else []
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a) for a in owned), count=1)
        trades = db.list_trades(user["id"]) if user else []
        html = replace_ul_inner(html, "trade-list", "".join(trade_card(t, user["id"]) for t in trades) if user else "")
    if name.startswith("game") and "games" not in name:
        pid = 0
        try:
            pid = int(qs.get("id") or qs.get("placeId") or qs.get("placeid") or 0)
        except Exception:
            pid = 0
        place = db.get_place(pid) if pid else None
        all_places = db.list_places()
        if not place and all_places:
            place = all_places[-1]
        if not place:
            place = {"id": 0, "name": "Untitled", "description": "", "creator_id": 0, "max_players": 10, "genre": "All", "created_at": int(time.time()), "visits": 0}
        html = fill_game_detail(html, place, suffix)
        fav_count = len(db.list_favorites(place["id"])) if False else 0
        # count favorites for this place
        con_fav = 0
        try:
            import sqlite3
            from database import connect
            c = connect()
            row = c.execute("SELECT COUNT(*) AS c FROM favorites WHERE place_id=?", (place["id"],)).fetchone()
            c.close()
            con_fav = int(row["c"] or 0) if row else 0
        except Exception:
            con_fav = 0
        html = html.replace("{{FAVORITE_COUNT}}", str(con_fav))
        if user and place["id"]:
            on = db.is_favorite(user["id"], place["id"])
            html = html.replace(
                "{{FAVORITE_FORM}}",
                '<form method="post" action="/places/favorite" class="inline-form">'
                '<input type="hidden" name="placeId" value="%s">'
                '<button type="submit" class="btn-secondary-md">%s</button></form>'
                % (place["id"], "Favorited" if on else "Favorite"),
            )
        else:
            html = html.replace("{{FAVORITE_FORM}}", "")
        jobs = db.list_jobs_for_place(place["id"]) if place["id"] else []
        servers = "".join(
            '<li class="list-item"><div class="list-body"><h2>Server</h2>'
            '<p class="list-content">%s:%s</p></div></li>'
            % (esc(j.get("host") or ""), esc(j.get("port") or ""))
            for j in jobs
        )
        html = replace_ul_inner(html, "server-list", servers)
        rec = [p for p in all_places if p["id"] != place["id"]][:8]
        html = replace_ul_inner(html, "game-cards", "".join(game_card(p, suffix) for p in rec), count=1)
        html = html.replace("{{PLAYING}}", str(len(jobs)))
    if "profile" in name:
        viewed = user
        try:
            qid = int(qs.get("id") or qs.get("userId") or 0)
        except Exception:
            qid = 0
        if qid:
            viewed = db.get_user(qid) or viewed
        if viewed:
            html = fill_profile(
                html,
                viewed,
                db.list_friends(viewed["id"]),
                db.places_by_creator(viewed["id"]),
                suffix,
            )
            wearing = db.list_wearing(viewed["id"])
            html = replace_ul_inner(html, "item-cards", "".join(item_card(a) for a in wearing), count=1)
            html = replace_ul_inner(html, "group-list", "".join(group_card(g, True) for g in db.groups_for_user(viewed["id"])))
            html = replace_ul_inner(html, "game-cards", "".join(game_card(p, suffix) for p in db.list_favorites(viewed["id"])), count=1)
            if user and viewed["id"] != user["id"]:
                html = html.replace(
                    "{{ADD_FRIEND}}",
                    '<form method="post" action="/friends/add">'
                    '<input type="hidden" name="userId" value="%s">'
                    '<button type="submit" class="btn-secondary-md">Add Friend</button></form>'
                    % viewed["id"],
                )
            else:
                html = html.replace("{{ADD_FRIEND}}", "")
        else:
            html = html.replace("{{ADD_FRIEND}}", "")
    if "search" in name:
        html = fill_search(
            html,
            keyword,
            db.search_users(keyword) if keyword else [],
            db.search_places(keyword) if keyword else [],
            suffix,
        )
        cats = db.list_assets_filtered(keyword=keyword) if keyword else []
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a, buy=True) for a in cats))
        html = replace_ul_inner(html, "group-list", "".join(group_card(g) for g in (db.search_groups(keyword) if keyword else [])))
    if "create" in name:
        html = html.replace('action="create.html"', 'action="/places/create"')
        html = html.replace('action="create-loggedin.html"', 'action="/places/create"')
        html = html.replace('action="https://www.roblox.com/places/create"', 'action="/places/create"')
        mine = db.places_by_creator(user["id"]) if user else []
        html = replace_ul_inner(html, "game-cards", "".join(game_card(p, suffix) for p in mine), count=1)
    if "signup" in name or "login" in name or "landing" in name or "index" in name:
        if 'name="gender"' not in html:
            html = html.replace(
                '<div class="form-group gender-container">',
                '<input type="hidden" name="gender" id="gender-field" value="Male">'
                '<div class="form-group gender-container">',
            )
    if "message" in name:
        inbox = db.list_inbox(user["id"]) if user else []
        sent = db.list_sent(user["id"]) if user else []
        html = replace_ul_inner(html, "inbox-list", "".join(message_item(m) for m in inbox))
        html = replace_ul_inner(html, "feeds", "".join(message_item(m) for m in inbox), count=1)
        html = replace_ul_inner(html, "sent-list", "".join(message_item(m, True) for m in sent))
        if inbox:
            html = html.replace('<p class="list-content inbox-empty">No messages.</p>', "")
        if sent:
            html = html.replace('<p class="list-content sent-empty">No sent messages.</p>', "")
    if "group" in name:
        groups = db.search_groups(keyword) if keyword else db.list_groups_detailed()
        mine = db.groups_for_user(user["id"]) if user else []
        html = replace_ul_inner(html, "my-group-list", "".join(group_card(g, True) for g in mine))
        html = replace_ul_inner(html, "group-list", "".join(group_card(g, any(x["id"]==g["id"] for x in mine)) for g in groups))
        if groups:
            html = html.replace('<p class="list-content">No Search Results Found</p>', "", 1)
        gid = 0
        try:
            gid = int(qs.get("id") or 0)
        except Exception:
            gid = 0
        g = db.get_group(gid) if gid else None
        if g:
            members = db.group_members(gid)
            owner = db.get_user(g.get("creator_id") or 0)
            html = html.replace("{{GROUP_NAME}}", esc(g.get("name") or ""))
            html = html.replace("{{GROUP_DESC}}", esc(g.get("description") or ""))
            html = html.replace("{{GROUP_OWNER}}", esc((owner or {}).get("username") or ""))
            html = html.replace("{{GROUP_MEMBERS}}", str(len(members)))
            joined = user and any(m["id"] == user["id"] for m in members)
            if user and not joined:
                html = html.replace(
                    "{{GROUP_JOIN}}",
                    '<form method="post" action="/groups/join"><input type="hidden" name="groupId" value="%s">'
                    '<button type="submit" class="btn-primary-md">Join</button></form>' % gid,
                )
            else:
                html = html.replace("{{GROUP_JOIN}}", "")
            html = replace_ul_inner(html, "group-member-list", "".join(friend_card(m, suffix) for m in members))
        else:
            html = html.replace("{{GROUP_NAME}}", "Group")
            html = html.replace("{{GROUP_DESC}}", "Select a group.")
            html = html.replace("{{GROUP_OWNER}}", "")
            html = html.replace("{{GROUP_MEMBERS}}", "0")
            html = html.replace("{{GROUP_JOIN}}", "")
    if "setting" in name and user:
        html = fill_settings(html, user)
    if "avatar" in name and user:
        tab = (qs.get("tab") or "accessories").lower()
        category = qs.get("category") or category
        wearing = db.list_wearing(user["id"])
        owned = db.list_inventory(user["id"])
        clothing = {"Shirt", "Pants", "T-Shirt"}
        accessories = {"Hat", "Hair", "Face", "Gear", "Accessory"}
        if tab == "clothing":
            cats = clothing
            owned = [a for a in owned if (a.get("asset_type") or "") in cats]
            if category in cats:
                owned = [a for a in owned if (a.get("asset_type") or "") == category]
        elif tab == "accessories":
            cats = accessories
            owned = [a for a in owned if (a.get("asset_type") or "") in cats]
            if category in cats:
                owned = [a for a in owned if (a.get("asset_type") or "") == category]
        elif tab == "recent":
            owned = wearing[:]
        elif tab == "animations":
            owned = []
        elif tab == "body":
            owned = []
        if category not in ("", "All") and tab not in ("body", "animations", "recent"):
            if qs.get("category"):
                owned = [a for a in owned if (a.get("asset_type") or "") == category]
        wear_ids = {a["id"] for a in wearing}
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a, wearing=True) for a in wearing), count=1)
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a, wear=a["id"] not in wear_ids, wearing=a["id"] in wear_ids) for a in owned), count=1)
        html = html.replace("{{PROFILE_ID}}", str(user["id"]))
        html = html.replace("{{R6_FIGURE}}", r6_figure(user, wearing))
        s = db.get_user_settings(user)
        at = (s.get("avatar_type") or "R6").upper()
        html = html.replace("{{R6_ACTIVE}}", "active" if at == "R6" else "")
        html = html.replace("{{R15_ACTIVE}}", "active" if at == "R15" else "")
        for key, val in (("recent", "TAB_RECENT"), ("clothing", "TAB_CLOTHING"), ("accessories", "TAB_ACCESSORIES"), ("body", "TAB_BODY"), ("animations", "TAB_ANIM")):
            html = html.replace("{{%s}}" % val, "active" if tab == key else "")
        html = html.replace("{{COLOR_SWATCHES}}", color_swatches())
        html = html.replace("{{BODY_HIDDEN}}", "" if tab == "body" else 'style="display:none"')
        html = html.replace("{{WARDROBE_HIDDEN}}", 'style="display:none"' if tab == "body" else "")
        sub = ""
        if tab == "clothing":
            sub = "".join(
                '<a href="/avatar-loggedin.html?tab=clothing&category=%s">%s</a>' % (c, c)
                for c in ("Shirt", "Pants")
            )
        elif tab == "accessories":
            sub = "".join(
                '<a href="/avatar-loggedin.html?tab=accessories&category=%s">%s</a>' % (c, c)
                for c in ("Hat", "Hair", "Face", "Gear", "Accessory")
            )
        elif tab == "body":
            sub = '<a href="/avatar-loggedin.html?tab=body">Skin Tone</a>'
        elif tab == "animations":
            sub = '<span class="text-label">Emotes and animations are not on this server.</span>'
        else:
            sub = '<a href="/avatar-loggedin.html?tab=recent">Currently Wearing</a>'
        html = html.replace("{{AVATAR_SUBCATS}}", sub)
        if owned:
            html = html.replace('<p class="list-content">No Search Results Found</p>', "", 1)
    if "promo" in name or "redeem" in name:
        html = html.replace('action="promocodes.html"', 'action="/promo/redeem"')
        html = html.replace('action="promocodes-loggedin.html"', 'action="/promo/redeem"')
    if "robux" in name and user:
        html = html.replace("{{ROBUX}}", str(user.get("robux") or 0))
    if name.startswith("game") and "games" not in name:
        try:
            vid = int(qs.get("id") or qs.get("placeId") or 0)
        except Exception:
            vid = 0
        if vid:
            db.bump_place_visits(vid)
    if "</body>" in html:
        html = html.replace("</body>", SITE_JS + "\n</body>", 1)
    else:
        html += SITE_JS
    return html
