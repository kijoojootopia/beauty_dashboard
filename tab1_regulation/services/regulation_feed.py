from flask import current_app
from platform_core.services.data_loader import read_data
from .screening_service import norm

def load_feed(country,product):
    data=read_data(current_app.config["REGULATION_DATA_ROOT"],country,"regulation_updates.json")
    names={norm(i.get("inci_name")) for i in (product or {}).get("ingredients",[]) if i.get("inci_name")}
    cases={norm(i.get("cas_no")) for i in (product or {}).get("ingredients",[]) if i.get("cas_no")}
    items=[]
    all_items=[]
    for row in data["data"]:
        if any(not isinstance(row.get(key,[]),list) or any(not isinstance(v,str) for v in row.get(key,[])) for key in ("ingredients","product_types")):
            return {"state":"data_error","message":"공지의 ingredients와 product_types는 문자열 배열이어야 합니다.","items":[],"all_items":[]}
        if not row.get("title"):
            continue
        common=row.get("scope")=="administrative"
        ingredient_match=(names|cases)&{norm(x) for x in row.get("ingredients",[])}
        category_match=bool(product and product["product_type"] in row.get("product_types",[]))
        related=bool(product and (common or ingredient_match or category_match))
        reason="공통 행정 요건" if common else "입력 성분 일치" if ingredient_match else "제품 유형 일치" if category_match else "권역 공지"
        item={**row,"related":related,"reason":reason,"match_label":("관련 가능성" if row.get("uncertain") else "관련 공지") if related else "제품 관련성 미확인"}
        all_items.append(item)
        if related or not product:
            items.append(item)
    return {"state":data["state"],"message":data["message"],"items":items,"all_items":all_items}
