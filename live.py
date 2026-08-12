"""Strip snapshot Roblox data from dump HTML and fill the same classes from the DB."""
from __future__ import annotations

import html as htmlmod
import re
import time
from datetime import datetime

import database as db


def esc(s) -> str:
    return htmlmod.escape("" if s is None else str(s))


def verified_badge(user) -> str:
    if user and user.get("verified"):
        return '<img class="verified-badge" src="/static/ecs/verified.svg" alt="Verified" title="Verified">'
    return ""


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
    href = "/games/%s" % pid
    thumb = "/thumbs/place.ashx?id=%s" % pid
    if "playing" in place:
        playing = int(place.get("playing") or 0)
    else:
        playing = db.place_playing(pid)
    return (
        '<li class="list-item game-card game-tile" title="%s">'
        '<div class="game-card-container sgc">'
        '<a class="game-card-link" href="%s">'
        '<div class="game-card-thumb-container">'
        '<img class="game-card-thumb sgc-thumb" src="%s" alt="%s" title="%s">'
        "</div>"
        '<div class="game-card-name game-name-title sgc-name" title="%s">%s</div>'
        '<div class="game-card-info sgc-playing">'
        '<span class="info-label icon-playing-counts-gray"></span>'
        '<span class="info-label playing-counts-label">%s Playing</span>'
        "</div></a>"
        '<span class="btn-play-green rbx-play-button game-card-play" data-placeid="%s" role="button">Play</span>'
        '<div class="sgc-vote"><span class="icon-thumbs-up"></span>'
        '<span class="vote-bar"><span class="vote-fill"></span></span></div>'
        "</div></li>"
    ) % (name, href, thumb, name, name, name, name, playing, pid)


def friend_card(user: dict, suffix: str) -> str:
    uid = user["id"]
    name = esc(user.get("username") or "")
    return (
        '<li id="friend_%s" class="list-item friend">'
        '<div class="avatar-container">'
        '<a href="/profile/user/%s" class="avatar avatar-card-fullbody friend-link" title="%s">'
        '<span class="avatar-card-link friend-avatar">'
        '<img alt="%s" class="avatar-card-image" src="/thumbs/headshot.ashx?userId=%s">'
        '</span><span class="text-overflow friend-name">%s%s</span></a></div></li>'
    ) % (uid, uid, name, name, uid, name, verified_badge(user))


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
            '<button type="submit" class="btn-play-green btn-item-grad">Buy</button></form>' % aid
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
        '<a href="/catalog/%s" class="item-card-link">'
        '<div class="item-card-thumb-container">'
        '<img class="item-card-thumb" src="/thumbs/asset.ashx?id=%s" alt="%s">'
        "</div>"
        '<div class="text-overflow item-card-name" title="%s">%s</div>'
        "</a>"
        '<div class="text-overflow item-card-price">'
        '<span class="icon-robux-16x16"></span><span class="text-robux">%s</span>'
        "</div>%s</div></li>"
    ) % (aid, aid, name, name, name, price, extra)


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
    html = replace_ul_inner(html, "game-tile-list", cards, count=0)
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



def server_list_html(place: dict, suffix: str) -> str:
    players = db.list_playing_users(place.get("id") or 0)
    if not players:
        return '<p class="ecs-nobody">Nobody is playing this game.</p>'
    maxp = int(place.get("max_players") or 10)
    pid = place["id"]
    bits = [
        '<div class="ecs-server">',
        '<div class="ecs-server-top">',
        '<button type="button" class="btn-join-blue rbx-play-button ecs-join" data-placeid="%s">Join</button>' % pid,
        '<p class="ecs-server-meta">',
        '<span class="ecs-stat-k">Player Count: </span>%s / %s Players' % (len(players), maxp),
        '<span class="ecs-stat-k"> FPS: </span>0',
        '<span class="ecs-stat-k"> Ping: </span>0</p></div>',
        '<div class="ecs-server-players">',
    ]
    for u in players:
        uid = u["id"]
        name = esc(u.get("username") or "Player")
        bits.append(
            '<div class="ecs-sp">'
            '<a href="/profile/user/%s"><img class="ecs-sp-shot" src="/thumbs/headshot.ashx?userId=%s" alt="%s"></a>'
            '<a class="ecs-sp-name" href="/profile/user/%s">%s</a></div>'
            % (uid, uid, name, uid, name)
        )
    bits.append('</div><div class="divider-top ecs-game-div"></div></div>')
    return "".join(bits)


def comments_html(place_id: int, suffix: str) -> str:
    rows = db.list_place_comments(place_id)
    if not rows:
        return '<p class="list-content">No comments yet.</p>'
    bits = []
    for c in rows:
        uid = c.get("user_id") or 0
        name = esc(c.get("username") or "Player")
        body = esc(c.get("body") or "")
        when = datetime.utcfromtimestamp(int(c.get("created_at") or time.time())).strftime("%m/%d/%Y")
        bits.append(
            '<div class="ecs-comment">'
            '<a href="/profile/user/%s"><img class="ecs-comment-shot" src="/thumbs/headshot.ashx?userId=%s" alt="%s"></a>'
            '<div class="ecs-comment-body"><p class="ecs-comment-when">%s · <a href="/profile/user/%s">%s</a></p>'
            '<p class="ecs-comment-text">%s</p></div></div>'
            % (uid, uid, name, when, uid, name, body)
        )
    return "".join(bits)



DEV_VIEWS = [
    (0, "Games", None, "games"),
    (9, "Places", None, "places"),
    (10, "Models", "Model", "models"),
    (13, "Decals", "Decal", "decals"),
    (1, "Images", "Image", "images"),
    (21, "Badges", "Badge", "badges"),
    (100, "Passes", "Pass", "passes"),
    (3, "Audio", "Audio", "audio"),
    (24, "Animations", "Animation", "animations"),
    (40, "Meshes", "Mesh", "meshes"),
    (101, "User Ads", "Ad", "ads"),
    (103, "Sponsored Games", None, "sponsored"),
    (11, "Shirts", "Shirt", "shirts"),
    (2, "T-Shirts", "T-Shirt", "tshirts"),
    (12, "Pants", "Pants", "pants"),
    (38, "Plugins", "Plugin", "plugins"),
]

DEV_UPLOAD = {1: "Image", 2: "T-Shirt", 3: "Audio", 11: "Shirt", 12: "Pants"}

_DEV_TEMPLATES = [
    ("95206881", "Baseplate"),
    ("6560363541", "Classic Baseplate"),
    ("95206192", "Flat Terrain"),
    ("203812057", "Obby"),
    ("215383192", "Racing"),
    ("203885589", "Combat"),
    ("379736082", "Starting Place"),
    ("203783329", "City"),
]
_DEV_GENRES = [
    "All", "Adventure", "Building", "Comedy", "Fighting", "FPS", "Horror",
    "Medieval", "Military", "Naval", "RPG", "Sci-Fi", "Sports", "Town and City", "Western",
]


def _place_create_form() -> str:
    tpls = "".join(
        '<div class="template" placeid="%s"><img src="/static/placeholder.png" alt="%s"><p>%s</p></div>'
        % (i, n, n)
        for i, n in _DEV_TEMPLATES
    )
    genres = "".join("<option>%s</option>" % g for g in _DEV_GENRES)
    maxp = "".join(
        '<option%s>%s</option>' % (" selected" if n == 10 else "", n) for n in range(1, 51)
    )
    return (
        '<form id="placeForm" method="POST" action="/places/create">'
        '<input id="TemplateID" name="TemplateID" type="hidden" value="95206881">'
        '<h2 id="StudioGameTemplates">Starting layouts</h2>'
        '<div class="templates">%s</div>'
        '<label class="form-label" for="Name">Name:</label>'
        '<input class="text-box text-box-medium" id="Name" name="Name" type="text" value="">'
        '<label class="form-label" for="Description">Description:</label>'
        '<textarea class="text-box text-area-medium" id="Description" name="Description" rows="4"></textarea>'
        '<label class="form-label" for="Genre">Genre:</label>'
        '<select class="form-select" id="Genre" name="Genre">%s</select>'
        '<label class="form-label" for="MaxPlayersInput">Maximum Visitor Count:</label>'
        '<select class="form-select" id="MaxPlayersInput" name="NumberOfPlayersMax">%s</select>'
        '<div id="buttonRow"><a class="btn-medium btn-primary" id="finishButton">Create Place</a></div>'
        "</form>"
    ) % (tpls, genres, maxp)


def _dev_asset_row(kind: str, item: dict, suffix: str) -> str:
    iid = item["id"]
    name = esc(item.get("name") or "Untitled")
    if kind == "place":
        href = "/games/%s" % iid
        thumb = "/thumbs/place.ashx?id=%s" % iid
        extra = (
            '<p class="dev-meta"><span class="dev-dim">Start Place: </span>'
            '<a href="%s">%s</a></p><p class="dev-meta"><a href="%s">Public</a></p>'
            % (href, name, href)
        )
        gear = (
            '<a href="/games/%s">Configure Game</a>'
            '<a href="/develop?tab=my&amp;View=9">Configure Start Place</a>'
            '<a href="/develop?tab=my&amp;View=21">Create Badge</a>'
            '<a href="/develop?tab=my&amp;View=100">Create Pass</a>'
            % iid
        )
    else:
        href = "/catalog/%s" % iid
        thumb = "/thumbs/asset.ashx?id=%s" % iid
        created = datetime.utcfromtimestamp(int(item.get("created_at") or time.time())).strftime("%m/%d/%Y")
        extra = '<p class="dev-meta"><span class="dev-dim">Created: </span>%s</p>' % created
        gear = (
            '<a href="/catalog/%s">Configure</a>'
            '<a href="/develop?tab=my&amp;View=101">Advertise</a>' % iid
        )
    return (
        '<div class="dev-asset-row">'
        '<a class="dev-asset-thumb" href="%s"><img src="%s" alt="%s"></a>'
        '<div class="dev-asset-copy"><p class="dev-asset-name"><a href="%s">%s</a></p>%s</div>'
        '<div class="ecs-gear-dd">'
        '<button type="button" class="ecs-gear-btn" aria-haspopup="true">&#9881; <span class="ecs-gear-caret">&#9660;</span></button>'
        '<div class="ecs-gear-menu">%s</div></div></div>'
    ) % (href, thumb, name, href, name, extra, gear)


def _dev_upload_form(view_id: int, asset_type: str, title: str) -> str:
    return (
        '<form method="post" action="/catalog/upload" class="dev-upload">'
        '<input type="hidden" name="asset_type" value="%s">'
        '<input type="hidden" name="view" value="%s">'
        '<p class="list-content">Name your %s. It shows in Catalog after you upload.</p>'
        '<label class="form-label">%s Name</label>'
        '<input class="input-field" name="name" type="text" maxlength="50">'
        '<button type="submit" class="btn-play-green">Upload</button></form>'
        % (esc(asset_type), view_id, esc(title), esc(title))
    )


def fill_develop(html: str, user: dict | None, qs: dict, suffix: str) -> str:
    tab = (qs.get("tab") or "my").lower()
    if tab not in ("my", "group", "library", "devex"):
        tab = "my"
    try:
        view = int(qs.get("View") or qs.get("view") or 0)
    except Exception:
        view = 0
    if view not in {v[0] for v in DEV_VIEWS}:
        view = 0
    view_meta = next(v for v in DEV_VIEWS if v[0] == view)
    html = html.replace("{{VIEW}}", str(view))
    for key, token in (("my", "MY"), ("group", "GROUP"), ("library", "LIBRARY"), ("devex", "DEVEX")):
        html = html.replace("{{TAB_%s}}" % token, "active" if tab == key else "")
    href_base = "/develop"

    if tab == "devex":
        body = '<div class="dev-pane"><p class="mt-2">This feature is not available right now.</p></div>'
        return html.replace("{{DEV_BODY}}", body)

    if tab == "library":
        keyword = qs.get("keyword") or ""
        assets = db.list_assets_filtered(keyword=keyword) if keyword else db.list_assets()
        rows = "".join(_dev_asset_row("asset", a, suffix) for a in assets[:40])
        if not rows:
            rows = '<p class="list-content">No items in the library yet.</p>'
        body = (
            '<div class="dev-pane">'
            "<h2>Library</h2>"
            '<p class="list-content">Models, decals, audio, and clothing made on this server.</p>'
            '<form class="games-filter-bar" method="get" action="%s">'
            '<input type="hidden" name="tab" value="library">'
            '<input class="input-field" name="keyword" placeholder="Search library" value="%s">'
            '<button type="submit" class="btn-primary-md">Search</button></form>'
            '<div class="dev-asset-list">%s</div></div>'
            % (href_base, esc(keyword), rows)
        )
        return html.replace("{{DEV_BODY}}", body)

    # My / Group creations
    gid = 0
    try:
        gid = int(qs.get("groupId") or 0)
    except Exception:
        gid = 0
    groups = db.groups_for_user(user["id"]) if user else []
    if tab == "group" and not gid and groups:
        gid = groups[0]["id"]
    group_sel = ""
    if tab == "group":
        opts = "".join(
            '<option value="%s"%s>%s</option>'
            % (g["id"], " selected" if g["id"] == gid else "", esc(g.get("name") or "Group"))
            for g in groups
        )
        group_sel = (
            '<div class="dev-group-pick"><p class="mb-0 mt-2">Select Group:</p>'
            '<form method="get" action="%s"><input type="hidden" name="tab" value="group">'
            '<input type="hidden" name="View" value="%s">'
            '<select class="input-field w-100" name="groupId" onchange="this.form.submit()">%s</select>'
            "</form></div>" % (href_base, view, opts or '<option>No groups</option>')
        )

    side = []
    for vid, name, _atype, _slug in DEV_VIEWS:
        cls = "dev-side-link selected" if vid == view else "dev-side-link"
        side.append(
            '<a class="%s" href="%s?tab=%s&amp;View=%s">%s</a>'
            % (cls, href_base, tab, vid, name)
        )
    side_html = (
        '<aside class="develop-left menu-area">'
        + group_sel
        + '<nav class="vertical-selector">'
        + "".join(side)
        + "</nav>"
        + '<div id="StudioWidget" class="dev-widget"><div class="widget-name">'
        '<h3><span class="brand-name">ROBLOX</span> Studio</h3></div>'
        '<div class="widget-body"><p class="list-content">Build places on this server with the Computer client.</p>'
        '<a class="studio-launch" href="/download">Get the client</a></div></div>'
        '<div id="CommunityWidget" class="dev-widget"><div class="widget-name"><h3>Creator Corner</h3></div>'
        '<div class="widget-body"><p class="list-content">Tips and notes for people making places here.</p>'
        '<a href="/help">Open Help</a></div></div></aside>'
    )

    title = view_meta[1]
    atype = view_meta[2]
    main = ['<div class="develop-right content-area">']
    if view in (0, 9):
        btn = "Create New Game" if view == 0 else "Create New Place"
        main.append('<a class="create-new-button btn-play-green" href="#placeForm">%s</a>' % btn)
        main.append("<h2>%s</h2>" % title)
        if tab == "group":
            places = []
            if gid:
                # group-owned places are not stored separately; show empty
                places = []
            if not places:
                main.append('<p class="mt-4">This group hasn\'t created any games.</p>')
        else:
            places = db.places_by_creator(user["id"]) if user else []
            if places:
                main.append(
                    '<div class="dev-asset-list">%s</div>'
                    % "".join(_dev_asset_row("place", p, suffix) for p in places)
                )
            else:
                main.append('<p class="mt-4">You haven\'t created any games.</p>')
        if tab != "group":
            main.append(_place_create_form())
    elif view in DEV_UPLOAD:
        utype = DEV_UPLOAD[view]
        main.append("<h2>Create %s</h2>" % utype)
        if tab == "group":
            main.append('<p class="list-content">Group uploads are not open on this tab yet.</p>')
        else:
            main.append(_dev_upload_form(view, utype, utype))
            owned = db.assets_by_creator(user["id"], utype) if user else []
            if owned:
                main.append(
                    '<div class="dev-asset-list">%s</div>'
                    % "".join(_dev_asset_row("asset", a, suffix) for a in owned)
                )
            else:
                main.append('<p class="mt-4">You haven\'t created any %s.</p>' % (title.lower()))
    else:
        main.append("<h2>%s</h2>" % title)
        if atype and user and tab != "group":
            owned = db.assets_by_creator(user["id"], atype)
            if owned:
                main.append(
                    '<div class="dev-asset-list">%s</div>'
                    % "".join(_dev_asset_row("asset", a, suffix) for a in owned)
                )
            else:
                main.append('<p class="mt-4">You haven\'t created any %s.</p>' % title.lower())
        else:
            main.append('<p class="mt-2">This feature is not available right now.</p>')
    main.append("</div>")
    body = '<div class="develop-creations">%s%s</div>' % (side_html, "".join(main))
    return html.replace("{{DEV_BODY}}", body)


def fill_game_detail(html: str, place: dict, suffix: str) -> str:
    name = esc(place.get("name") or "Untitled")
    raw_desc = (place.get("description") or "").strip()
    desc = esc(raw_desc) if raw_desc else "No description available"
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
    html = html.replace("{{PLAYING}}", str(db.place_playing(pid)))
    html = html.replace("{{UPDATED}}", created)
    up, down = db.place_votes(pid)
    total = up + down
    pct = int(round((up / total) * 100)) if total else 50
    html = html.replace("{{UPVOTES}}", str(up))
    html = html.replace("{{DOWNVOTES}}", str(down))
    html = html.replace("{{VOTE_PCT}}", str(pct))
    html = html.replace("/profile.html?id=", "/profile/user/")
    return html


def fill_item_detail(html: str, asset: dict, suffix: str) -> str:
    name = esc(asset.get("name") or "Item")
    desc = esc(asset.get("description") or "No description available.")
    aid = asset["id"]
    creator = db.get_user(asset.get("creator_id") or 0)
    cname = esc(creator["username"]) if creator else "ROBLOX"
    cid = creator["id"] if creator else 0
    html = html.replace("{{ITEM_NAME}}", name)
    html = html.replace("{{ITEM_DESC}}", desc)
    html = html.replace("{{ITEM_ID}}", str(aid))
    html = html.replace("{{ITEM_TYPE}}", esc(asset.get("asset_type") or "Item"))
    html = html.replace("{{ITEM_PRICE}}", str(int(asset.get("price") or 0)))
    html = html.replace("{{CREATOR_NAME}}", cname)
    html = html.replace("{{CREATOR_ID}}", str(cid))
    html = html.replace("/profile.html?id=", "/profile/user/")
    return html



def request_card(user: dict) -> str:
    uid = user["id"]
    name = esc(user.get("username") or "")
    return (
        '<li class="list-item"><div class="list-body">'
        '<a href="/profile/user/%s">%s</a> '
        '<form method="post" action="/friends/accept" class="inline-form">'
        '<input type="hidden" name="userId" value="%s">'
        '<button type="submit" class="btn-primary-xs">Accept</button></form> '
        '<form method="post" action="/friends/decline" class="inline-form">'
        '<input type="hidden" name="userId" value="%s">'
        '<button type="submit" class="btn-secondary-xs">Decline</button></form>'
        "</div></li>"
    ) % (uid, name, uid, uid)


def group_rail_item(group: dict) -> str:
    gid = group["id"]
    name = esc(group.get("name") or "Group")
    letter = esc((group.get("name") or "G")[:1].upper())
    return (
        '<li class="GroupListItemContainer">'
        '<a class="group-rail-link" href="/groups/%s">'
        '<span class="GroupListImageContainer" aria-hidden="true">%s</span>'
        '<span class="GroupListName">%s</span></a></li>'
    ) % (gid, letter, name)


def group_card(group: dict, joined=False) -> str:
    gid = group["id"]
    name = esc(group.get("name") or "Group")
    desc = esc(group.get("description") or "")
    members = int(group.get("member_count") or 0)
    owner = esc(group.get("owner_name") or "")
    letter = esc((group.get("name") or "G")[:1].upper())
    join = ""
    if not joined:
        join = (
            '<form method="post" action="/groups/join" class="inline-form">'
            '<input type="hidden" name="groupId" value="%s">'
            '<button type="submit" class="btn-secondary-xs">Join</button></form>' % gid
        )
    return (
        '<li class="list-item group-card">'
        '<div class="group-card-emblem" aria-hidden="true">%s</div>'
        '<div class="list-body">'
        '<h2><a href="/groups/%s">%s</a></h2>'
        '<p class="list-content">%s</p>'
        '<p class="text-label">%s · Members %s</p>%s</div></li>'
    ) % (letter, gid, name, desc, owner, members, join)


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
    tab = ""
    # filled later from qs in prepare; defaults
    g = (user.get("gender") or "Male")
    html = html.replace("{{GENDER_MALE_CHECKED}}", "checked" if g == "Male" else "")
    html = html.replace("{{GENDER_FEMALE_CHECKED}}", "checked" if g == "Female" else "")
    html = html.replace("{{GENDER_MALE}}", "selected" if g == "Male" else "")
    html = html.replace("{{GENDER_FEMALE}}", "selected" if g == "Female" else "")
    return html


def fill_profile(html: str, viewed: dict, friends: list, places: list, suffix: str) -> str:
    name = esc(viewed.get("username") or "")
    uid = viewed["id"]
    s = db.get_user_settings(viewed)
    joined = datetime.utcfromtimestamp(int(viewed.get("created_at") or time.time())).strftime("%m/%d/%Y")
    blurb = esc(viewed.get("blurb") or "This user has no description.")
    status = esc(viewed.get("status") or "")
    html = html.replace("{{PROFILE_NAME}}", name)
    html = html.replace("{{VERIFIED_BADGE}}", verified_badge(viewed))
    html = html.replace("{{PROFILE_ID}}", str(uid))
    html = html.replace("{{PROFILE_STATUS}}", status)
    html = html.replace("{{PROFILE_STATUS_DISPLAY}}", ('"%s"' % status) if status else "")
    html = html.replace("{{PROFILE_BLURB}}", blurb)
    html = html.replace("{{PROFILE_JOINED}}", joined)
    html = html.replace("{{FRIEND_COUNT}}", str(len(friends)))
    html = html.replace("{{FOLLOWER_COUNT}}", "0")
    html = html.replace("{{FOLLOWING_COUNT}}", "0")
    html = html.replace("{{PLACE_VISITS}}", str(db.user_place_visits(uid)))
    html = html.replace("{{DISPLAY_NAME}}", esc(s.get("display_name") or name))
    html = fill_friends(html, friends, suffix)
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


  var picker = document.querySelector('.cc-picker');
  var mannequin = document.querySelectorAll('.cc-mannequin [data-part]');
  var closePicker = document.getElementById('color-close');
  for (var m = 0; m < mannequin.length; m++) {
    mannequin[m].addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      if (partField) partField.value = this.getAttribute('data-part') || 'all';
      if (picker) picker.hidden = false;
    });
  }
  if (closePicker) closePicker.addEventListener('click', function () {
    if (picker) picker.hidden = true;
  });

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
    box.className = 'modal-container protocol-handler-container';
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.innerHTML = '<div class="modal-backdrop" id="rbx-play-backdrop"></div>'
      + '<div class="modal-window ph-modal-popup">'
      + '<div class="ph-modal-header"><button type="button" class="ph-close" id="rbx-play-close" aria-label="Close">x</button></div>'
      + '<div id="ph-starting">'
      + '<div class="ph-logo-row"><img class="play-logo-image" src="/static/ecs/logo_R.svg" width="90" height="90" alt="R"></div>'
      + '<p class="ph-copy" id="rbx-play-status">Roblox is now loading. Get ready to play!</p>'
      + '<div class="ph-startingdialog-spinner-row" aria-hidden="true"><span></span><span></span><span></span></div>'
      + '</div>'
      + '<div id="ph-install" hidden>'
      + '<div class="ph-logo-row"><img class="play-logo-image" src="/static/ecs/logo_R.svg" width="90" height="90" alt="R"></div>'
      + '<p class="ph-copy">You\'re moments away from getting into the game!</p>'
      + '<a class="btn-primary-md ph-install-btn" id="ProtocolHandlerInstallButton" href="/download">Download and Install Roblox</a>'
      + '<p class="ph-help"><a href="/help">Click here for help</a></p>'
      + '</div></div>';
    document.body.appendChild(box);
  }
  var lastPlaceId = '';
  var phTimer = null;
  function showPhStarting() {
    var a = document.getElementById('ph-starting');
    var b = document.getElementById('ph-install');
    if (a) a.hidden = false;
    if (b) b.hidden = true;
  }
  function showPhInstall() {
    var a = document.getElementById('ph-starting');
    var b = document.getElementById('ph-install');
    if (a) a.hidden = true;
    if (b) b.hidden = false;
  }
  function closePlayModal() {
    var m = document.getElementById('rbx-play-modal');
    if (m) m.classList.remove('open');
    if (phTimer) { window.clearTimeout(phTimer); phTimer = null; }
  }
  function launchGame(placeId) {
    if (!placeId) return;
    lastPlaceId = String(placeId);
    ensurePlayModal();
    var modal = document.getElementById('rbx-play-modal');
    var status = document.getElementById('rbx-play-status');
    if (modal) modal.classList.add('open');
    showPhStarting();
    if (status) status.textContent = 'Roblox is now loading. Get ready to play!';
    if (phTimer) window.clearTimeout(phTimer);
    phTimer = window.setTimeout(showPhInstall, 8000);
    fetch('/game/get-join-script?placeId=' + encodeURIComponent(lastPlaceId), {
      credentials: 'same-origin'
    }).then(function (r) {
      if (r.status === 401) { window.location.href = '/signup'; return null; }
      return r.json();
    }).then(function (data) {
      if (!data) return;
      if (data.error || !data.joinScriptUrl) {
        if (status) status.textContent = data.error || 'Could not start the client.';
        showPhInstall();
        return;
      }
      var href = (data.prefix || '') + (data.joinScriptUrl || '');
      var aTag = document.createElement('a');
      aTag.setAttribute('href', href);
      document.body.appendChild(aTag);
      aTag.click();
      setTimeout(function () { aTag.remove(); }, 1000);
    }).catch(function () {
      if (status) status.textContent = 'Could not start the client.';
      showPhInstall();
    });
  }
  function launchPlace(placeId) { launchGame(placeId); }
  document.addEventListener('click', function (e) {
    var t = e.target;
    if (!t) return;
    if (t.id === 'rbx-play-close' || t.id === 'rbx-play-cancel' || t.id === 'rbx-play-backdrop') {
      closePlayModal();
      return;
    }
    if (t.id === 'rbx-play-retry') {
      launchGame(lastPlaceId);
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
    var pid = idm ? idm[1] : '';
    if (!pid) {
      var pm = location.pathname.match(/\/games\/(\d+)/);
      if (pm) pid = pm[1];
    }
    if (pid) launchPlace(pid);
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
  function spinGear() {
    if (!setBtn) return;
    setBtn.classList.remove('is-spinning');
    void setBtn.offsetWidth;
    setBtn.classList.add('is-spinning');
    window.setTimeout(function () { setBtn.classList.remove('is-spinning'); }, 520);
  }
  function placeSettingsMenu() {
    if (!setBtn || !setMenu) return;
    var r = setBtn.getBoundingClientRect();
    setMenu.style.position = 'fixed';
    setMenu.style.top = Math.round(r.bottom) + 'px';
    setMenu.style.right = '10px';
    setMenu.style.left = 'auto';
    setMenu.style.zIndex = '10050';
  }
  if (setBtn && setMenu) {
    if (setMenu.parentNode !== document.body) document.body.appendChild(setMenu);
    setBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var open = !setMenu.classList.contains('open');
      setMenu.classList.toggle('open', open);
      setBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
      if (open) placeSettingsMenu();
      spinGear();
    });
    window.addEventListener('resize', function () {
      if (setMenu.classList.contains('open')) placeSettingsMenu();
    });
  }

  var gearDrops = document.querySelectorAll('.ecs-gear-dd');
  function closeGearDrops(except) {
    for (var g = 0; g < gearDrops.length; g++) {
      if (gearDrops[g] !== except) gearDrops[g].classList.remove('open');
    }
  }
  for (var gd = 0; gd < gearDrops.length; gd++) {
    (function (box) {
      var btn = box.querySelector('.ecs-gear-btn');
      if (!btn) return;
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var open = !box.classList.contains('open');
        closeGearDrops(box);
        box.classList.toggle('open', open);
      });
    })(gearDrops[gd]);
  }
  document.addEventListener('click', function () { closeGearDrops(); });

  var aeDrops = document.querySelectorAll('.ae-dd');
  function closeAeDrops(except) {
    for (var i = 0; i < aeDrops.length; i++) {
      if (aeDrops[i] !== except) aeDrops[i].classList.remove('open');
    }
  }
  for (var ad = 0; ad < aeDrops.length; ad++) {
    (function (box) {
      var btn = box.querySelector('.ae-dd-btn');
      if (!btn) return;
      btn.addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        var open = !box.classList.contains('open');
        closeAeDrops(box);
        box.classList.toggle('open', open);
      });
    })(aeDrops[ad]);
  }
  var catBar = document.querySelector('.ae-catbar');
  if (catBar) {
    var current = catBar.getAttribute('data-current') || '';
    var links = catBar.querySelectorAll('.ae-dd-menu a');
    for (var cl = 0; cl < links.length; cl++) {
      var href = links[cl].getAttribute('href') || '';
      if (current && href.indexOf('category=' + encodeURIComponent(current)) >= 0 ||
          (current && href.indexOf('category=' + current) >= 0)) {
        links[cl].classList.add('selected');
        var parent = links[cl].closest('.ae-dd');
        if (parent) parent.classList.add('active-group');
      }
    }
  }
  var skinLink = document.getElementById('ae-skin-tone');
  if (skinLink) {
    skinLink.addEventListener('click', function (e) {
      e.preventDefault();
      closeAeDrops();
      var man = document.querySelector('.cc-mannequin');
      if (man) man.scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (picker) picker.hidden = false;
    });
  }

  var gearBtn = document.getElementById('profile-gear');
  var gearMenu = document.getElementById('profile-gear-menu');
  if (gearBtn && gearMenu) {
    gearBtn.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      var open = !gearMenu.classList.contains('open');
      gearMenu.classList.toggle('open', open);
      gearBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }
  var statusLink = document.getElementById('update-status-link');
  var statusForm = document.getElementById('profile-status-form');
  var statusText = document.getElementById('profile-status-text');
  if (statusLink && statusForm) {
    statusLink.addEventListener('click', function (e) {
      e.preventDefault();
      statusForm.hidden = false;
      if (statusText) statusText.hidden = true;
      if (gearMenu) gearMenu.classList.remove('open');
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
      if (gearMenu) gearMenu.classList.remove('open');
      if (loginBar) loginBar.classList.remove('open');
      closeAeDrops();
      closeGearDrops();
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
        html = html.replace("{{VERIFIED_BADGE}}", verified_badge(user))
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
    if name.startswith("item"):
        try:
            iid = int(qs.get("id") or qs.get("assetId") or 0)
        except Exception:
            iid = 0
        asset = db.get_asset(iid) if iid else None
        if not asset:
            all_a = db.list_assets()
            asset = all_a[0] if all_a else {"id": 0, "name": "Item", "description": "", "creator_id": 0, "asset_type": "Hat", "price": 0}
        html = fill_item_detail(html, asset, suffix)
        rec = [a for a in db.list_assets() if a["id"] != asset.get("id")][:8]
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a, buy=True) for a in rec), count=1)
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
        con_fav = db.favorite_count(place["id"])
        html = html.replace("{{FAVORITE_COUNT}}", str(con_fav))
        if user and place["id"]:
            on = db.is_favorite(user["id"], place["id"])
            html = html.replace(
                "{{FAVORITE_FORM}}",
                '<div class="ecs-fav-row"><span class="ecs-fav-star" aria-hidden="true"></span>'
                '<span class="ecs-fav-n">%s</span> '
                '<form method="post" action="/places/favorite" class="inline-form">'
                '<input type="hidden" name="placeId" value="%s">'
                '<button type="submit" class="ecs-fav-link">%s</button></form></div>'
                % (con_fav, place["id"], "Unfavorite" if on else "Favorite"),
            )
        else:
            html = html.replace(
                "{{FAVORITE_FORM}}",
                '<div class="ecs-fav-row"><span class="ecs-fav-star" aria-hidden="true"></span>'
                '<span class="ecs-fav-n">%s</span></div>' % con_fav,
            )
        if user and place.get("creator_id") and user["id"] == place["creator_id"]:
            html = html.replace(
                "{{GAME_GEAR}}",
                '<div class="ecs-game-gear"><a href="/develop">Configure</a></div>',
            )
        else:
            html = html.replace("{{GAME_GEAR}}", "")
        vote_msg = ""
        if (qs.get("vote") or "") == "play":
            vote_msg = "You must play this game before you can vote on it."
        html = html.replace("{{VOTE_MSG}}", vote_msg)
        html = html.replace("{{SERVERS}}", server_list_html(place, suffix))
        if user and place["id"]:
            html = html.replace(
                "{{COMMENT_FORM}}",
                '<form method="post" action="/places/comment" class="ecs-comment-form">'
                '<input type="hidden" name="placeId" value="%s">'
                '<img class="ecs-comment-shot" src="/thumbs/headshot.ashx?userId=%s" alt="">'
                '<div class="ecs-comment-write">'
                '<textarea class="text-box" name="body" maxlength="200" rows="5" placeholder="Write a comment"></textarea>'
                '<button type="submit" class="btn-join-blue">Continue</button></div></form>'
                % (place["id"], user["id"]),
            )
        else:
            html = html.replace(
                "{{COMMENT_FORM}}",
                '<p class="list-content">Log in to write a comment.</p>',
            )
        html = html.replace("{{COMMENTS}}", comments_html(place["id"], suffix))
        rec = [p for p in all_places if p["id"] != place["id"]][:8]
        html = replace_ul_inner(html, "game-cards", "".join(game_card(p, suffix) for p in rec), count=1)
        html = html.replace("{{PLAYING}}", str(db.place_playing(place["id"])))
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
            html = replace_ul_inner(html, "profile-fav-list", "".join(game_card(p, suffix) for p in db.list_favorites(viewed["id"])))
            html = replace_ul_inner(html, "profile-create-list", "".join(game_card(p, suffix) for p in db.places_by_creator(viewed["id"])))
            own = user and viewed["id"] == user["id"]
            if own:
                html = html.replace(
                    "{{PROFILE_GEAR}}",
                    '<a href="#" id="update-status-link">Update Status</a>'
                    '<a href="/inventory">Inventory</a>',
                )
                html = html.replace("{{ADD_FRIEND}}", "")
                html = html.replace("{{MESSAGE_BTN}}", "")
            elif user:
                html = html.replace(
                    "{{PROFILE_GEAR}}",
                    (
                        '<a href="/inventory?id=%s">Inventory</a>'
                        '<a href="/trades">Trade</a>'
                    )
                    % viewed["id"],
                )
                html = html.replace(
                    "{{ADD_FRIEND}}",
                    '<form method="post" action="/friends/add" class="profile-action-form">'
                    '<input type="hidden" name="userId" value="%s">'
                    '<button type="submit" class="profile-action-btn">Add Friend</button></form>'
                    % viewed["id"],
                )
                html = html.replace(
                    "{{MESSAGE_BTN}}",
                    '<a class="profile-action-btn" href="/messages#compose-pane">Message</a>',
                )
            else:
                html = html.replace("{{PROFILE_GEAR}}", "")
                html = html.replace("{{ADD_FRIEND}}", "")
                html = html.replace("{{MESSAGE_BTN}}", "")
        else:
            html = html.replace("{{ADD_FRIEND}}", "")
            html = html.replace("{{MESSAGE_BTN}}", "")
            html = html.replace("{{PROFILE_GEAR}}", "")
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
    if "create" in name or "develop" in name:
        html = fill_develop(html, user, qs, suffix)
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
        html = replace_ul_inner(html, "my-group-list", "".join(group_rail_item(g) for g in mine))
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
            html = html.replace("{{GROUP_LETTER}}", esc((g.get("name") or "G")[:1].upper()))
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
        stab = (qs.get("tab") or "account").lower()
        for key, token in (("account","ACCOUNT"),("security","SECURITY"),("privacy","PRIVACY"),("billing","BILLING")):
            html = html.replace("{{TAB_%s}}" % token, "active" if stab == key else "")
            html = html.replace("{{PANE_%s}}" % token, "" if stab == key else 'style="display:none"')
    if "avatar" in name and user:
        tab = (qs.get("tab") or "wardrobe").lower()
        category = qs.get("category") or category
        wearing = db.list_wearing(user["id"])
        owned = db.list_inventory(user["id"])
        catmap = {
            "Heads": None,
            "Faces": "Face",
            "T-Shirts": "Shirt",
            "Shirts": "Shirt",
            "Pants": "Pants",
            "Gear": "Gear",
            "Hats": "Hat",
            "Hair": "Hair",
            "Face": "Face",
            "Neck": "Accessory",
            "Shoulder": "Accessory",
            "Front": "Accessory",
            "Back": "Accessory",
            "Waist": "Accessory",
            "Torsos": None,
            "L Arms": None,
            "R Arms": None,
            "L Legs": None,
            "R Legs": None,
            "Packages": None,
        }
        shown = owned
        if category in catmap:
            mapped = catmap[category]
            shown = [a for a in owned if (a.get("asset_type") or "") == mapped] if mapped else []
        wear_ids = {a["id"] for a in wearing}
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a, wearing=True) for a in wearing), count=1)
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a, wear=a["id"] not in wear_ids, wearing=a["id"] in wear_ids) for a in shown), count=1)
        html = html.replace("{{PROFILE_ID}}", str(user["id"]))
        html = html.replace(
            "{{R6_FIGURE}}",
            '<img class="cc-avatar-img" src="/thumbs/avatar.ashx?userId=%s" alt="Avatar">'
            % user["id"],
        )
        s = db.get_user_settings(user)
        html = html.replace("{{HEAD_COLOR}}", s.get("head_color") or "#F5CD30")
        html = html.replace("{{TORSO_COLOR}}", s.get("torso_color") or "#0D69AC")
        html = html.replace("{{LEFT_ARM_COLOR}}", s.get("left_arm_color") or "#F5CD30")
        html = html.replace("{{RIGHT_ARM_COLOR}}", s.get("right_arm_color") or "#F5CD30")
        html = html.replace("{{LEFT_LEG_COLOR}}", s.get("left_leg_color") or "#4B974B")
        html = html.replace("{{RIGHT_LEG_COLOR}}", s.get("right_leg_color") or "#4B974B")
        html = html.replace("{{COLOR_SWATCHES}}", color_swatches())
        html = html.replace("{{AVATAR_CATEGORY}}", esc(category if category not in ("", "All") else ""))
        html = html.replace("{{TAB_WARDROBE}}", "active" if tab != "outfits" else "")
        html = html.replace("{{TAB_OUTFITS}}", "active" if tab == "outfits" else "")
        html = html.replace("{{WARDROBE_HIDDEN}}", 'style="display:none"' if tab == "outfits" else "")
        html = html.replace("{{OUTFITS_HIDDEN}}", "" if tab == "outfits" else 'style="display:none"')
        groups = [
            ["Heads", "Faces", "T-Shirts", "Shirts", "Pants", "Gear"],
            ["Hats", "Hair", "Face", "Neck", "Shoulder", "Front", "Back", "Waist"],
            ["Torsos", "L Arms", "R Arms", "L Legs", "R Legs", "Packages"],
        ]
        labels = ["", "Accessories", ""]
        bits = []
        for lab, grp in zip(labels, groups):
            line = ('<span class="cc-cat-label">%s </span>' % lab) if lab else ""
            parts = []
            for c in grp:
                cls = "cc-cat selected" if category == c else "cc-cat"
                parts.append('<a class="%s" href="/avatar?tab=wardrobe&category=%s">%s</a>' % (cls, c, c))
            bits.append('<span class="cc-cat-line">' + line + " | ".join(parts) + "</span>")
        html = html.replace("{{AVATAR_SUBCATS}}", "<br>".join(bits))
        outfits = db.list_outfits(user["id"])
        cards = []
        for o in outfits:
            cards.append(
                '<li class="list-item outfit-card"><div class="item-card-container">'
                '<img class="item-card-thumb" src="/static/placeholder.png" alt="">'
                '<div class="item-card-name">%s</div>'
                '<form method="post" action="/avatar/outfit/wear" class="item-buy-form">'
                '<input type="hidden" name="id" value="%s">'
                '<button type="submit" class="btn-primary-xs">Wear</button></form>'
                '<form method="post" action="/avatar/outfit/delete" class="item-buy-form">'
                '<input type="hidden" name="id" value="%s">'
                '<button type="submit" class="btn-secondary-xs">Delete</button></form>'
                "</div></li>" % (esc(o.get("name") or "Outfit"), o["id"], o["id"])
            )
        html = replace_ul_inner(html, "outfit-list", "".join(cards))
        if outfits:
            html = html.replace('<p class="list-content outfit-empty">No outfits</p>', "")
        if shown:
            html = html.replace('<p class="list-content">No items available</p>', "", 1)
        if wearing:
            html = html.replace('<p class="list-content wearing-empty">You aren\'t wearing anything</p>', "")

    if "promo" in name or "redeem" in name:
        html = html.replace('action="promocodes.html"', 'action="/promo/redeem"')
        html = html.replace('action="promocodes-loggedin.html"', 'action="/promo/redeem"')
    if "robux" in name and user:
        html = html.replace("{{ROBUX}}", str(user.get("robux") or 0))
    html = html.replace("{{VERIFIED_BADGE}}", "")
    html = html.replace("{{DEV_BODY}}", "")
    html = html.replace("{{VIEW}}", "0")
    html = html.replace("{{TAB_MY}}", "")
    html = html.replace("{{TAB_GROUP}}", "")
    html = html.replace("{{TAB_LIBRARY}}", "")
    html = html.replace("{{TAB_DEVEX}}", "")
    html = html.replace("{{GROUP_LETTER}}", "G")
    if "</body>" in html:
        html = html.replace("</body>", SITE_JS + "\n</body>", 1)
    else:
        html += SITE_JS
    return html
