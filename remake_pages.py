#!/usr/bin/env python3
"""Write every site page using Economy Simulator 2016 layouts, dark theme."""
from pathlib import Path

PAGES = Path(__file__).resolve().parent / "pages"
PH = "/static/placeholder.png"
ICO = "/static/ecs/logo_R.svg"

YEARS = "".join('<option value="%s">%s</option>' % (y, y) for y in range(2026, 1916, -1))
DAYS = "".join('<option value="%s">%s</option>' % (d, d) for d in range(1, 32))
MONTHS = "".join(
    '<option value="%s">%s</option>' % (i, n)
    for i, n in enumerate(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
)
GENRES = "".join(
    "<option>%s</option>" % g
    for g in [
        "All",
        "Adventure",
        "Building",
        "Comedy",
        "Fighting",
        "FPS",
        "Horror",
        "Medieval",
        "Military",
        "Naval",
        "RPG",
        "Sci-Fi",
        "Sports",
        "Town and City",
        "Western",
    ]
)
MAXP = "".join(
    '<option%s>%s</option>' % (" selected" if n == 10 else "", n) for n in range(1, 51)
)
TEMPLATES = [
    ("95206881", "Baseplate"),
    ("6560363541", "Classic Baseplate"),
    ("95206192", "Flat Terrain"),
    ("203812057", "Obby"),
    ("215383192", "Racing"),
    ("203885589", "Combat"),
    ("379736082", "Starting Place"),
    ("203783329", "City"),
]
TPL_HTML = "".join(
    '<div class="template" placeid="%s"><img src="%s" alt="%s"><p>%s</p></div>' % (i, PH, n, n)
    for i, n in TEMPLATES
)

FOOTER = """<footer class="container-footer" id="footer-container">
<div class="footer ecs-footer">
<div class="footer-link-row">
<a class="text-footer-nav" href="/about">About Us</a>
<a class="text-footer-nav" href="/jobs">Jobs</a>
<a class="text-footer-nav" href="/blog">Blog</a>
<a class="text-footer-nav" href="/privacy">Privacy</a>
<a class="text-footer-nav" href="/help">Help</a>
<a class="text-footer-nav" href="/terms">Terms</a>
<a class="text-footer-nav" href="/credits">Credits</a>
</div>
<p class="text-footer footer-note">ROBLOX, "Online Building Toy", characters, logos, names, and all related indicia are trademarks of their respective owners. This is a private revival. Use of this site signifies your acceptance of the <a href="/terms">Terms and Conditions</a>.</p>
</div></footer>"""

GENDER = """<div class="form-group gender-container"><label class="text-label">Gender</label>
<div class="gender-row">
<button type="button" id="MaleButton" class="gender-button btn-control-md selected"><span class="icon-male"></span><span>Male</span></button>
<button type="button" id="FemaleButton" class="gender-button btn-control-md"><span class="icon-female"></span><span>Female</span></button>
</div></div>"""


def page(title, inner, extra_head=""):
    return """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s - ROBLOX</title>
<link rel="icon" href="%s">
<link rel="stylesheet" href="/static/site.css">
%s
</head>
<body id="rbx-body" class="rbx-body dark-theme theme-2016">
<div id="wrap" class="wrap no-gutter-ads dark-theme">
<div id="header" class="navbar-fixed-top rbx-header" role="navigation">
  <div class="container-fluid">
    <div class="rbx-navbar-header">
      <div id="header-menu-icon" class="rbx-nav-collapse" role="button" tabindex="0" aria-label="Menu"></div>
      <a class="navbar-brand" href="/"><span class="icon-logo">ROBLOX</span></a>
    </div>
  </div>
</div>
<div class="container-main" id="container-main">
<div class="content">
%s
</div>
</div>
%s
</div>
</body>
</html>
""" % (
        title,
        ICO,
        extra_head,
        inner,
        FOOTER,
    )


SIGNUP = """<div id="react-login-container" class="login-container ecs-login">
<div class="section-content login-section">
<p class="signup-kicker">Not a member?</p>
<h1 class="login-header">Sign Up to Build &amp; Make Friends</h1>
<form class="login-form" name="loginForm" method="post" action="/signup">
<input type="hidden" name="gender" id="gender-field" value="Male">
<div class="form-group birthday-container"><label class="text-label">Birthday</label>
<div class="birthday-row">
<div class="rbx-select-group"><select class="input-field rbx-select" id="MondDropdown" name="BirthMonth"><option value="" selected disabled>Month</option>%s</select></div>
<div class="rbx-select-group"><select class="input-field rbx-select" id="DayDropdown" name="BirthDay"><option value="" selected disabled>Day</option>%s</select></div>
<div class="rbx-select-group"><select class="input-field rbx-select" id="YearDropdown" name="BirthYear"><option value="" selected disabled>Year</option>%s</select></div>
</div></div>
<div class="form-group"><label class="text-label" for="login-username">Username</label>
<input id="login-username" name="username" type="text" class="form-control input-field" placeholder="Username"></div>
<div class="form-group"><label class="text-label" for="login-password">Password</label>
<input id="login-password" name="password" type="password" class="form-control input-field" placeholder="Password"></div>
%s
<button type="submit" id="login-button" class="btn-full-width login-button btn-growth-md">Sign Up</button>
</form>
</div></div>""" % (
    MONTHS,
    DAYS,
    YEARS,
    GENDER,
)

HOME = """<div class="ecs-dash">
<div class="ecs-hello">
<a href="/profile" class="avatar avatar-headshot-lg ecs-hello-shot">
<img alt="avatar" src="/thumbs/headshot.ashx?userId={{PROFILE_ID}}" id="home-avatar-thumb" class="avatar-card-image">
</a>
<div class="home-header-content">
<h1 class="hello-message"><a href="/profile">Hello, {{USERNAME}}!</a>{{VERIFIED_BADGE}}</h1>
<p class="profile-status text-lead">{{STATUS}}</p>
<form class="status-update-form" method="post" action="/settings/update">
<input class="input-field" name="status" maxlength="140" placeholder="What are you up to?">
<button type="submit" class="btn-secondary-xs">Share</button>
</form>
</div>
</div>
<div class="section home-friends ecs-card">
<div class="container-header"><h3 class="ecs-row-title">Friends (0)</h3><a href="/friends" class="btn-secondary-xs">See All</a></div>
<div class="section-content"><ul class="hlist friend-list"></ul></div>
</div>
<div class="container-list home-continue">
<div class="container-header"><h3 class="ecs-row-title">Continue</h3></div>
<ul class="hlist games game-cards" id="continue-list"></ul>
</div>
<div class="container-list home-favorites">
<div class="container-header"><h3 class="ecs-row-title">Favorites</h3></div>
<ul class="hlist games game-cards" id="favorites-list"></ul>
</div>
<div class="container-list home-games">
<div class="container-header"><h3 class="ecs-row-title">Recommended</h3><a href="/games" class="btn-secondary-xs">See All</a></div>
<ul class="hlist games game-cards game-tile-list" id="games-list"></ul>
</div>
<div class="container-list home-creations">
<div class="container-header"><h3 class="ecs-row-title">My Creations</h3><a href="/develop" class="btn-secondary-xs">Create</a></div>
<ul class="hlist games game-cards" id="my-places-list"></ul>
</div>
</div>"""

DISCOVER = """<div class="games-list-container ecs-games">
<div class="ecs-games-bar">
<form class="games-filter-bar" method="get" action="/games">
<input class="input-field" name="keyword" placeholder="Search games" value="{{SEARCH_KEYWORD}}">
<select class="input-field rbx-select" name="genre">{{GENRE_OPTS}}</select>
<select class="input-field rbx-select" name="sort">{{SORT_OPTS}}</select>
<button type="submit" class="btn-primary-md">Search</button>
</form>
</div>
<div class="container-list games-shelf">
<div class="container-header"><h3 class="ecs-row-title">Popular</h3></div>
<ul class="hlist games game-cards game-tile-list" id="games-popular"></ul>
</div>
<div class="container-list games-shelf">
<div class="container-header"><h3 class="ecs-row-title">Recommended</h3></div>
<ul class="hlist games game-cards game-tile-list" id="games-spotlight"></ul>
</div>
<div class="container-list games-shelf">
<div class="container-header"><h3 class="ecs-row-title">Top Favorite</h3></div>
<ul class="hlist games game-cards game-tile-list" id="games-fresh"></ul>
</div>
<div class="container-list games-shelf">
<div class="container-header"><h3 class="ecs-row-title">Top Rated</h3></div>
<ul class="hlist games game-cards game-tile-list" id="games-rated"></ul>
<p class="list-content">No Search Results Found</p>
</div>
</div>"""

FRIENDS = """<div class="section friends-content ecs-friends">
<h1 class="ecs-page-title">My Friends</h1>
<ul class="nav nav-tabs settings-tabs" role="tablist">
<li class="rbx-tab active"><a class="rbx-tab-heading" href="#friends-pane" data-tab="friends-pane">Friends</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#requests-pane" data-tab="requests-pane">Friend Requests</a></li>
</ul>
<div id="friends-pane" class="tab-pane settings-tab-pane active">
<div class="section-content ecs-card">
<form method="post" action="/friends/add" class="add-friend-form">
<label class="form-label" for="friend-username">Add a Friend</label>
<input class="input-field" id="friend-username" name="username" placeholder="Username">
<button type="submit" class="btn-primary-md">Send Request</button>
</form>
<h2 class="ecs-subhead">FRIENDS (0)</h2>
<ul class="hlist friend-list"></ul>
<p class="list-content">No Search Results Found</p>
</div>
</div>
<div id="requests-pane" class="tab-pane settings-tab-pane">
<div class="section-content ecs-card">
<h2 class="ecs-subhead">FRIEND REQUESTS</h2>
<ul class="vlist request-list"></ul>
<p class="list-content request-empty">No pending requests.</p>
</div>
</div>
</div>"""

CAT_NAV = "".join(
    '<li class="menu-option"><a href="/catalog?category=%s">%s</a></li>'
    % (slug, label)
    for slug, label in [
        ("", "Featured"),
        ("Hat", "Hats"),
        ("Hair", "Hair"),
        ("Face", "Faces"),
        ("Shirt", "Shirts"),
        ("Pants", "Pants"),
        ("Gear", "Gear"),
        ("Accessory", "Accessories"),
    ]
)

CATALOG = """<div class="ecs-catalog">
<div class="ecs-catalog-top">
<h1 class="ecs-page-title">Catalog</h1>
<form class="games-filter-bar catalog-search" method="get" action="/catalog">
<input class="input-field" name="keyword" placeholder="Search" value="{{SEARCH_KEYWORD}}">
<select class="input-field rbx-select" name="category">{{CATEGORY_OPTS}}</select>
<button type="submit" class="btn-legacy">Search</button>
</form>
</div>
<div class="catalog-container">
<aside class="menu-vertical catalog-left">
<p class="browse-by">Browse by</p>
<h2 class="browse-cat">Category</h2>
<ul class="menu-vertical">%s</ul>
<div class="catalog-legend">
<details open>
<summary>Legend</summary>
<div class="legend-entry"><img src="/static/ecs/overlay_bcCatalog.png" alt=""><p class="legend-title">Builders Club Only</p><p class="legend-desc">Only purchasable by Builders Club members.</p></div>
<div class="legend-entry"><img src="/static/ecs/limitedOverlay_small.png" alt=""><p class="legend-title">Limited Items</p><p class="legend-desc">Owners of these discontinued items can re-sell them to other users at any price.</p></div>
<div class="legend-entry"><img src="/static/ecs/limitedUOverlay_small.png" alt=""><p class="legend-title">Limited Unique Items</p><p class="legend-desc">A limited supply originally sold by ROBLOX. Each unit is labeled with a serial number.</p></div>
</details>
</div>
</aside>
<div class="catalog-right">
<div class="catalog-results-head">
<h2 class="catalog-showing">FEATURED ITEMS ON ROBLOX</h2>
<form method="get" action="/catalog" class="sort-by-form">
<span class="sort-by-label">Sort By:</span>
<select class="input-field rbx-select" name="sort">{{CATALOG_SORT_OPTS}}</select>
</form>
</div>
<div id="catalog-results" class="section-content ecs-catalog-grid">
<ul class="hlist item-cards"></ul>
<p class="list-content">No Search Results Found</p>
</div>
</div>
</div>
</div>""" % CAT_NAV

PROFILE = """<div class="ecs-profile">
<div class="section profile-header">
<div class="section-content profile-header-content">
<div class="profile-header-top">
<div class="avatar avatar-headshot-lg card-plain profile-avatar-image">
<img class="avatar-card-image profile-avatar-thumb" src="/thumbs/headshot.ashx?userId={{PROFILE_ID}}" alt="{{PROFILE_NAME}}">
</div>
<div class="header-caption">
<div class="header-title">
<h2>{{PROFILE_NAME}}{{VERIFIED_BADGE}}</h2>
<div class="profile-dots-wrap">
<button type="button" class="profile-dots" id="profile-gear" aria-haspopup="true" aria-expanded="false">...</button>
<div class="profile-gear-menu" id="profile-gear-menu">{{PROFILE_GEAR}}</div>
</div>
</div>
<div class="header-details">
<ul class="details-info">
<li><div class="text-label">Friends</div><a class="text-name" href="/friends"><h3>{{FRIEND_COUNT}}</h3></a></li>
<li><div class="text-label">Followers</div><h3 class="text-name">{{FOLLOWER_COUNT}}</h3></li>
<li><div class="text-label">Following</div><h3 class="text-name">{{FOLLOWING_COUNT}}</h3></li>
</ul>
<div class="profile-actions">{{MESSAGE_BTN}}{{ADD_FRIEND}}</div>
</div>
<p class="profile-status-quote" id="profile-status-text">{{PROFILE_STATUS_DISPLAY}}</p>
<form id="profile-status-form" class="profile-status-form" method="post" action="/settings/update" hidden>
<input class="input-field" name="status" maxlength="255" value="{{PROFILE_STATUS}}" placeholder="What are you doing?">
<button type="submit" class="profile-status-save">Save Status</button>
</form>
</div>
</div>
</div>
</div>

<div class="profile-tabs-card">
<a class="profile-tab active" href="#about-pane" data-tab="about-pane">About</a>
<a class="profile-tab" href="#creations-pane" data-tab="creations-pane">Creations</a>
</div>

<div id="about-pane" class="tab-pane settings-tab-pane active">
<h3 class="ecs-subtitle">About</h3>
<div class="ecs-card about-card">
<p class="about-body profile-blurb">{{PROFILE_BLURB}}</p>
<div class="divider-top"></div>
<p class="prev-names">Past usernames stay on this page when someone changes theirs.</p>
</div>

<h3 class="ecs-subtitle">Currently Wearing</h3>
<div class="wearing-row">
<div class="wearing-avatar ecs-card">
<img class="cc-avatar-img" src="/thumbs/avatar.ashx?userId={{PROFILE_ID}}" alt="{{PROFILE_NAME}}">
</div>
<div class="wearing-items">
<ul class="hlist item-cards" id="profile-wearing"></ul>
</div>
</div>

<div class="section home-friends">
<div class="container-header"><h3 class="ecs-subtitle">Friends (0)</h3><a href="/friends" class="see-all">See All</a></div>
<div class="ecs-card"><ul class="hlist friend-list"></ul></div>
</div>

<h3 class="ecs-subtitle">Collections</h3>
<div class="ecs-card"><ul class="vlist group-list"></ul></div>

<h3 class="ecs-subtitle">Favorite Games</h3>
<ul class="hlist games game-cards profile-fav-list" id="profile-favorites"></ul>

<h3 class="ecs-subtitle">Player Badges</h3>
<div class="ecs-card badge-row">
<p class="list-content">Badges earned on this server show up here.</p>
</div>

<h3 class="ecs-subtitle">Statistics</h3>
<div class="ecs-card stats-row">
<div class="stat-cell"><p class="stat-label">Join Date</p><p class="stat-value">{{PROFILE_JOINED}}</p></div>
<div class="stat-cell"><p class="stat-label">Place Visits</p><p class="stat-value">{{PLACE_VISITS}}</p></div>
<div class="stat-cell"><p class="stat-label">Forum Posts</p><p class="stat-value">0</p></div>
</div>
</div>

<div id="creations-pane" class="tab-pane settings-tab-pane">
<h3 class="ecs-subtitle">Games</h3>
<ul class="hlist games game-cards profile-create-list" id="profile-creations"></ul>
</div>
</div>"""

GAME = """<div class="ecs-game ecs-game-2016">
  <div class="ecs-game-head">
    <h1 class="ecs-game-title">{{GAME_NAME}}</h1>
    {{GAME_GEAR}}
  </div>
  <div class="ecs-game-overview">
    <div class="ecs-game-left">
      <div class="ecs-game-thumb-wrap">
        <img class="ecs-game-thumb" src="/thumbs/place.ashx?id={{GAME_ID}}" alt="{{GAME_NAME}}">
      </div>
      <div class="ecs-vote-row">
        <div class="ecs-vote-counts">
          <form method="post" action="/places/vote" class="ecs-vote-hit">
            <input type="hidden" name="placeId" value="{{GAME_ID}}">
            <input type="hidden" name="up" value="1">
            <button type="submit" class="ecs-thumb ecs-thumb-up" title="Like" aria-label="Like"></button>
            <span class="ecs-vote-n">{{UPVOTES}}</span>
          </form>
          <form method="post" action="/places/vote" class="ecs-vote-hit ecs-vote-hit-down">
            <input type="hidden" name="placeId" value="{{GAME_ID}}">
            <input type="hidden" name="up" value="0">
            <span class="ecs-vote-n">{{DOWNVOTES}}</span>
            <button type="submit" class="ecs-thumb ecs-thumb-down" title="Dislike" aria-label="Dislike"></button>
          </form>
        </div>
        <div class="ecs-vote-track"><div class="ecs-vote-green" style="width:{{VOTE_PCT}}%"></div></div>
        <p class="ecs-vote-msg">{{VOTE_MSG}}</p>
      </div>
      <p class="ecs-game-desc">{{GAME_DESC}}</p>
    </div>
    <div class="ecs-game-right">
      <div class="ecs-builder">
        <a class="ecs-builder-shot-link" href="/profile/user/{{CREATOR_ID}}">
          <img class="ecs-builder-shot" src="/thumbs/headshot.ashx?userId={{CREATOR_ID}}" alt="{{CREATOR_NAME}}">
        </a>
        <div class="ecs-builder-copy">
          <p class="ecs-builder-label">Builder:</p>
          <a class="ecs-builder-name" href="/profile/user/{{CREATOR_ID}}">{{CREATOR_NAME}}</a>
        </div>
      </div>
      <div class="divider-top ecs-game-div"></div>
      <div class="game-play-buttons">
        <div id="MultiplayerVisitButton" class="VisitButton VisitButtonPlayGLI" placeid="{{GAME_ID}}">
          <a class="btn-play-green rbx-play-button btn-primary-lg" href="#" data-placeid="{{GAME_ID}}">Play</a>
        </div>
      </div>
      <div class="ecs-stat-list">
        <p><span class="ecs-stat-k">Created:</span> {{CREATED}}</p>
        <p><span class="ecs-stat-k">Updated:</span> {{UPDATED}}</p>
        <p><span class="ecs-stat-k">Favorited:</span> {{FAVORITE_COUNT}}</p>
        <p><span class="ecs-stat-k">Visited:</span> {{VISITS}}</p>
        <p><span class="ecs-stat-k">Max Players:</span> {{MAX_PLAYERS}}</p>
        <p><span class="ecs-stat-k">Genres:</span> {{GENRE}}</p>
        <p><span class="ecs-stat-k">Allowed Gear Types:</span></p>
        <p>None</p>
      </div>
      <div class="divider-top ecs-game-div"></div>
      <div class="ecs-favorite">{{FAVORITE_FORM}}</div>
    </div>
  </div>
  <div class="vtab-bar ecs-vtabs">
    <a class="vtab active" href="#rec-pane" data-tab="rec-pane">Recommendations</a>
    <a class="vtab" href="#servers-pane" data-tab="servers-pane">Games</a>
    <a class="vtab" href="#comments-pane" data-tab="comments-pane">Commentary</a>
  </div>
  <div id="rec-pane" class="tab-pane settings-tab-pane active">
    <div class="container-list">
      <ul class="hlist games game-cards" id="recommended-list"></ul>
    </div>
  </div>
  <div id="servers-pane" class="tab-pane settings-tab-pane">
    <div class="ecs-servers">{{SERVERS}}</div>
  </div>
  <div id="comments-pane" class="tab-pane settings-tab-pane">
    {{COMMENT_FORM}}
    <div class="ecs-comments">{{COMMENTS}}</div>
  </div>
</div>"""

ITEM = """<div class="ecs-item">
  <h1 class="item-title">{{ITEM_NAME}}</h1>
  <h3 class="item-subtitle">ROBLOX {{ITEM_TYPE}}</h3>
  <div class="item-layout">
    <div class="item-preview ecs-card">
      <img class="item-detail-thumb" src="/thumbs/asset.ashx?id={{ITEM_ID}}" alt="{{ITEM_NAME}}">
    </div>
    <div class="item-copy">
      <p class="text-label">By <a class="text-name" href="/profile/user/{{CREATOR_ID}}">{{CREATOR_NAME}}</a></p>
      <p class="item-desc">{{ITEM_DESC}}</p>
    </div>
    <div class="item-buy-col ecs-card">
      <p class="item-price"><span class="icon-robux-16x16"></span> <span class="text-robux">R$ {{ITEM_PRICE}}</span></p>
      <form method="post" action="/catalog/buy">
        <input type="hidden" name="id" value="{{ITEM_ID}}">
        <button type="submit" class="btn-play-green btn-item-buy">Buy with R$</button>
      </form>
    </div>
  </div>
  <h3 class="ecs-subtitle">Recommendations</h3>
  <ul class="hlist item-cards"></ul>
</div>"""

CREATE = """<div class="ecs-develop">
<div class="vtab-bar ecs-vtabs develop-vtabs">
<a class="vtab {{TAB_MY}}" href="/develop?tab=my&amp;View={{VIEW}}">My Creations</a>
<a class="vtab {{TAB_GROUP}}" href="/develop?tab=group&amp;View={{VIEW}}">Group Creations</a>
<a class="vtab {{TAB_LIBRARY}}" href="/develop?tab=library">Library</a>
<a class="vtab {{TAB_DEVEX}}" href="/develop?tab=devex">Developer Exchange</a>
</div>
<div class="develop-body">{{DEV_BODY}}</div>
</div>"""

AVATAR = """<div class="character-customizer">
<h1 class="cc-title">Character</h1>
<div class="cc-row">
<div class="cc-left">
  <h2 class="cc-h2">Avatar</h2>
  <div class="cc-thumb">
    <img class="cc-avatar-img" src="/thumbs/avatar.ashx?userId={{PROFILE_ID}}" alt="Avatar">
  </div>
  <p class="mb-0">Something wrong with your Avatar?</p>
  <p class="mb-0"><a href="/avatar">Click here to re-draw it!</a></p>
  <h2 class="cc-h2">Avatar Colors</h2>
  <div class="cc-mannequin">
    <div class="cc-head" data-part="head" style="background:{{HEAD_COLOR}}"></div>
    <div class="cc-torso" data-part="torso" style="background:{{TORSO_COLOR}}">
      <div class="cc-arm-l" data-part="left_arm" style="background:{{LEFT_ARM_COLOR}}"></div>
      <div class="cc-arm-r" data-part="right_arm" style="background:{{RIGHT_ARM_COLOR}}"></div>
    </div>
    <div class="cc-legs">
      <div class="cc-leg-l" data-part="left_leg" style="background:{{LEFT_LEG_COLOR}}"></div>
      <div class="cc-leg-r" data-part="right_leg" style="background:{{RIGHT_LEG_COLOR}}"></div>
    </div>
  </div>
  <form method="post" action="/avatar/colors" id="skinForm" class="cc-picker" hidden>
    <input type="hidden" name="part" id="color-part" value="all">
    <p class="cc-picker-close" id="color-close">Close</p>
    <div class="color-palette">{{COLOR_SWATCHES}}</div>
  </form>
</div>
<div class="cc-right">
  <div class="vtab-bar">
    <a class="vtab {{TAB_WARDROBE}}" href="/avatar?tab=wardrobe">Wardrobe</a>
    <a class="vtab {{TAB_OUTFITS}}" href="/avatar?tab=outfits">Outfits</a>
  </div>
  <div class="wardrobe-panel" {{WARDROBE_HIDDEN}}>
    <div class="ae-catbar" data-current="{{AVATAR_CATEGORY}}">
      <div class="ae-dd">
        <button type="button" class="ae-dd-btn">Recent <span class="ae-caret"></span></button>
        <div class="ae-dd-menu">
          <a href="/avatar?tab=wardrobe">All Items</a>
        </div>
      </div>
      <div class="ae-dd">
        <button type="button" class="ae-dd-btn">Clothing <span class="ae-caret"></span></button>
        <div class="ae-dd-menu">
          <a href="/avatar?tab=wardrobe&amp;category=Shirts">Shirts</a>
          <a href="/avatar?tab=wardrobe&amp;category=T-Shirts">T-Shirts</a>
          <a href="/avatar?tab=wardrobe&amp;category=Pants">Pants</a>
        </div>
      </div>
      <div class="ae-dd">
        <button type="button" class="ae-dd-btn">Accessories <span class="ae-caret"></span></button>
        <div class="ae-dd-menu">
          <a href="/avatar?tab=wardrobe&amp;category=Hats">Hats</a>
          <a href="/avatar?tab=wardrobe&amp;category=Hair">Hair</a>
          <a href="/avatar?tab=wardrobe&amp;category=Face">Face</a>
          <a href="/avatar?tab=wardrobe&amp;category=Neck">Neck</a>
          <a href="/avatar?tab=wardrobe&amp;category=Shoulder">Shoulder</a>
          <a href="/avatar?tab=wardrobe&amp;category=Front">Front</a>
          <a href="/avatar?tab=wardrobe&amp;category=Back">Back</a>
          <a href="/avatar?tab=wardrobe&amp;category=Waist">Waist</a>
          <a href="/avatar?tab=wardrobe&amp;category=Gear">Gear</a>
        </div>
      </div>
      <div class="ae-dd">
        <button type="button" class="ae-dd-btn">Head &amp; Body <span class="ae-caret"></span></button>
        <div class="ae-dd-menu">
          <a href="/avatar?tab=wardrobe&amp;category=Heads">Heads</a>
          <a href="/avatar?tab=wardrobe&amp;category=Faces">Faces</a>
          <a href="/avatar?tab=wardrobe&amp;category=Torsos">Torsos</a>
          <a href="/avatar?tab=wardrobe&amp;category=L Arms">Left Arms</a>
          <a href="/avatar?tab=wardrobe&amp;category=R Arms">Right Arms</a>
          <a href="/avatar?tab=wardrobe&amp;category=L Legs">Left Legs</a>
          <a href="/avatar?tab=wardrobe&amp;category=R Legs">Right Legs</a>
          <a href="/avatar?tab=wardrobe&amp;category=Packages">Packages</a>
          <a href="#" id="ae-skin-tone">Skin Tone</a>
        </div>
      </div>
    </div>
    <p class="ae-shop"><a href="/catalog">Shop</a> <span class="ae-sep">|</span> <a href="/catalog">Create</a></p>
    <div class="row wardrobe-grid">
      <ul class="hlist item-cards" id="wardrobe-list"></ul>
    </div>
    <p class="list-content">No items available</p>
  </div>
  <div class="outfits-panel" {{OUTFITS_HIDDEN}}>
    <form method="post" action="/avatar/outfit/create" class="create-outfit-form">
      <input class="input-field" name="name" placeholder="Outfit name" maxlength="25">
      <button type="submit" class="btn-growth-sm">Create Outfit</button>
    </form>
    <ul class="hlist outfit-list"></ul>
    <p class="list-content outfit-empty">No outfits</p>
  </div>
  <div class="divider-top"></div>
  <h2 class="cc-h2">Currently Wearing</h2>
  <ul class="hlist item-cards" id="wearing-list"></ul>
  <p class="list-content wearing-empty">You aren't wearing anything</p>
</div>
</div>
</div>"""

MESSAGES = """<div class="ecs-messages">
<h1 class="ecs-page-title">Messages</h1>
<div class="vtab-bar">
<a class="vtab active" href="#inbox-pane" data-tab="inbox-pane">Inbox</a>
<a class="vtab" href="#sent-pane" data-tab="sent-pane">Sent</a>
<a class="vtab" href="#compose-pane" data-tab="compose-pane">New Message</a>
</div>
<div id="inbox-pane" class="tab-pane settings-tab-pane active">
<div class="section-content ecs-card"><ul class="vlist feeds inbox-list"></ul>
<p class="list-content inbox-empty">No messages.</p></div>
</div>
<div id="sent-pane" class="tab-pane settings-tab-pane">
<div class="section-content ecs-card"><ul class="vlist sent-list"></ul>
<p class="list-content sent-empty">No sent messages.</p></div>
</div>
<div id="compose-pane" class="tab-pane settings-tab-pane">
<div class="section-content ecs-card">
<form method="post" action="/messages/send">
<label class="form-label">To</label>
<input class="input-field" name="username" placeholder="Username">
<label class="form-label">Subject</label>
<input class="input-field" name="subject" placeholder="Subject">
<label class="form-label">Message</label>
<textarea class="text-box text-area-medium" name="body" rows="4" placeholder="Write a message"></textarea>
<button type="submit" class="btn-primary-md">Send</button>
</form></div>
</div>
</div>"""

GROUPS = """<div class="ecs-groups groups-2016">
<div class="groups-layout">
<aside class="groups-side" id="left-column">
<div class="CreateGroupContainer">
<form method="post" action="/groups/create" class="create-group-form">
<label class="form-label">Start a Group</label>
<input class="input-field" name="name" placeholder="Group name" maxlength="50">
<input class="input-field" name="description" placeholder="What is this group about?">
<button type="submit" class="btn-primary-md">Create</button>
</form>
</div>
<h3 class="my-groups-label">My Groups</h3>
<ul class="vlist my-group-list GroupThumbnails" id="GroupThumbnails"></ul>
</aside>
<div class="groups-main" id="mid-column">
<div id="SearchControls">
<form method="get" action="/groups" class="group-search-bar">
<input class="input-field SearchKeyword" name="keyword" placeholder="Search all groups" value="{{SEARCH_KEYWORD}}" maxlength="100">
<button type="submit" class="group-search-button">Search</button>
</form>
</div>
<div id="description" class="GroupPanelContainer">
<div class="group-emblem-col">
<div class="GroupEmblem" aria-hidden="true">{{GROUP_LETTER}}</div>
</div>
<div class="group-copy-col">
<h2 class="group-panel-name">{{GROUP_NAME}}</h2>
<p class="GroupDescription">{{GROUP_DESC}}</p>
<p class="text-label">Owner {{GROUP_OWNER}} · Members {{GROUP_MEMBERS}}</p>
{{GROUP_JOIN}}
</div>
</div>
<div class="section group-wall-card">
<div class="container-header"><h3>Group Wall</h3></div>
<p class="list-content">Wall posts stay on this server. Pick a group to read its page.</p>
</div>
<div class="section">
<div class="container-header"><h3>Members</h3></div>
<ul class="hlist friend-list group-member-list"></ul>
</div>
<div class="section">
<div class="container-header"><h3>Find Groups</h3></div>
<ul class="vlist group-list"></ul>
<p class="list-content">No Search Results Found</p>
</div>
</div>
</div>
</div>"""

SETTINGS = """<div class="my-settings">
<h1 class="user-account-header">My Settings</h1>
<ul class="settings-tabs">
<li class="{{TAB_ACCOUNT}}"><a href="/settings?tab=account">Account Info</a></li>
<li class="{{TAB_SECURITY}}"><a href="/settings?tab=security">Security</a></li>
<li class="{{TAB_PRIVACY}}"><a href="/settings?tab=privacy">Privacy</a></li>
<li class="{{TAB_BILLING}}"><a href="/settings?tab=billing">Billing</a></li>
</ul>

<div class="settings-pane" {{PANE_ACCOUNT}}>
  <h3 class="settings-sub">Account Info</h3>
  <div class="settings-card">
    <p class="acct-row">Username: <span class="acct-val">{{USERNAME}}</span></p>
    <p class="acct-row">Password: <span class="acct-val">**********</span></p>
    <p class="acct-row">Email Address: <span class="acct-val">{{EMAIL}}</span></p>
  </div>
  <h3 class="settings-sub">Personal</h3>
  <div class="settings-card">
    <form method="post" action="/settings/update">
      <input type="hidden" name="tab" value="account-info">
      <textarea class="desc-input" name="blurb" rows="3" placeholder="About">{{BLURB}}</textarea>
      <p class="list-content">Do not provide any details that can be used to identify you outside ROBLOX.</p>
      <div class="bday-grid">
        <input class="input-field disabled-fake" value="Birthday" readonly>
        <input class="input-field" name="birthday" value="{{BIRTHDAY}}" placeholder="Month/Day/Year">
      </div>
      <div class="gender-grid">
        <input class="input-field disabled-fake" value="Gender" readonly>
        <label class="gender-card {{GENDER_MALE}}"><input type="radio" name="gender" value="Male" {{GENDER_MALE_CHECKED}}> Male</label>
        <label class="gender-card {{GENDER_FEMALE}}"><input type="radio" name="gender" value="Female" {{GENDER_FEMALE_CHECKED}}> Female</label>
      </div>
      <div class="form-group"><label class="form-label">Display Name</label>
      <input class="input-field" name="display_name" value="{{DISPLAY_NAME}}"></div>
      <div class="form-group"><label class="form-label">Status</label>
      <input class="input-field" name="status" value="{{STATUS}}"></div>
      <div class="save-right"><button type="submit" class="btn-settings-save">Save</button></div>
    </form>
  </div>
</div>

<div class="settings-pane" {{PANE_SECURITY}}>
  <h3 class="settings-sub">Password</h3>
  <div class="settings-card">
    <form method="post" action="/settings/password">
      <div class="form-group"><label class="form-label">Current Password</label>
      <input class="input-field" name="current_password" type="password"></div>
      <div class="form-group"><label class="form-label">New Password</label>
      <input class="input-field" name="new_password" type="password"></div>
      <button type="submit" class="btn-settings-save">Change Password</button>
    </form>
  </div>
  <h3 class="settings-sub">Secure Sign Out</h3>
  <div class="settings-card settings-row-split">
    <p>Sign out of all other sessions</p>
    <form method="post" action="/settings/sessions/logout"><button type="submit" class="btn-settings-save">Sign Out</button></form>
  </div>
</div>

<div class="settings-pane" {{PANE_PRIVACY}}>
  <h3 class="settings-sub">Privacy Setting</h3>
  <div class="settings-card">
    <form method="post" action="/settings/update">
      <input type="hidden" name="tab" value="privacy">
      <p class="acct-row">Who can message me:</p>
      <select class="input-field" name="who_message">{{WHO_MESSAGE_OPTS}}</select>
      <p class="acct-row">Who can Invite me to VIP Servers:</p>
      <select class="input-field" name="who_join">{{WHO_JOIN_OPTS}}</select>
      <p class="acct-row">Who can follow me into the game:</p>
      <select class="input-field" name="who_chat_game">{{WHO_CHAT_GAME_OPTS}}</select>
      <p class="acct-row">Who can see my inventory:</p>
      <select class="input-field" name="who_inventory">{{WHO_INVENTORY_OPTS}}</select>
      <p class="acct-row">Who can trade with me:</p>
      <select class="input-field" name="who_trade">{{WHO_TRADE_OPTS}}</select>
      <div class="save-right"><button type="submit" class="btn-settings-save">Save</button></div>
    </form>
  </div>
</div>

<div class="settings-pane" {{PANE_BILLING}}>
  <h3 class="settings-sub">Billing</h3>
  <div class="settings-card">
    <p class="list-content">Premium is not sold on this private server.</p>
    <p class="list-content">Robux balance: <span class="text-robux"><span class="icon-robux-16x16"></span> R$ {{ROBUX}}</span></p>
    <p class="list-content">No live payments. This page does not take cards.</p>
    <a class="btn-secondary-md" href="/promocodes">Redeem Code</a>
  </div>
</div>
</div>"""

INV_CATS = "".join(
    '<a href="/inventory?category=%s">%s</a>' % (c, n)
    for c, n in [
        ("", "Heads"),
        ("Face", "Faces"),
        ("Gear", "Gears"),
        ("Hat", "Hats"),
        ("Hair", "Hair"),
        ("Shirt", "T-Shirts"),
        ("Shirt", "Shirts"),
        ("Pants", "Pants"),
    ]
)

INVENTORY = """<div class="ecs-inventory">
<h1 class="ecs-page-title">Inventory</h1>
<div class="inventory-layout">
<aside class="inventory-cats ecs-card">
<h2 class="category-title">CATEGORY</h2>
<div class="menu-vertical catalog-cats">
<a href="/inventory">All</a>
%s
</div>
</aside>
<div class="inventory-main">
<div class="section-content ecs-card"><h2>Currently Wearing</h2><ul class="hlist item-cards"></ul></div>
<div class="section-content ecs-card"><h2>Items</h2><ul class="hlist item-cards"></ul>
<p class="list-content">No Search Results Found</p></div>
</div>
</div>
</div>""" % INV_CATS

TRADES = """<div class="ecs-money">
<h1 class="ecs-page-title">Trade</h1>
<div class="vtab-bar">
<a class="vtab active" href="/trades">Trade</a>
<a class="vtab" href="/robux">Summary</a>
</div>
<div class="section-content ecs-card">
<h3>Send a Trade</h3>
<form method="post" action="/trades/send">
<label class="form-label">To</label>
<input class="input-field" name="username" placeholder="Username">
<label class="form-label">Your item IDs (comma separated)</label>
<input class="input-field" name="offer" placeholder="1,2">
<button type="submit" class="btn-primary-md" id="shareButton">Send Trade</button>
</form>
</div>
<div class="section-content ecs-card">
<h3>Open Trades</h3>
<ul class="vlist trade-list"></ul>
</div>
<div class="section-content ecs-card"><h3>Your Inventory</h3><ul class="hlist item-cards"></ul></div>
</div>"""

SEARCH = """<div class="ecs-search">
<h1 class="ecs-page-title">Search</h1>
<form action="/search" method="get" class="games-filter-bar">
<input class="input-field" name="keyword" placeholder="Search" value="{{SEARCH_KEYWORD}}">
<button type="submit" class="btn-primary-md">Search</button>
</form>
<ul class="nav nav-tabs settings-tabs" role="tablist">
<li class="rbx-tab active"><a class="rbx-tab-heading" href="#people-pane" data-tab="people-pane">People</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#experiences-pane" data-tab="experiences-pane">Games</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#catalog-pane" data-tab="catalog-pane">Catalog</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#groups-pane" data-tab="groups-pane">Groups</a></li>
</ul>
<div id="people-pane" class="tab-pane settings-tab-pane active section-content ecs-card">
<ul class="hlist friend-list"></ul>
</div>
<div id="experiences-pane" class="tab-pane settings-tab-pane section-content ecs-card">
<ul class="hlist games game-cards"></ul>
</div>
<div id="catalog-pane" class="tab-pane settings-tab-pane section-content ecs-card">
<ul class="hlist item-cards"></ul>
</div>
<div id="groups-pane" class="tab-pane settings-tab-pane section-content ecs-card">
<ul class="vlist group-list"></ul>
</div>
<p class="list-content">No Search Results Found</p>
</div>"""

PROMO = """<h1>Redeem ROBLOX Promotions</h1>
<div class="section-content ecs-card">
<p class="list-content">Enter a promotional code.</p>
<form method="post" action="/promo/redeem">
<label class="form-label" for="pin">Enter Your Code:</label>
<input class="input-field" id="pin" name="code" type="text">
<button type="submit" class="btn-primary-md">Redeem</button>
</form></div>"""


DOWNLOAD = """<div class="ecs-download">
  <h1 class="dl-title">Download</h1>
  <p class="dl-sub">Download the ROBLOX Player to get into the game.</p>
  <div class="dl-grid">
    <div class="dl-col">
      <a class="dl-card" href="#computer">
        <img class="dl-card-img" src="/static/ecs/dl-player.svg" alt="Download the Computer Player">
        <h4 class="dl-card-name">Download the Computer Player</h4>
      </a>
    </div>
    <div class="dl-col">
      <a class="dl-card" href="#studio">
        <img class="dl-card-img" src="/static/ecs/dl-studio.svg" alt="ROBLOX Studio for Computer">
        <h4 class="dl-card-name">ROBLOX Studio for Computer</h4>
      </a>
    </div>
  </div>
  <div class="dl-help ecs-card" id="computer">
    <h2>Computer Player</h2>
    <p class="list-content">Install the Computer client, then point it at this site. There is no Linux client in the official dumps.</p>
    <ol class="list-content">
      <li>Install the Computer client on your machine</li>
      <li>Point it at this site URL</li>
      <li>Press Play on an experience</li>
    </ol>
  </div>
  <div class="dl-help ecs-card" id="studio">
    <h2>Studio</h2>
    <p class="list-content">Studio uses the same Computer client. Build a place on Develop after the client is pointed at this server.</p>
  </div>
</div>"""

SIMPLE = {
    "about": ("About Us", '<h1>About Us</h1><div class="section-content ecs-card"><p class="list-content">ROBLOX is a place to imagine, create, and play together.</p></div>'),
    "jobs": ("Jobs", '<h1>Jobs</h1><div class="section-content ecs-card"><p class="list-content">No open jobs.</p></div>'),
    "parents": ("Parents", '<h1>Parents</h1><div class="section-content ecs-card"><p class="list-content">This is a private ROBLOX revival. Accounts are local to this server.</p></div>'),
    "help": ("Help", '<h1>Help</h1><div class="section-content ecs-card"><h3>Play</h3><p class="list-content">Open Games, pick an experience, press Play. A launcher popup fires roblox-player.</p><h3>Create</h3><p class="list-content">Create an experience, then it shows on Games and your profile.</p><h3>Catalog</h3><p class="list-content">Catalog starts empty. Create an item, then others can buy it with local Robux.</p><h3>Friends and Messages</h3><p class="list-content">Send a friend request from Friends or a profile. Messages stay on this server.</p></div>'),
    "terms": ("Terms", '<h1>Terms</h1><div class="section-content ecs-card"><p class="list-content">Use this private server at your own risk. Do not use real ROBLOX passwords.</p></div>'),
    "privacy": ("Privacy", '<h1>Privacy</h1><div class="section-content ecs-card"><p class="list-content">Accounts are stored only in this machine\'s data/site.db.</p></div>'),
    "accessibility": ("Accessibility", '<h1>Accessibility</h1><div class="section-content ecs-card"><p class="list-content">This site uses a simple dark layout for readability.</p></div>'),
    "credits": ("Credits", '<h1>Credits</h1><div class="section-content ecs-card"><h2>made by thuggy</h2><p class="list-content">made by thuggy</p></div>'),
    "blog": ("Blog", '<h1>Blog News</h1><div class="section-content ecs-card"><ul class="blog-news"></ul><p class="list-content">No Search Results Found</p></div>'),
    "robux": ("Robux", '<h1>Buy Robux</h1><div class="section-content ecs-card"><p class="list-content">Your balance: <span class="text-robux"><span class="icon-robux-16x16"></span> R$ {{ROBUX}}</span></p><p class="list-content">Robux on this private server is stored in the local database. Purchasing is not connected to roblox.com.</p><div class="robux-products"><div class="section-content"><h3>400 Robux</h3><p class="list-content">Not for sale here.</p></div><div class="section-content"><h3>800 Robux</h3><p class="list-content">Not for sale here.</p></div><div class="section-content"><h3>1700 Robux</h3><p class="list-content">Not for sale here.</p></div></div><a class="btn-secondary-md" href="/promocodes">Redeem Code</a></div>'),
    "premium": ("Premium", '<h1>Builders Club</h1><div class="section-content ecs-card"><p class="list-content">Builders Club / Premium is not sold on this private server.</p><p class="list-content"><span class="icon-bc"></span> Upgrade is local only.</p></div>'),
    "giftcards": ("Gift Cards", '<h1>Gift Cards</h1><div class="section-content ecs-card"><p class="list-content">Gift cards are not sold here.</p></div>'),
    "payment": ("Payment", '<h1>Payment</h1><div class="section-content ecs-card"><p class="list-content">No live payments. This page does not take cards.</p></div>'),
}


def write(name, text):
    (PAGES / name).write_text(text, encoding="utf-8")
    print("wrote", name)


def main():
    signup = page("Sign Up and Log In", SIGNUP)
    for n in ("signup.html", "login.html", "index.html", "landing.html"):
        write(n, signup)

    home = page("Home", HOME)
    write("home.html", home)
    write("home-loggedin.html", home)
    write("landing-loggedin.html", home)

    disc = page("Games", DISCOVER)
    write("discover.html", disc)
    write("discover-loggedin.html", disc)
    write("games.html", disc)
    write("games-loggedin.html", disc)

    write("friends.html", page("Friends", FRIENDS))
    write("friends-loggedin.html", page("Friends", FRIENDS))
    write("catalog.html", page("Catalog", CATALOG))
    write("catalog-loggedin.html", page("Catalog", CATALOG))
    write("catalog-filters.html", page("Catalog", CATALOG))
    write("catalog-filters-loggedin.html", page("Catalog", CATALOG))
    write("profile.html", page("Profile", PROFILE))
    write("profile-loggedin.html", page("Profile", PROFILE))
    write("game.html", page("Game", GAME))
    write("game-loggedin.html", page("Game", GAME))
    write("game-shindo.html", page("Game", GAME))
    write("game-shindo-loggedin.html", page("Game", GAME))
    write("item.html", page("Item", ITEM))
    write("item-loggedin.html", page("Item", ITEM))
    write("create.html", page("Develop", CREATE))
    write("create-loggedin.html", page("Develop", CREATE))
    write("develop.html", page("Develop", CREATE))
    write("develop-loggedin.html", page("Develop", CREATE))
    write("avatar.html", page("Character", AVATAR))
    write("avatar-loggedin.html", page("Character", AVATAR))
    write("messages.html", page("Messages", MESSAGES))
    write("messages-loggedin.html", page("Messages", MESSAGES))
    write("groups.html", page("Groups", GROUPS))
    write("groups-loggedin.html", page("Groups", GROUPS))
    write("settings.html", page("Settings", SETTINGS))
    write("settings-loggedin.html", page("Settings", SETTINGS))
    write("inventory.html", page("Inventory", INVENTORY))
    write("inventory-loggedin.html", page("Inventory", INVENTORY))
    write("trades.html", page("Trade", TRADES))
    write("trades-loggedin.html", page("Trade", TRADES))
    write("search.html", page("Search", SEARCH))
    write("search-loggedin.html", page("Search", SEARCH))
    write("promocodes.html", page("Promocodes", PROMO))
    write("promocodes-loggedin.html", page("Promocodes", PROMO))
    write("redeem.html", page("Redeem", PROMO))
    write("redeem-loggedin.html", page("Redeem", PROMO))
    write("download.html", page("Download", DOWNLOAD))
    write("download-loggedin.html", page("Download", DOWNLOAD))

    for key, (title, inner) in SIMPLE.items():
        html = page(title, inner)
        write(key + ".html", html)
        write(key + "-loggedin.html", html)


if __name__ == "__main__":
    main()
