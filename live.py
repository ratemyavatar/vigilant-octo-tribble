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
        '<span class="info-label icon-playing-counts-gray"></span>'
        '<span class="info-label playing-counts-label">0</span>'
        "</div></a></div></li>"
    ) % (name, href, thumb, name, name, name, name)


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


def item_card(asset: dict) -> str:
    aid = asset["id"]
    name = esc(asset.get("name") or "Item")
    price = int(asset.get("price") or 0)
    return (
        '<li class="list-item item-card">'
        '<div class="item-card-container">'
        '<a href="#" class="item-card-link">'
        '<div class="item-card-thumb-container">'
        '<img class="item-card-thumb" src="/thumbs/asset.ashx?id=%s" alt="%s">'
        "</div>"
        '<div class="text-overflow item-card-name" title="%s">%s</div>'
        "</a>"
        '<div class="text-overflow item-card-price">'
        '<span class="icon-robux-16x16"></span><span class="text-robux">%s</span>'
        "</div></div></li>"
    ) % (aid, name, name, name, price)


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


def fill_catalog(html: str, assets: list) -> str:
    cards = "".join(item_card(a) for a in assets)
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
    html = html.replace("/profile.html?id=", "/profile%s?id=" % suffix)
    return html


def fill_profile(html: str, viewed: dict, friends: list, places: list, suffix: str) -> str:
    name = esc(viewed.get("username") or "")
    uid = viewed["id"]
    html = html.replace("{{PROFILE_NAME}}", name)
    html = html.replace("{{PROFILE_ID}}", str(uid))
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
  var plays = document.querySelectorAll('.VisitButtonPlayGLI a, a.btn-primary-lg');
  for (var p = 0; p < plays.length; p++) {
    var wrap = plays[p].closest('[placeid]');
    if (wrap && wrap.getAttribute('placeid') && (!plays[p].getAttribute('href') || plays[p].getAttribute('href') === '#')) {
      plays[p].setAttribute('href', '/play?placeId=' + wrap.getAttribute('placeid'));
    }
  }
})();
</script>
"""


def prepare(html: str, page_name: str, user: dict | None, qs: dict) -> str:
    logged_in = user is not None
    suffix = _suffix(logged_in)
    html = sanitize(html)
    name = (page_name or "").lower()

    places = db.list_places()
    assets = db.list_assets()
    friends = db.list_friends(user["id"]) if user else []

    if any(x in name for x in ("discover", "games", "home")):
        html = fill_games(html, places, suffix)
    if "home" in name and user:
        html = html.replace("Hello!", "Hello, {{USERNAME}}!")
        html = fill_friends(html, friends, suffix)
    if "friend" in name:
        html = fill_friends(html, friends, suffix)
    if "catalog" in name or "inventory" in name or "trade" in name:
        owned = db.list_inventory(user["id"]) if user and "inventory" in name else assets
        if "inventory" in name:
            html = fill_catalog(html, owned)
        elif "trade" in name:
            html = fill_catalog(html, owned if user else [])
        else:
            html = fill_catalog(html, assets)
    if name.startswith("game") and "games" not in name:
        pid = 0
        try:
            pid = int(qs.get("id") or qs.get("placeId") or qs.get("placeid") or 0)
        except Exception:
            pid = 0
        place = db.get_place(pid) if pid else None
        if not place and places:
            place = places[-1] if places else None
        if not place:
            place = {
                "id": 0,
                "name": "Untitled",
                "description": "",
                "creator_id": 0,
                "max_players": 10,
                "genre": "All",
                "created_at": int(time.time()),
            }
        html = fill_game_detail(html, place, suffix)
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
        keyword = qs.get("keyword") or qs.get("search") or qs.get("q") or ""
        html = fill_search(
            html,
            keyword,
            db.search_users(keyword) if keyword else [],
            db.search_places(keyword) if keyword else [],
            suffix,
        )
    if "create" in name:
        html = html.replace('action="create.html"', 'action="/places/create"')
        html = html.replace('action="create-loggedin.html"', 'action="/places/create"')
        html = html.replace(
            'action="https://www.roblox.com/places/create"',
            'action="/places/create"',
        )
    if "signup" in name or "login" in name or "landing" in name or "index" in name:
        if 'name="gender"' not in html:
            html = html.replace(
                '<div class="form-group gender-container">',
                '<input type="hidden" name="gender" id="gender-field" value="Male">'
                '<div class="form-group gender-container">',
            )
    if "message" in name:
        notes = db.list_messages(user["id"]) if user else []
        items = []
        for m in notes:
            items.append(
                '<li class="list-item"><div class="list-body"><h2>%s</h2>'
                '<p class="list-content">%s</p></div></li>'
                % (esc(m.get("from_name") or ""), esc(m.get("body") or ""))
            )
        html = replace_ul_inner(html, "feeds", "".join(items))
        if user and '<form method="post" action="/messages/send"' not in html:
            html = html.replace(
                "</div></div></div>",
                '<form method="post" action="/messages/send" class="section-content">'
                '<label class="form-label">To</label>'
                '<input class="form-control input-field" name="username" placeholder="Username">'
                '<label class="form-label">Message</label>'
                '<input class="form-control input-field" name="body" placeholder="Message">'
                '<button type="submit" class="btn-primary-md">Send</button></form></div></div></div>',
                1,
            )
    if "group" in name:
        groups = db.list_groups()
        cards = "".join(
            '<li class="list-item"><div class="list-body"><h2>%s</h2>'
            '<p class="list-content">%s</p></div></li>'
            % (esc(g.get("name") or ""), esc(g.get("description") or ""))
            for g in groups
        )
        if groups:
            html = html.replace(
                '<p class="list-content">No Search Results Found</p>',
                '<ul class="vlist feeds">%s</ul>' % cards,
                1,
            )
        if user and 'action="/groups/create"' not in html:
            html = html.replace(
                "</div></div></div>",
                '<form method="post" action="/groups/create" class="section-content">'
                '<label class="form-label">Name</label>'
                '<input class="form-control input-field" name="name" placeholder="Group name">'
                '<label class="form-label">Description</label>'
                '<input class="form-control input-field" name="description" placeholder="Description">'
                '<button type="submit" class="btn-primary-md">Create Group</button></form></div></div></div>',
                1,
            )
    if "setting" in name and user:
        html = html.replace("{{BLURB}}", esc(user.get("blurb") or ""))
        html = html.replace("{{STATUS}}", esc(user.get("status") or ""))
        html = html.replace('value="{{USERNAME}}"', 'value="%s"' % esc(user["username"]))
    if "avatar" in name and user:
        wearing = db.list_wearing(user["id"])
        owned = db.list_inventory(user["id"])
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a) for a in wearing), count=1)
        html = replace_ul_inner(html, "item-cards", "".join(item_card(a) for a in owned), count=1)
    if "promo" in name or "redeem" in name:
        html = html.replace('action="promocodes.html"', 'action="/promo/redeem"')
        html = html.replace('action="promocodes-loggedin.html"', 'action="/promo/redeem"')
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
