# ROBLOX site + RCC backend

Static pages from the HTML dump, plus a local API so a Roblox client and RCCService can talk to this machine.

## Run the site

    python3 server.py

Open http://127.0.0.1:8080

Landing is the Sign Up form with Log In in the navbar. There is no default account — sign up; that writes a row to `data/site.db`.

Games, friends, catalog, and inventory are empty until users create them. Create an experience on Develop.

config.json:

- port: site listen port (default 8080)
- public_url: URL the client and RCC use to reach this site
- rcc_enabled: true after RCCService is running
- rcc_soap: RCC SOAP URL, usually http://127.0.0.1:64989
- game_port_start: first game listen port RCC should bind

## RCCService (you install this)

RCCService.exe is Roblox's game/render process. This repo does not include it. Put your copy on a Windows machine.

1. Start RCCService so it listens for SOAP (common port 64989).
2. Point rcc_soap at that host (http://WINDOWS_IP:64989).
3. Set public_url to a URL RCC can open (not 127.0.0.1 if RCC is on another PC).
4. Set rcc_enabled to true.
5. Restart python3 server.py.
6. Check http://127.0.0.1:8080/rcc/hello — reachable should be true.

Play hits /game/PlaceLauncher.ashx, which SOAP OpenJobEx to RCC and stores the job id. The client then loads /game/join.ashx?job=...

Lua jobs: scripts/gameserver.lua, scripts/render.lua, scripts/join.lua.

## Client

Point the player at this site (hosts file, bootstrapper, or ClientAppSettings WebsiteUrl / BaseUrl = public_url).

Implemented (2016-era names):

- /Login/Negotiate.ashx
- /Login/RequestAuth.ashx
- /game/join.ashx
- /game/PlaceLauncher.ashx
- /game/GetCurrentUser.ashx
- /game/players/{id}
- /Game/KeepAlivePinger.ashx
- /Game/ClientPresence.ashx
- /Game/LoadPlaceInfo.ashx
- /Game/LuaWebService/HandleSocialRequest.ashx
- /Game/ChatFilter.ashx
- /asset/
- /Thumbs/Asset.ashx
- /v1.1/avatar-fetch
- /Setting/QuietGet/ClientAppSettings/
- /marketplace/productinfo
- /currency/balance
- /my/settings/json
- /universes/get-universe-containing-place
- /signup /login /logout /places/create

Cookie: .ROBLOSECURITY (same name the client expects).

## Headshots and place renders

All thumbs are on-site (not rbxcdn):

- `/thumbs/headshot.ashx?userId=1` or `?hash=...`
- `/thumbs/asset.ashx?id=...` or `?hash=...`
- `/thumbs/place.ashx?id=...`

Files live in `data/renders/headshots/`, `places/`, `assets/`.
If RCC is down or the PNG is missing, the site serves `data/renders/placeholder-headshot.png` or `placeholder-place.png`.
RCC can POST a finished PNG to the same `/thumbs/...` URL to replace the placeholder.

## Site JSON API

All of these read/write `data/site.db` (no snapshot data):

- GET/POST `/api/me`
- GET `/api/users`  GET `/api/users/{id}`  GET `/api/users?q=`
- GET/POST `/api/places`  GET `/api/places/{id}`
- GET/POST `/api/catalog`  POST `/api/catalog/{id}/buy`
- GET/POST `/api/friends`  DELETE `/api/friends/{id}`
- GET/POST `/api/messages`
- GET `/api/inventory`  POST `/api/inventory/{id}/wear`
- GET/POST `/api/groups`  POST `/api/groups/{id}/join`
- GET `/api/search?q=`
- GET/POST `/api/trades`
- POST `/api/promo`  POST `/api/status`

Forms: `/signup` `/login` `/logout` `/places/create` `/friends/add` `/messages/send` `/groups/create` `/settings/update` `/promo/redeem` `/catalog/buy` `/play`

## Pages

HTML is in pages/. Logged-in twins end with -loggedin.html.
Lists (games, friends, catalog, inventory, messages, groups, blog) start empty and fill from the database.
Navbar is injected from partials/nav_out.html and partials/nav_in.html.

SQLite file: data/site.db.
