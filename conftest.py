import json
from pathlib import Path
import shutil
import pytest
from platform_core.app_factory import create_app

@pytest.fixture
def app(tmp_path):
    root=Path(__file__).parent
    for module,target in [("tab1_regulation/data","regulation"),("tab2_customs/data","customs"),("tab3_market/data/export","market")]:
        shutil.copytree(root/module,tmp_path/target)
    return create_app({"TESTING":True,"SECRET_KEY":"tests-only-key", "DATABASE":str(tmp_path/"test.sqlite3"),
        "REGULATION_DATA_ROOT":tmp_path/"regulation","CUSTOMS_DATA_ROOT":tmp_path/"customs","MARKET_DATA_ROOT":tmp_path/"market"})

@pytest.fixture
def client(app):
    return app.test_client()

def post(client,path,data=None,**kwargs):
    client.get("/login")
    with client.session_transaction() as session:
        token=session["csrf_token"]
    return client.post(path,data={**(data or {}),"csrf_token":token},**kwargs)

def signup(client,email="owner@example.test"):
    return post(client,"/register",{"email":email,"name":"테스트 사용자","password":"a-long-test-password","password_confirm":"a-long-test-password"})

def write_json(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False),encoding="utf-8")

@pytest.fixture
def rules(app):
    root=app.config["REGULATION_DATA_ROOT"]/"jp"
    # 합성 검증 데이터. 실제 규제나 성분을 의미하지 않습니다.
    write_json(root/"prohibited_ingredients.json",[{"inci_name":"Test Banned","cas_no":"111-11-1","product_type_scope":"ALL","conditions":"","max_concentration":0}])
    write_json(root/"restricted_ingredients.json",[{"inci_name":"Test Limited","cas_no":"222-22-2","product_type_scope":"ALL","conditions":"","max_concentration":1.0}])
    write_json(root/"metadata.json",{"version":"TEST-ONLY","source":"합성 테스트 데이터"})
    write_json(root/"pipeline_checklist.json",[{"task_id":"test-task","stage_step":1,"task_name":"테스트 서류","required_doc":"규격서(성분, 함량), 기타 자료","estimated_days":None,"guide_url":"https://example.test","is_mandatory":True}])
    return root

@pytest.fixture
def owned(client,rules):
    from urllib.parse import urlsplit,parse_qs
    signup(client)
    response=post(client,"/projects",{"name":"테스트 일본 프로젝트","country":"jp"})
    pid=parse_qs(urlsplit(response.location).query)["project_id"][0]
    response=post(client,f"/projects/{pid}/products/analyze",{"name":"테스트 크림","product_type":"leave_on","hs_code":"330499","inci_name":"Test Limited","cas_no":"","concentration":"0.5"})
    product_id=parse_qs(urlsplit(response.location).query)["product_id"][0]
    return pid,product_id
