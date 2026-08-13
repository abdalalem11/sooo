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
            db.commit()

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

    def delete(self, install_id):
        with self.connect() as db:
            db.execute(
                "DELETE FROM installs WHERE id=?",
                (install_id,)
            )
            db.commit()
