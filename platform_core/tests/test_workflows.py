import json
import sqlite3
import pytest
from urllib.parse import urlsplit,parse_qs
from conftest import post,signup,write_json
from platform_core.services.database import get_db

def test_all_country_tabs_render(client):
    for country in ["eac","eu","uae","us","jp","cn","asean"]:
        for tab in ["regulation","customs","market"]:
            assert client.get(f"/beauty/{country}/{tab}").status_code==200
    assert client.get("/beauty/invalid/regulation").status_code==404

def test_csrf_required_and_password_hashed(app,client):
    assert client.post("/register",data={"email":"x"}).status_code==400
    signup(client)
    with app.app_context():
        user=get_db().execute("SELECT * FROM users").fetchone()
        assert user["password_hash"]!="a-long-test-password"
        assert user["password_hash"].startswith("scrypt:")

def test_snapshots_products_tasks_and_restart(app,client,owned):
    pid,product_id=owned
    before=client.get(f"/api/projects/{pid}").json
    post(client,f"/projects/{pid}/products/analyze",{"name":"수정 크림","product_type":"leave_on","hs_code":"330499","product_id":product_id,"inci_name":"Test Limited","cas_no":"","concentration":"2"})
    after=client.get(f"/api/projects/{pid}").json
    records=after["products"][0]["analyses"]
    assert len(records)==2
    assert records[0]["snapshot"]["results"][0]["result"]=="부적합"
    assert records[1]["snapshot"]==before["products"][0]["analyses"][0]["snapshot"]
    post(client,f"/projects/{pid}/products/analyze",{"name":"두 번째 제품","product_type":"rinse_off","inci_name":"Water","cas_no":"","concentration":"80"})
    assert len(client.get(f"/api/projects/{pid}").json["products"])==2
    post(client,f"/products/{product_id}/tasks",{"task_id":"test-task","completed":"1"})
    post(client,f"/products/{product_id}/notes",{"notes":"제품별 메모"})
    assert client.get(f"/beauty/jp/regulation?project_id={pid}&product_id={product_id}").status_code==200
    assert client.get(f"/beauty/jp/regulation?project_id={pid}&edit={product_id}").status_code==200
    assert client.get(f"/beauty/jp/customs?project_id={pid}").status_code==200
    assert client.get(f"/beauty/jp/market?project_id={pid}").status_code==200
    from platform_core.app_factory import create_app
    restarted=create_app({key:app.config[key] for key in ["TESTING","DATABASE","SECRET_KEY","REGULATION_DATA_ROOT","CUSTOMS_DATA_ROOT","MARKET_DATA_ROOT"]})
    other=restarted.test_client()
    post(other,"/login",{"email":"owner@example.test","password":"a-long-test-password"})
    data=other.get(f"/api/projects/{pid}").json
    p=next(p for p in data["products"] if p["id"]==product_id)
    assert p["note_list"][0]["content"]=="제품별 메모" and p["task_states"]["test-task"] is True

def test_owner_isolation_every_write_and_read(app,client,owned):
    pid,product_id=owned
    stranger=app.test_client()
    signup(stranger,"stranger@example.test")
    for path in [f"/api/projects/{pid}",f"/projects/{pid}/export",f"/projects/{pid}/bookmarks",f"/beauty/jp/regulation?project_id={pid}"]:
        assert stranger.get(path).status_code==404
    for path,data in [(f"/products/{product_id}/notes",{"notes":"hijack"}),(f"/products/{product_id}/reanalyze",{}),(f"/products/{product_id}/tasks",{"task_id":"test-task","completed":"1"}),(f"/projects/{pid}/copy",{"name":"copy","country":"us"}),(f"/projects/{pid}/products/analyze",{}),(f"/projects/{pid}/bookmarks",{})]:
        assert post(stranger,path,data).status_code==404
    assert app.test_client().get(f"/api/projects/{pid}").status_code==401

def test_copy_and_bookmarks_and_export(client,owned):
    pid,product_id=owned
    r=post(client,f"/projects/{pid}/copy",{"name":"미국 복사","country":"us"})
    target=parse_qs(urlsplit(r.location).query)["project_id"][0]
    copy=client.get(f"/api/projects/{target}").json
    assert copy["project"]["country"]=="us"
    assert copy["products"][0]["analyses"]==[] and copy["products"][0]["task_states"]=={}
    assert copy["products"][0]["id"]!=product_id
    data={"title":"테스트 뉴스","kind":"news","url":"https://example.test/article"}
    post(client,f"/projects/{pid}/bookmarks",data)
    post(client,f"/projects/{pid}/bookmarks",data)
    assert len(client.get(f"/api/projects/{pid}").json["bookmarks"])==1
    response=client.get(f"/projects/{pid}/export")
    assert response.headers["Content-Disposition"].startswith("attachment;")
    assert "password" not in response.text

def test_copy_failure_rolls_back(tmp_path):
    from platform_core.app_factory import create_app
    from platform_core.services.auth_service import register
    from platform_core.services import project_service as store

    app = create_app({"TESTING": True, "SECRET_KEY": "tests-only-key",
                      "DATABASE": str(tmp_path / "copy.sqlite3")})
    with app.app_context():
        user_id = register("copy@example.test", "복사 테스트", "a-long-test-password")
        source_id = store.create_project(user_id, "원본", "jp")
        for name in ("합성 제품 A", "합성 제품 B"):
            store.save_product_analysis(user_id, source_id, {
                "name": name, "product_type": "leave_on",
                "ingredients": [{"inci_name": "Test Ingredient", "concentration": 1}],
            }, {"state": "data_pending"})

        db = get_db()
        tables = ("projects", "products", "analyses")
        before = {table: [tuple(row) for row in db.execute(f"SELECT * FROM {table}")]
                  for table in tables}
        # 첫 제품 저장 후 두 번째 제품에서 실제 DB 오류를 발생시킵니다.
        db.execute("""CREATE TEMP TRIGGER fail_second_product BEFORE INSERT ON products
            WHEN (SELECT count(*) FROM products WHERE project_id=NEW.project_id)=1
            BEGIN SELECT RAISE(ABORT, 'test copy failure'); END""")
        with pytest.raises(sqlite3.IntegrityError, match="test copy failure"):
            store.copy_project(user_id, source_id, "실패할 복사", "us", "")

        for table in tables:
            assert [tuple(row) for row in db.execute(f"SELECT * FROM {table}")] == before[table]
        assert not db.in_transaction

        db.execute("DROP TRIGGER fail_second_product")
        copied_id = store.copy_project(user_id, source_id, "재시도", "us", "")
        assert len(store.products_for(user_id, copied_id)) == 2
        assert len(store.products_for(user_id, source_id)) == 2


def test_invalid_payload_and_data_preserve_previous(client,owned):
    pid,product_id=owned
    r=post(client,f"/projects/{pid}/products/analyze",{"name":"bad","product_type":"leave_on","inci_name":"A","cas_no":"","concentration":"NaN","product_id":product_id})
    assert r.status_code==400
    assert len(client.get(f"/api/projects/{pid}").json["products"][0]["analyses"])==1

def test_eu_requires_member_and_login_preserves_country(client):
    r=client.get("/projects?country=eu")
    assert "country%3Deu" in r.location or "country%3Deu" in r.location.replace("%253D","%3D")
    signup(client)
    r=post(client,"/projects",{"country":"eu","name":"EU 프로젝트"})
    assert "EU 수출 목적 회원국" in r.text
    r=post(client,"/projects",{"country":"eu","name":"프랑스 수출","member_state":"FR"})
    assert r.status_code==302

def test_open_redirect_rejected_and_logout_is_post(client):
    signup(client)
    post(client,"/logout")
    r=post(client,"/login",{"email":"owner@example.test","password":"a-long-test-password","next":"//evil.example"})
    assert r.location=="/projects"
    assert client.get("/logout").status_code==405

def test_populated_data_renders_all_tabs(app,client,owned):
    pid,product_id=owned
    customs=app.config["CUSTOMS_DATA_ROOT"]
    market=app.config["MARKET_DATA_ROOT"]
    regulation=app.config["REGULATION_DATA_ROOT"]
    write_json(customs/"jp/tariffs.json",[{"origin":"KR","hs_code":"330499","rate":0,"rate_unit":"%","rate_type":"TEST ONLY","source_url":"https://example.test","as_of":"2025-01-01"}])
    write_json(customs/"exchange_rates.json",{"as_of":"2025-01-01","source":"TEST ONLY","rates":[{"currency":"JPY","krw_rate":900,"unit":100}]})
    row={"period":"2024","reporter":"JP","coverage":"TEST annual","hs_scope":"3304","hs_version":"2022","unit":"USD","source":"TEST ONLY","total_imports":100,"korean_imports":20,"korea_exports":30,"export_reporter":"KR","export_source":"TEST ONLY"}
    write_json(market/"jp/trade_statistics.json",{"series":[row,{**row,"period":"2025","previous_period":"2024","total_imports":120}]})
    write_json(market/"jp/distributors.json",[{"name":"합성 검증용 기업","source_url":"https://example.test","verified_at":"2025-01-01","product_types":["leave_on"],"channels":["TEST"],"brands":[]}])
    write_json(market/"jp/news.json",[{"title":"합성 검증 기사","url":"https://example.test","source":"TEST ONLY"}])
    write_json(regulation/"jp/regulation_updates.json",[{"title":"합성 검증 공지","scope":"administrative","ingredients":[],"product_types":[],"url":"https://example.test"}])
    write_json(market/"korea/export_overview.json",{"period":"2025","previous_period":"2024","unit":"USD","source":"TEST ONLY","total_exports":120,"previous_exports":100,"series":[{"period":"2025","value":120}],"rankings":[{"country":"jp","name":"일본","value":20}]})
    assert client.get("/beauty").status_code==200
    for tab in ["regulation","customs","market"]:
        response=client.get(f"/beauty/jp/{tab}?project_id={pid}&product_id={product_id}")
        assert response.status_code==200
    response=post(client,f"/beauty/jp/customs?project_id={pid}",{"action":"exchange","amount":"900","from_currency":"KRW","to_currency":"JPY"})
    assert response.status_code==200 and "100.00" in response.text
