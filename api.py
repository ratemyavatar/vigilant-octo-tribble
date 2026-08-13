"""JSON API for the site. Returns None if the path is not an API route."""
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


def handle(method, path, low, q, user, req):
    if not (low.startswith("/api/") or low == "/api"):
        return None

    parts = _parts(low)
    # parts[0] == 'api'
    resource = parts[1] if len(parts) > 1 else ""
    ident = parts[2] if len(parts) > 2 else ""
    extra = parts[3] if len(parts) > 3 else ""

    if resource == "me":
        if not user:
            return _json({"guest": True})
        if method == "POST":
            form = req.parse_form()
            updated = db.update_user(
                user["id"],
                status=form.get("status"),
                blurb=form.get("blurb"),
                username=form.get("username"),
            )
            if not updated:
                return _json({"error": "username taken"}, 400)
            user = updated
        return _json(
            {
                "id": user["id"],
                "username": user["username"],
                "robux": user.get("robux") or 0,
                "status": user.get("status") or "",
                "blurb": user.get("blurb") or "",
                "created_at": user.get("created_at") or 0,
            }
        )

    if resource == "users":
        if ident == "search" or q.get("q") or q.get("keyword"):
            qstr = ident if ident not in ("", "search") else (q.get("q") or q.get("keyword") or "")
            if ident == "search":
                qstr = q.get("q") or q.get("keyword") or ""
            rows = db.search_users(qstr) if qstr else db.list_users()
            return _json([db.public_user(u) for u in rows])
        if ident.isdigit():
            u = db.get_user(int(ident))
            if not u:
                return _json({"error": "NotFound"}, 404)
            out = db.public_user(u)
            out["friends"] = [db.public_user(f) for f in db.list_friends(u["id"])]
            out["places"] = db.places_by_creator(u["id"])
            return _json(out)
        return _json([db.public_user(u) for u in db.list_users()])

    if resource == "places":
        if method == "POST":
            if not user:
                return _json({"error": "login"}, 401)
            form = req.parse_form()
            pid = db.create_place(
                user["id"],
                form.get("name") or form.get("Name") or "Untitled",
                form.get("description") or form.get("Description") or "",
                form.get("genre") or form.get("Genre") or "All",
                form.get("template_id") or form.get("TemplateID") or "",
                form.get("max_players") or form.get("NumberOfPlayersMax") or 10,
            )
            return _json({"id": pid})
        if ident.isdigit():
            place = db.get_place(int(ident))
            if not place:
                return _json({"error": "NotFound"}, 404)
            creator = db.get_user(place.get("creator_id") or 0)
            place["creator"] = db.public_user(creator) if creator else None
            return _json(place)
        return _json(db.list_places())

    if resource == "catalog":
        if method == "POST":
            if not user:
                return _json({"error": "login"}, 401)
            form = req.parse_form()
            aid = db.create_asset(
                user["id"],
                form.get("name") or "Item",
                form.get("asset_type") or "Hat",
                form.get("description") or "",
                "",
                "",
                form.get("price") or 0,
            )
            return _json({"id": aid})
        if ident.isdigit() and extra == "buy" and method == "POST":
            if not user:
                return _json({"error": "login"}, 401)
            ok, reason = db.buy_asset(user["id"], int(ident))
            return _json({"ok": ok, "reason": reason}, 200 if ok else 400)
        if ident.isdigit():
            asset = db.get_asset(int(ident))
            if not asset:
                return _json({"error": "NotFound"}, 404)
            return _json(asset)
        return _json(db.list_assets())

    if resource == "friends":
        if not user:
            return _json({"error": "login"}, 401)
        if method == "POST":
            form = req.parse_form()
            other = form.get("userId") or form.get("id") or ""
            if not str(other).isdigit():
                named = db.get_user_by_name(form.get("username") or "")
                other = named["id"] if named else 0
            ok = db.add_friend(user["id"], other)
            return _json({"ok": bool(ok)})
        if ident.isdigit() and method == "DELETE":
            db.remove_friend(user["id"], int(ident))
            return _json({"ok": True})
        return _json([db.public_user(u) for u in db.list_friends(user["id"])])

    if resource == "messages":
        if not user:
            return _json({"error": "login"}, 401)
        if method == "POST":
            form = req.parse_form()
            to_id = form.get("toId") or form.get("to") or ""
            if not str(to_id).isdigit():
                named = db.get_user_by_name(form.get("username") or form.get("to") or "")
                to_id = named["id"] if named else 0
            mid = db.send_message(user["id"], to_id, form.get("body") or "", form.get("subject") or "")
            if not mid:
                return _json({"error": "invalid"}, 400)
            return _json({"id": mid})
        return _json(db.list_messages(user["id"]))

    if resource == "inventory":
        if not user:
            return _json({"error": "login"}, 401)
        if ident.isdigit() and extra == "wear" and method == "POST":
            ok = db.wear_asset(user["id"], int(ident))
            return _json({"ok": ok}, 200 if ok else 400)
        if ident.isdigit() and extra == "unwear" and method == "POST":
            db.unwear_asset(user["id"], int(ident))
            return _json({"ok": True})
        return _json(
            {
                "inventory": db.list_inventory(user["id"]),
                "wearing": db.list_wearing(user["id"]),
            }
        )

    if resource == "groups":
        if method == "POST" and not ident:
            if not user:
                return _json({"error": "login"}, 401)
            form = req.parse_form()
            gid = db.create_group(user["id"], form.get("name") or "", form.get("description") or "")
            if not gid:
                return _json({"error": "invalid"}, 400)
            return _json({"id": gid})
        if ident.isdigit() and extra == "join" and method == "POST":
            if not user:
                return _json({"error": "login"}, 401)
            ok = db.join_group(int(ident), user["id"])
            return _json({"ok": ok})
        if ident.isdigit():
            g = db.get_group(int(ident))
            if not g:
                return _json({"error": "NotFound"}, 404)
            g["members"] = [
                {"id": m["id"], "username": m["username"], "role": m.get("role")}
                for m in db.group_members(int(ident))
            ]
            return _json(g)
        return _json(db.list_groups())

    if resource == "search":
        keyword = q.get("q") or q.get("keyword") or q.get("search") or ""
        return _json(
            {
                "users": [db.public_user(u) for u in (db.search_users(keyword) if keyword else [])],
                "places": db.search_places(keyword) if keyword else [],
                "assets": [a for a in db.list_assets() if keyword.lower() in (a.get("name") or "").lower()]
                if keyword
                else [],
            }
        )

    if resource == "trades":
        if not user:
            return _json({"error": "login"}, 401)
        if method == "POST":
            form = req.parse_form()
            to_id = form.get("toId") or form.get("to") or ""
            if not str(to_id).isdigit():
                named = db.get_user_by_name(form.get("username") or "")
                to_id = named["id"] if named else 0
            tid = db.create_trade(user["id"], to_id)
            if not tid:
                return _json({"error": "invalid"}, 400)
            return _json({"id": tid})
        return _json(db.list_trades(user["id"]))

    if resource == "promo" and method == "POST":
        if not user:
            return _json({"error": "login"}, 401)
        form = req.parse_form()
        ok, reward = db.redeem_promo(user["id"], form.get("code") or q.get("code") or "")
        return _json({"ok": ok, "reward": reward}, 200 if ok else 400)

    if resource == "status" and method == "POST":
        if not user:
            return _json({"error": "login"}, 401)
        form = req.parse_form()
        db.update_user(user["id"], status=form.get("status") or form.get("txtStatusMessage") or "")
        return _json({"ok": True})

    return _json({"error": "NotFound"}, 404)
