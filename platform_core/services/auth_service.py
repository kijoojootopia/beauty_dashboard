import hashlib
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import urlsplit
from flask import abort, g, redirect, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from .database import get_db

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def register(email, name, password):
    email = email.strip().lower()
    name = name.strip()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(email)>254:
        raise ValueError("이메일 주소를 확인해 주세요.")
    if not 1 <= len(name) <= 50:
        raise ValueError("이름은 1~50자로 입력해 주세요.")
    if not 10 <= len(password) <= 128:
        raise ValueError("비밀번호는 10~128자로 입력해 주세요.")
    try:
        with get_db() as db:
            cursor = db.execute("INSERT INTO users(email,name,password_hash,created_at) VALUES(?,?,?,?)",
                                (email, name, generate_password_hash(password), now()))
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        raise ValueError("가입 정보를 확인해 주세요. 이미 가입했다면 로그인해 주세요.") from None

def authenticate(email, password, address):
    email = email.strip().lower()
    key = hashlib.sha256(f"{address}:{email}".encode()).hexdigest()
    db = get_db()
    attempt = db.execute("SELECT * FROM login_attempts WHERE attempt_key=?", (key,)).fetchone()
    if attempt and time.time()-attempt["window_started"] < 900 and attempt["count"] >= 10:
        raise ValueError("로그인 시도가 많습니다. 15분 후 다시 시도해 주세요.")
    user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
    if user and len(password)<=128 and check_password_hash(user["password_hash"],password):
        with db:
            db.execute("DELETE FROM login_attempts WHERE attempt_key=?", (key,))
        return user["id"]
    started = attempt["window_started"] if attempt and time.time()-attempt["window_started"]<900 else time.time()
    count = attempt["count"]+1 if attempt and started==attempt["window_started"] else 1
    with db:
        db.execute("INSERT OR REPLACE INTO login_attempts VALUES(?,?,?)",(key,count,started))
    raise ValueError("이메일 또는 비밀번호를 확인해 주세요.")

def csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]

def load_user_and_protect():
    g.user = None
    if session.get("user_id"):
        g.user = get_db().execute("SELECT id,email,name FROM users WHERE id=?", (session["user_id"],)).fetchone()
    if request.method in {"POST","PUT","PATCH","DELETE"}:
        provided = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token", "")
        expected = session.get("csrf_token", "")
        if not expected or not secrets.compare_digest(str(provided),str(expected)):
            abort(400, description="화면이 만료되었습니다. 새로고침 후 다시 시도해 주세요.")

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            if request.path.startswith("/api/"):
                abort(401)
            return redirect(url_for("platform_core.login", next=request.full_path))
        return view(*args, **kwargs)
    return wrapped

def safe_next(value):
    value = value or ""
    parsed = urlsplit(value)
    if not value.startswith("/") or value.startswith("//") or parsed.scheme or parsed.netloc or "\\" in value:
        return url_for("platform_core.projects")
    if any(ord(c)<32 for c in value):
        return url_for("platform_core.projects")
    return value
