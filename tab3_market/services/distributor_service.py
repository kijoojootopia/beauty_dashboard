from flask import current_app
from platform_core.services.data_loader import read_data

def candidates(country,product,member_state="",live=True):
    from platform_core.services.country_service import destination
    from platform_core.integrations.http_client import setting,IntegrationError
    target=destination(country,member_state)
    if country in {"eu","asean"} and not member_state:
        return {"state":"data_pending","items":[],"message":"실제 목적 회원국을 선택해 주세요."}
    if live and setting("OPENAI_API_KEY"):
        from ..integrations.openai_client import fetch
        try: return fetch(target["name"],(product or {}).get("product_type",""))
        except IntegrationError as error: return {"state":"data_error","items":[],"message":str(error)}

    data=read_data(current_app.config["MARKET_DATA_ROOT"],country,"distributors.json")
    result=[]
    for row in data["data"]:
        if any(not isinstance(row.get(key,[]),list) or any(not isinstance(v,str) for v in row.get(key,[])) for key in ("product_types","channels","brands")):
            return {"state":"data_error","message":"유통사의 제품 유형·채널·브랜드는 문자열 배열이어야 합니다.","items":[]}
        if not row.get("name") or not row.get("source_url") or not row.get("verified_at"):
            continue
        categories=row.get("product_types",[])
        match=bool(product and product["product_type"] in categories)
        result.append({**row,"matched":match,"reason":"등록 자료의 취급 제품 유형이 일치합니다." if match else "등록 자료를 바탕으로 검토할 후보입니다."})
    result.sort(key=lambda r:not r["matched"])
    return {"state":data["state"] if data["state"]!="ready" or result else "data_pending","items":result,"message":data["message"]}
