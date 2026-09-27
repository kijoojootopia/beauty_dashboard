import hashlib
from flask import current_app
from platform_core.services.data_loader import read_data

def load_roadmap(country):
    data=read_data(current_app.config["REGULATION_DATA_ROOT"],country,"pipeline_checklist.json")
    tasks=[]
    seen=set()
    try:
        for row in sorted(data["data"],key=lambda r:float(r["stage_step"])):
            tid=str(row["task_id"])
            if not tid or tid in seen or not row.get("task_name"):
                raise ValueError()
            seen.add(tid)
            docs=row.get("required_doc",[])
            if not isinstance(docs,(str,list)):
                raise ValueError()
            docs=docs if isinstance(docs,list) else [docs]
            if any(not isinstance(d,str) for d in docs):
                raise ValueError()
            documents=[{"label":d,"key":tid+":doc:"+hashlib.sha256(d.encode()).hexdigest()[:16]} for d in docs if d]
            tasks.append({**row,"task_id":tid,"documents":documents,"duration_label":"기간 확인 필요" if row.get("estimated_days") is None else f'{row["estimated_days"]}일'})
    except (KeyError,ValueError,TypeError):
        return {"state":"data_error","message":"로드맵 단계·작업 ID·문서 구조를 확인해 주세요.","tasks":[]}
    return {"state":data["state"],"message":data["message"],"tasks":tasks}
