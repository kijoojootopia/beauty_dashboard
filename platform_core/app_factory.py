import os
import secrets
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit
from flask import Flask, render_template, request
from dotenv import load_dotenv
from werkzeug.exceptions import HTTPException

def create_app(test_config=None):
    root=Path(__file__).resolve().parents[1]
    load_dotenv(root/".env")
    app=Flask(__name__, instance_path=str(root/"instance"), instance_relative_config=True)
    Path(app.instance_path).mkdir(parents=True,exist_ok=True)
    secret=os.getenv("SECRET_KEY")
    if not secret:
        keyfile=Path(app.instance_path)/"secret.key"
        try:
            fd=os.open(str(keyfile),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            with os.fdopen(fd,"w") as f:
                f.write(secrets.token_hex(32))
        except FileExistsError:
            pass
        secret=keyfile.read_text().strip()
    app.config.update(SECRET_KEY=secret,DATABASE=os.getenv("DATABASE_PATH") or str(root/"instance/beauty.sqlite3"),
        MAX_CONTENT_LENGTH=2*1024*1024,SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE","").lower()=="true",PERMANENT_SESSION_LIFETIME=timedelta(hours=12),
        REGULATION_DATA_ROOT=root/"tab1_regulation/data",CUSTOMS_DATA_ROOT=root/"tab2_customs/data",
        MARKET_DATA_ROOT=root/"tab3_market/data/export")
    if test_config:
        app.config.update(test_config)
    from .services import database, auth_service
    from .services.country_service import COUNTRIES, EU_MEMBERS, ASEAN_MEMBERS, MEMBER_NAMES
    app.teardown_appcontext(database.close_db)
    app.before_request(auth_service.load_user_and_protect)
    from .routes import bp as core
    from tab1_regulation.routes import bp as regulation
    from tab2_customs.routes import bp as customs
    from tab3_market.routes import bp as market
    for bp in (core,regulation,customs,market):
        app.register_blueprint(bp)
    app.jinja_env.globals.update(csrf_token=auth_service.csrf_token,countries=COUNTRIES,eu_members=EU_MEMBERS,asean_members=ASEAN_MEMBERS,member_names=MEMBER_NAMES)
    @app.before_request
    def legacy_country_redirect():
        from flask import redirect, url_for
        if request.view_args and request.view_args.get("country") in {"vn","th","as"}:
            args=dict(request.args)
            old=request.view_args["country"]
            if old in {"vn","th"}: args.setdefault("member_state",old.upper())
            return redirect(url_for(request.endpoint,**{**args,**request.view_args,"country":"asean"}),code=302)
    @app.template_filter("safe_url")
    def safe_url(value):
        try:
            p=urlsplit(value or "")
            return value if p.scheme in {"http","https"} and p.netloc else ""
        except ValueError:
            return ""
    @app.template_filter("number")
    def number(value):
        return "—" if value is None else f"{value:,.1f}"
    @app.template_filter("compact_number")
    def compact_number(value):
        if value is None: return "—"
        if abs(value)>=100000000: return f"{value/100000000:,.1f}억"
        if abs(value)>=10000: return f"{value/10000:,.1f}만"
        return f"{value:,.0f}"
    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith("/api/"):
            return {"error":error.name,"message":error.description},error.code
        return render_template("platform_core/error.html",error=error),error.code
    @app.after_request
    def headers(response):
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["X-Frame-Options"]="SAMEORIGIN"
        response.headers["Referrer-Policy"]="same-origin"
        response.headers["Content-Security-Policy"]="default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'self'"
        if not request.path.startswith(("/core-assets/","/regulation-assets/","/customs-assets/","/market-assets/")):
            response.headers["Cache-Control"]="no-store"
        return response
    with app.app_context():
        database.init_db()
    return app
