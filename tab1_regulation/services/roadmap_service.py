import hashlib
from flask import current_app
from platform_core.services.data_loader import read_data

def load_roadmap(country, product_type=None):
    data=read_data(current_app.config["REGULATION_DATA_ROOT"],country,"pipeline_checklist.json",expected=dict if country=="us" else list)
    tasks=[]
    seen=set()
    try:
        rows=data["data"]
        scope_label=None
        if country=="us":
            branch="OTC" if product_type=="sunscreen" else "GENERAL"
            scope_label="OTC · 선케어" if branch=="OTC" else "일반 화장품"
            rows=rows.get(branch,[]) if data["state"]=="data_pending" else rows[branch]
            if not isinstance(rows,list) or any(not isinstance(row,dict) for row in rows):
                raise ValueError()
        for row in sorted(rows,key=lambda r:float(r["stage_step"])):
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
            legacy_document=row.get("legacy_required_doc")
            if legacy_document is not None and not isinstance(legacy_document,str):
                raise ValueError()
            documents=[{"label":d,"key":tid+":doc:"+hashlib.sha256(d.encode()).hexdigest()[:16]} for d in docs if d]
            task={**row,"task_id":tid,"documents":documents,"duration_label":"기간 확인 필요" if row.get("estimated_days") is None else f'{row["estimated_days"]}일'}
            if legacy_document:
                task["legacy_document_key"]=tid+":doc:"+hashlib.sha256(legacy_document.encode()).hexdigest()[:16]
            tasks.append(task)
    except (KeyError,ValueError,TypeError):
        return {"state":"data_error","message":"로드맵 단계·작업 ID·문서 구조를 확인해 주세요.","tasks":[]}
    return {"state":data["state"],"message":data["message"],"tasks":tasks,"scope_label":scope_label}

def apply_legacy_document_states(task, task_states):
    legacy_key=task.get("legacy_document_key")
    document_keys=[document["key"] for document in task["documents"]]
    if not legacy_key or not document_keys or not task_states.get(legacy_key) or any(key in task_states for key in document_keys):
        return False
    task_states.update({key:True for key in document_keys})
    return True

def completed_task_ids(tasks, task_states):
    completed=set()
    for task in tasks:
        documents=task["documents"]
        if task_states.get(task["task_id"]) or (documents and all(task_states.get(document["key"]) for document in documents)):
            completed.add(task["task_id"])
    return completed
