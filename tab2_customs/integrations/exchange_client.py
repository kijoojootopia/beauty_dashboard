from datetime import datetime,timedelta,timezone
import re
from platform_core.integrations.http_client import setting,request_json,cached,IntegrationError

URL='https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON'


def fetch():
    key=setting('EXCHANGE_API_KEY')
    if not key: return {'state':'data_pending','message':'한국수출입은행 인증키를 설정해 주세요.','data':{}}
    today=datetime.now(timezone(timedelta(hours=9))).date()
    def load():
        for days in range(10):
            target=today-timedelta(days=days)
            if target.weekday()>=5: continue
            rows=request_json(URL,params={'authkey':key,'searchdate':target.strftime('%Y%m%d'),'data':'AP01'})
            if not isinstance(rows,list): raise IntegrationError('수출입은행 응답 형식을 확인할 수 없습니다.')
            if not rows: continue
            rates=[]
            for row in rows:
                if row.get('result')!=1: raise IntegrationError('수출입은행 인증키 또는 호출 한도를 확인해 주세요.')
                m=re.fullmatch(r'([A-Z]{3})(?:\((\d+)\))?',str(row.get('cur_unit','')))
                if not m: continue
                try: rate=float(str(row.get('deal_bas_r','')).replace(',',''))
                except ValueError: continue
                if rate>0: rates.append({'currency':m[1],'unit':int(m[2] or 1),'krw_rate':rate})
            if rates:
                return {'state':'ready','message':'','data':{'as_of':target.isoformat(),'source':'한국수출입은행 매매기준율','source_url':'https://www.koreaexim.go.kr/ir/HPHKIR055M01','rates':rates}}
        return {'state':'data_pending','message':'최근 10일간 제공된 환율이 없습니다.','data':{}}
    return cached('exchange',[key,str(today)],load,ttl=3600)
