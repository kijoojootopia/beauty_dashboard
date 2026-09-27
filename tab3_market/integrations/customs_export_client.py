"""관세청 품목별/품목별 국가별 수출입실적. 전체 응답을 검증한 뒤 합산합니다."""
from datetime import date
from decimal import Decimal,InvalidOperation
import re
import json
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from flask import current_app
import xml.etree.ElementTree as ET
from platform_core.integrations.http_client import cached,setting,request_bytes,IntegrationError,hs_codes

TOTAL_URL='https://apis.data.go.kr/1220000/Itemtrade/getItemtradeList'
COUNTRY_URL='https://apis.data.go.kr/1220000/nitemtrade/getNitemtradeList'


def records(url, key, year, hs, country=None):
    result=[];seen_pages=set()
    for page in range(1,101):
        params={'serviceKey':key,'strtYymm':f'{year}01','endYymm':f'{year}12','hsSgn':hs,'pageNo':page,'numOfRows':1000}
        if country: params['cntyCd']=country
        raw=request_bytes(url,params=params)
        try: root=ET.fromstring(raw)
        except ET.ParseError: raise IntegrationError('관세청 응답을 읽을 수 없습니다.') from None
        for el in root.iter(): el.tag=el.tag.split('}')[-1]
        code=root.findtext('.//resultCode') or root.findtext('.//returnReasonCode')
        if code not in ('00','0','000','NORMAL_SERVICE'):
            raise IntegrationError('관세청 API 오류 · 인증키·서비스 활용 승인·요청 범위를 확인해 주세요.')
        items=[{c.tag:c.text or '' for c in el} for el in root.findall('.//item')]
        signature=tuple(tuple(sorted(i.items())) for i in items)
        if signature in seen_pages: raise IntegrationError('관세청 페이지 응답이 반복됩니다. 불완전한 합계는 표시하지 않습니다.')
        seen_pages.add(signature);result.extend(items)
        total=root.findtext('.//totalCount')
        if total and not total.strip().isdigit(): raise IntegrationError('관세청 페이지 수 형식이 올바르지 않습니다.')
        if not total or len(result)>=int(total): return result
        if not items: raise IntegrationError('관세청 통계 일부 페이지가 누락되었습니다.')
    raise IntegrationError('관세청 조회 결과가 페이지 한도를 초과했습니다.')


def money(value):
    try: number=Decimal(str(value).replace(',',''))
    except InvalidOperation: raise IntegrationError('관세청 금액 형식이 올바르지 않습니다.') from None
    if not number.is_finite() or number<0: raise IntegrationError('관세청 금액이 유효하지 않습니다.')
    return number


def period_rows(rows,year,hs):
    matching=[r for r in rows if str(r.get('hsCode') or r.get('hsCd','')).strip().startswith(hs)]
    # API는 합계와 월별 행을 함께 반환합니다. 월별 행만 합산해 중복을 막습니다.
    monthly=[r for r in matching if re.fullmatch(str(year)+r'[.\-/]?(0[1-9]|1[0-2])',str(r.get('year','')).strip())]
    annual=[r for r in matching if str(r.get('year','')).strip()==str(year)]
    return monthly or annual


def export_amount(rows,year,hs,country=None):
    details=period_rows(rows,year,hs)
    summaries=[r for r in rows if str(r.get('hsCode') or r.get('hsCd','')).strip()=='-']
    if len(summaries)>1: raise IntegrationError('관세청 합계 행이 중복되었습니다.')
    seen=set();periods=set();codes=set();amount=Decimal(0)
    for row in details:
        code=str(row.get('hsCode') or row.get('hsCd','')).strip()
        period=re.sub(r'[.\-/]','',str(row['year']).strip())
        if country and row.get('statCd','').strip()!=country:
            raise IntegrationError('관세청 응답 국가가 조회 국가와 다릅니다.')
        if (period,code) in seen: raise IntegrationError('관세청 기간·품목이 중복되어 합산을 중단했습니다.')
        seen.add((period,code));periods.add(period);codes.add(code)
        amount+=money(row.get('expDlr'))
    if any(a!=b and b.startswith(a) for a in codes for b in codes):
        raise IntegrationError('관세청 상위·하위 품목이 중복되어 합산을 중단했습니다.')
    if summaries:
        reported=money(summaries[0].get('expDlr'))
        if reported!=amount: raise IntegrationError('관세청 합계와 상세 수출액이 일치하지 않습니다.')
        # 국가별 거래가 없는 달을 0으로 추정하지 않고 제공처의 조회 기간 합계를 사용합니다.
        if country: return reported
    if not details: return None
    if periods!={str(year)} and periods!={f'{year}{month:02}' for month in range(1,13)}:
        if country: raise IntegrationError('국가별 연간 합계가 없어 불완전한 순위를 표시하지 않습니다.')
        return None
    return amount


def annual_total(year,codes,key):
    total=Decimal(0)
    for hs in codes:
        amount=export_amount(records(TOTAL_URL,key,year,hs),year,hs)
        if amount is None: return None
        total+=amount
    return float(total)


def rankings(year,codes,key):
    reference=json.loads((Path(__file__).parents[2]/"platform_core/data/customs_countries.json").read_text(encoding="utf-8"))["countries"]
    app=current_app._get_current_object()
    def one_country(iso):
        with app.app_context():
            def load():
                amount=Decimal(0);found=False
                for hs in codes:
                    value=export_amount(records(COUNTRY_URL,key,year,hs,iso),year,hs,iso)
                    if value is not None: amount+=value;found=True
                return {'country':iso,'name':reference[iso],'value':float(amount)} if found else None
            return cached('exports-by-country-v2',[key,year,codes,iso],load)
    # 권역 집계(EU)는 개별 회원국과 중복되므로 국가별 순위에서 제외합니다.
    items=[iso for iso in reference if iso!="EU"]
    # 첫 호출로 인증/서비스 승인을 확인한 뒤 국가별 조회를 진행합니다.
    first=one_country(items[0])
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=[first]+list(pool.map(one_country,items[1:]))
    return sorted([r for r in results if r is not None],key=lambda r:r['value'],reverse=True)


def fetch(include_rankings=False):
    key=setting('CUSTOMS_API_KEY');rank_key=setting('CUSTOMS_COUNTRY_API_KEY') or key
    if not key: return {'state':'data_pending','message':'관세청 API 키를 설정하면 수출 통계가 표시됩니다.'}
    codes=hs_codes();end=date.today().year-1
    try: end=int(setting('TRADE_END_YEAR',str(end)));count=int(setting('TRADE_YEARS','5'))
    except ValueError: raise IntegrationError('통계 연도 설정을 확인해 주세요.') from None
    if end<2005 or end>=date.today().year or not 2<=count<=10: raise IntegrationError('통계는 최근 완료 연도까지 2~10개년을 조회합니다.')
    def load():
        series=[{'period':str(y),'value':annual_total(y,codes,key)} for y in range(end-count+1,end+1)]
        available=[r for r in series if r['value'] is not None]
        if not available: return {'state':'data_pending','message':'선택한 품목의 완전한 연간 수출 통계가 아직 없습니다.'}
        latest=available[-1];year=int(latest['period']);previous=next((r for r in series if r['period']==str(year-1)),{})
        return {'state':'ready','total_exports':latest['value'],'previous_exports':previous.get('value'),'period':latest['period'],
            'previous_period':previous.get('period'),'series':series,'rankings':[],
            'unit':'USD','source':'관세청 수출입무역통계','source_url':'https://www.data.go.kr/data/15101609/openapi.do','hs_scope':','.join(codes),'coverage':'한국 → 전 세계 · 연간 · FOB · 선택 HS 범위'}
    result=cached('korea-exports-totals-v2',[key,codes,end,count],load)
    if not include_rankings or result.get('state')!='ready': return result
    def load_rankings():
        rank=rankings(int(result['period']),codes,rank_key)
        if rank and abs(sum(r['value'] for r in rank)-result['total_exports'])>max(1,result['total_exports']*0.000001):
            raise IntegrationError('국가별 집계와 전체 수출액이 일치하지 않아 순위를 표시하지 않습니다.')
        return rank
    try:
        rank=cached('korea-export-rankings-v2',[key,rank_key,codes,result['period'],result['total_exports']],load_rankings)
        return {**result,'rankings':rank,'ranking_state':'ready' if rank else 'data_pending','ranking_message':'' if rank else '조회된 국가별 수출 통계가 없습니다.'}
    except IntegrationError as error:
        return {**result,'rankings':[],'ranking_state':'data_error','ranking_message':str(error)}
