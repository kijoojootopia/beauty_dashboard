from flask import current_app
from platform_core.services.data_loader import read_data

def load_news(country,member_state="",live=True):
    from platform_core.services.country_service import destination
    from platform_core.integrations.http_client import setting,IntegrationError
    target=destination(country,member_state)
    if country in {"eu","asean"} and not member_state:
        return {"state":"data_pending","items":[],"message":"실제 목적 회원국을 선택해 주세요."}
    if live and setting("KOTRA_API_KEY"):
        from ..integrations.kotra_client import fetch
        try: return fetch(target["name"])
        except IntegrationError as error: return {"state":"data_error","items":[],"message":str(error)}

    data=read_data(current_app.config["MARKET_DATA_ROOT"],country,"news.json")
    return {"state":data["state"],"items":[r for r in data["data"] if r.get("title") and r.get("url")],"message":data["message"]}
