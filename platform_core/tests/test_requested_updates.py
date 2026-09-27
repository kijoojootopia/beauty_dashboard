import json
from urllib.parse import urlsplit,parse_qs
from conftest import post,signup
from platform_core.services.database import get_db,init_db
from platform_core.services.country_service import ASEAN_MEMBERS,COUNTRIES


def test_asean_members_migration_and_navigation(app,client):
    signup(client)
    assert len(COUNTRIES)==7 and len(ASEAN_MEMBERS)==10
    for country in ASEAN_MEMBERS:
        r=post(client,'/projects',{'name':'목적국 '+country,'country':'asean','member_state':country})
        assert r.status_code==302
        assert client.get(r.location).status_code==200
    r=post(client,'/projects',{'name':'잘못된 회원국','country':'asean','member_state':'FR'})
    assert 'ASEAN 수출 목적 회원국' in r.text
    for legacy in ['vn','th']:
        r=client.get('/beauty/'+legacy+'/market')
        assert r.status_code==302 and 'asean' in r.location and legacy.upper() in r.location
    with app.app_context():
        db=get_db();owner=db.execute('SELECT id FROM users').fetchone()[0]
        db.execute("INSERT INTO projects VALUES('legacy',?,'old','vn','','2025')",(owner,));db.commit();init_db();init_db()
        p=dict(db.execute("SELECT * FROM projects WHERE id='legacy'").fetchone())
        assert p['country']=='asean' and p['member_state']=='VN'
    assert client.get('/beauty/asean/market?member_state=FR').status_code==404
    assert 'member_state=VN' in client.get('/beauty/asean/market?member_state=VN').text
    assert '<option value="VN" selected>' in client.get('/projects?country=asean&member_state=VN').text


def test_append_notes_stay_in_place_and_delete_is_owned(app,client,owned):
    pid,product=owned
    for note in ['첫 메모','두 번째 <script>메모']:
        response=post(client,f'/products/{product}/notes',{'notes':note},headers={'Accept':'application/json'})
        assert response.status_code==200 and response.json['note']['content']==note
    data=client.get(f'/projects/{pid}/export').json
    assert [n['content'] for n in data['products'][0]['note_list']]==['두 번째 <script>메모','첫 메모']
    assert post(client,f'/products/{product}/notes',{'notes':'   '},headers={'Accept':'application/json'}).status_code==400
    response=post(client,f'/products/{product}/notes',{'notes':'세 번째'})
    assert response.location.endswith('#product-notes')
    stranger=app.test_client();signup(stranger,'other@example.test')
    assert post(stranger,f'/projects/{pid}/delete').status_code==404
    assert client.post(f'/projects/{pid}/delete').status_code==400
    assert client.get(f'/projects/{pid}/delete').status_code==405
    post(client,f'/projects/{pid}/bookmarks',{'kind':'news','title':'test','url':'https://example.test'})
    assert post(client,f'/projects/{pid}/delete').status_code==302
    assert client.get(f'/projects/{pid}/export').status_code==404
    with app.app_context():
        for table in ['projects','products','analyses','task_states','product_notes','bookmarks']:
            assert get_db().execute('SELECT count(*) FROM '+table).fetchone()[0]==0


def test_legacy_note_migrates_once(app,client,owned):
    pid,product=owned
    with app.app_context():
        db=get_db();db.execute('UPDATE products SET notes=? WHERE id=?',('보존 메모',product));db.commit();init_db();init_db()
        assert db.execute('SELECT count(*) FROM product_notes WHERE product_id=?',(product,)).fetchone()[0]==1
        assert db.execute('SELECT content FROM product_notes WHERE product_id=?',(product,)).fetchone()[0]=='보존 메모'


def test_banned_review_is_red_restricted_review_yellow(app):
    from flask import render_template
    with app.test_request_context():
        snapshot={'state':'ready','results':[{'inci_name':'A','regulation_type':'금지','result':'확인 필요'},{'inci_name':'B','regulation_type':'제한','result':'확인 필요'}]}
        html=render_template('tab1_regulation/screening_table.html',snapshot=snapshot)
        assert '<span class="status bad">확인 필요</span>' in html
        assert '<span class="status warning">확인 필요</span>' in html
