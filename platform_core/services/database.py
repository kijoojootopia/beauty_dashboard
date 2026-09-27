import sqlite3
from pathlib import Path
from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 password_hash TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS projects (
 id TEXT PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id),
 name TEXT NOT NULL, country TEXT NOT NULL, member_state TEXT,
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS products (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 name TEXT NOT NULL, product_type TEXT NOT NULL, hs_code TEXT NOT NULL DEFAULT '',
 ingredients TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS product_notes (
 id TEXT PRIMARY KEY, product_id TEXT NOT NULL REFERENCES products(id),
 content TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS analyses (
 id TEXT PRIMARY KEY, product_id TEXT NOT NULL REFERENCES products(id),
 snapshot TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS task_states (
 product_id TEXT NOT NULL REFERENCES products(id), task_id TEXT NOT NULL,
 completed INTEGER NOT NULL CHECK(completed IN (0,1)), updated_at TEXT NOT NULL,
 PRIMARY KEY(product_id, task_id)
);
CREATE TABLE IF NOT EXISTS bookmarks (
 id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
 kind TEXT NOT NULL, title TEXT NOT NULL, url TEXT NOT NULL, created_at TEXT NOT NULL,
 UNIQUE(project_id,kind,url)
);
CREATE TABLE IF NOT EXISTS login_attempts (
 attempt_key TEXT PRIMARY KEY, count INTEGER NOT NULL, window_started REAL NOT NULL
);
"""

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"], timeout=10)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

def init_db():
    Path(current_app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    get_db().executescript(SCHEMA)
    db=get_db()
    with db:
        db.execute("UPDATE projects SET member_state=upper(country), country='asean' WHERE country IN ('vn','th')")
        db.execute("UPDATE projects SET country='asean' WHERE country='as'")
        # 기존 한 칸 메모를 단 한 번 목록으로 옮깁니다. 재시작해도 중복되지 않습니다.
        db.execute("INSERT OR IGNORE INTO product_notes SELECT 'legacy-' || id,id,notes,updated_at FROM products WHERE trim(notes)<>''")
        db.execute("UPDATE products SET notes='' WHERE trim(notes)<>''")

def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
