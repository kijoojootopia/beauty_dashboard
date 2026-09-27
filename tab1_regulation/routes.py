from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from platform_core.services.auth_service import login_required
from platform_core.services.workspace_service import workspace_context
from platform_core.services import project_service as store
from .services.ingredient_parser import parse_csv, parse_text, normalize_row
from .services.screening_service import analyze
from .services.regulation_loader import load_regulations
from .services.roadmap_service import apply_legacy_document_states, completed_task_ids, load_roadmap
from .services.regulation_feed import load_feed

bp=Blueprint("tab1_regulation",__name__,template_folder="templates",static_folder="static",static_url_path="/regulation-assets")
PRODUCT_TYPES={"leave_on":"스킨케어 · 씻어내지 않음","rinse_off":"클렌저 · 씻어냄","lip":"립 제품","eye":"눈 주위 제품","sunscreen":"선케어","other":"기타 · 범위 확인 필요"}

@bp.get("/beauty/<country>/regulation")
def index(country):
    try:
        ctx=workspace_context(country)
    except ValueError:
        abort(404)
    from tab3_market.services.market_service import market_summary
    cards=[]
    for product in ctx["products"]:
        history=store.analyses_for(g.user["id"],product["id"])
        cards.append({"product":product,"history":history,"latest":history[0] if history else None})
    selected=ctx["selected_product"]
    roadmap=load_roadmap(country,selected["product_type"] if selected else None)
    task_states=store.tasks_for(g.user["id"],selected["id"]) if selected else {}
    for task_data in roadmap["tasks"]:
        apply_legacy_document_states(task_data,task_states)
    completed_stages=completed_task_ids(roadmap["tasks"],task_states)
    editing=None
    if request.args.get("edit"):
        if not g.user:
            abort(401)
        editing=store.product_for(g.user["id"],request.args["edit"])
        if not ctx["project"] or editing["project_id"]!=ctx["project"]["id"]:
            abort(404)
    return render_template("tab1_regulation/index.html",**ctx,tab="regulation",cards=cards,editing=editing,
        product_types=PRODUCT_TYPES,roadmap=roadmap,task_states=task_states,completed_stages=completed_stages,
        notes=store.notes_for(g.user["id"],selected["id"]) if selected else [],dataset=load_regulations(country),feed=load_feed(country,selected),summary=market_summary(country,ctx["member_state"],live=False))

@bp.post("/projects/<project_id>/products/analyze")
@login_required
def save_analysis(project_id):
    project=store.project_for(g.user["id"],project_id)
    try:
        if request.form.get("product_type") not in PRODUCT_TYPES:
            raise ValueError("제품 유형을 선택해 주세요.")
        uploaded=request.files.get("ingredients_csv")
        if uploaded and uploaded.filename:
            if not uploaded.filename.lower().endswith(".csv"):
                raise ValueError("UTF-8 CSV 파일을 선택해 주세요.")
            try:
                ingredients=parse_csv(uploaded.read())
            except UnicodeError:
                raise ValueError("CSV를 UTF-8로 저장한 후 다시 올려주세요.") from None
        elif request.form.get("ingredients_text","").strip():
            ingredients=parse_text(request.form["ingredients_text"])
        else:
            ingredients=[]
            names=request.form.getlist("inci_name")
            cases=request.form.getlist("cas_no")
            amounts=request.form.getlist("concentration")
            if not len(names)==len(cases)==len(amounts):
                raise ValueError("성분 입력 행을 확인해 주세요.")
            for name,cas,amount in zip(names,cases,amounts):
                if name.strip() or cas.strip() or amount.strip():
                    ingredients.append(normalize_row({"inci_name":name,"cas_no":cas,"concentration":amount}))
        if not ingredients or len(ingredients)>500:
            raise ValueError("성분을 1~500개 입력해 주세요.")
        if sum(r["concentration"] or 0 for r in ingredients)>100.000001:
            raise ValueError("입력한 배합량 합계가 100%를 초과합니다.")
        result=analyze(project["country"],ingredients,request.form["product_type"])
        if result["state"]=="data_error":
            raise ValueError(result["message"])
        product_id=store.save_product_analysis(g.user["id"],project_id,{"name":request.form.get("name",""),"product_type":request.form["product_type"],"hs_code":request.form.get("hs_code",""),"ingredients":ingredients},result,request.form.get("product_id") or None)
        flash("제품과 새 분석 기록을 저장했습니다." if result["state"]=="ready" else "제품을 저장했습니다. 규제 데이터를 등록한 뒤 재분석해 주세요.","success")
        return redirect(url_for("tab1_regulation.index",country=project["country"],project_id=project_id,product_id=product_id))
    except ValueError as error:
        flash(str(error),"error")
        # 실패한 처방을 쿠키/URL에 담지 않습니다. 성공 시에만 DB에 저장합니다.
        return render_template("tab1_regulation/input_error.html",message=str(error),project=project),400

@bp.post("/products/<product_id>/reanalyze")
@login_required
def reanalyze(product_id):
    product=store.product_for(g.user["id"],product_id)
    project=store.project_for(g.user["id"],product["project_id"])
    result=analyze(project["country"],product["ingredients"],product["product_type"])
    if result["state"]=="data_error":
        flash(result["message"],"error")
    else:
        store.save_product_analysis(g.user["id"],project["id"],product,result,product_id)
        flash("새 분석 이력을 저장했습니다. 기존 결과는 보존됩니다.","success")
    return redirect(url_for("tab1_regulation.index",country=project["country"],project_id=project["id"],product_id=product_id))

@bp.post("/products/<product_id>/delete")
@login_required
def delete_product(product_id):
    product=store.product_for(g.user["id"],product_id)
    project=store.project_for(g.user["id"],product["project_id"])
    store.delete_product(g.user["id"],product_id)
    flash("제품을 삭제했습니다.","success")
    return redirect(url_for("tab1_regulation.index",country=project["country"],project_id=project["id"]))

@bp.post("/products/<product_id>/tasks")
@login_required
def task(product_id):
    product=store.product_for(g.user["id"],product_id)
    project=store.project_for(g.user["id"],product["project_id"])
    g.destination_member=project["member_state"]
    roadmap=load_roadmap(project["country"],product["product_type"])
    anchors={}
    for index,task_data in enumerate(roadmap["tasks"],1):
        anchor=f"task-{index}"
        anchors[task_data["task_id"]]=anchor
        anchors.update({doc["key"]:anchor for doc in task_data["documents"]})
    key=request.form.get("task_id")
    if key not in anchors:
        abort(400,description="현재 로드맵에 없는 항목입니다.")
    task_data=next(task_data for task_data in roadmap["tasks"] if key==task_data["task_id"] or any(document["key"]==key for document in task_data["documents"]))
    if key!=task_data["task_id"]:
        task_states=store.tasks_for(g.user["id"],product_id)
        if apply_legacy_document_states(task_data,task_states):
            for document in task_data["documents"]:
                if document["key"]!=key:
                    store.save_task(g.user["id"],product_id,document["key"],True)
    store.save_task(g.user["id"],product_id,key,request.form.get("completed")=="1")
    if request.headers.get("X-Requested-With")=="XMLHttpRequest" or request.accept_mimetypes.best == "application/json":
        from flask import jsonify
        task_states=store.tasks_for(g.user["id"],product_id)
        return jsonify(
            states={state_key:task_states.get(state_key,False) for state_key in [task_data["task_id"], *(doc["key"] for doc in task_data["documents"])]},
            task_completed=task_data["task_id"] in completed_task_ids([task_data],task_states),
        )
    return redirect(url_for("tab1_regulation.index",country=project["country"],project_id=project["id"],product_id=product_id,_anchor=anchors[key]))

@bp.post("/api/ingredients/preview")
@login_required
def ingredient_preview():
    import json
    from .services.ingredient_parser import read_table,infer_columns,table_rows
    try:
        upload=request.files.get("ingredients_csv")
        if not upload or not upload.filename: raise ValueError("CSV 파일을 선택해 주세요.")
        table=read_table(upload.read())
        header,mapping=infer_columns(table,use_ai=request.form.get("use_ai")=="1")
        if request.form.get("mapping"):
            mapping=json.loads(request.form["mapping"])
            if not isinstance(mapping,dict): raise ValueError("열 선택을 확인해 주세요.")
            header=request.form.get("has_header")=="1"
        ingredients=[];message=""
        try: ingredients=table_rows(table,header,mapping)
        except ValueError as error: message=str(error)
        return {"has_header":header,"mapping":mapping,"columns":table[0] if header else ["열 "+str(i+1) for i in range(len(table[0]))],"ingredients":ingredients,"message":message,"sample":table[:6]}
    except (ValueError,TypeError) as error:
        return {"message":str(error)},400
