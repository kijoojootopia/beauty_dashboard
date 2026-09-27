"""탭 모듈에서 호출하는 공통 저장 계약. 모든 접근은 user_id로 확인합니다."""
import json
import re
from uuid import uuid4
from flask import abort
from .database import get_db
from .auth_service import now
from .country_service import get_country, EU_MEMBERS, MEMBER_GROUPS

def project_for(user_id, project_id):
    row = get_db().execute("SELECT * FROM projects WHERE id=? AND user_id=?", (project_id,user_id)).fetchone()
    if row is None:
        abort(404)
    return dict(row)

def list_projects(user_id):
    return [dict(r) for r in get_db().execute("SELECT p.*, (SELECT count(*) FROM products WHERE project_id=p.id) AS product_count FROM projects p WHERE user_id=? ORDER BY created_at DESC",(user_id,))]

def create_project(user_id, name, country, member_state=""):
    get_country(country)
    if not name.strip() or len(name.strip())>100:
        raise ValueError("프로젝트명은 1~100자로 입력해 주세요.")
    if country in MEMBER_GROUPS and member_state not in MEMBER_GROUPS[country]:
        raise ValueError(("EU" if country=="eu" else "ASEAN")+" 수출 목적 회원국을 선택해 주세요.")
    pid=uuid4().hex
    with get_db() as db:
        db.execute("INSERT INTO projects VALUES(?,?,?,?,?,?)",(pid,user_id,name.strip(),country,member_state if country in MEMBER_GROUPS else "",now()))
    return pid

def unpack_product(row):
    result=dict(row)
    result["ingredients"]=json.loads(result["ingredients"])
    return result

def product_for(user_id, product_id):
    row=get_db().execute("SELECT p.* FROM products p JOIN projects j ON p.project_id=j.id WHERE p.id=? AND j.user_id=?",(product_id,user_id)).fetchone()
    if row is None:
        abort(404)
    return unpack_product(row)

def products_for(user_id, project_id):
    project_for(user_id, project_id)
    return [unpack_product(r) for r in get_db().execute("SELECT * FROM products WHERE project_id=? ORDER BY updated_at DESC",(project_id,))]

def analyses_for(user_id, product_id):
    product_for(user_id, product_id)
    return [{**dict(r),"snapshot":json.loads(r["snapshot"])} for r in get_db().execute("SELECT * FROM analyses WHERE product_id=? ORDER BY created_at DESC, rowid DESC",(product_id,))]

def save_product_analysis(user_id, project_id, payload, snapshot, product_id=None):
    project=project_for(user_id, project_id)
    if product_id and product_for(user_id,product_id)["project_id"]!=project_id:
        abort(404)
    name=str(payload.get("name","")).strip()
    hs=str(payload.get("hs_code","")).strip()
    if not 1<=len(name)<=100:
        raise ValueError("제품명은 1~100자로 입력해 주세요.")
    if hs and not re.fullmatch(r"\d{6,12}",hs):
        raise ValueError("HS 코드는 6~12자리 숫자로 입력해 주세요.")
    ingredients=payload["ingredients"]
    if not ingredients or len(ingredients)>500:
        raise ValueError("성분을 1~500개 입력해 주세요.")
    product_id=product_id or uuid4().hex
    recorded=now()
    full_snapshot={**snapshot,"product":{"name":name,"product_type":payload["product_type"],"hs_code":hs,"ingredients":ingredients},"country":project["country"],"member_state":project["member_state"],"recorded_at":recorded}
    with get_db() as db:
        db.execute("""INSERT INTO products(id,project_id,name,product_type,hs_code,ingredients,updated_at) VALUES(?,?,?,?,?,?,?)
         ON CONFLICT(id) DO UPDATE SET name=excluded.name,product_type=excluded.product_type,
         hs_code=excluded.hs_code,ingredients=excluded.ingredients,updated_at=excluded.updated_at""",
         (product_id,project_id,name,payload["product_type"],hs,json.dumps(ingredients,ensure_ascii=False),recorded))
        db.execute("INSERT INTO analyses VALUES(?,?,?,?)",(uuid4().hex,product_id,json.dumps(full_snapshot,ensure_ascii=False),recorded))
    return product_id

def tasks_for(user_id, product_id):
    product_for(user_id,product_id)
    return {r["task_id"]:bool(r["completed"]) for r in get_db().execute("SELECT * FROM task_states WHERE product_id=?",(product_id,))}

def save_task(user_id, product_id, task_id, completed):
    product_for(user_id,product_id)
    if not task_id or len(task_id)>200 or type(completed) is not bool:
        raise ValueError("체크리스트 값을 확인해 주세요.")
    with get_db() as db:
        db.execute("INSERT INTO task_states VALUES(?,?,?,?) ON CONFLICT(product_id,task_id) DO UPDATE SET completed=excluded.completed,updated_at=excluded.updated_at",(product_id,task_id,int(completed),now()))

def notes_for(user_id, product_id):
    product_for(user_id,product_id)
    return [dict(r) for r in get_db().execute("SELECT * FROM product_notes WHERE product_id=? ORDER BY created_at DESC,rowid DESC",(product_id,))]

def save_notes(user_id, product_id, notes):
    product_for(user_id, product_id)
    notes=notes.strip()
    if not notes or len(notes)>5000:
        raise ValueError("메모는 1~5,000자로 입력해 주세요.")
    note={"id":uuid4().hex,"product_id":product_id,"content":notes,"created_at":now()}
    with get_db() as db:
        db.execute("INSERT INTO product_notes VALUES(?,?,?,?)",tuple(note.values()))
    return note

def delete_project(user_id, project_id):
    project_for(user_id, project_id)
    with get_db() as db:
        for table in ("product_notes","task_states","analyses"):
            db.execute(f"DELETE FROM {table} WHERE product_id IN (SELECT id FROM products WHERE project_id=?)",(project_id,))
        db.execute("DELETE FROM bookmarks WHERE project_id=?",(project_id,))
        db.execute("DELETE FROM products WHERE project_id=?",(project_id,))
        db.execute("DELETE FROM projects WHERE id=? AND user_id=?",(project_id,user_id))

def copy_project(user_id, project_id, name, country, member_state):
    source=products_for(user_id,project_id)
    pid=create_project(user_id,name,country,member_state)
    with get_db() as db:
        for p in source:
            db.execute("INSERT INTO products VALUES(?,?,?,?,?,?,?,?)",(uuid4().hex,pid,p["name"],p["product_type"],p["hs_code"],json.dumps(p["ingredients"],ensure_ascii=False),"",now()))
    return pid

def bookmarks_for(user_id, project_id):
    project_for(user_id,project_id)
    return [dict(r) for r in get_db().execute("SELECT * FROM bookmarks WHERE project_id=? ORDER BY created_at DESC",(project_id,))]

def save_bookmark(user_id, project_id, kind, title, url):
    from urllib.parse import urlsplit
    project_for(user_id,project_id)
    parsed=urlsplit(url)
    if kind not in {"distributor","news","regulation"} or not title.strip() or len(title)>300 or len(url)>2000 or parsed.scheme not in {"https","http"} or not parsed.netloc:
        raise ValueError("저장할 정보의 제목과 웹 주소를 확인해 주세요.")
    with get_db() as db:
        db.execute("INSERT OR IGNORE INTO bookmarks VALUES(?,?,?,?,?,?)",(uuid4().hex,project_id,kind,title,url,now()))

def export_project(user_id, project_id):
    project=project_for(user_id,project_id)
    products=products_for(user_id,project_id)
    for p in products:
        p["note_list"]=notes_for(user_id,p["id"])
        p["analyses"]=analyses_for(user_id,p["id"])
        p["task_states"]=tasks_for(user_id,p["id"])
    return {"schema_version":1,"exported_at":now(),"project":project,"products":products,"bookmarks":bookmarks_for(user_id,project_id)}
