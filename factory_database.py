import sqlite3
import time
from pathlib import Path


class Database:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def init(self):
        with self.connect() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS installs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    expires_at REAL,
                    unlimited INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'stopped',
                    phone TEXT,
                    session_path TEXT,
                    created_at REAL NOT NULL
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS access_requests (
                    user_id INTEGER PRIMARY KEY,
                    status TEXT DEFAULT 'pending',
                    created_at REAL NOT NULL
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id INTEGER PRIMARY KEY,
                    created_at REAL NOT NULL
                )
            """)

            db.execute("""
                CREATE TABLE IF NOT EXISTS install_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    install_mode TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    days INTEGER,
                    created_at REAL NOT NULL
                )
            """)
            db.commit()

    def access_request(self, user_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM access_requests WHERE user_id=?",
                (user_id,)
            ).fetchone()

            return dict(row) if row else None

    def request_access(self, user_id):
        with self.connect() as db:
            db.execute("""
                INSERT INTO access_requests
                (user_id, status, created_at)
                VALUES (?, 'pending', ?)
                ON CONFLICT(user_id)
                DO UPDATE SET
                    status='pending',
                    created_at=excluded.created_at
            """, (user_id, time.time()))

            db.commit()

    def set_access(self, user_id, status):
        with self.connect() as db:
            db.execute("""
                INSERT INTO access_requests
                (user_id, status, created_at)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id)
                DO UPDATE SET status=excluded.status
            """, (user_id, status, time.time()))

            db.commit()

    def access_users(self, status="pending"):
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM access_requests "
                "WHERE status=? ORDER BY created_at ASC",
                (status,)
            ).fetchall()

            return [dict(x) for x in rows]

    def create(self, user_id, name, expires_at=None, unlimited=False):
        with self.connect() as db:
            cur = db.execute("""
                INSERT INTO installs
                (user_id,name,expires_at,unlimited,status,created_at)
                VALUES (?,?,?,?,?,?)
            """, (
                user_id,
                name,
                expires_at,
                int(unlimited),
                "stopped",
                time.time()
            ))
            db.commit()
            return cur.lastrowid

    def get(self, install_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM installs WHERE id=?",
                (install_id,)
            ).fetchone()
            return dict(row) if row else None

    def user(self, user_id):
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM installs WHERE user_id=? ORDER BY id DESC",
                (user_id,)
            ).fetchall()
            return [dict(x) for x in rows]

    def all(self):
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM installs ORDER BY id DESC"
            ).fetchall()
            return [dict(x) for x in rows]

    def status(self, install_id, status):
        with self.connect() as db:
            db.execute(
                "UPDATE installs SET status=? WHERE id=?",
                (status, install_id)
            )
            db.commit()

    def session(self, install_id, path, phone=None):
        with self.connect() as db:
            db.execute("""
                UPDATE installs
                SET session_path=?, phone=?
                WHERE id=?
            """, (path, phone, install_id))
            db.commit()

    def unlimited(self, install_id):
        with self.connect() as db:
            db.execute("""
                UPDATE installs
                SET unlimited=1, expires_at=NULL
                WHERE id=?
            """, (install_id,))
            db.commit()

    def ban_user(self, user_id):
        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO banned_users (user_id, created_at) VALUES (?, ?)",
                (user_id, time.time())
            )
            db.commit()

    def unban_user(self, user_id):
        with self.connect() as db:
            db.execute(
                "DELETE FROM banned_users WHERE user_id=?",
                (user_id,)
            )
            db.commit()

    def is_banned(self, user_id):
        with self.connect() as db:
            row = db.execute(
                "SELECT 1 FROM banned_users WHERE user_id=?",
                (user_id,)
            ).fetchone()
            return row is not None

    def extend_install(self, install_id, days):
        with self.connect() as db:
            row = db.execute(
                "SELECT expires_at, unlimited FROM installs WHERE id=?",
                (install_id,)
            ).fetchone()

            if not row:
                raise ValueError("التنصيب غير موجود.")

            if row["unlimited"]:
                return None

            base = row["expires_at"] or time.time()
            new_expiry = max(base, time.time()) + (days * 86400)

            db.execute(
                "UPDATE installs SET expires_at=?, status=? WHERE id=?",
                (new_expiry, "stopped", install_id)
            )
            db.commit()

            return new_expiry

    def delete(self, install_id):
        with self.connect() as db:
            db.execute(
                "DELETE FROM installs WHERE id=?",
                (install_id,)
            )
            db.commit()

    def delete_temporary(self):
        with self.connect() as db:
            db.execute(
                "DELETE FROM installs WHERE unlimited=0"
            )
            db.commit()
