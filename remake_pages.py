#!/usr/bin/env python3
"""Write every site page with local dark-theme chrome. No rbxcdn CSS."""
from pathlib import Path

PAGES = Path(__file__).resolve().parent / "pages"
PH = "/static/placeholder.png"
ICO = "https://images.rbxcdn.com/3b43a5c16ec359053fef735551716fc5.ico"

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
<div class="footer">
<ul class="footer-links">
<li class="footer-link"><a class="text-footer-nav" href="about.html">About Us</a></li>
<li class="footer-link"><a class="text-footer-nav" href="jobs.html">Jobs</a></li>
<li class="footer-link"><a class="text-footer-nav" href="blog.html">Blog</a></li>
<li class="footer-link"><a class="text-footer-nav" href="parents.html">Parents</a></li>
<li class="footer-link"><a class="text-footer-nav" href="help.html">Help</a></li>
<li class="footer-link"><a class="text-footer-nav" href="terms.html">Terms</a></li>
<li class="footer-link"><a class="text-footer-nav" href="privacy.html">Privacy</a></li>
<li class="footer-link"><a class="text-footer-nav" href="credits.html">Credits</a></li>
</ul>
<p class="text-footer footer-note">ROBLOX and the ROBLOX logo are trademarks of their respective owners. This is a private revival.</p>
</div></footer>"""

GENDER = """<div class="form-group gender-container"><label class="text-label">Gender</label>
<div class="gender-row">
<button type="button" id="MaleButton" class="gender-button btn-control-md selected"><div class="gender-icon icon-male"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10" cy="14" r="5" fill="none" stroke="#fff" stroke-width="2"/><path d="M14 10L20 4M15 4h5v5" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg></div><span>Male</span></button>
<button type="button" id="FemaleButton" class="gender-button btn-control-md"><div class="gender-icon icon-female"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="9" r="5" fill="none" stroke="#fff" stroke-width="2"/><path d="M12 14v7M9 18h6" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg></div><span>Female</span></button>
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
<body id="rbx-body" class="rbx-body dark-theme">
<div id="wrap" class="wrap no-gutter-ads dark-theme">
<div id="header" class="navbar-fixed-top rbx-header" role="navigation">
  <div class="container-fluid">
    <div class="rbx-navbar-header">
      <div id="header-menu-icon" class="rbx-nav-collapse" role="button" tabindex="0" aria-label="Menu"></div>
      <a class="navbar-brand" href="/"><span class="brand-text">ROBLOX</span></a>
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


SIGNUP = """<div id="react-login-container" class="login-container">
<div class="section-content login-section">
<h2 class="login-header">Sign Up</h2>
<form class="login-form" name="loginForm" method="post" action="/signup">
<input type="hidden" name="gender" id="gender-field" value="Male">
<div class="form-group birthday-container"><label class="text-label">Birthday</label>
<div class="birthday-row">
<div class="rbx-select-group"><select class="input-field rbx-select" id="MondDropdown" name="BirthMonth"><option value="" selected disabled>Month</option>%s</select></div>
<div class="rbx-select-group"><select class="input-field rbx-select" id="DayDropdown" name="BirthDay"><option value="" selected disabled>Day</option>%s</select></div>
<div class="rbx-select-group"><select class="input-field rbx-select" id="YearDropdown" name="BirthYear"><option value="" selected disabled>Year</option>%s</select></div>
</div></div>
<div class="form-group"><input id="login-username" name="username" type="text" class="form-control input-field" placeholder="Username"></div>
<div class="form-group"><input id="login-password" name="password" type="password" class="form-control input-field" placeholder="Password"></div>
%s
<button type="submit" id="login-button" class="btn-full-width login-button btn-growth-md">Sign Up</button>
</form>
</div></div>""" % (
    MONTHS,
    DAYS,
    YEARS,
    GENDER,
)

HOME = """<div class="col-xs-12 home-header">
<a href="/profile-loggedin.html" class="avatar avatar-headshot-lg">
<img alt="avatar" src="/thumbs/headshot.ashx?userId={{PROFILE_ID}}" id="home-avatar-thumb" class="avatar-card-image">
</a>
<div class="home-header-content">
<h1><a href="/profile-loggedin.html">Hello, {{USERNAME}}!</a></h1>
<p class="profile-status text-lead">{{STATUS}}</p>
<form class="status-update-form" method="post" action="/settings/update">
<input class="input-field" name="status" maxlength="140" placeholder="What are you up to?">
<button type="submit" class="btn-secondary-xs">Share</button>
</form>
</div>
</div>
<div class="section home-friends">
<div class="container-header"><h3>Friends (0)</h3><a href="friends.html" class="btn-secondary-xs">See All</a></div>
<div class="section-content"><ul class="hlist friend-list"></ul></div>
</div>
<div class="container-list home-games">
<div class="container-header"><h3>Experiences</h3><a href="discover.html" class="btn-secondary-xs">See All</a></div>
<ul class="hlist games game-cards game-tile-list" id="games-list"></ul>
</div>"""

DISCOVER = """<div class="games-list-container">
<div class="container-header"><h3>Experiences</h3></div>
<ul class="hlist games game-cards game-tile-list" id="games-list"></ul>
<p class="list-content">No Search Results Found</p>
</div>"""

FRIENDS = """<div class="section home-friends">
<div class="container-header"><h3>Friends (0)</h3></div>
<div class="section-content">
<form method="post" action="/friends/add" class="add-friend-form">
<label class="form-label" for="friend-username">Add a Friend</label>
<input class="input-field" id="friend-username" name="username" placeholder="Username">
<button type="submit" class="btn-primary-md">Add Friend</button>
</form>
<ul class="hlist friend-list"></ul>
<p class="list-content">No Search Results Found</p>
</div>
</div>"""

CATALOG = """<div class="container-header"><h1>Catalog</h1></div>
<div id="catalog-results" class="section-content">
<ul class="hlist item-cards"></ul>
<p class="list-content">No Search Results Found</p>
</div>"""

PROFILE = """<div class="section profile-header">
<div class="section-content">
<img class="avatar-card-image" src="/thumbs/headshot.ashx?userId={{PROFILE_ID}}" alt="{{PROFILE_NAME}}">
<h2 class="profile-name">{{PROFILE_NAME}}</h2>
<p class="text-label profile-display">@{{PROFILE_NAME}}</p>
<p class="profile-status text-lead">{{PROFILE_STATUS}}</p>
<div>{{ADD_FRIEND}}</div>
<ul class="profile-stats-container">
<li class="profile-stat"><p class="text-label">Friends</p><p class="text-lead">{{FRIEND_COUNT}}</p></li>
<li class="profile-stat"><p class="text-label">Place Visits</p><p class="text-lead">{{PLACE_VISITS}}</p></li>
<li class="profile-stat"><p class="text-label">Join Date</p><p class="text-lead">{{PROFILE_JOINED}}</p></li>
</ul>
</div></div>
<div class="section">
<div class="container-header"><h3>About</h3></div>
<div class="section-content"><p class="list-content profile-blurb">{{PROFILE_BLURB}}</p></div>
</div>
<div class="section home-friends">
<div class="container-header"><h3>Friends (0)</h3></div>
<div class="section-content"><ul class="hlist friend-list"></ul></div>
</div>
<div class="container-list">
<div class="container-header"><h3>Experiences</h3></div>
<ul class="hlist games game-cards"></ul>
</div>"""

GAME = """<div class="game-main-content">
<div class="game-thumb-container">
<img class="carousel-thumb" src="/thumbs/place.ashx?id={{GAME_ID}}" alt="{{GAME_NAME}}">
</div>
<div class="game-calls-to-action">
<h2 class="game-name" title="{{GAME_NAME}}">{{GAME_NAME}}</h2>
<div class="game-creator"><span class="text-label">By</span> <a class="text-name" href="/profile.html?id={{CREATOR_ID}}">{{CREATOR_NAME}}</a></div>
<div class="game-play-button-container">
<div id="MultiplayerVisitButton" class="VisitButton VisitButtonPlayGLI" placeid="{{GAME_ID}}">
<a class="btn-primary-lg rbx-play-button" href="#" data-placeid="{{GAME_ID}}">Play</a>
</div></div></div></div>
<div class="section game-about-container">
<div class="container-header"><h3>Description</h3></div>
<div class="section-content">
<pre class="game-description linkify">{{GAME_DESC}}</pre>
<ul class="game-stats-container">
<li class="game-stat"><p class="text-label">Playing</p><p class="text-lead">{{PLAYING}}</p></li>
<li class="game-stat"><p class="text-label">Visits</p><p class="text-lead">{{VISITS}}</p></li>
<li class="game-stat"><p class="text-label">Created</p><p class="text-lead">{{CREATED}}</p></li>
<li class="game-stat"><p class="text-label">Max Players</p><p class="text-lead">{{MAX_PLAYERS}}</p></li>
<li class="game-stat"><p class="text-label">Genre</p><p class="text-lead">{{GENRE}}</p></li>
</ul>
</div></div>"""

CREATE = """<h1>Create Experience</h1>
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
</form>""" % (
    TPL_HTML,
    GENRES,
    MAXP,
)

AVATAR = """<div class="container-header"><h1>Avatar</h1></div>
<div class="section-content"><h2>Currently Wearing</h2><ul class="hlist item-cards" id="wearing-list"></ul></div>
<div class="section-content"><h2>Wardrobe</h2><ul class="hlist item-cards" id="wardrobe-list"></ul>
<p class="list-content">No Search Results Found</p></div>"""

MESSAGES = """<div class="container-header"><h3>Inbox</h3></div>
<div class="section-content"><ul class="vlist feeds"></ul></div>
<div class="container-header"><h3>New Message</h3></div>
<div class="section-content">
<form method="post" action="/messages/send">
<label class="form-label">To</label>
<input class="input-field" name="username" placeholder="Username">
<label class="form-label">Subject</label>
<input class="input-field" name="subject" placeholder="Subject">
<label class="form-label">Message</label>
<textarea class="text-box text-area-medium" name="body" rows="4" placeholder="Write a message"></textarea>
<button type="submit" class="btn-primary-md">Send</button>
</form></div>"""

GROUPS = """<div class="container-header"><h1>Groups</h1></div>
<div class="section-content">
<p class="list-content">No Search Results Found</p>
<form method="post" action="/groups/create">
<label class="form-label">Name</label>
<input class="input-field" name="name" placeholder="Group name">
<label class="form-label">Description</label>
<input class="input-field" name="description" placeholder="Description">
<button type="submit" class="btn-primary-md">Create Group</button>
</form></div>"""

SETTINGS = """<h1 class="user-account-header">Settings</h1>
<div id="user-account" class="rbx-tabs-horizontal">
<ul id="horizontal-tabs" class="nav nav-tabs" role="tablist">
<li class="rbx-tab active"><a class="rbx-tab-heading" href="#account-info" data-tab="account-info">Account Info</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#security" data-tab="security">Security</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#privacy" data-tab="privacy">Privacy</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#billing" data-tab="billing">Billing</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#notifications" data-tab="notifications">Notifications</a></li>
<li class="rbx-tab"><a class="rbx-tab-heading" href="#parental-controls" data-tab="parental-controls">Parental Controls</a></li>
</ul>
<div class="tab-content rbx-tab-content">
<div id="account-info" class="tab-pane settings-tab-pane active">
<form id="settingsForm" method="post" action="/settings/update">
<input type="hidden" name="tab" value="account-info">
<div class="section-content">
<h3>Account Info</h3>
<div class="form-group"><label class="form-label" for="username">Username</label>
<input class="text-box text-box-medium" id="username" name="username" type="text" value="{{USERNAME}}"></div>
<div class="form-group"><label class="form-label" for="display_name">Display Name</label>
<input class="text-box text-box-medium" id="display_name" name="display_name" type="text" value="{{DISPLAY_NAME}}"></div>
<div class="form-group"><label class="form-label" for="email">Email</label>
<input class="text-box text-box-medium" id="email" name="email" type="email" value="{{EMAIL}}" placeholder="Saved on this server only">
<p class="list-content">This is not sent to roblox.com.</p></div>
<div class="form-group"><label class="form-label" for="status">Status</label>
<input class="text-box text-box-medium" id="status" name="status" type="text" maxlength="140" value="{{STATUS}}"></div>
<div class="form-group"><label class="form-label" for="blurb">About</label>
<textarea class="text-box text-area-medium" id="blurb" name="blurb" rows="4">{{BLURB}}</textarea></div>
</div>
<div class="section-content">
<h3>Personal</h3>
<div class="form-group"><label class="form-label" for="birthday">Birthday</label>
<input class="text-box text-box-medium" id="birthday" name="birthday" type="text" value="{{BIRTHDAY}}"></div>
<div class="form-group"><label class="form-label" for="gender">Gender</label>
<select class="input-field rbx-select" id="gender" name="gender">{{GENDER_OPTS}}</select></div>
<div class="form-group"><label class="form-label" for="language">Language</label>
<select class="input-field rbx-select" id="language" name="language">{{LANGUAGE_OPTS}}</select></div>
<button type="submit" class="btn-primary-md" id="settingsSave">Save</button>
</div>
</form>
</div>
<div id="security" class="tab-pane settings-tab-pane">
<div class="section-content">
<h3>Password</h3>
<form id="passwordForm" method="post" action="/settings/password">
<div class="form-group"><label class="form-label" for="current_password">Current Password</label>
<input class="text-box text-box-medium" id="current_password" name="current_password" type="password" autocomplete="current-password"></div>
<div class="form-group"><label class="form-label" for="new_password">New Password</label>
<input class="text-box text-box-medium" id="new_password" name="new_password" type="password" autocomplete="new-password"></div>
<button type="submit" class="btn-primary-md">Change Password</button>
</form>
</div>
<form method="post" action="/settings/update">
<input type="hidden" name="tab" value="security">
<div class="section-content">
<h3>2-Step Verification</h3>
<label class="form-label checkbox-row"><input type="checkbox" name="two_step" value="1" {{TWO_STEP_CHECKED}}> Require extra check on this account</label>
<p class="list-content">Stored on this server only. No email or SMS is sent.</p>
</div>
<div class="section-content">
<h3>Where You're Logged In</h3>
<p class="list-content">Active sessions: {{SESSION_COUNT}}</p>
</div>
<button type="submit" class="btn-primary-md">Save</button>
</form>
<form method="post" action="/settings/sessions/logout" class="section-content">
<button type="submit" class="btn-secondary-md">Log Out of All Other Sessions</button>
</form>
</div>
<div id="privacy" class="tab-pane settings-tab-pane">
<form method="post" action="/settings/update">
<input type="hidden" name="tab" value="privacy">
<div class="section-content">
<h3>Communication</h3>
<div class="form-group"><label class="form-label" for="who_message">Who can message me?</label>
<select class="input-field rbx-select" id="who_message" name="who_message">{{WHO_MESSAGE_OPTS}}</select></div>
<div class="form-group"><label class="form-label" for="who_chat_app">Who can chat with me in app?</label>
<select class="input-field rbx-select" id="who_chat_app" name="who_chat_app">{{WHO_CHAT_APP_OPTS}}</select></div>
<div class="form-group"><label class="form-label" for="who_chat_game">Who can chat with me in experiences?</label>
<select class="input-field rbx-select" id="who_chat_game" name="who_chat_game">{{WHO_CHAT_GAME_OPTS}}</select></div>
</div>
<div class="section-content">
<h3>Other Settings</h3>
<div class="form-group"><label class="form-label" for="who_join">Who can join me in experiences?</label>
<select class="input-field rbx-select" id="who_join" name="who_join">{{WHO_JOIN_OPTS}}</select></div>
<div class="form-group"><label class="form-label" for="who_inventory">Who can see my inventory?</label>
<select class="input-field rbx-select" id="who_inventory" name="who_inventory">{{WHO_INVENTORY_OPTS}}</select></div>
<div class="form-group"><label class="form-label" for="who_trade">Who can trade with me?</label>
<select class="input-field rbx-select" id="who_trade" name="who_trade">{{WHO_TRADE_OPTS}}</select></div>
<div class="form-group"><label class="form-label" for="who_friends">Who can see my friends list?</label>
<select class="input-field rbx-select" id="who_friends" name="who_friends">{{WHO_FRIENDS_OPTS}}</select></div>
<button type="submit" class="btn-primary-md">Save</button>
</div>
</form>
</div>
<div id="billing" class="tab-pane settings-tab-pane">
<div class="section-content">
<h3>Subscriptions</h3>
<p class="list-content">Premium is not sold on this private server.</p>
<p class="list-content">Robux balance: <span class="text-robux">R$ {{ROBUX}}</span></p>
<p class="list-content">No live payments. This page does not take cards.</p>
<a class="btn-secondary-md" href="/promocodes-loggedin.html">Redeem Code</a>
<a class="btn-secondary-md" href="/robux-loggedin.html">Robux</a>
</div>
</div>
<div id="notifications" class="tab-pane settings-tab-pane">
<form method="post" action="/settings/update">
<input type="hidden" name="tab" value="notifications">
<div class="section-content">
<h3>Notification Stream</h3>
<label class="form-label checkbox-row"><input type="checkbox" name="notify_messages" value="1" {{NOTIFY_MESSAGES_CHECKED}}> Messages</label>
<label class="form-label checkbox-row"><input type="checkbox" name="notify_friends" value="1" {{NOTIFY_FRIENDS_CHECKED}}> Friend requests</label>
<label class="form-label checkbox-row"><input type="checkbox" name="notify_trades" value="1" {{NOTIFY_TRADES_CHECKED}}> Trades</label>
<label class="form-label checkbox-row"><input type="checkbox" name="notify_updates" value="1" {{NOTIFY_UPDATES_CHECKED}}> Experience updates</label>
<button type="submit" class="btn-primary-md">Save</button>
</div>
</form>
</div>
<div id="parental-controls" class="tab-pane settings-tab-pane">
<form method="post" action="/settings/update">
<input type="hidden" name="tab" value="parental-controls">
<div class="section-content">
<h3>Account Restrictions</h3>
<label class="form-label checkbox-row"><input type="checkbox" name="account_restrictions" value="1" {{RESTRICTIONS_CHECKED}}> Limit to milder experiences</label>
<div class="form-group"><label class="form-label" for="content_maturity">Content maturity</label>
<select class="input-field rbx-select" id="content_maturity" name="content_maturity">{{MATURITY_OPTS}}</select></div>
<div class="form-group"><label class="form-label" for="monthly_spend">Monthly spending limit</label>
<select class="input-field rbx-select" id="monthly_spend" name="monthly_spend">{{SPEND_OPTS}}</select></div>
</div>
<div class="section-content">
<h3>Account PIN</h3>
<p class="list-content">{{PIN_STATUS}}</p>
<div class="form-group"><label class="form-label" for="new_pin">Set or change PIN</label>
<input class="text-box text-box-medium" id="new_pin" name="new_pin" type="password" inputmode="numeric" autocomplete="off"></div>
<label class="form-label checkbox-row"><input type="checkbox" name="clear_pin" value="1"> Turn PIN off</label>
<button type="submit" class="btn-primary-md">Save</button>
</div>
</form>
</div>
</div>
</div>"""

INVENTORY = """<div class="container-header"><h3>Inventory</h3></div>
<div class="section-content"><h2>Currently Wearing</h2><ul class="hlist item-cards"></ul></div>
<div class="section-content"><h2>Items</h2><ul class="hlist item-cards"></ul>
<p class="list-content">No Search Results Found</p></div>"""

TRADES = """<div class="container-header"><h1>Trade</h1></div>
<div class="section-content"><h3>Inventory</h3><ul class="hlist item-cards"></ul>
<h3>Trade</h3><ul class="hlist item-cards"></ul>
<a class="btn-primary-md" id="shareButton">Trade</a></div>"""

SEARCH = """<div class="container-header"><h3>Search</h3></div>
<div class="section-content">
<form action="/search.html" method="get">
<input class="input-field" name="keyword" placeholder="Search">
<button type="submit" class="btn-primary-md">Search</button>
</form>
<p class="list-content">No Search Results Found</p>
</div>"""

PROMO = """<h1>Redeem ROBLOX Promotions</h1>
<div class="section-content">
<p class="list-content">Enter a promotional code.</p>
<form method="post" action="/promo/redeem">
<label class="form-label" for="pin">Enter Your Code:</label>
<input class="input-field" id="pin" name="code" type="text">
<button type="submit" class="btn-primary-md">Redeem</button>
</form></div>"""

SIMPLE = {
    "about": ("About Us", "<h1>About Us</h1><div class=\"section-content\"><p class=\"list-content\">ROBLOX is a place to imagine, create, and play together.</p></div>"),
    "jobs": ("Jobs", "<h1>Jobs</h1><div class=\"section-content\"><p class=\"list-content\">No open jobs.</p></div>"),
    "parents": ("Parents", "<h1>Parents</h1><div class=\"section-content\"><p class=\"list-content\">This is a private ROBLOX revival. Accounts are local to this server.</p></div>"),
    "help": ("Help", "<h1>Help</h1><div class=\"section-content\"><p class=\"list-content\">Sign up, create a place on Create, then open it from Discover.</p></div>"),
    "terms": ("Terms", "<h1>Terms</h1><div class=\"section-content\"><p class=\"list-content\">Use this private server at your own risk. Do not use real ROBLOX passwords.</p></div>"),
    "privacy": ("Privacy", "<h1>Privacy</h1><div class=\"section-content\"><p class=\"list-content\">Accounts are stored only in this machine's data/site.db.</p></div>"),
    "accessibility": ("Accessibility", "<h1>Accessibility</h1><div class=\"section-content\"><p class=\"list-content\">This site uses a simple dark layout for readability.</p></div>"),
    "credits": ("Credits", "<h1>Credits</h1><div class=\"section-content\"><h2>made by thuggy</h2><p class=\"list-content\">made by thuggy</p></div>"),
    "blog": ("Blog", "<h1>Blog News</h1><div class=\"section-content\"><ul class=\"blog-news\"></ul><p class=\"list-content\">No Search Results Found</p></div>"),
    "download": ("Download", "<h1>Download</h1><div class=\"section-content\"><p class=\"list-content\">Install the ROBLOX client for Computer, then point it at this site.</p><p class=\"list-content\">Computer is the desktop client.</p></div>"),
    "robux": ("Robux", "<h1>Buy Robux</h1><div class=\"section-content\"><p class=\"list-content\">Robux on this private server is stored in the local database. Purchasing is not connected to roblox.com.</p></div>"),
    "premium": ("Premium", "<h1>Premium</h1><div class=\"section-content\"><p class=\"list-content\">Premium is not sold on this private server.</p></div>"),
    "giftcards": ("Gift Cards", "<h1>Gift Cards</h1><div class=\"section-content\"><p class=\"list-content\">Gift cards are not sold here.</p></div>"),
    "payment": ("Payment", "<h1>Payment</h1><div class=\"section-content\"><p class=\"list-content\">No live payments. This page does not take cards.</p></div>"),
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

    disc = page("Discover", DISCOVER)
    write("discover.html", disc)
    write("discover-loggedin.html", disc)
    write("games.html", page("Games", DISCOVER))
    write("games-loggedin.html", page("Games", DISCOVER))

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
    write("create.html", page("Create Experience", CREATE))
    write("create-loggedin.html", page("Create Experience", CREATE))
    write("avatar.html", page("Avatar", AVATAR))
    write("avatar-loggedin.html", page("Avatar", AVATAR))
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
