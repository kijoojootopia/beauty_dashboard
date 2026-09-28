from flask import Blueprint,abort,render_template
from platform_core.routes import export_overview_context
from platform_core.services.workspace_service import workspace_context
from .services.market_service import market_summary,overview
from .services.distributor_service import candidates
from .services.news_service import load_news

bp=Blueprint("tab3_market",__name__,template_folder="templates",static_folder="static",static_url_path="/market-assets")

@bp.get("/beauty/<country>/market")
def index(country):
    try:
        ctx=workspace_context(country)
    except ValueError:
        abort(404)
    return render_template("tab3_market/index.html",**ctx,tab="market",market=market_summary(country,ctx["member_state"],live=False),distributors=candidates(country,ctx["selected_product"],ctx["member_state"],live=False),news=load_news(country,ctx["member_state"],live=False))

@bp.get("/api/market/<country>/summary")
def summary_api(country):
    try:
        ctx=workspace_context(country)
        return market_summary(country,ctx["member_state"])
    except ValueError:
        abort(404)

@bp.get("/api/exports/overview")
def overview_api():
    return overview(include_rankings=True)

@bp.get("/api/market/<country>/<section>/fragment")
def live_section(country,section):
    if section not in {"statistics","distributors","news"}: abort(404)
    try: ctx=workspace_context(country)
    except ValueError: abort(404)
    data={}
    if section=="statistics": data["market"]=market_summary(country,ctx["member_state"])
    elif section=="distributors": data["distributors"]=candidates(country,ctx["selected_product"],ctx["member_state"])
    else: data["news"]=load_news(country,ctx["member_state"])
    return render_template("tab3_market/"+section+".html",**ctx,**data)

@bp.get("/api/exports/fragment")
def overview_fragment():
    return export_fragment("export_stats.html")

@bp.get("/api/exports/rankings-fragment")
def overview_rankings_fragment():
    return export_fragment("export_rankings.html",include_rankings=True)

@bp.get("/api/exports/rank-card")
def overview_rank_card():
    return export_fragment("export_rank_card.html",include_rankings=True)


def export_fragment(template,include_rankings=False):
    context=export_overview_context(include_rankings=include_rankings)
    data=context['overview']
    html=render_template("platform_core/"+template,**context)
    if data.get('state')=='data_error' or (include_rankings and data.get('ranking_state')=='data_error'):
        # The integration cache retains failures for 60 seconds.
        return html,503,{'Retry-After':'60'}
    return html
