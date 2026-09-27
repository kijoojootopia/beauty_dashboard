from datetime import date
import json,math
from pathlib import Path
from platform_core.integrations.http_client import setting,request_json,cached,IntegrationError,hs_codes

REPORTERS=json.loads((Path(__file__).parents[2]/'platform_core/data/comtrade_reporters.json').read_text(encoding="utf-8"))
URL='https://comtradeapi.un.org/data/v1/get/C/A/'


def fetch(iso):
    key=setting('COMTRADE_API_KEY')
    if not key: return {'state':'data_pending','message':'UN Comtrade 키를 설정하면 수입 통계가 표시됩니다.','series':[]}
    if iso not in REPORTERS: return {'state':'data_pending','message':'실제 목적 회원국을 선택해 주세요.','series':[]}
    codes=hs_codes();version=str(setting('COMTRADE_HS_VERSION','H6'))
    if version not in {'H4','H5','H6'}: raise IntegrationError('COMTRADE_HS_VERSION은 H4/H5/H6 중 하나여야 합니다.')
    try: end=int(setting('TRADE_END_YEAR',str(date.today().year-1)));count=int(setting('TRADE_YEARS','5'))
    except ValueError: raise IntegrationError('통계 연도 설정을 확인해 주세요.') from None
    if not 2<=count<=10 or not 2005<=end<date.today().year: raise IntegrationError('통계 조회 연도 범위를 확인해 주세요.')
    reporter=REPORTERS[iso]['code']
    def load():
        series=[]
        for year in range(end-count+1,end+1):
            obj=request_json(URL+version,params={'period':year,'reporterCode':reporter,'cmdCode':','.join(codes),'flowCode':'M','partnerCode':'0,410','partner2Code':0,'customsCode':'C00','motCode':0,'maxRecords':500,'aggregateBy':6,'breakdownMode':'classic','includeDesc':'true'},headers={'Ocp-Apim-Subscription-Key':key})
            rows=obj.get('data') if isinstance(obj,dict) else None
            if not isinstance(rows,list) or obj.get('error') or obj.get('errorMessage'): raise IntegrationError('UN Comtrade 응답을 확인할 수 없습니다.')
            if len(rows)>=500: raise IntegrationError('UN Comtrade 응답이 잘렸을 수 있어 합산을 중단했습니다.')
            values={}
            for row in rows:
                if not isinstance(row,dict): raise IntegrationError('UN Comtrade 행 형식이 올바르지 않습니다.')
                if (str(row.get('reporterCode'))!=str(reporter) or str(row.get('period'))!=str(year) or row.get('flowCode')!='M' or str(row.get('cmdCode')) not in codes or str(row.get('partnerCode')) not in {'0','410'} or str(row.get('partner2Code',0))!='0' or row.get('customsCode','C00')!='C00' or str(row.get('motCode',0))!='0'): continue
                if row.get('classificationCode',version)!=version: raise IntegrationError('통계 HS 버전이 조회 기준과 다릅니다.')
                identity=(str(row['partnerCode']),str(row['cmdCode']))
                if identity in values: raise IntegrationError('UN Comtrade 품목·파트너 통계가 중복되었습니다.')
                value=row.get('primaryValue')
                if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0: raise IntegrationError('UN Comtrade 금액 형식이 올바르지 않습니다.')
                values[identity]=value
            def total(partner):
                return sum(values[(partner,hs)] for hs in codes) if all((partner,hs) in values for hs in codes) else None
            series.append({'period':str(year),'previous_period':str(year-1),'reporter':iso,'hs_scope':','.join(codes),'hs_version':version,'unit':'USD','source':'UN Comtrade','coverage':f'{iso} 보고 수입 · 전 세계/한국 · 동일 HS 버전','total_imports':total('0'),'korean_imports':total('410'),'korea_exports':None})
        return {'state':'ready' if any(r['total_imports'] is not None or r['korean_imports'] is not None for r in series) else 'data_pending','series':series,'message':''}
    return cached('comtrade',[key,iso,codes,version,end,count],load)
