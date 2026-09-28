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

class Database:
    def __init__(self, connection, postgres=False):
        self.connection, self.postgres = connection, postgres

    def execute(self, sql, params=()):
        return self.connection.execute(sql.replace("?", "%s") if self.postgres else sql, params)

    def __enter__(self):
        return self

    def __exit__(self, kind, value, traceback):
        self.connection.rollback() if kind else self.connection.commit()

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def is_integrity_error(self, error):
        if self.postgres:
            import psycopg
            return isinstance(error, psycopg.IntegrityError)
        return isinstance(error, sqlite3.IntegrityError)


def get_db():
    if "db" not in g:
        address = current_app.config["DATABASE"]
        if str(address).startswith(("postgres://", "postgresql://")):
            import psycopg
            from psycopg.rows import dict_row
            connection = psycopg.connect(address, row_factory=dict_row)
            g.db = Database(connection, postgres=True)
        else:
            connection = sqlite3.connect(address, timeout=10)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys=ON")
            g.db = Database(connection)
    return g.db

def init_db():
    db = get_db()
    if db.postgres:
        schema = SCHEMA.replace("id INTEGER PRIMARY KEY", "id SERIAL PRIMARY KEY")
        for statement in schema.split(";"):
            if statement.strip():
                db.execute(statement)
    else:
        Path(current_app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
        db.connection.executescript(SCHEMA)
    with db:
        db.execute("UPDATE projects SET member_state=upper(country), country='asean' WHERE country IN ('vn','th')")
        db.execute("UPDATE projects SET country='asean' WHERE country='as'")
        # 기존 한 칸 메모를 단 한 번 목록으로 옮깁니다. 재시작해도 중복되지 않습니다.
        db.execute("INSERT INTO product_notes SELECT 'legacy-' || id,id,notes,updated_at FROM products WHERE trim(notes)<>'' ON CONFLICT DO NOTHING")
        db.execute("UPDATE products SET notes='' WHERE trim(notes)<>''")

def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()
