import pytest
from platform_core.integrations.http_client import IntegrationError
from tab3_market.integrations import customs_export_client as exports,comtrade_client as comtrade,kotra_client as kotra,openai_client as distributors
from tab2_customs.integrations import exchange_client


def xml(rows,total=None):
    data='<response><header><resultCode>00</resultCode></header><body><items>'
    data+=''.join('<item>'+''.join(f'<{k}>{v}</{k}>' for k,v in row.items())+'</item>' for row in rows)
    return (data+'</items>'+('' if total is None else f'<totalCount>{total}</totalCount>')+'</body></response>').encode()


def test_export_annual_ignores_summary_and_validates_completeness(app,monkeypatch):
    rows=[{'hsCd':'3304','year':f'2025.{i:02}','expDlr':'100'} for i in range(1,13)]
    rows.append({'hsCd':'3304','year':'총계','expDlr':'1200'})
    monkeypatch.setattr(exports,'request_bytes',lambda *a,**kw:xml(rows))
    assert exports.annual_total(2025,['3304'],'test-only')==1200
    monkeypatch.setattr(exports,'request_bytes',lambda *a,**kw:xml(rows[:10]))
    assert exports.annual_total(2025,['3304'],'test-only') is None
    monkeypatch.setattr(exports,'request_bytes',lambda *a,**kw:xml(rows[:2],99))
    with pytest.raises(IntegrationError): exports.records('https://example.test','test-only',2025,'3304')


def test_comtrade_reporter_partner_and_missing_values(app,monkeypatch):
    app.config.update(COMTRADE_API_KEY='test-only',TRADE_END_YEAR='2025',TRADE_YEARS='2',COSMETICS_HS_CODES='3304')
    calls=[]
    def response(url,params,headers):
        calls.append(params)
        year=params['period']
        return {'data':[{'reporterCode':704,'period':year,'cmdCode':'3304','classificationCode':'H6','flowCode':'M','partnerCode':partner,'primaryValue':val} for partner,val in [(0,100),(410,20 if year==2024 else 24)]]}
    monkeypatch.setattr(comtrade,'request_json',response)
    from tab3_market.services.market_service import market_summary
    with app.app_context():
        data=market_summary('asean','VN');assert data['growth']==20 and data['share']==24 and data['korean_imports']==24
        assert data['charts'][1]['key']=='korean_imports'
    assert all(c['reporterCode']==704 and c['partnerCode']=='0,410' and c['flowCode']=='M' for c in calls)
    assert calls[0]['period']==2024
    app.config.update(COMTRADE_API_KEY='test-missing')
    monkeypatch.setattr(comtrade,'request_json',lambda *a,**kw:{'data':[]})
    with app.app_context():
        data=market_summary('asean','VN');assert data['state']=='data_pending' and data['share'] is None


def test_fx_weekend_fallback_and_100_unit(app,monkeypatch):
    app.config.update(EXCHANGE_API_KEY='test-only')
    calls=[]
    def response(url,params):
        calls.append(params)
        if len(calls)==1:return []
        assert 'oapi.koreaexim.go.kr' in url
        return [{'result':1,'cur_unit':'JPY(100)','deal_bas_r':'900.00'},{'result':1,'cur_unit':'USD','deal_bas_r':'1,300.00'}]
    monkeypatch.setattr(exchange_client,'request_json',response)
    from tab2_customs.services.customs_service import calculate_exchange
    with app.app_context():
        assert calculate_exchange('900','KRW','JPY')['amount']=='100.00'
        assert calculate_exchange('1','USD','KRW')['amount']=='1300.00'
    assert len(calls)==2


@pytest.mark.parametrize('country_name,search_name',[
    ('베트남','베트남'),('UAE','아랍에미리트'),('러시아(EAEU)','러시아'),
])
def test_kotra_real_response_mapping(app,monkeypatch,country_name,search_name):
    app.config.update(KOTRA_API_KEY='test-only')
    def response(url,params):
        assert params['search1']==search_name and params['search2']=='화장품'
        return b'{"response":{"header":{"resultCode":"00"},"body":{"itemList":{"item":{"newsTitl":"Example","kotraNewsUrl":"https://example.test/news","othbcDt":"20250901"}}}}}'
    monkeypatch.setattr(kotra,'request_bytes',response)
    with app.app_context():
        result=kotra.fetch(country_name);assert result['items'][0]['url']=='https://example.test/news'


def test_kotra_title_decodes_html_entities(app,monkeypatch):
    import json
    app.config.update(KOTRA_API_KEY='synthetic-only')
    title='화장품을 넘어서&hellip; 일본에서 &lsquo;K-피부관리&rsquo; 수요 &amp; 성장 &#39;기회&#39;'
    payload={'response':{'header':{'resultCode':'00'},'body':{'itemList':{'item':[
        {'newsTitl':title,'kotraNewsUrl':'https://example.test/article'}]}}}}
    monkeypatch.setattr(kotra,'request_bytes',lambda *args,**kwargs:json.dumps(payload).encode())
    with app.app_context():
        result=kotra.fetch('일본')
    assert result['items'][0]['title']=='화장품을 넘어서… 일본에서 ‘K-피부관리’ 수요 & 성장 \'기회\''


def test_distributors_must_have_search_evidence(app,monkeypatch):
    app.config.update(OPENAI_API_KEY='test-only')
    text='{"items":[{"name":"Sourced","source_url":"https://example.test/company","evidence":"공개 사업 내용","channels":[]},{"name":"Invented","source_url":"https://invented.test","evidence":"unsupported"}]}'
    monkeypatch.setattr(distributors,'respond',lambda *a,**kw:(text,{'output':[{'type':'web_search_call','action':{'sources':[{'url':'https://example.test/company'}]}}]}))
    with app.app_context():
        result=distributors.fetch('태국');assert [i['name'] for i in result['items']]==['Sourced']


def test_live_errors_are_visible_without_zero(app,client,monkeypatch):
    app.config.update(CUSTOMS_API_KEY='test-only')
    def fail(*a,**kw): raise IntegrationError('인증키를 확인해 주세요.')
    monkeypatch.setattr(exports,'fetch',fail)
    response=client.get('/api/exports/overview')
    assert response.json['state']=='data_error' and response.json['total_exports'] is None
    assert '인증키' in client.get('/api/exports/fragment').text


def test_export_country_ranking_covers_global_countries_once(app,monkeypatch):
    calls=[]
    def response(url,params):
        assert url==exports.COUNTRY_URL and params['cntyCd']
        iso=params['cntyCd'];calls.append(iso)
        values={'US':100,'DE':60,'VN':30,'TH':10}
        if iso not in values:return xml([])
        return xml([{'statCd':iso,'hsCd':'3304','year':'2025','expDlr':values[iso]},
                    {'statCd':iso,'hsCd':'3304','year':'총계','expDlr':values[iso]}])
    monkeypatch.setattr(exports,'request_bytes',response)
    with app.app_context():
        rows=exports.rankings(2025,['3304'],'test-country-key')
        assert [row['country'] for row in rows]==['US','DE','VN','TH']
        assert sum(row['value'] for row in rows)==200
        assert len(calls)>200 and len(calls)==len(set(calls)) and 'EU' not in calls
        exports.rankings(2025,['3304'],'test-country-key')
        assert len(calls)==len(set(calls))  # 국가별 캐시 재사용


def test_cache_retains_korean_text(app,tmp_path):
    from platform_core.integrations.http_client import cached
    app.config['API_CACHE_DIR']=tmp_path/'cache'
    with app.app_context():
        value=cached('encoding',['fixture'],lambda:{'name':'태국·베트남'})
        def unexpected():raise AssertionError('캐시를 읽어야 합니다.')
        assert cached('encoding',['fixture'],unexpected)==value


@pytest.mark.parametrize("text,expected", [
    ('{"items":[]}', 'data_pending'),
    ('Search results are available.', 'error'),
    ('', 'error'),
    ('{"items":"invalid"}', 'error'),
    ('{"items":[{"name":"Unsupported","source_url":"https://example.test/unknown","evidence":"unsupported"}]}', 'data_pending'),
    ('{"items":[{"name":"Sourced","source_url":"https://example.test/company","evidence":"Public evidence","product_types":["leave_on"]}]}', 'ready'),
])
def test_distributor_structured_response(monkeypatch, text, expected):
    from flask import Flask
    from platform_core.integrations import openai_client as common
    app = Flask(__name__)
    app.config.update(TESTING=True, OPENAI_API_KEY='synthetic-only')
    calls = []

    def response(url, **kwargs):
        payload = kwargs['body']
        assert payload['text']['format']['type'] == 'json_schema'
        assert payload['text']['format']['strict'] is True
        schema = payload['text']['format']['schema']
        item_schema = schema['properties']['items']['items']
        assert item_schema['additionalProperties'] is False
        assert set(item_schema['required']) == set(item_schema['properties'])
        if not calls:
            assert payload['tools'] == [{'type': 'web_search'}]
        else:
            assert 'tools' not in payload
        calls.append(payload)
        return {'status': 'completed', 'output': [
            {'type': 'web_search_call', 'action': {'sources': [{'url': 'https://example.test/company/?utm_source=openai'}]}},
            {'type': 'message', 'content': [{'type': 'output_text', 'text': text}]},
        ]}

    monkeypatch.setattr(common, 'request_json', response)
    monkeypatch.setattr(distributors, 'cached', lambda namespace, criteria, loader, ttl: loader())
    with app.app_context():
        if expected == 'error':
            with pytest.raises(IntegrationError, match='유통사 검색'):
                distributors.fetch('Japan', 'leave_on')
        else:
            result = distributors.fetch('Japan', 'leave_on')
            assert result['state'] == expected
            assert len(result['items']) == (1 if expected == 'ready' else 0)
            if expected == 'ready':
                assert result['items'][0]['matched'] is True
                assert result['items'][0]['source_url'] == 'https://example.test/company'
    assert len(calls) == (2 if text == 'Search results are available.' else 1)


def test_distributor_source_identity_preserves_page_and_query():
    identity = distributors.source_identity
    assert identity('https://example.test/company/?utm_source=openai') == identity('https://example.test/company')
    assert identity('https://example.test/company?id=1') != identity('https://example.test/company?id=2')
    assert identity('https://example.test/company') != identity('https://example.test/other')
    assert identity('javascript:alert(1)') == identity('https://[') == ''


def test_distributor_recovers_format_using_original_search_sources(monkeypatch):
    import json
    from flask import Flask
    from platform_core.integrations import openai_client as common
    app = Flask(__name__)
    app.config.update(TESTING=True, OPENAI_API_KEY='synthetic-only')
    calls = []
    malformed = '{"items":[{"name":"Synthetic company"'

    def response(url, **kwargs):
        body = kwargs['body']
        calls.append(body)
        if len(calls) == 1:
            assert body['tools'] == [{'type': 'web_search'}]
            return {'status': 'completed', 'output': [
                {'type': 'web_search_call', 'action': {'sources': [{'url': 'https://example.test/company?utm_source=openai'}]}},
                {'type': 'message', 'content': [{'type': 'output_text', 'text': malformed}]},
            ]}
        assert len(calls) == 2 and 'tools' not in body
        assert json.loads(body['input'])['search_response'] == malformed
        rows = [{'name': 'Synthetic company', 'source_url': link, 'evidence': 'Synthetic evidence'}
                for link in ['https://example.test/company', 'https://example.test/unsupported']]
        return {'status': 'completed', 'output': [
            {'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps({'items': rows})}]},
        ]}

    monkeypatch.setattr(common, 'request_json', response)
    monkeypatch.setattr(distributors, 'cached', lambda namespace, criteria, loader, ttl: loader())
    with app.app_context():
        result = distributors.fetch('United States', '')
    assert len(calls) == 2 and result['state'] == 'ready'
    assert [row['source_url'] for row in result['items']] == ['https://example.test/company']


def test_empty_market_results_are_retried_after_five_minutes(app,monkeypatch):
    import json
    from platform_core.integrations import http_client
    clock=[1000]
    monkeypatch.setattr(http_client.time,'time',lambda:clock[0])
    app.config.update(KOTRA_API_KEY='synthetic-only',OPENAI_API_KEY='synthetic-only')
    news_calls=[]
    distributor_calls=[]

    def news_response(url,params):
        news_calls.append(params)
        items=[] if len(news_calls)==1 else [{'newsTitl':'Synthetic article','kotraNewsUrl':'https://example.test/news'}]
        return json.dumps({'response':{'header':{'resultCode':'00'},'body':{'itemList':{'item':items}}}}).encode()

    def distributor_response(*args,**kwargs):
        distributor_calls.append(kwargs)
        items=[] if len(distributor_calls)==1 else [{
            'name':'Synthetic company','source_url':'https://example.test/company','evidence':'Synthetic evidence'}]
        return json.dumps({'items':items}),{'output':[{
            'type':'web_search_call','action':{'sources':[{'url':'https://example.test/company'}]}}]}

    monkeypatch.setattr(kotra,'request_bytes',news_response)
    monkeypatch.setattr(distributors,'respond',distributor_response)
    with app.app_context():
        assert kotra.fetch('UAE')['state']=='data_pending'
        assert distributors.fetch('United States')['state']=='data_pending'
        clock[0]+=301
        assert len(kotra.fetch('UAE')['items'])==1
        assert len(distributors.fetch('United States')['items'])==1
    assert len(news_calls)==len(distributor_calls)==2
    assert news_calls[0]['search1']=='아랍에미리트'
