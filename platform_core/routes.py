import json
from decimal import Decimal, ROUND_HALF_UP
from flask import Blueprint, Response, abort, flash, g, redirect, render_template, request, session, url_for
from .services.auth_service import register, authenticate, login_required, safe_next
from .services.country_service import get_country
from .services import project_service as store

bp=Blueprint("platform_core",__name__,template_folder="templates",static_folder="static",static_url_path="/core-assets")

@bp.get("/")
@bp.get("/beauty")
def home():
    context=export_overview_context(live=False)
    return render_template("platform_core/home.html",**context)

def export_overview_context(live=True,include_rankings=False):
    from tab3_market.services.market_service import overview
    data=overview(live=live,include_rankings=include_rankings)
    exchange=None
    try:
        from tab2_customs.services.customs_service import calculate_exchange
        rate=calculate_exchange("1","USD","KRW")
        exchange={"rate":Decimal(rate["rate"]),"as_of":rate["as_of"],"source":rate["source"]}
    except (ValueError,KeyError,TypeError):
        pass
    for item in data.get("rankings",[]):
        item["thousand_usd"]=item["value"]/1000
        if exchange:
            item["krw_label"]=_won_label(item["value"],exchange["rate"])
    if exchange:
        data["total_krw"]=_won_label(data.get("total_exports"),exchange["rate"])
    return {"overview":data,"exchange":exchange}

def _won_label(usd,rate):
    if usd is None:
        return None
    won=(Decimal(str(usd))*rate).quantize(Decimal("1"),rounding=ROUND_HALF_UP)
    trillion=Decimal("1000000000000")
    eok=Decimal("100000000")
    if won>=trillion:
        whole=int(won//trillion)
        remainder=int((won%trillion)//eok)
        return f"{whole:,}조 {remainder:,}억 원" if remainder else f"{whole:,}조 원"
    if won>=eok:
        return f"{(won/eok).quantize(Decimal('0.1'),rounding=ROUND_HALF_UP):,}억 원"
    return f"{(won/Decimal('10000')).quantize(Decimal('1'),rounding=ROUND_HALF_UP):,}만 원"

@bp.route("/login",methods=["GET","POST"])
def login():
    next_url=safe_next(request.values.get("next"))
    if request.method=="POST":
        try:
            user_id=authenticate(request.form.get("email",""),request.form.get("password",""),request.remote_addr or "local")
            session.clear()
            session["user_id"]=user_id
            session.permanent=True
            return redirect(next_url)
        except ValueError as error:
            flash(str(error),"error")
    return render_template("platform_core/auth.html",mode="login",next_url=next_url)

@bp.route("/register",methods=["GET","POST"])
def signup():
    next_url=safe_next(request.values.get("next"))
    if request.method=="POST":
        try:
            if request.form.get("password")!=request.form.get("password_confirm"):
                raise ValueError("비밀번호 확인이 일치하지 않습니다.")
            user_id=register(request.form.get("email",""),request.form.get("name",""),request.form.get("password",""))
            session.clear()
            session["user_id"]=user_id
            session.permanent=True
            return redirect(next_url)
        except ValueError as error:
            flash(str(error),"error")
    return render_template("platform_core/auth.html",mode="signup",next_url=next_url)

@bp.get("/account")
@login_required
def account():
    return render_template("platform_core/account.html")

@bp.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("platform_core.home"))

@bp.route("/projects",methods=["GET","POST"])
@login_required
def projects():
    if request.method=="POST":
        try:
            pid=store.create_project(g.user["id"],request.form.get("name",""),request.form.get("country",""),request.form.get("member_state",""))
            project=store.project_for(g.user["id"],pid)
            flash("프로젝트를 만들었습니다. 첫 제품을 등록해 주세요.","success")
            return redirect(url_for("tab1_regulation.index",country=project["country"],project_id=pid))
        except ValueError as error:
            flash(str(error),"error")
    selected=request.values.get("country","jp")
    try:
        get_country(selected)
    except ValueError:
        selected="jp"
    return render_template("platform_core/projects.html",projects=store.list_projects(g.user["id"]),selected_country=selected)

@bp.post("/projects/<project_id>/copy")
@login_required
def copy_project(project_id):
    try:
        pid=store.copy_project(g.user["id"],project_id,request.form.get("name",""),request.form.get("country",""),request.form.get("member_state",""))
        flash("제품을 새 프로젝트에 복사했습니다. 새 국가 기준으로 다시 분석해 주세요.","success")
        return redirect(url_for("tab1_regulation.index",country=store.project_for(g.user["id"],pid)["country"],project_id=pid))
    except ValueError as error:
        flash(str(error),"error")
        return redirect(url_for("platform_core.projects"))

@bp.get("/projects/<project_id>/export")
@login_required
def export_project(project_id):
    payload=store.export_project(g.user["id"],project_id)
    return Response(json.dumps(payload,ensure_ascii=False,indent=2),mimetype="application/json",headers={"Content-Disposition":f'attachment; filename="beauty-project-{project_id[:8]}.json"'})

@bp.post("/products/<product_id>/notes")
@login_required
def save_notes(product_id):
    product=store.product_for(g.user["id"],product_id)
    project=store.project_for(g.user["id"],product["project_id"])
    try:
        note=store.save_notes(g.user["id"],product_id,request.form.get("notes",""))
        if request.headers.get("Accept")=="application/json":
            return {"note":note}
        flash("메모를 저장했습니다.","success")
    except ValueError as error:
        if request.headers.get("Accept")=="application/json":
            return {"message":str(error)},400
        flash(str(error),"error")
    return redirect(url_for("tab1_regulation.index",country=project["country"],project_id=project["id"],product_id=product_id,_anchor="product-notes"))

@bp.post("/products/<product_id>/notes/<note_id>/update")
@login_required
def update_note(product_id,note_id):
    product=store.product_for(g.user["id"],product_id)
    project=store.project_for(g.user["id"],product["project_id"])
    try:
        note=store.update_note(g.user["id"],product_id,note_id,request.form.get("notes",""))
        if request.headers.get("Accept")=="application/json":
            return {"note":note}
        flash("메모를 수정했습니다.","success")
    except ValueError as error:
        if request.headers.get("Accept")=="application/json":
            return {"message":str(error)},400
        flash(str(error),"error")
    return redirect(url_for("tab1_regulation.index",country=project["country"],project_id=project["id"],product_id=product_id,_anchor="product-notes"))


@bp.post("/products/<product_id>/notes/<note_id>/delete")
@login_required
def delete_note(product_id,note_id):
    product=store.product_for(g.user["id"],product_id)
    project=store.project_for(g.user["id"],product["project_id"])
    store.delete_note(g.user["id"],product_id,note_id)
    if request.headers.get("Accept")=="application/json":
        return {"deleted":note_id}
    flash("메모를 삭제했습니다.","success")
    return redirect(url_for("tab1_regulation.index",country=project["country"],project_id=project["id"],product_id=product_id,_anchor="product-notes"))


@bp.post("/projects/<project_id>/bookmarks")
@login_required
def bookmark(project_id):
    try:
        store.save_bookmark(g.user["id"],project_id,request.form.get("kind",""),request.form.get("title",""),request.form.get("url",""))
        flash("관심 정보에 저장했습니다.","success")
    except ValueError as error:
        flash(str(error),"error")
    return redirect(safe_next(request.form.get("next")))

@bp.get("/projects/<project_id>/bookmarks")
@login_required
def bookmarks(project_id):
    return render_template("platform_core/bookmarks.html",project=store.project_for(g.user["id"],project_id),bookmarks=store.bookmarks_for(g.user["id"],project_id))

@bp.post("/projects/<project_id>/bookmarks/<bookmark_id>/delete")
@login_required
def delete_bookmark(project_id,bookmark_id):
    from .services.database import get_db
    store.project_for(g.user["id"],project_id)
    with get_db() as db:
        db.execute("DELETE FROM bookmarks WHERE id=? AND project_id=?",(bookmark_id,project_id))
    return redirect(url_for("platform_core.bookmarks",project_id=project_id))

@bp.get("/api/projects/<project_id>")
@login_required
def project_api(project_id):
    return store.export_project(g.user["id"],project_id)

@bp.post("/projects/<project_id>/delete")
@login_required
def delete_project(project_id):
    store.delete_project(g.user["id"],project_id)
    flash("프로젝트를 삭제했습니다.","success")
    return redirect(url_for("platform_core.projects"))

