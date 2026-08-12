"""Official-shaped Roblox web APIs served locally."""
from __future__ import annotations

import json
import time

import database as db


def _json(obj, status=200):
    return status, "application/json; charset=utf-8", json.dumps(obj).encode("utf-8")


def _parts(path: str):
    return [p for p in path.split("/") if p]


def _int(val, default=0):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def _iso(ts):
    return db.iso(ts)


def _display(user):
    if not user:
        return ""
    s = db.get_user_settings(user)
    return s.get("display_name") or user.get("username") or ""


def _user_obj(user):
    if not user:
        return None
    return {
        "id": user["id"],
        "name": user["username"],
        "displayName": _display(user),
        "description": user.get("blurb") or "",
        "created": _iso(user.get("created_at")),
        "isBanned": False,
        "hasVerifiedBadge": False,
        "externalAppDisplayName": None,
    }


PREFIXES = (
    "/v1/",
    "/v2/",
    "/catalog/v1/",
    "/users/v1/",
    "/friends/v1/",
    "/games/v1/",
    "/avatar/v1/",
    "/inventory/v1/",
    "/trades/v1/",
    "/groups/v1/",
    "/privatemessages/v1/",
    "/economy/v1/",
    "/thumbnails/v1/",
    "/presence/v1/",
    "/accountsettings/v1/",
    "/accountinformation/v1/",
    "/auth/v1/",
    "/auth/v2/",
)


def handle(method, path, low, q, user, req):
    if not any(low.startswith(p) or low == p.rstrip("/") for p in PREFIXES):
        if low not in ("/v1/users/authenticated", "/v2/users/authenticated"):
            return None

    parts = _parts(low)
    # drop host-style first segment if present
    if parts and parts[0] in (
        "catalog",
        "users",
        "friends",
        "games",
        "avatar",
        "inventory",
        "trades",
        "groups",
        "privatemessages",
        "economy",
        "thumbnails",
        "presence",
        "accountsettings",
        "accountinformation",
        "auth",
    ):
        parts = parts[1:]
    if parts and parts[0] in ("v1", "v2"):
        parts = parts[1:]
    resource = parts[0] if parts else ""
    ident = parts[1] if len(parts) > 1 else ""
    extra = parts[2] if len(parts) > 2 else ""
    extra2 = parts[3] if len(parts) > 3 else ""

    if resource == "users" and ident == "authenticated":
        if not user:
            return _json({"errors": [{"message": "Unauthorized", "code": 0}]}, 401)
        return _json({"id": user["id"], "name": user["username"], "displayName": _display(user)})

    if resource == "users" and ident.isdigit() and extra == "friends":
        uid = int(ident)
        if extra2 == "count":
            return _json({"count": len(db.list_friends(uid))})
        return _json(
            [
                {
                    **_user_obj(f),
                    "isOnline": False,
                    "isDeleted": False,
                    "friendFrequentScore": 0,
                    "friendFrequentRank": i + 1,
                }
                for i, f in enumerate(db.list_friends(uid))
            ]
        )

    if resource == "users" and ident.isdigit() and extra == "request-friendship" and method == "POST":
        if not user:
            return _json({"errors": [{"message": "Unauthorized"}]}, 401)
        ok, reason = db.request_friend(user["id"], int(ident))
        return _json({"success": ok, "reason": reason}, 200 if ok else 400)

    if resource == "users" and ident.isdigit() and extra == "accept-friend-request" and method == "POST":
        if not user:
            return _json({"errors": [{"message": "Unauthorized"}]}, 401)
        db.accept_friend(user["id"], int(ident))
        return _json({"success": True})

    if resource == "users" and ident.isdigit() and extra == "unfriend" and method == "POST":
        if not user:
            return _json({"errors": [{"message": "Unauthorized"}]}, 401)
        db.remove_friend(user["id"], int(ident))
        return _json({"success": True})

    if resource == "users" and ident.isdigit() and not extra:
        u = db.get_user(int(ident))
        if not u:
            return _json({"errors": [{"message": "NotFound"}]}, 404)
        return _json(_user_obj(u))

    if resource == "user" and ident == "currency":
        return _json({"robux": user.get("robux", 0) if user else 0})

    if resource == "currency":
        return _json({"robux": user.get("robux", 0) if user else 0})

    if resource == "presence" and ident == "users" and method == "POST":
        form = req.parse_form()
        ids = form.get("userIds") or []
        if isinstance(ids, str):
            ids = [x for x in ids.split(",") if x]
        out = []
        for raw in ids:
            uid = _int(raw)
            u = db.get_user(uid)
            if not u:
                continue
            out.append(
                {
                    "userPresenceType": 0,
                    "lastLocation": "Website",
                    "placeId": None,
                    "rootPlaceId": None,
                    "gameId": None,
                    "universeId": None,
                    "userId": uid,
                    "lastOnline": _iso(int(time.time())),
                }
            )
        return _json({"userPresences": out})

    if resource == "avatar" and (not ident or ident == "details"):
        wearing = db.list_wearing(user["id"]) if user else []
        return _json(
            {
                "scales": {"height": 1, "width": 1, "head": 1, "depth": 1, "proportion": 0, "bodyType": 0},
                "playerAvatarType": "R6",
                "bodyColors": {
                    "headColorId": 1001,
                    "torsoColorId": 1001,
                    "rightArmColorId": 1001,
                    "leftArmColorId": 1001,
                    "rightLegColorId": 1001,
                    "leftLegColorId": 1001,
                },
                "assets": [
                    {"id": a["id"], "name": a.get("name") or "", "assetType": {"id": 8, "name": a.get("asset_type") or "Hat"}}
                    for a in wearing
                ],
                "defaultShirtApplied": not wearing,
                "defaultPantsApplied": not wearing,
                "emotes": [],
            }
        )

    if resource == "avatar" and ident == "set-wearing-assets" and method == "POST":
        if not user:
            return _json({"errors": [{"message": "Unauthorized"}]}, 401)
        form = req.parse_form()
        ids = form.get("assetIds") or form.get("ids") or []
        if isinstance(ids, str):
            ids = [x for x in ids.split(",") if x.strip()]
        current = db.list_wearing(user["id"])
        for a in current:
            db.unwear_asset(user["id"], a["id"])
        for raw in ids:
            db.wear_asset(user["id"], _int(raw))
        return _json({"success": True})

    if resource == "search" and ident == "items":
        keyword = q.get("keyword") or q.get("Keyword") or ""
        cat = q.get("category") or q.get("Category") or ""
        assets = db.list_assets_filtered(asset_type=None if str(cat) in ("", "0", "1") else cat, keyword=keyword)
        return _json(
            {
                "keyword": keyword or None,
                "previousPageCursor": None,
                "nextPageCursor": None,
                "data": [{"id": a["id"], "itemType": "Asset"} for a in assets],
            }
        )

    if resource == "catalog" and ident == "items" and extra == "details":
        assets = db.list_assets()
        return _json(
            {
                "data": [
                    {
                        "id": a["id"],
                        "itemType": "Asset",
                        "assetType": a.get("asset_type") or "Hat",
                        "name": a.get("name"),
                        "description": a.get("description") or "",
                        "price": a.get("price") or 0,
                        "creatorTargetId": a.get("creator_id") or 0,
                        "itemStatus": [],
                    }
                    for a in assets
                ]
            }
        )

    if resource == "games" and ident == "multiget-place-details":
        raw = q.get("placeIds") or q.get("placeids") or ""
        ids = [x for x in str(raw).split(",") if x.strip().isdigit()]
        out = []
        for pid in ids:
            place = db.get_place(int(pid))
            if not place:
                continue
            creator = db.get_user(place.get("creator_id") or 0)
            out.append(
                {
                    "placeId": place["id"],
                    "name": place.get("name"),
                    "description": place.get("description") or "",
                    "sourceName": place.get("name"),
                    "sourceDescription": place.get("description") or "",
                    "url": "/games/%s" % place["id"],
                    "builder": (creator or {}).get("username") or "ROBLOX",
                    "builderId": (creator or {}).get("id") or 0,
                    "isPlayable": True,
                    "reasonProhibited": "None",
                    "universeId": place["id"],
                    "universeRootPlaceId": place["id"],
                    "price": 0,
                    "imageToken": "",
                }
            )
        return _json(out)

    if resource == "games" and not ident:
        rows = db.list_places()
        data = []
        for place in rows:
            creator = db.get_user(place.get("creator_id") or 0)
            data.append(
                {
                    "id": place["id"],
                    "rootPlaceId": place["id"],
                    "name": place.get("name"),
                    "description": place.get("description") or "",
                    "creator": {
                        "id": (creator or {}).get("id") or 0,
                        "name": (creator or {}).get("username") or "ROBLOX",
                        "type": "User",
                    },
                    "playing": db.place_playing(place["id"]),
                    "visits": place.get("visits") or 0,
                    "maxPlayers": place.get("max_players") or 10,
                    "created": _iso(place.get("created_at")),
                    "updated": _iso(place.get("created_at")),
                    "genre": place.get("genre") or "All",
                }
            )
        return _json({"data": data})

    if resource == "games" and ident.isdigit() and extra == "favorites" and method == "POST":
        if not user:
            return _json({"errors": [{"message": "Unauthorized"}]}, 401)
        ok, reason = db.toggle_favorite(user["id"], int(ident))
        return _json({"success": ok, "reason": reason})

    if resource == "inventory" and ident == "users" and extra.isdigit():
        uid = int(extra)
        owned = db.list_inventory(uid)
        return _json(
            {
                "previousPageCursor": None,
                "nextPageCursor": None,
                "data": [
                    {
                        "assetId": a["id"],
                        "name": a.get("name"),
                        "assetType": a.get("asset_type") or "Hat",
                        "created": _iso(a.get("created_at")),
                    }
                    for a in owned
                ],
            }
        )

    if resource == "trades":
        if not user:
            return _json({"errors": [{"message": "Unauthorized"}]}, 401)
        if ident == "send" and method == "POST":
            form = req.parse_form()
            named = db.get_user_by_name(form.get("username") or "")
            to_id = _int(form.get("toUserId") or form.get("toId") or (named["id"] if named else 0))
            tid = db.create_trade(user["id"], to_id)
            if not tid:
                return _json({"errors": [{"message": "invalid"}]}, 400)
            return _json({"id": tid})
        status = ident or "inbound"
        rows = db.list_trades(user["id"])
        if status == "inbound":
            rows = [t for t in rows if t["to_id"] == user["id"] and t.get("status") == "open"]
        elif status == "outbound":
            rows = [t for t in rows if t["from_id"] == user["id"] and t.get("status") == "open"]
        elif status == "completed":
            rows = [t for t in rows if t.get("status") == "completed"]
        data = []
        for t in rows:
            other_id = t["to_id"] if t["from_id"] == user["id"] else t["from_id"]
            other = db.get_user(other_id)
            data.append(
                {
                    "id": t["id"],
                    "user": {"id": other_id, "name": (other or {}).get("username") or ""},
                    "created": _iso(t.get("created_at")),
                    "isActive": t.get("status") == "open",
                    "status": t.get("status") or "Open",
                }
            )
        return _json({"previousPageCursor": None, "nextPageCursor": None, "data": data})

    if resource == "groups" and ident == "search":
        keyword = q.get("keyword") or q.get("query") or ""
        rows = db.search_groups(keyword)
        return _json(
            {
                "data": [
                    {
                        "id": g["id"],
                        "name": g.get("name"),
                        "description": g.get("description") or "",
                        "memberCount": g.get("member_count") or 0,
                    }
                    for g in rows
                ]
            }
        )

    if resource == "groups" and ident.isdigit():
        g = db.get_group(int(ident))
        if not g:
            return _json({"errors": [{"message": "NotFound"}]}, 404)
        members = db.group_members(int(ident))
        owner = db.get_user(g.get("creator_id") or 0)
        return _json(
            {
                "id": g["id"],
                "name": g.get("name"),
                "description": g.get("description") or "",
                "owner": {"userId": (owner or {}).get("id") or 0, "username": (owner or {}).get("username") or ""},
                "memberCount": len(members),
                "isBuildersClubOnly": False,
                "publicEntryAllowed": True,
            }
        )

    if resource == "messages":
        if not user:
            return _json({"errors": [{"message": "Unauthorized"}]}, 401)
        tab = (q.get("messageTab") or q.get("tab") or "Inbox").lower()
        rows = db.list_sent(user["id"]) if tab == "sent" else db.list_inbox(user["id"])
        collection = []
        for m in rows:
            collection.append(
                {
                    "id": m["id"],
                    "sender": {"id": m["from_id"], "name": m.get("from_name")},
                    "recipient": {"id": m["to_id"], "name": m.get("to_name")},
                    "subject": m.get("subject") or "",
                    "body": m.get("body") or "",
                    "created": _iso(m.get("created_at")),
                    "updated": _iso(m.get("created_at")),
                    "isRead": bool(m.get("is_read")),
                    "isSystemMessage": False,
                }
            )
        return _json(
            {
                "collection": collection,
                "totalCollectionSize": len(collection),
                "totalPages": 1,
                "pageNumber": 0,
            }
        )

    if resource == "thumbnails" and ident == "assets":
        return _json(
            {
                "data": [
                    {
                        "targetId": a["id"],
                        "state": "Completed",
                        "imageUrl": "/thumbs/asset.ashx?id=%s" % a["id"],
                    }
                    for a in db.list_assets()
                ]
            }
        )

    if resource == "thumbnails" and ident == "users" and extra == "avatar-headshot":
        raw = q.get("userIds") or ""
        ids = [x for x in str(raw).split(",") if x.strip().isdigit()]
        return _json(
            {
                "data": [
                    {
                        "targetId": int(i),
                        "state": "Completed",
                        "imageUrl": "/thumbs/headshot.ashx?userId=%s" % i,
                    }
                    for i in ids
                ]
            }
        )

    if resource in ("accountsettings", "accountinformation"):
        if not user:
            return _json({"errors": [{"message": "Unauthorized"}]}, 401)
        s = db.get_user_settings(user)
        return _json({"id": user["id"], "name": user["username"], "settings": s})

    return None
