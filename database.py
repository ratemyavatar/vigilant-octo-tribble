import hashlib
import json
import os
import secrets
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "site.db"


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init():
    con = connect()
    cur = con.cursor()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            birthday TEXT DEFAULT '',
            gender TEXT DEFAULT '',
            robux INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS places (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            genre TEXT DEFAULT 'All',
            template_id TEXT DEFAULT '',
            max_players INTEGER DEFAULT 10,
            file_path TEXT DEFAULT '',
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            place_id INTEGER NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            status INTEGER DEFAULT 0,
            opened_at INTEGER NOT NULL,
            FOREIGN KEY(place_id) REFERENCES places(id)
        );
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            asset_type TEXT DEFAULT 'Hat',
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            file_path TEXT DEFAULT '',
            thumbnail_path TEXT DEFAULT '',
            price INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            asset_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS friendships (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            friend_id INTEGER NOT NULL,
            status TEXT DEFAULT 'accepted'
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            body TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_id INTEGER NOT NULL,
            to_id INTEGER NOT NULL,
            status TEXT DEFAULT 'open',
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            reward TEXT DEFAULT '',
            redeemed_by INTEGER
        );
        """
    )
    con.commit()
    # Older builds seeded a fake Player / player account. Accounts now come
    # from signup only — drop that leftover row if it is still around.
    seeded = cur.execute(
        "SELECT id FROM users WHERE username=? AND birthday=? AND gender=?",
        ("Player", "1/1/2000", "Male"),
    ).fetchone()
    if seeded:
        uid = seeded["id"]
        cur.execute("DELETE FROM sessions WHERE user_id=?", (uid,))
        cur.execute("DELETE FROM inventory WHERE user_id=?", (uid,))
        cur.execute("DELETE FROM friendships WHERE user_id=? OR friend_id=?", (uid, uid))
        cur.execute("DELETE FROM messages WHERE from_id=? OR to_id=?", (uid, uid))
        cur.execute("DELETE FROM trades WHERE from_id=? OR to_id=?", (uid, uid))
        cur.execute("DELETE FROM users WHERE id=?", (uid,))
        cur.execute("UPDATE places SET creator_id=0 WHERE creator_id=?", (uid,))
        cur.execute("UPDATE assets SET creator_id=0 WHERE creator_id=?", (uid,))
        con.commit()
    if not cur.execute("SELECT id FROM places").fetchone():
        cur.execute(
            "INSERT INTO places (creator_id, name, description, genre, max_players, created_at) VALUES (0, ?, ?, ?, 10, ?)",
            ("Baseplate", "A starting place.", "All", int(time.time())),
        )
        con.commit()
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            creator_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role TEXT DEFAULT 'Member',
            UNIQUE(group_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS wearing (
            user_id INTEGER NOT NULL,
            asset_id INTEGER NOT NULL,
            PRIMARY KEY(user_id, asset_id)
        );
        CREATE TABLE IF NOT EXISTS trade_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            asset_id INTEGER NOT NULL
        );
        """
    )
    def _col(table, col, decl):
        names = [r[1] for r in cur.execute("PRAGMA table_info(%s)" % table)]
        if col not in names:
            cur.execute("ALTER TABLE %s ADD COLUMN %s" % (table, decl))
    _col("users", "status", "status TEXT DEFAULT ''")
    _col("users", "blurb", "blurb TEXT DEFAULT ''")
    _col("users", "settings", "settings TEXT DEFAULT '{}'")
    _col("users", "pin_hash", "pin_hash TEXT DEFAULT ''")
    _col("places", "visits", "visits INTEGER DEFAULT 0")
    _col("messages", "subject", "subject TEXT DEFAULT ''")
    _col("messages", "is_read", "is_read INTEGER DEFAULT 0")
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS favorites (
            user_id INTEGER NOT NULL,
            place_id INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            PRIMARY KEY(user_id, place_id)
        );
        CREATE TABLE IF NOT EXISTS recently_played (
            user_id INTEGER NOT NULL,
            place_id INTEGER NOT NULL,
            played_at INTEGER NOT NULL,
            PRIMARY KEY(user_id, place_id)
        );
        CREATE TABLE IF NOT EXISTS outfits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            colors TEXT DEFAULT '{}',
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS outfit_items (
            outfit_id INTEGER NOT NULL,
            asset_id INTEGER NOT NULL
        );
        """
    )
    con.commit()
    con.close()


def _hash(password: str, salt: str = None):
    salt = salt or secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return salt + "$" + dk.hex()


def _check(password: str, stored: str):
    try:
        salt, hx = stored.split("$", 1)
    except ValueError:
        return False
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120000)
    return dk.hex() == hx


def create_user(username, password, birthday="", gender=""):
    username = (username or "").strip()
    password = password or ""
    if not username or not password:
        return None
    con = connect()
    try:
        con.execute(
            "INSERT INTO users (username, password_hash, birthday, gender, created_at) VALUES (?,?,?,?,?)",
            (username, _hash(password), birthday, gender, int(time.time())),
        )
        con.commit()
        row = con.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        return None
    finally:
        con.close()


def verify_user(username, password):
    con = connect()
    row = con.execute("SELECT * FROM users WHERE username=?", (username.strip(),)).fetchone()
    con.close()
    if not row or not _check(password, row["password_hash"]):
        return None
    return dict(row)


def get_user(user_id):
    con = connect()
    row = con.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def get_user_by_name(username):
    con = connect()
    row = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    con.close()
    return dict(row) if row else None


def create_session(user_id):
    sid = secrets.token_hex(32)
    now = int(time.time())
    con = connect()
    con.execute(
        "INSERT INTO sessions (id, user_id, created_at, expires_at) VALUES (?,?,?,?)",
        (sid, user_id, now, now + 60 * 60 * 24 * 14),
    )
    con.commit()
    con.close()
    return sid


def session_user(sid):
    if not sid:
        return None
    con = connect()
    row = con.execute(
        "SELECT u.* FROM users u JOIN sessions s ON s.user_id=u.id WHERE s.id=? AND s.expires_at>?",
        (sid, int(time.time())),
    ).fetchone()
    con.close()
    return dict(row) if row else None


def delete_session(sid):
    con = connect()
    con.execute("DELETE FROM sessions WHERE id=?", (sid,))
    con.commit()
    con.close()


def list_places():
    con = connect()
    rows = con.execute("SELECT * FROM places ORDER BY id DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_place(pid):
    con = connect()
    row = con.execute("SELECT * FROM places WHERE id=?", (pid,)).fetchone()
    con.close()
    return dict(row) if row else None


def create_place(creator_id, name, description, genre, template_id, max_players, file_path=""):
    con = connect()
    cur = con.execute(
        "INSERT INTO places (creator_id, name, description, genre, template_id, max_players, file_path, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (creator_id, name, description or "", genre or "All", template_id or "", int(max_players or 10), file_path, int(time.time())),
    )
    con.commit()
    pid = cur.lastrowid
    con.close()
    return pid


def list_assets():
    con = connect()
    rows = con.execute("SELECT * FROM assets ORDER BY id DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_asset(aid):
    con = connect()
    row = con.execute("SELECT * FROM assets WHERE id=?", (aid,)).fetchone()
    con.close()
    return dict(row) if row else None


def create_asset(creator_id, name, asset_type, description, file_path, thumbnail_path, price):
    con = connect()
    cur = con.execute(
        "INSERT INTO assets (creator_id, asset_type, name, description, file_path, thumbnail_path, price, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (creator_id, asset_type or "Hat", name, description or "", file_path, thumbnail_path, int(price or 0), int(time.time())),
    )
    con.commit()
    aid = cur.lastrowid
    con.close()
    return aid


def create_job(job_id, place_id, host, port, status=2):
    con = connect()
    con.execute(
        "INSERT OR REPLACE INTO jobs (id, place_id, host, port, status, opened_at) VALUES (?,?,?,?,?,?)",
        (job_id, place_id, host, port, status, int(time.time())),
    )
    con.commit()
    con.close()


def get_job(job_id):
    con = connect()
    row = con.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    con.close()
    return dict(row) if row else None


def latest_job_for_place(place_id):
    con = connect()
    row = con.execute(
        "SELECT * FROM jobs WHERE place_id=? ORDER BY opened_at DESC LIMIT 1",
        (place_id,),
    ).fetchone()
    con.close()
    return dict(row) if row else None


def list_friends(user_id):
    if not user_id:
        return []
    con = connect()
    rows = con.execute(
        """
        SELECT u.* FROM users u
        JOIN friendships f ON (
            (f.friend_id = u.id AND f.user_id = ?)
            OR (f.user_id = u.id AND f.friend_id = ?)
        )
        WHERE u.id != ? AND IFNULL(f.status, 'accepted') = 'accepted'
        ORDER BY u.username COLLATE NOCASE
        """,
        (user_id, user_id, user_id),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def add_friend(user_id, other_id):
    try:
        user_id = int(user_id)
        other_id = int(other_id)
    except (TypeError, ValueError):
        return False
    if not user_id or not other_id or user_id == other_id:
        return False
    if not get_user(other_id):
        return False
    con = connect()
    exists = con.execute(
        "SELECT id FROM friendships WHERE (user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)",
        (user_id, other_id, other_id, user_id),
    ).fetchone()
    if not exists:
        con.execute(
            "INSERT INTO friendships (user_id, friend_id, status) VALUES (?,?,?)",
            (user_id, other_id, "accepted"),
        )
        con.commit()
    con.close()
    return True


def list_inventory(user_id):
    if not user_id:
        return []
    con = connect()
    rows = con.execute(
        """
        SELECT a.* FROM assets a
        JOIN inventory i ON i.asset_id = a.id
        WHERE i.user_id = ?
        ORDER BY i.id DESC
        """,
        (user_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def search_users(q):
    q = (q or "").strip()
    if not q:
        return []
    con = connect()
    rows = con.execute(
        "SELECT * FROM users WHERE username LIKE ? ORDER BY id DESC LIMIT 50",
        ("%" + q + "%",),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def search_places(q):
    q = (q or "").strip()
    if not q:
        return []
    con = connect()
    rows = con.execute(
        "SELECT * FROM places WHERE name LIKE ? OR description LIKE ? ORDER BY id DESC LIMIT 50",
        ("%" + q + "%", "%" + q + "%"),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def places_by_creator(user_id):
    con = connect()
    rows = con.execute(
        "SELECT * FROM places WHERE creator_id=? ORDER BY id DESC",
        (user_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]



def public_user(row):
    if not row:
        return None
    return {
        "id": row["id"],
        "username": row["username"],
        "robux": row.get("robux") or 0,
        "status": row.get("status") or "",
        "blurb": row.get("blurb") or "",
        "created_at": row.get("created_at") or 0,
    }



DEFAULT_SETTINGS = {
    "display_name": "",
    "email": "",
    "language": "English",
    "who_message": "Friends",
    "who_chat_app": "Friends",
    "who_chat_game": "Everyone",
    "who_join": "Everyone",
    "who_inventory": "Everyone",
    "who_trade": "Friends",
    "who_friends": "Everyone",
    "two_step": False,
    "account_restrictions": False,
    "content_maturity": "Minimal",
    "monthly_spend": "None",
    "notify_messages": True,
    "notify_friends": True,
    "notify_trades": True,
    "notify_updates": False,
    "avatar_type": "R6",
    "head_color": "#F5CD30",
    "torso_color": "#0D69AC",
    "left_arm_color": "#F5CD30",
    "right_arm_color": "#F5CD30",
    "left_leg_color": "#4B974B",
    "right_leg_color": "#4B974B",
}


def get_user_settings(user):
    out = dict(DEFAULT_SETTINGS)
    raw = (user or {}).get("settings") or ""
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                for k, v in data.items():
                    out[k] = v
        except Exception:
            pass
    if not out.get("display_name"):
        out["display_name"] = (user or {}).get("username") or ""
    return out


def save_user_settings(user_id, updates):
    user = get_user(user_id)
    if not user:
        return None
    cur = get_user_settings(user)
    for k, v in (updates or {}).items():
        if k in DEFAULT_SETTINGS:
            cur[k] = v
    con = connect()
    con.execute("UPDATE users SET settings=? WHERE id=?", (json.dumps(cur), user_id))
    con.commit()
    con.close()
    return get_user_settings(get_user(user_id))


def update_password(user_id, current, new):
    user = get_user(user_id)
    if not user or not new:
        return False
    if not _check(current or "", user["password_hash"]):
        return False
    con = connect()
    con.execute("UPDATE users SET password_hash=? WHERE id=?", (_hash(new), user_id))
    con.commit()
    con.close()
    return True


def set_pin(user_id, pin):
    pin = (pin or "").strip()
    con = connect()
    if not pin:
        con.execute("UPDATE users SET pin_hash='' WHERE id=?", (user_id,))
    else:
        con.execute("UPDATE users SET pin_hash=? WHERE id=?", (_hash(pin), user_id))
    con.commit()
    con.close()


def check_pin(user_id, pin):
    user = get_user(user_id)
    if not user:
        return False
    stored = user.get("pin_hash") or ""
    if not stored:
        return True
    return _check(pin or "", stored)


def session_count(user_id):
    con = connect()
    row = con.execute(
        "SELECT COUNT(*) AS c FROM sessions WHERE user_id=? AND expires_at>?",
        (user_id, int(time.time())),
    ).fetchone()
    con.close()
    return int(row["c"] or 0) if row else 0


def delete_other_sessions(user_id, keep_sid):
    con = connect()
    if keep_sid:
        con.execute("DELETE FROM sessions WHERE user_id=? AND id!=?", (user_id, keep_sid))
    else:
        con.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
    con.commit()
    con.close()


def user_place_visits(user_id):
    con = connect()
    row = con.execute(
        "SELECT SUM(IFNULL(visits,0)) AS v FROM places WHERE creator_id=?",
        (user_id,),
    ).fetchone()
    con.close()
    return int(row["v"] or 0) if row else 0


def update_user(user_id, **fields):
    allowed = {"username", "status", "blurb", "robux", "birthday", "gender"}
    sets, vals = [], []
    for k, v in fields.items():
        if k not in allowed:
            continue
        if k == "username":
            v = (v or "").strip()
            if not v:
                continue
        sets.append("%s=?" % k)
        vals.append(v)
    if not sets:
        return get_user(user_id)
    vals.append(user_id)
    con = connect()
    try:
        con.execute("UPDATE users SET %s WHERE id=?" % ",".join(sets), vals)
        con.commit()
    except sqlite3.IntegrityError:
        con.close()
        return None
    con.close()
    return get_user(user_id)


def bump_place_visits(pid):
    con = connect()
    con.execute("UPDATE places SET visits = IFNULL(visits,0) + 1 WHERE id=?", (pid,))
    con.commit()
    con.close()


def list_messages(user_id):
    if not user_id:
        return []
    con = connect()
    rows = con.execute(
        """
        SELECT m.*, fu.username AS from_name, tu.username AS to_name
        FROM messages m
        JOIN users fu ON fu.id = m.from_id
        JOIN users tu ON tu.id = m.to_id
        WHERE m.to_id=? OR m.from_id=?
        ORDER BY m.id DESC LIMIT 100
        """,
        (user_id, user_id),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def send_message(from_id, to_id, body, subject=""):
    if not from_id or not to_id or not (body or "").strip():
        return None
    if not get_user(to_id):
        return None
    con = connect()
    cur = con.execute(
        "INSERT INTO messages (from_id, to_id, body, created_at, subject, is_read) VALUES (?,?,?,?,?,0)",
        (from_id, to_id, body.strip(), int(time.time()), subject or ""),
    )
    con.commit()
    mid = cur.lastrowid
    con.close()
    return mid


def list_groups():
    con = connect()
    rows = con.execute("SELECT * FROM groups ORDER BY id DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]


def get_group(gid):
    con = connect()
    row = con.execute("SELECT * FROM groups WHERE id=?", (gid,)).fetchone()
    con.close()
    return dict(row) if row else None


def create_group(creator_id, name, description=""):
    name = (name or "").strip()
    if not name:
        return None
    con = connect()
    cur = con.execute(
        "INSERT INTO groups (creator_id, name, description, created_at) VALUES (?,?,?,?)",
        (creator_id, name, description or "", int(time.time())),
    )
    gid = cur.lastrowid
    con.execute(
        "INSERT INTO group_members (group_id, user_id, role) VALUES (?,?,?)",
        (gid, creator_id, "Owner"),
    )
    con.commit()
    con.close()
    return gid


def join_group(group_id, user_id):
    if not get_group(group_id) or not get_user(user_id):
        return False
    con = connect()
    try:
        con.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id, role) VALUES (?,?,?)",
            (group_id, user_id, "Member"),
        )
        con.commit()
    finally:
        con.close()
    return True


def group_members(group_id):
    con = connect()
    rows = con.execute(
        """
        SELECT u.*, gm.role FROM users u
        JOIN group_members gm ON gm.user_id=u.id
        WHERE gm.group_id=?
        ORDER BY u.username COLLATE NOCASE
        """,
        (group_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def list_wearing(user_id):
    con = connect()
    rows = con.execute(
        """
        SELECT a.* FROM assets a
        JOIN wearing w ON w.asset_id=a.id
        WHERE w.user_id=?
        """,
        (user_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def wear_asset(user_id, asset_id):
    if not get_asset(asset_id):
        return False
    con = connect()
    owned = con.execute(
        "SELECT id FROM inventory WHERE user_id=? AND asset_id=?",
        (user_id, asset_id),
    ).fetchone()
    if not owned:
        con.close()
        return False
    con.execute("INSERT OR IGNORE INTO wearing (user_id, asset_id) VALUES (?,?)", (user_id, asset_id))
    con.commit()
    con.close()
    return True


def unwear_asset(user_id, asset_id):
    con = connect()
    con.execute("DELETE FROM wearing WHERE user_id=? AND asset_id=?", (user_id, asset_id))
    con.commit()
    con.close()


def grant_asset(user_id, asset_id):
    con = connect()
    exists = con.execute(
        "SELECT id FROM inventory WHERE user_id=? AND asset_id=?",
        (user_id, asset_id),
    ).fetchone()
    if not exists:
        con.execute(
            "INSERT INTO inventory (user_id, asset_id, created_at) VALUES (?,?,?)",
            (user_id, asset_id, int(time.time())),
        )
        con.commit()
    con.close()


def buy_asset(user_id, asset_id):
    user = get_user(user_id)
    asset = get_asset(asset_id)
    if not user or not asset:
        return False, "not found"
    price = int(asset.get("price") or 0)
    if int(user.get("robux") or 0) < price:
        return False, "robux"
    con = connect()
    owned = con.execute(
        "SELECT id FROM inventory WHERE user_id=? AND asset_id=?",
        (user_id, asset_id),
    ).fetchone()
    if owned:
        con.close()
        return False, "owned"
    con.execute("UPDATE users SET robux = robux - ? WHERE id=?", (price, user_id))
    con.execute(
        "INSERT INTO inventory (user_id, asset_id, created_at) VALUES (?,?,?)",
        (user_id, asset_id, int(time.time())),
    )
    con.commit()
    con.close()
    return True, "ok"


def remove_friend(user_id, other_id):
    con = connect()
    con.execute(
        "DELETE FROM friendships WHERE (user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)",
        (user_id, other_id, other_id, user_id),
    )
    con.commit()
    con.close()


def list_trades(user_id):
    con = connect()
    rows = con.execute(
        "SELECT * FROM trades WHERE from_id=? OR to_id=? ORDER BY id DESC",
        (user_id, user_id),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def create_trade(from_id, to_id):
    if from_id == to_id or not get_user(to_id):
        return None
    con = connect()
    cur = con.execute(
        "INSERT INTO trades (from_id, to_id, status, created_at) VALUES (?,?,?,?)",
        (from_id, to_id, "open", int(time.time())),
    )
    con.commit()
    tid = cur.lastrowid
    con.close()
    return tid


def redeem_promo(user_id, code):
    code = (code or "").strip()
    if not code:
        return False, "invalid"
    con = connect()
    row = con.execute("SELECT * FROM promo_codes WHERE code=?", (code,)).fetchone()
    if not row:
        con.close()
        return False, "invalid"
    if row["redeemed_by"]:
        con.close()
        return False, "used"
    reward = row["reward"] or ""
    con.execute("UPDATE promo_codes SET redeemed_by=? WHERE code=?", (user_id, code))
    if reward.startswith("robux:"):
        try:
            amt = int(reward.split(":", 1)[1])
            con.execute("UPDATE users SET robux = IFNULL(robux,0) + ? WHERE id=?", (amt, user_id))
        except ValueError:
            pass
    con.commit()
    con.close()
    return True, reward


def list_users(limit=50):
    con = connect()
    rows = con.execute("SELECT * FROM users ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    con.close()
    return [dict(r) for r in rows]



def list_places_filtered(genre=None, keyword=None, sort="new"):
    sql = "SELECT * FROM places WHERE 1=1"
    args = []
    if genre and genre not in ("", "All"):
        sql += " AND IFNULL(genre,'All')=?"
        args.append(genre)
    if keyword:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if sort == "visits":
        sql += " ORDER BY IFNULL(visits,0) DESC, id DESC"
    elif sort == "name":
        sql += " ORDER BY name COLLATE NOCASE"
    else:
        sql += " ORDER BY id DESC"
    con = connect()
    rows = con.execute(sql, args).fetchall()
    con.close()
    return [dict(r) for r in rows]


def list_assets_filtered(asset_type=None, keyword=None, sort="new"):
    sql = "SELECT * FROM assets WHERE 1=1"
    args = []
    if asset_type and asset_type not in ("", "All", "Featured"):
        sql += " AND IFNULL(asset_type,'Hat')=?"
        args.append(asset_type)
    if keyword:
        sql += " AND (name LIKE ? OR description LIKE ?)"
        args.extend(["%" + keyword + "%", "%" + keyword + "%"])
    if sort == "price":
        sql += " ORDER BY IFNULL(price,0) ASC, id DESC"
    elif sort == "price_desc":
        sql += " ORDER BY IFNULL(price,0) DESC, id DESC"
    else:
        sql += " ORDER BY id DESC"
    con = connect()
    rows = con.execute(sql, args).fetchall()
    con.close()
    return [dict(r) for r in rows]


def request_friend(user_id, other_id):
    try:
        user_id = int(user_id)
        other_id = int(other_id)
    except (TypeError, ValueError):
        return False, "invalid"
    if not user_id or not other_id or user_id == other_id:
        return False, "invalid"
    if not get_user(other_id):
        return False, "not found"
    con = connect()
    row = con.execute(
        "SELECT * FROM friendships WHERE (user_id=? AND friend_id=?) OR (user_id=? AND friend_id=?)",
        (user_id, other_id, other_id, user_id),
    ).fetchone()
    if row:
        st = row["status"] or "accepted"
        if st == "accepted":
            con.close()
            return True, "friends"
        if int(row["user_id"]) == other_id and st == "pending":
            con.execute("UPDATE friendships SET status='accepted' WHERE id=?", (row["id"],))
            con.commit()
            con.close()
            return True, "accepted"
        con.close()
        return True, "pending"
    con.execute(
        "INSERT INTO friendships (user_id, friend_id, status) VALUES (?,?,?)",
        (user_id, other_id, "pending"),
    )
    con.commit()
    con.close()
    return True, "requested"


def list_friend_requests(user_id):
    if not user_id:
        return []
    con = connect()
    rows = con.execute(
        """
        SELECT u.* FROM users u
        JOIN friendships f ON f.user_id = u.id
        WHERE f.friend_id=? AND IFNULL(f.status,'accepted')='pending'
        ORDER BY u.username COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def accept_friend(user_id, other_id):
    con = connect()
    con.execute(
        "UPDATE friendships SET status='accepted' WHERE user_id=? AND friend_id=? AND IFNULL(status,'pending')='pending'",
        (other_id, user_id),
    )
    con.commit()
    con.close()
    return True


def decline_friend(user_id, other_id):
    con = connect()
    con.execute(
        "DELETE FROM friendships WHERE user_id=? AND friend_id=? AND IFNULL(status,'pending')='pending'",
        (other_id, user_id),
    )
    con.commit()
    con.close()
    return True


def list_inbox(user_id):
    if not user_id:
        return []
    con = connect()
    rows = con.execute(
        """
        SELECT m.*, fu.username AS from_name, tu.username AS to_name
        FROM messages m
        JOIN users fu ON fu.id = m.from_id
        JOIN users tu ON tu.id = m.to_id
        WHERE m.to_id=?
        ORDER BY m.id DESC LIMIT 100
        """,
        (user_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def list_sent(user_id):
    if not user_id:
        return []
    con = connect()
    rows = con.execute(
        """
        SELECT m.*, fu.username AS from_name, tu.username AS to_name
        FROM messages m
        JOIN users fu ON fu.id = m.from_id
        JOIN users tu ON tu.id = m.to_id
        WHERE m.from_id=?
        ORDER BY m.id DESC LIMIT 100
        """,
        (user_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def mark_message_read(user_id, mid):
    con = connect()
    con.execute("UPDATE messages SET is_read=1 WHERE id=? AND to_id=?", (mid, user_id))
    con.commit()
    con.close()


def list_groups_detailed():
    con = connect()
    rows = con.execute(
        """
        SELECT g.*, u.username AS owner_name,
               (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id=g.id) AS member_count
        FROM groups g
        LEFT JOIN users u ON u.id = g.creator_id
        ORDER BY g.id DESC
        """
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def groups_for_user(user_id):
    con = connect()
    rows = con.execute(
        """
        SELECT g.*, gm.role,
               (SELECT COUNT(*) FROM group_members x WHERE x.group_id=g.id) AS member_count
        FROM groups g
        JOIN group_members gm ON gm.group_id=g.id
        WHERE gm.user_id=?
        ORDER BY g.name COLLATE NOCASE
        """,
        (user_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def search_groups(q):
    q = (q or "").strip()
    if not q:
        return list_groups_detailed()
    con = connect()
    rows = con.execute(
        """
        SELECT g.*, u.username AS owner_name,
               (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id=g.id) AS member_count
        FROM groups g
        LEFT JOIN users u ON u.id = g.creator_id
        WHERE g.name LIKE ? OR g.description LIKE ?
        ORDER BY g.id DESC
        """,
        ("%" + q + "%", "%" + q + "%"),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def toggle_favorite(user_id, place_id):
    if not get_place(place_id):
        return False, "missing"
    con = connect()
    row = con.execute(
        "SELECT user_id FROM favorites WHERE user_id=? AND place_id=?",
        (user_id, place_id),
    ).fetchone()
    if row:
        con.execute("DELETE FROM favorites WHERE user_id=? AND place_id=?", (user_id, place_id))
        con.commit()
        con.close()
        return True, "removed"
    con.execute(
        "INSERT INTO favorites (user_id, place_id, created_at) VALUES (?,?,?)",
        (user_id, place_id, int(time.time())),
    )
    con.commit()
    con.close()
    return True, "added"


def is_favorite(user_id, place_id):
    con = connect()
    row = con.execute(
        "SELECT user_id FROM favorites WHERE user_id=? AND place_id=?",
        (user_id, place_id),
    ).fetchone()
    con.close()
    return bool(row)


def list_favorites(user_id):
    con = connect()
    rows = con.execute(
        """
        SELECT p.* FROM places p
        JOIN favorites f ON f.place_id=p.id
        WHERE f.user_id=?
        ORDER BY f.created_at DESC
        """,
        (user_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def record_play(user_id, place_id):
    if not user_id or not place_id:
        return
    con = connect()
    con.execute(
        "INSERT OR REPLACE INTO recently_played (user_id, place_id, played_at) VALUES (?,?,?)",
        (user_id, place_id, int(time.time())),
    )
    con.commit()
    con.close()


def list_recent(user_id, limit=12):
    con = connect()
    rows = con.execute(
        """
        SELECT p.* FROM places p
        JOIN recently_played r ON r.place_id=p.id
        WHERE r.user_id=?
        ORDER BY r.played_at DESC LIMIT ?
        """,
        (user_id, int(limit)),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def list_jobs_for_place(place_id):
    con = connect()
    rows = con.execute(
        "SELECT * FROM jobs WHERE place_id=? ORDER BY opened_at DESC LIMIT 10",
        (place_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def add_trade_item(trade_id, user_id, asset_id):
    if not get_asset(asset_id):
        return False
    con = connect()
    owned = con.execute(
        "SELECT id FROM inventory WHERE user_id=? AND asset_id=?",
        (user_id, asset_id),
    ).fetchone()
    if not owned:
        con.close()
        return False
    con.execute(
        "INSERT INTO trade_items (trade_id, user_id, asset_id) VALUES (?,?,?)",
        (trade_id, user_id, asset_id),
    )
    con.commit()
    con.close()
    return True


def list_trade_items(trade_id):
    con = connect()
    rows = con.execute(
        """
        SELECT ti.*, a.name, a.asset_type, a.price
        FROM trade_items ti
        JOIN assets a ON a.id = ti.asset_id
        WHERE ti.trade_id=?
        """,
        (trade_id,),
    ).fetchall()
    con.close()
    return [dict(r) for r in rows]


def set_trade_status(trade_id, user_id, status):
    trade = None
    con = connect()
    row = con.execute("SELECT * FROM trades WHERE id=?", (trade_id,)).fetchone()
    if not row:
        con.close()
        return False
    trade = dict(row)
    if user_id not in (trade["from_id"], trade["to_id"]):
        con.close()
        return False
    if status == "completed":
        items = con.execute("SELECT * FROM trade_items WHERE trade_id=?", (trade_id,)).fetchall()
        for it in items:
            other = trade["to_id"] if it["user_id"] == trade["from_id"] else trade["from_id"]
            con.execute(
                "DELETE FROM inventory WHERE user_id=? AND asset_id=? AND id IN (SELECT id FROM inventory WHERE user_id=? AND asset_id=? LIMIT 1)",
                (it["user_id"], it["asset_id"], it["user_id"], it["asset_id"]),
            )
            exists = con.execute(
                "SELECT id FROM inventory WHERE user_id=? AND asset_id=?",
                (other, it["asset_id"]),
            ).fetchone()
            if not exists:
                con.execute(
                    "INSERT INTO inventory (user_id, asset_id, created_at) VALUES (?,?,?)",
                    (other, it["asset_id"], int(time.time())),
                )
            con.execute("DELETE FROM wearing WHERE user_id=? AND asset_id=?", (it["user_id"], it["asset_id"]))
    con.execute("UPDATE trades SET status=? WHERE id=?", (status, trade_id))
    con.commit()
    con.close()
    return True


def iso(ts):
    import datetime
    try:
        return datetime.datetime.utcfromtimestamp(int(ts or time.time())).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except Exception:
        return "2020-01-01T00:00:00.000Z"



def create_outfit(user_id, name):
    name = (name or "").strip() or "Outfit"
    wearing = list_wearing(user_id)
    user = get_user(user_id)
    colors = json.dumps(get_user_settings(user))
    con = connect()
    cur = con.execute(
        "INSERT INTO outfits (user_id, name, colors, created_at) VALUES (?,?,?,?)",
        (user_id, name[:25], colors, int(time.time())),
    )
    oid = cur.lastrowid
    for a in wearing:
        con.execute("INSERT INTO outfit_items (outfit_id, asset_id) VALUES (?,?)", (oid, a["id"]))
    con.commit()
    con.close()
    return oid


def list_outfits(user_id):
    con = connect()
    rows = con.execute("SELECT * FROM outfits WHERE user_id=? ORDER BY id DESC", (user_id,)).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        items = con.execute("SELECT asset_id FROM outfit_items WHERE outfit_id=?", (d["id"],)).fetchall()
        d["asset_ids"] = [i["asset_id"] for i in items]
        out.append(d)
    con.close()
    return out


def wear_outfit(user_id, outfit_id):
    con = connect()
    row = con.execute("SELECT * FROM outfits WHERE id=? AND user_id=?", (outfit_id, user_id)).fetchone()
    if not row:
        con.close()
        return False
    items = con.execute("SELECT asset_id FROM outfit_items WHERE outfit_id=?", (outfit_id,)).fetchall()
    con.close()
    wearing = list_wearing(user_id)
    for a in wearing:
        unwear_asset(user_id, a["id"])
    for it in items:
        wear_asset(user_id, it["asset_id"])
    try:
        data = json.loads(row["colors"] or "{}")
        keys = ("head_color","torso_color","left_arm_color","right_arm_color","left_leg_color","right_leg_color")
        save_user_settings(user_id, {k: data[k] for k in keys if k in data})
    except Exception:
        pass
    return True


def delete_outfit(user_id, outfit_id):
    con = connect()
    con.execute("DELETE FROM outfit_items WHERE outfit_id=?", (outfit_id,))
    con.execute("DELETE FROM outfits WHERE id=? AND user_id=?", (outfit_id, user_id))
    con.commit()
    con.close()
