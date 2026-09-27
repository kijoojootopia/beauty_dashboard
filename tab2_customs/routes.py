from flask import Blueprint, abort, render_template, request
from platform_core.services.workspace_service import workspace_context
from .services.customs_service import lookup_tariffs,load_customs,calculate_exchange,rates_dataset

bp=Blueprint("tab2_customs",__name__,template_folder="templates",static_folder="static",static_url_path="/customs-assets")

@bp.route("/beauty/<country>/customs",methods=["GET","POST"])
def index(country):
    try:
        ctx=workspace_context(country)
    except ValueError:
        abort(404)
    product=ctx["selected_product"] or {}
    hs=request.values.get("hs_code",product.get("hs_code",""))
    origin=request.values.get("origin","KR").upper()
    result=None
    exchange=None
    error=None
    try:
        if request.method=="POST" and request.form.get("action")=="exchange":
            exchange=calculate_exchange(request.form.get("amount",""),request.form.get("from_currency","KRW"),request.form.get("to_currency",ctx["destination"]["currency"]))
        if hs:
            result=lookup_tariffs(country,origin,hs)
    except ValueError as exc:
        error=str(exc)
    return render_template("tab2_customs/index.html",**ctx,tab="customs",result=result,hs_code=hs,origin=origin,error=error,exchange=exchange,customs=load_customs(country),rates=rates_dataset(),available_currencies=sorted({"KRW",ctx["destination"]["currency"]}|{r["currency"] for r in rates_dataset()["data"].get("rates",[])}))
