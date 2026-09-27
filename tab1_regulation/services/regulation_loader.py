import hashlib
import json
from flask import current_app
from platform_core.services.data_loader import read_data

def load_regulations(country, data_root=None):
    root=data_root or current_app.config["REGULATION_DATA_ROOT"]
    p=read_data(root,country,"prohibited_ingredients.json")
    r=read_data(root,country,"restricted_ingredients.json")
    m=read_data(root,country,"metadata.json",dict)
    if "data_error" in {p["state"],r["state"],m["state"]}:
        return {"state":"data_error","message":"규제 JSON 구조 또는 문법을 확인해 주세요.","prohibited":[],"restricted":[],"metadata":{}}
    # 한쪽 목록이 빈 경우 해당 목록의 검토 완료가 명시되어야 합니다.
    completeness=m["data"].get("complete_lists",{})
    if not isinstance(completeness,dict):
        return {"state":"data_error","message":"complete_lists는 객체여야 합니다.","prohibited":[],"restricted":[],"metadata":m["data"]}
    ready=all(v["data"] or (v["message"]=="데이터 준비 중" and completeness.get(k) is True) for k,v in (("prohibited",p),("restricted",r)))
    for rules in (p["data"],r["data"]):
        for row in rules:
            if not (row.get("inci_name") or row.get("cas_no")) or not isinstance(row.get("aliases",[]),list):
                return {"state":"data_error","message":"규칙에 성분명 또는 CAS가 필요하며 aliases는 배열이어야 합니다.","prohibited":[],"restricted":[],"metadata":m["data"]}
    digest=hashlib.sha256(json.dumps([p["data"],r["data"],m["data"]],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {"state":"ready" if ready else "data_pending","message":"" if ready else "규제 데이터 준비 중 · 금지·제한 목록을 모두 등록해 주세요.",
            "prohibited":p["data"],"restricted":r["data"],"metadata":m["data"],"data_hash":digest}
