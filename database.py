import hashlib
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
    if not cur.execute("SELECT id FROM users WHERE username=?", ("Player",)).fetchone():
        create_user("Player", "player", "1/1/2000", "Male")
    if not cur.execute("SELECT id FROM places").fetchone():
        cur.execute(
            "INSERT INTO places (creator_id, name, description, genre, max_players, created_at) VALUES (1, ?, ?, ?, 10, ?)",
            ("Baseplate", "A starting place.", "All", int(time.time())),
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
    con = connect()
    try:
        con.execute(
            "INSERT INTO users (username, password_hash, birthday, gender, created_at) VALUES (?,?,?,?,?)",
            (username.strip(), _hash(password), birthday, gender, int(time.time())),
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
