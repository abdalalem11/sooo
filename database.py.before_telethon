import os, sqlite3
from datetime import datetime, timezone

class DB:
    def __init__(self, path):
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        self.path = path
        with sqlite3.connect(path) as c:
            c.execute('''CREATE TABLE IF NOT EXISTS installs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'stopped',
                created_at TEXT NOT NULL
            )''')
            c.commit()
    def add(self, user_id, name, expires_at):
        with sqlite3.connect(self.path) as c:
            cur=c.execute('INSERT INTO installs(user_id,name,expires_at,status,created_at) VALUES(?,?,?,\'stopped\',?)',(user_id,name,expires_at,datetime.now(timezone.utc).isoformat()))
            c.commit(); return cur.lastrowid
    def get(self, iid, user_id):
        with sqlite3.connect(self.path) as c:
            c.row_factory=sqlite3.Row
            return c.execute('SELECT * FROM installs WHERE id=? AND user_id=?',(iid,user_id)).fetchone()
    def list(self, user_id):
        with sqlite3.connect(self.path) as c:
            c.row_factory=sqlite3.Row
            return c.execute('SELECT * FROM installs WHERE user_id=? ORDER BY id DESC',(user_id,)).fetchall()
    def set_status(self,iid,user_id,status):
        with sqlite3.connect(self.path) as c:
            c.execute('UPDATE installs SET status=? WHERE id=? AND user_id=?',(status,iid,user_id)); c.commit()
    def delete(self,iid,user_id):
        with sqlite3.connect(self.path) as c:
            c.execute('DELETE FROM installs WHERE id=? AND user_id=?',(iid,user_id)); c.commit()
    def all_running(self):
        with sqlite3.connect(self.path) as c:
            c.row_factory=sqlite3.Row
            return c.execute('SELECT * FROM installs WHERE status=\'running\'').fetchall()
