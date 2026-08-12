#!/usr/bin/env python3
"""Rewrite snapshot pages: keep dump chrome, drop cached Roblox lists."""
from pathlib import Path
import re
import shutil

PAGES = Path(__file__).resolve().parent / "pages"
SHELL = (PAGES / "catalog.html").read_text(encoding="utf-8", errors="replace")
SIGNUP = (PAGES / "signup.html").read_text(encoding="utf-8", errors="replace")
HOME = (PAGES / "home.html").read_text(encoding="utf-8", errors="replace")

CATALOG_INNER = """<div class="content">
  <div class="container-header">
    <h1>Catalog</h1>
  </div>
  <div class="tab-content-group">
    <div class="category-dropdown">
      <h3>Category</h3>
      <div class="input-group-btn">
        <button type="button" class="input-dropdown-btn">
          <span class="rbx-selection-label">Featured</span>
          <span class="icon-down-16x16"></span>
        </button>
      </div>
    </div>
  </div>
  <div id="catalog-results" class="section-content">
    <ul class="hlist item-cards"></ul>
    <p class="list-content">No Search Results Found</p>
  </div>
</div>"""


def with_content(title: str, inner: str) -> str:
    html = SHELL
    html = html.replace("<title>Catalog - Roblox</title>", "<title>%s - Roblox</title>" % title)
    if CATALOG_INNER not in html:
        raise SystemExit("catalog shell inner block not found")
    return html.replace(CATALOG_INNER, inner, 1)


DISCOVER = """<div class="content">
  <div class="games-list-container is-windows">
    <div class="container-header games-filter-changer">
      <h3>Experiences</h3>
    </div>
    <div class="games-list">
      <ul class="hlist games game-cards game-tile-list" id="games-list"></ul>
      <p class="list-content">No Search Results Found</p>
    </div>
  </div>
</div>"""

FRIENDS = """<div class="content">
  <div class="col-xs-12 section home-friends">
    <div class="container-header"><h3>Friends (0)</h3></div>
    <div class="section-content">
      <ul class="hlist friend-list"></ul>
      <p class="list-content">No Search Results Found</p>
    </div>
  </div>
</div>"""

GROUPS = """<div class="content">
  <div class="container-header"><h1>Groups</h1></div>
  <div class="section-content">
    <p class="list-content">No Search Results Found</p>
  </div>
</div>"""

PROFILE = """<div class="content">
  <div class="section profile-header">
    <div class="section-content profile-header-content">
      <div class="profile-header-top">
        <div class="avatar avatar-headshot-lg card-plain profile-avatar-image">
          <span class="avatar-card-link avatar-image-link">
            <img class="avatar-card-image profile-avatar-thumb" src="/thumbs/headshot.ashx?userId={{PROFILE_ID}}" alt="{{PROFILE_NAME}}">
          </span>
        </div>
        <div class="header-caption">
          <div class="header-title"><h2 class="profile-name">{{PROFILE_NAME}}</h2></div>
          <div class="header-details">{{ADD_FRIEND}}</div>
        </div>
      </div>
    </div>
  </div>
  <div class="col-xs-12 section home-friends">
    <div class="container-header"><h3>Friends (0)</h3></div>
    <div class="section-content"><ul class="hlist friend-list"></ul></div>
  </div>
  <div class="col-xs-12 container-list">
    <div class="container-header"><h3>Experiences</h3></div>
    <ul class="hlist games game-cards"></ul>
  </div>
</div>"""

GAME = """<div class="content">
  <div class="game-main-content">
    <div class="game-thumb-container">
      <div id="carousel-game-details" class="carousel slide">
        <div class="carousel-inner" role="listbox">
          <div class="item active">
            <span><img class="carousel-thumb" src="/thumbs/place.ashx?id={{GAME_ID}}" alt="{{GAME_NAME}}"></span>
          </div>
        </div>
      </div>
    </div>
    <div class="game-calls-to-action">
      <div class="game-title-container">
        <h2 class="game-name" title="{{GAME_NAME}}">{{GAME_NAME}}</h2>
        <div class="game-creator"><span class="text-label">By</span> <a class="text-name" href="/profile.html?id={{CREATOR_ID}}">{{CREATOR_NAME}}</a></div>
      </div>
      <div class="game-buttons-container">
        <div class="game-play-buttons">
          <div class="game-play-button-container">
            <div id="MultiplayerVisitButton" class="VisitButton VisitButtonPlayGLI" placeid="{{GAME_ID}}" data-action="play">
              <a class="btn-primary-lg" href="/play?placeId={{GAME_ID}}">Play</a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="section game-about-container">
    <div class="container-header"><h3>Description</h3></div>
    <div class="section-content">
      <pre class="game-description linkify">{{GAME_DESC}}</pre>
      <ul class="game-stats-container">
        <li class="game-stat"><p class="text-label">Playing</p><p class="text-lead">0</p></li>
        <li class="game-stat"><p class="text-label">Visits</p><p class="text-lead">0</p></li>
        <li class="game-stat"><p class="text-label">Created</p><p class="text-lead">{{CREATED}}</p></li>
        <li class="game-stat"><p class="text-label">Updated</p><p class="text-lead">{{CREATED}}</p></li>
        <li class="game-stat"><p class="text-label">Max Players</p><p class="text-lead">{{MAX_PLAYERS}}</p></li>
        <li class="game-stat"><p class="text-label">Genre</p><p class="text-lead"><a class="text-name" href="games.html">{{GENRE}}</a></p></li>
      </ul>
    </div>
  </div>
</div>"""


def write(name: str, text: str):
    (PAGES / name).write_text(text, encoding="utf-8")
    print("wrote", name, len(text))


def main():
    for name in ("landing.html", "login.html", "index.html"):
        write(name, SIGNUP)

    write("discover.html", with_content("Discover", DISCOVER))
    write("discover-loggedin.html", with_content("Discover", DISCOVER))
    write("games.html", with_content("Games", DISCOVER))
    write("friends.html", with_content("Friends", FRIENDS))
    write("friends-loggedin.html", with_content("Friends", FRIENDS))
    write("groups.html", with_content("Groups", GROUPS))
    write("groups-loggedin.html", with_content("Groups", GROUPS))
    write("profile.html", with_content("Profile", PROFILE))
    write("profile-loggedin.html", with_content("Profile", PROFILE))
    write("game.html", with_content("Game", GAME))
    write("game-loggedin.html", with_content("Game", GAME))
    write("game-shindo.html", with_content("Game", GAME))
    write("game-shindo-loggedin.html", with_content("Game", GAME))
    write("catalog-filters.html", SHELL)
    write("catalog-filters-loggedin.html", SHELL)

    home = HOME
    home = home.replace("<h1><a href=/users/profile> Hello! </a></h1>", "<h1><a href=/users/profile> Hello, {{USERNAME}}! </a></h1>")
    home = re.sub(
        r'(<ul id="FeaturedGamesContainer" class="list-gallery">).*?(</ul>)',
        r"\1\2",
        home,
        flags=re.S,
    )
    write("home-loggedin.html", home)

    # landing logged-in should just be home
    shutil.copyfile(PAGES / "home-loggedin.html", PAGES / "landing-loggedin.html")
    print("copied landing-loggedin.html")

    AVATAR = """<div class="content">
  <div class="container-header"><h1>Avatar</h1></div>
  <div class="section-content">
    <h2><span>Currently Wearing</span></h2>
    <ul class="hlist item-cards" id="wearing-list"></ul>
  </div>
  <div class="section-content">
    <h2><span>Wardrobe</span></h2>
    <ul class="hlist item-cards" id="wardrobe-list"></ul>
    <p class="list-content">No Search Results Found</p>
  </div>
</div>"""
    write("avatar.html", with_content("Avatar", AVATAR))
    write("avatar-loggedin.html", with_content("Avatar", AVATAR))

    BLOG = """<div class="content">
  <div class="section">
    <div class="section-header"><h3>Blog News</h3></div>
    <div class="section-content">
      <ul class="blog-news"></ul>
      <p class="list-content">No Search Results Found</p>
    </div>
  </div>
</div>"""
    write("blog.html", with_content("Blog", BLOG))
    write("blog-loggedin.html", with_content("Blog", BLOG))

    SETTINGS = """<div class="content">
  <h1 class="user-account-header">My Settings</h1>
  <form id="settingsForm" method="post" action="/settings/update">
    <label class="form-label" for="username">Username:</label>
    <input class="text-box text-box-medium" id="username" name="username" type="text" value="{{USERNAME}}">
    <label class="form-label" for="status">Status:</label>
    <input class="text-box text-box-medium" id="status" name="status" type="text" value="{{STATUS}}">
    <label class="form-label" for="blurb">About:</label>
    <textarea class="text-box text-area-medium" id="blurb" name="blurb" cols="80" rows="4">{{BLURB}}</textarea>
    <div id="buttonRow">
      <button type="submit" class="btn-primary-md" id="finishButton">Save</button>
    </div>
  </form>
</div>"""
    write("settings.html", with_content("Settings", SETTINGS))
    write("settings-loggedin.html", with_content("Settings", SETTINGS))

    MESSAGES = """<div class="content">
  <div class="col-xs-12 section home-friends">
    <div class="container-header"><h3>Messages</h3></div>
    <div class="section-content"><ul class="vlist feeds"></ul></div>
  </div>
</div>"""
    write("messages.html", with_content("Messages", MESSAGES))
    write("messages-loggedin.html", with_content("Messages", MESSAGES))

    PROMO = """<div class="content">
  <div class="container-header"><h1>Redeem ROBLOX Promotions</h1></div>
  <div class="section-content">
    <p class="list-content">Have you received a promotional code? Enter it here.</p>
    <form method="post" action="/promo/redeem">
      <label class="form-label" for="pin">Enter Your Code:</label>
      <input class="form-control input-field" id="pin" name="code" type="text">
      <button type="submit" class="btn-primary-md">Redeem</button>
    </form>
  </div>
</div>"""
    write("promocodes.html", with_content("Promocodes", PROMO))
    write("promocodes-loggedin.html", with_content("Promocodes", PROMO))
    write("redeem.html", with_content("Redeem", PROMO))
    write("redeem-loggedin.html", with_content("Redeem", PROMO))

    # strip leftover snapshot names/counts from every remaining page
    for fp in PAGES.glob("*.html"):
        t = fp.read_text(encoding="utf-8", errors="replace")
        orig = t
        t = re.sub(r'data-name="Player"', 'data-name="{{USERNAME}}"', t)
        t = re.sub(r'data-displayname="Player"', 'data-displayname="{{USERNAME}}"', t)
        t = re.sub(r'data-displayname="a_randomperson"', 'data-displayname="{{USERNAME}}"', t)
        t = re.sub(r">Player<", ">{{USERNAME}}<", t)
        t = re.sub(r"Player:", "{{USERNAME}}:", t)
        t = re.sub(r"(notification-red[^>]*>)\s*\d+", r"\g<1>0", t)
        t = re.sub(r"(notification-blue[^>]*>)\s*\d+", r"\g<1>0", t)
        t = re.sub(r'data-count=["\']?\d+', 'data-count="0"', t)
        t = re.sub(
            r"(<ul\b[^>]*\bblog-news\b[^>]*>).*?(</ul>)",
            r"\1\2",
            t,
            flags=re.I | re.S,
        )
        if t != orig:
            fp.write_text(t, encoding="utf-8")
            print("sanitized", fp.name)


if __name__ == "__main__":
    main()
