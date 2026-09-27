import pytest
from conftest import write_json,post
from tab1_regulation.services.ingredient_parser import parse_csv,parse_text,percentage
from tab1_regulation.services.screening_service import screen_rows,analyze
from tab1_regulation.services.regulation_loader import load_regulations
from tab1_regulation.services.roadmap_service import apply_legacy_document_states,completed_task_ids,load_roadmap

def test_csv_and_text_preserve_comma_names():
    rows=parse_csv('inci_name,cas_no,concentration\n"1,2-Hexanediol",6920-22-5,0.5\n')
    assert rows[0]["inci_name"]=="1,2-Hexanediol"
    assert parse_text('1,2-Hexanediol\t0.5')[0]["concentration"]==0.5

@pytest.mark.parametrize("value",["NaN","Infinity",-1,101,True,"not-a-number"])
def test_invalid_percent_rejected(value):
    with pytest.raises(ValueError):percentage(value)

def test_limit_scope_cas_and_unknown():
    rule={"inci_name":"TEST","cas_no":"111-11-1","product_type_scope":"ALL","max_concentration":1}
    assert screen_rows([{"inci_name":"test","concentration":1}],[],[rule])[0]["result"]=="적합"
    assert screen_rows([{"inci_name":"test","concentration":1.1}],[],[rule])[0]["result"]=="부적합"
    assert screen_rows([{"inci_name":"test"}],[],[rule])[0]["result"]=="확인 필요"
    assert screen_rows([{"inci_name":"test","cas_no":"999-99-9"}],[],[rule])[0]["result"]=="확인 필요"
    assert screen_rows([{"inci_name":"test","concentration":0.1}],[rule],[])[0]["result"]=="부적합"
    scoped={**rule,"product_type_scope":"rinse only","applicable_product_scopes":["rinse_off"]}
    assert screen_rows([{"inci_name":"test"}],[scoped],[],"leave_on")[0]["result"]=="해당 없음"


def test_three_identifier_paths_and_unidentified_rules():
    rule={"inci_name":"Test Acid","kr_name":"테스트산","cas_no":"111-11-1","product_type_scope":"ALL","max_concentration":1}
    cas_only=screen_rows([{"cas_no":"111-11-1","concentration":0.5}],[],[rule])[0]
    assert (cas_only["result"],cas_only["resolved_name"])==("적합","Test Acid")
    name_only=screen_rows([{"inci_name":"테스트산","concentration":0.5}],[],[rule])[0]
    assert (name_only["result"],name_only["resolved_cas"])==("적합","111-11-1")
    assert screen_rows([{"inci_name":"Test Acid","cas_no":"111-11-1","concentration":0.5}],[],[rule])[0]["result"]=="적합"
    assert screen_rows([{"inci_name":"Wrong Name","cas_no":"111-11-1","concentration":0.5}],[],[rule])[0]["result"]=="확인 필요"
    other={**rule,"inci_name":"Other Acid","cas_no":"222-22-2"}
    assert screen_rows([{"inci_name":"Test Acid","cas_no":"111-11-1"}],[rule,other],[])[0]["result"]=="부적합"
    assert screen_rows([{"inci_name":"Test Acid","cas_no":"222-22-2"}],[rule,other],[])[0]["result"]=="확인 필요"
    assert screen_rows([{"inci_name":"Test Acid"}],[],[rule,{**rule,"cas_no":"333-33-3"}])[0]["result"]=="확인 필요"
    assert screen_rows([{"cas_no":"111-11-1"}],[],[rule,{**rule,"inci_name":"Another Acid"}])[0]["result"]=="확인 필요"
    assert screen_rows([{"inci_name":"Test Acdi","concentration":0.5}],[],[rule])[0]["result"]=="확인 필요"
    assert screen_rows([{"inci_name":"Test Acdi","cas_no":"999-99-9","concentration":0.5}],[],[rule])[0]["result"]=="해당 없음"
    unidentified={"inci_name":"","cas_no":"","regulation_source":"Annex 1/10"}
    assert screen_rows([{"inci_name":"Water"}],[unidentified],[rule])[0]["result"]=="해당 없음"
    assert screen_rows([{"inci_name":"Test Acid","concentration":2}],[unidentified],[rule])[0]["result"]=="부적합"


def test_unidentified_rules_do_not_break_loader(app,rules):
    with app.app_context():
        write_json(rules/"prohibited_ingredients.json",[{"inci_name":"","cas_no":"","regulation_source":"Annex 1/10"}])
        dataset=load_regulations("jp")
        assert dataset["state"]=="ready"
        assert dataset["unidentified"]==[{"type":"금지","source":"Annex 1/10"}]
        result=analyze("jp",[{"inci_name":"Water"}])
        assert result["results"][0]["result"]=="해당 없음"

def test_natural_conditions_null_and_scope_need_review():
    base={"inci_name":"TEST","product_type_scope":"ALL","max_concentration":1}
    for rule in [{**base,"conditions":"예외 성분·합계량 조건"},{**base,"max_concentration":None},{**base,"product_type_scope":"원문 서술 범위"},{**base,"limit_basis":"group_total"}]:
        assert screen_rows([{"inci_name":"TEST","concentration":0.5}],[],[rule])[0]["result"]=="확인 필요"
    assert screen_rows([{"inci_name":"TEST"}],[{**base,"conditions":"특정 예외 존재"}],[])[0]["result"]=="확인 필요"

def test_duplicate_ingredients_cannot_bypass_limit():
    rule={"inci_name":"TEST","product_type_scope":"ALL","max_concentration":1}
    result=screen_rows([{"inci_name":"TEST","concentration":0.8},{"inci_name":"test","concentration":0.8}],[],[rule])
    assert all(r["result"]=="확인 필요" for r in result)

def test_malformed_unquoted_csv_is_rejected():
    with pytest.raises(ValueError,match="큰따옴표"):
        parse_csv('inci_name,concentration\n1,2-Hexanediol,0.5')

def test_empty_partial_and_broken_are_not_approval(app,rules):
    with app.app_context():
        write_json(app.config["REGULATION_DATA_ROOT"]/"us/prohibited_ingredients.json",[])
        write_json(app.config["REGULATION_DATA_ROOT"]/"us/restricted_ingredients.json",[])
        assert analyze("us",[{"inci_name":"Water"}])["state"]=="data_pending"
        assert analyze("jp",[{"inci_name":"Test Limited","concentration":0.5}])["state"]=="ready"
        write_json(rules/"restricted_ingredients.json",[])
        assert load_regulations("jp")["state"]=="data_pending"
        write_json(rules/"metadata.json",{"complete_lists":{"restricted":True}})
        assert load_regulations("jp")["state"]=="ready"
        (rules/"restricted_ingredients.json").write_text('{bad json')
        assert load_regulations("jp")["state"]=="data_error"
        (rules/"restricted_ingredients.json").unlink()
        assert load_regulations("jp")["state"]=="data_pending"

def test_roadmap_preserves_document_string(app,rules,client,owned):
    with app.app_context():
        roadmap=load_roadmap("jp")
    assert len(roadmap["tasks"][0]["documents"])==1
    assert roadmap["tasks"][0]["duration_label"]=="기간 확인 필요"
    key=roadmap["tasks"][0]["documents"][0]["key"]
    pid,product_id=owned
    response=post(client,f"/products/{product_id}/tasks",{"task_id":key,"completed":"1"})
    assert response.status_code==302
    assert response.location.endswith("#task-1")
    assert post(client,f"/products/{product_id}/tasks",{"task_id":"invented","completed":"1"}).status_code==400

def test_eu_split_documents_keep_legacy_completion(app):
    with app.app_context():
        roadmap=load_roadmap("eu")
    tasks={task["stage_step"]:task for task in roadmap["tasks"]}
    assert len(tasks[2]["documents"])==3
    assert len(tasks[3]["documents"])==1
    assert len(tasks[5]["documents"])==4
    assert tasks[6]["documents"]==[] and tasks[6]["guidance_text"]
    task=tasks[2]
    states={task["legacy_document_key"]:True}
    assert apply_legacy_document_states(task,states)
    assert all(states[document["key"]] for document in task["documents"])
    assert task["task_id"] in completed_task_ids([task],states)
    partial={task["legacy_document_key"]:True,task["documents"][0]["key"]:False}
    assert not apply_legacy_document_states(task,partial)


def test_product_delete_and_note_controls(app,client,owned):
    project_id,product_id=owned
    note=post(client,f"/products/{product_id}/notes",{"notes":"수정할 메모"},headers={"Accept":"application/json"}).json["note"]
    page=client.get(f"/beauty/jp/regulation?project_id={project_id}&product_id={product_id}")
    assert page.status_code==200
    assert f'/products/{product_id}/delete'.encode() in page.data
    assert f'/products/{product_id}/notes/{note["id"]}/update'.encode() in page.data
    assert f'/products/{product_id}/notes/{note["id"]}/delete'.encode() in page.data
    assert b'data-note-form' not in page.data

    assert client.get(f"/products/{product_id}/delete").status_code==405
    assert client.post(f"/products/{product_id}/delete").status_code==400
    response=post(client,f"/products/{product_id}/delete")
    assert response.status_code==302
    assert f"project_id={project_id}" in response.location
    assert "product_id=" not in response.location
    with app.app_context():
        from platform_core.services.database import get_db
        assert get_db().execute("SELECT count(*) FROM products WHERE id=?",(product_id,)).fetchone()[0]==0
        assert get_db().execute("SELECT count(*) FROM product_notes WHERE product_id=?",(product_id,)).fetchone()[0]==0
        assert get_db().execute("SELECT count(*) FROM projects WHERE id=?",(project_id,)).fetchone()[0]==1


def test_screening_export_downloads_excel_columns(client,owned):
    from io import BytesIO
    from xml.etree import ElementTree as ET
    from zipfile import ZipFile

    project_id,product_id=owned
    response=client.get(f"/projects/{project_id}/screening.xlsx")
    assert response.status_code==200
    assert response.mimetype=="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert ".xlsx" in response.headers["Content-Disposition"]
    with ZipFile(BytesIO(response.data)) as workbook:
        sheet=ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
    namespace={"x":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    values=[]
    for row in sheet.findall(".//x:sheetData/x:row",namespace):
        cells=[]
        for cell in row.findall("x:c",namespace):
            value=cell.find("x:is/x:t",namespace)
            if value is None:
                value=cell.find("x:v",namespace)
            cells.append(value.text if value is not None else "")
        values.append(cells)
    assert values[0]==["제품명","국가·권역","분석일","성분명(INCI)","CAS 번호","배합량(%)","규제 유형","판정 결과","상세 조건"]
    assert len(values)==2
    assert values[1][0]=="테스트 크림"
    assert values[1][3]=="Test Limited"
    assert values[1][5]=="0.5"
    assert values[1][7]=="적합"
    page=client.get(f"/beauty/jp/regulation?project_id={project_id}&product_id={product_id}")
    assert f'/projects/{project_id}/screening.xlsx'.encode() in page.data
