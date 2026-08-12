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
<a class="text-footer-nav" href="about.html">About Us</a>
<a class="text-footer-nav" href="jobs.html">Jobs</a>
<a class="text-footer-nav" href="blog.html">Blog</a>
<a class="text-footer-nav" href="privacy.html">Privacy</a>
<a class="text-footer-nav" href="help.html">Help</a>
<a class="text-footer-nav" href="terms.html">Terms</a>
<a class="text-footer-nav" href="credits.html">Credits</a>
</div>
<p class="text-footer footer-note">ROBLOX, "Online Building Toy", characters, logos, names, and all related indicia are trademarks of their respective owners. This is a private revival. Use of this site signifies your acceptance of the <a href="terms.html">Terms and Conditions</a>.</p>
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
<a href="/profile-loggedin.html" class="avatar avatar-headshot-lg ecs-hello-shot">
<img alt="avatar" src="/thumbs/headshot.ashx?userId={{PROFILE_ID}}" id="home-avatar-thumb" class="avatar-card-image">
</a>
<div class="home-header-content">
<h1 class="hello-message"><a href="/profile-loggedin.html">Hello, {{USERNAME}}!</a></h1>
<p class="profile-status text-lead">{{STATUS}}</p>
<form class="status-update-form" method="post" action="/settings/update">
<input class="input-field" name="status" maxlength="140" placeholder="What are you up to?">
<button type="submit" class="btn-secondary-xs">Share</button>
</form>
</div>
</div>
<div class="section home-friends ecs-card">
<div class="container-header"><h3 class="ecs-row-title">Friends (0)</h3><a href="friends.html" class="btn-secondary-xs">See All</a></div>
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
<div class="container-header"><h3 class="ecs-row-title">Recommended</h3><a href="games.html" class="btn-secondary-xs">See All</a></div>
<ul class="hlist games game-cards game-tile-list" id="games-list"></ul>
</div>
<div class="container-list home-creations">
<div class="container-header"><h3 class="ecs-row-title">My Creations</h3><a href="create.html" class="btn-secondary-xs">Create</a></div>
<ul class="hlist games game-cards" id="my-places-list"></ul>
</div>
</div>"""

DISCOVER = """<div class="games-list-container ecs-games">
<div class="ecs-games-bar">
<form class="games-filter-bar" method="get" action="/games.html">
<input class="input-field" name="keyword" placeholder="Search games" value="{{SEARCH_KEYWORD}}">
<select class="input-field rbx-select" name="genre">{{GENRE_OPTS}}</select>
<select class="input-field rbx-select" name="sort">{{SORT_OPTS}}</select>
<button type="submit" class="btn-primary-md">Search</button>
</form>
</div>
<div class="container-list">
<div class="container-header"><h3 class="ecs-row-title">Popular</h3></div>
<ul class="hlist games game-cards game-tile-list" id="games-list"></ul>
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
    '<li class="menu-option"><a href="/catalog.html?category=%s">%s</a></li>'
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
<form class="games-filter-bar catalog-search" method="get" action="/catalog.html">
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
<form method="get" action="/catalog.html" class="sort-by-form">
<span class="sort-by-label">Sort By:</span>
<select class="input-field rbx-select" name="sort">{{CATALOG_SORT_OPTS}}</select>
</form>
</div>
<div id="catalog-results" class="section-content ecs-catalog-grid">
<ul class="hlist item-cards"></ul>
<p class="list-content">No Search Results Found</p>
</div>
<div class="section-content ecs-card">
<h3>Create Item</h3>
<p class="list-content">Upload an item to this server. Catalog starts empty until someone creates one.</p>
<form method="post" action="/catalog/upload">
<label class="form-label">Name</label>
<input class="input-field" name="name" placeholder="Item name">
<label class="form-label">Type</label>
<select class="input-field" name="asset_type">
<option>Hat</option><option>Hair</option><option>Face</option><option>Shirt</option><option>Pants</option><option>Gear</option><option>Accessory</option>
</select>
<label class="form-label">Price (Robux)</label>
<input class="input-field" name="price" type="number" min="0" value="0">
<label class="form-label">Description</label>
<input class="input-field" name="description" placeholder="Description">
<button type="submit" class="btn-primary-md">Create</button>
</form>
</div>
</div>
</div>
</div>""" % CAT_NAV

PROFILE = """<div class="ecs-profile">
<div class="section profile-header ecs-card">
<div class="section-content profile-header-inner">
<div class="profile-shot">
<img class="avatar-card-image" src="/thumbs/headshot.ashx?userId={{PROFILE_ID}}" alt="{{PROFILE_NAME}}">
</div>
<div class="profile-header-main">
<h2 class="profile-name">{{PROFILE_NAME}}</h2>
<p class="profile-status text-lead">{{PROFILE_STATUS}}</p>
<div>{{ADD_FRIEND}}</div>
<ul class="profile-stats-container">
<li class="profile-stat"><p class="text-label">Friends</p><p class="text-lead">{{FRIEND_COUNT}}</p></li>
<li class="profile-stat"><p class="text-label">Place Visits</p><p class="text-lead">{{PLACE_VISITS}}</p></li>
<li class="profile-stat"><p class="text-label">Join Date</p><p class="text-lead">{{PROFILE_JOINED}}</p></li>
</ul>
</div>
</div></div>
<ul class="nav nav-tabs settings-tabs" role="tablist">
<li class="rbx-tab active"><a class="rbx-tab-heading" href="#about-pane" data-tab="about-pane">About</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#creations-pane" data-tab="creations-pane">Creations</a></li>
</ul>
<div id="about-pane" class="tab-pane settings-tab-pane active">
<div class="section ecs-card">
<div class="container-header"><h3>About</h3></div>
<div class="section-content"><p class="list-content profile-blurb">{{PROFILE_BLURB}}</p></div>
</div>
<div class="section ecs-card">
<div class="container-header"><h3>Currently Wearing</h3></div>
<div class="section-content"><ul class="hlist item-cards" id="profile-wearing"></ul></div>
</div>
<div class="section home-friends ecs-card">
<div class="container-header"><h3>Friends (0)</h3></div>
<div class="section-content"><ul class="hlist friend-list"></ul></div>
</div>
<div class="section ecs-card">
<div class="container-header"><h3>Groups</h3></div>
<div class="section-content"><ul class="vlist group-list"></ul></div>
</div>
<div class="container-list">
<div class="container-header"><h3 class="ecs-row-title">Favorites</h3></div>
<ul class="hlist games game-cards" id="profile-favorites"></ul>
</div>
</div>
<div id="creations-pane" class="tab-pane settings-tab-pane">
<div class="container-list">
<div class="container-header"><h3 class="ecs-row-title">Creations</h3></div>
<ul class="hlist games game-cards"></ul>
</div>
</div>
</div>"""

GAME = """<div class="ecs-game">
<h1 class="game-name" title="{{GAME_NAME}}">{{GAME_NAME}}</h1>
<div class="game-main-content ecs-game-grid">
<div class="game-left">
<div class="game-thumb-container">
<img class="carousel-thumb" src="/thumbs/place.ashx?id={{GAME_ID}}" alt="{{GAME_NAME}}">
</div>
<div class="ecs-vote">
<span class="icon-thumbs-up"></span>
<span class="vote-bar"><span class="vote-fill"></span></span>
<span class="icon-thumbs-down"></span>
</div>
<div class="section game-about-container">
<div class="container-header"><h3>Description</h3></div>
<div class="section-content">
<pre class="game-description linkify">{{GAME_DESC}}</pre>
</div></div>
</div>
<div class="game-right">
<div class="game-creator ecs-card"><span class="text-label">By</span> <a class="text-name" href="/profile.html?id={{CREATOR_ID}}">{{CREATOR_NAME}}</a></div>
<div class="game-play-button-container">
<div id="MultiplayerVisitButton" class="VisitButton VisitButtonPlayGLI" placeid="{{GAME_ID}}">
<a class="btn-primary-lg rbx-play-button btn-play-green" href="#" data-placeid="{{GAME_ID}}">Play</a>
</div>
{{FAVORITE_FORM}}
</div>
<ul class="game-stats-container">
<li class="game-stat"><p class="text-label">Playing</p><p class="text-lead">{{PLAYING}}</p></li>
<li class="game-stat"><p class="text-label">Visits</p><p class="text-lead">{{VISITS}}</p></li>
<li class="game-stat"><p class="text-label">Created</p><p class="text-lead">{{CREATED}}</p></li>
<li class="game-stat"><p class="text-label">Max Players</p><p class="text-lead">{{MAX_PLAYERS}}</p></li>
<li class="game-stat"><p class="text-label">Genre</p><p class="text-lead">{{GENRE}}</p></li>
<li class="game-stat"><p class="text-label">Favorites</p><p class="text-lead">{{FAVORITE_COUNT}}</p></li>
</ul>
</div>
</div>
<div class="section ecs-card">
<div class="container-header"><h3>Servers</h3></div>
<div class="section-content"><ul class="vlist server-list"></ul>
<p class="list-content">No running servers. Play starts one.</p></div>
</div>
<div class="container-list">
<div class="container-header"><h3 class="ecs-row-title">Recommended</h3></div>
<ul class="hlist games game-cards" id="recommended-list"></ul>
</div>
</div>"""

CREATE = """<div class="ecs-develop">
<div class="vtab-bar">
<a class="vtab active" href="/create-loggedin.html">My Creations</a>
<a class="vtab" href="/create-loggedin.html">Group Creations</a>
</div>
<div class="develop-body">
<aside class="develop-left">
<p class="browse-by">Creations</p>
<ul class="menu-vertical">
<li class="menu-option"><a href="/create.html">Games</a></li>
<li class="menu-option"><a href="/create.html">Places</a></li>
<li class="menu-option"><a href="/catalog.html">Shirts</a></li>
<li class="menu-option"><a href="/catalog.html">T-Shirts</a></li>
<li class="menu-option"><a href="/catalog.html">Pants</a></li>
<li class="menu-option"><a href="/catalog.html">Decals</a></li>
<li class="menu-option"><a href="/catalog.html">Models</a></li>
</ul>
</aside>
<div class="develop-right">
<h1>Create</h1>
<div class="section">
<div class="container-header"><h3 class="ecs-row-title">My Games</h3></div>
<ul class="hlist games game-cards" id="my-places-list"></ul>
</div>
<form id="placeForm" method="POST" action="/places/create">
<input id="TemplateID" name="TemplateID" type="hidden" value="95206881">
<h2 id="StudioGameTemplates">GAME TEMPLATES</h2>
<div class="templates">%s</div>
<label class="form-label" for="Name">Name:</label>
<input class="text-box text-box-medium" id="Name" name="Name" type="text" value="">
<label class="form-label" for="Description">Description:</label>
<textarea class="text-box text-area-medium" id="Description" name="Description" rows="4"></textarea>
<label class="form-label" for="Genre">Genre:</label>
<select class="form-select" id="Genre" name="Genre">%s</select>
<label class="form-label" for="MaxPlayersInput">Maximum Visitor Count:</label>
<select class="form-select" id="MaxPlayersInput" name="NumberOfPlayersMax">%s</select>
<div id="buttonRow">
<a class="btn-medium btn-primary" id="finishButton">Create Experience</a>
</div>
</form>
</div>
</div>
</div>""" % (
    TPL_HTML,
    GENRES,
    MAXP,
)

AVATAR = """<div class="character-customizer">
<h1 class="cc-title">Character</h1>
<div class="cc-row">
<div class="cc-left">
  <h2 class="cc-h2">Avatar</h2>
  <div class="cc-thumb">
    <img class="cc-avatar-img" src="/thumbs/avatar.ashx?userId={{PROFILE_ID}}" alt="Avatar">
  </div>
  <p class="mb-0">Something wrong with your Avatar?</p>
  <p class="mb-0"><a href="/avatar-loggedin.html">Click here to re-draw it!</a></p>
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
    <a class="vtab {{TAB_WARDROBE}}" href="/avatar-loggedin.html?tab=wardrobe">Wardrobe</a>
    <a class="vtab {{TAB_OUTFITS}}" href="/avatar-loggedin.html?tab=outfits">Outfits</a>
  </div>
  <div class="wardrobe-panel" {{WARDROBE_HIDDEN}}>
    <p class="cc-cats">{{AVATAR_SUBCATS}}</p>
    <p class="cc-cats"><a href="/catalog-loggedin.html">Shop</a> | <a href="/catalog-loggedin.html">Create</a></p>
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

GROUPS = """<div class="ecs-groups">
<h1 class="ecs-page-title">Groups</h1>
<div class="groups-layout">
<aside class="groups-side ecs-card">
<h3>My Groups</h3>
<ul class="vlist my-group-list"></ul>
<form method="post" action="/groups/create" class="create-group-form">
<label class="form-label">Create Group</label>
<input class="input-field" name="name" placeholder="Group name">
<input class="input-field" name="description" placeholder="Description">
<button type="submit" class="btn-primary-md">Create</button>
</form>
</aside>
<div class="groups-main">
<div class="section ecs-card">
<div class="container-header"><h3>Find Groups</h3></div>
<div class="section-content">
<form method="get" action="/groups.html" class="games-filter-bar">
<input class="input-field" name="keyword" placeholder="Search groups" value="{{SEARCH_KEYWORD}}">
<button type="submit" class="btn-primary-md">Search</button>
</form>
<ul class="vlist group-list"></ul>
<p class="list-content">No Search Results Found</p>
</div>
</div>
<div class="section group-detail ecs-card">
<div class="container-header"><h3>{{GROUP_NAME}}</h3></div>
<div class="section-content">
<p class="list-content">{{GROUP_DESC}}</p>
<p class="text-label">Owner {{GROUP_OWNER}} · Members {{GROUP_MEMBERS}}</p>
{{GROUP_JOIN}}
<ul class="hlist friend-list group-member-list"></ul>
</div>
</div>
</div>
</div>
</div>"""

SETTINGS = """<div class="my-settings">
<h1 class="user-account-header">My Settings</h1>
<ul class="settings-tabs">
<li class="{{TAB_ACCOUNT}}"><a href="/settings-loggedin.html?tab=account">Account Info</a></li>
<li class="{{TAB_SECURITY}}"><a href="/settings-loggedin.html?tab=security">Security</a></li>
<li class="{{TAB_PRIVACY}}"><a href="/settings-loggedin.html?tab=privacy">Privacy</a></li>
<li class="{{TAB_BILLING}}"><a href="/settings-loggedin.html?tab=billing">Billing</a></li>
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
    <a class="btn-secondary-md" href="/promocodes-loggedin.html">Redeem Code</a>
  </div>
</div>
</div>"""

INV_CATS = "".join(
    '<a href="/inventory.html?category=%s">%s</a>' % (c, n)
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
<a href="/inventory.html">All</a>
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
<a class="vtab active" href="/trades-loggedin.html">Trade</a>
<a class="vtab" href="/robux-loggedin.html">Summary</a>
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
<form action="/search.html" method="get" class="games-filter-bar">
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
    "download": ("Download", '<h1>Download ROBLOX</h1><div class="section-content ecs-card"><p class="list-content">Install the ROBLOX client for Computer, then point it at this site.</p><p class="list-content">Computer is the desktop client. There is no Linux client in the official dumps.</p><p class="list-content">Play on a game page opens a launcher popup that fires the roblox-player URI.</p><ol class="list-content"><li>Install the Computer client</li><li>Point it at this site URL</li><li>Press Play on an experience</li></ol></div>'),
    "robux": ("Robux", '<h1>Buy Robux</h1><div class="section-content ecs-card"><p class="list-content">Your balance: <span class="text-robux"><span class="icon-robux-16x16"></span> R$ {{ROBUX}}</span></p><p class="list-content">Robux on this private server is stored in the local database. Purchasing is not connected to roblox.com.</p><div class="robux-products"><div class="section-content"><h3>400 Robux</h3><p class="list-content">Not for sale here.</p></div><div class="section-content"><h3>800 Robux</h3><p class="list-content">Not for sale here.</p></div><div class="section-content"><h3>1700 Robux</h3><p class="list-content">Not for sale here.</p></div></div><a class="btn-secondary-md" href="/promocodes-loggedin.html">Redeem Code</a></div>'),
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
    write("create.html", page("Develop", CREATE))
    write("create-loggedin.html", page("Develop", CREATE))
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

    for key, (title, inner) in SIMPLE.items():
        html = page(title, inner)
        write(key + ".html", html)
        write(key + "-loggedin.html", html)


if __name__ == "__main__":
    main()
