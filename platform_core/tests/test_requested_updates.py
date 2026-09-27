import json
import sqlite3
import pytest
from werkzeug.exceptions import NotFound
from platform_core.services import project_service as store
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


def test_note_update_delete_and_access(app,client,owned):
    pid,product=owned
    headers={'Accept':'application/json'}
    note=post(client,f'/products/{product}/notes',{'notes':'원본'},headers=headers).json['note']
    base=f'/products/{product}/notes/{note["id"]}'
    stranger=app.test_client();signup(stranger,'stranger@example.test')
    with app.app_context():
        owner=get_db().execute('SELECT user_id FROM projects WHERE id=?',(pid,)).fetchone()[0]
        other=store.save_product_analysis(owner,pid,{'name':'다른 제품','product_type':'leave_on','ingredients':[{'inci_name':'Synthetic'}]}, {})
    for action in ['update','delete']:
        assert post(stranger,base+'/'+action,{'notes':'침입'}).status_code==404
        assert post(client,f'/products/{other}/notes/{note["id"]}/{action}',{'notes':'잘못된 제품'}).status_code==404
        assert post(client,f'/products/{product}/notes/missing/{action}',{'notes':'없음'}).status_code==404
        assert client.post(base+'/'+action).status_code==400
        assert client.get(base+'/'+action).status_code==405
    for invalid in ['   ','x'*5001]:
        assert post(client,base+'/update',{'notes':invalid},headers=headers).status_code==400
    with app.app_context():
        assert store.notes_for(owner,product)==[note]
    result=post(client,base+'/update',{'notes':'  수정 내용  '},headers=headers)
    assert result.json['note']=={**note,'content':'수정 내용'}
    assert post(client,base+'/update',{'notes':'폼 수정'}).location.endswith('#product-notes')
    assert post(client,base+'/delete',headers=headers).json=={'deleted':note['id']}
    assert post(client,base+'/delete',headers=headers).status_code==404
    note2=post(client,f'/products/{product}/notes',{'notes':'삭제할 메모'},headers=headers).json['note']
    assert post(client,f'/products/{product}/notes/{note2["id"]}/delete').location.endswith('#product-notes')
    with app.app_context():
        assert store.notes_for(owner,product)==[]


def test_delete_product_owned_atomic_and_isolated(app,client,owned):
    pid,product=owned
    with app.app_context():
        db=get_db()
        owner=db.execute('SELECT user_id FROM projects WHERE id=?',(pid,)).fetchone()[0]
        other=store.save_product_analysis(owner,pid,{'name':'보존 제품','product_type':'leave_on','ingredients':[{'inci_name':'Synthetic'}]}, {})
        for product_id in [product,other]:
            store.save_notes(owner,product_id,'보존 확인')
            store.save_task(owner,product_id,'test-task',True)
        store.save_bookmark(owner,pid,'news','보존 기사','https://example.test')
        before=store.export_project(owner,pid)
        with pytest.raises(NotFound):
            store.delete_product(owner+100,product)
        assert store.export_project(owner,pid)==before
        db.execute("CREATE TEMP TRIGGER fail_delete BEFORE DELETE ON products BEGIN SELECT RAISE(ABORT, 'test failure'); END")
        with pytest.raises(sqlite3.IntegrityError):
            store.delete_product(owner,product)
        assert store.export_project(owner,pid)==before
        db.execute('DROP TRIGGER fail_delete')
        store.delete_product(owner,product)
        for table in ['product_notes','task_states','analyses']:
            assert db.execute(f'SELECT count(*) FROM {table} WHERE product_id=?',(product,)).fetchone()[0]==0
        with pytest.raises(NotFound):
            store.product_for(owner,product)
        after=store.export_project(owner,pid)
        assert after['project']==before['project']
        assert after['bookmarks']==before['bookmarks']
        assert after['products']==[p for p in before['products'] if p['id']==other]


def test_banned_review_is_red_restricted_review_yellow(app):
    from flask import render_template
    with app.test_request_context():
        snapshot={'state':'ready','results':[{'inci_name':'A','regulation_type':'금지','result':'확인 필요'},{'inci_name':'B','regulation_type':'제한','result':'확인 필요'}]}
        html=render_template('tab1_regulation/screening_table.html',snapshot=snapshot)
        assert '<span class="status bad">확인 필요</span>' in html
        assert '<span class="status warning">확인 필요</span>' in html
