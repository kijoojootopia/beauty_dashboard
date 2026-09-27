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


def test_kotra_real_response_mapping(app,monkeypatch):
    app.config.update(KOTRA_API_KEY='test-only')
    def response(url,params):
        assert params['search1']=='베트남' and params['search2']=='화장품'
        return b'{"response":{"header":{"resultCode":"00"},"body":{"itemList":{"item":{"newsTitl":"Example","kotraNewsUrl":"https://example.test/news","othbcDt":"20250901"}}}}}'
    monkeypatch.setattr(kotra,'request_bytes',response)
    with app.app_context():
        result=kotra.fetch('베트남');assert result['items'][0]['url']=='https://example.test/news'


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
