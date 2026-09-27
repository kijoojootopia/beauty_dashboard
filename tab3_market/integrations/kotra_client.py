import re
import xml.etree.ElementTree as ET
from platform_core.integrations.http_client import setting,request_bytes,cached,IntegrationError
import json

URL='https://apis.data.go.kr/B410001/kotra_overseasMarketNews/ovseaMrktNews'


def fetch(country_name):
    key=setting('KOTRA_API_KEY')
    if not key: return {'state':'data_pending','message':'KOTRA API 키를 설정하면 시장 기사를 불러옵니다.','items':[]}
    def load():
        raw=request_bytes(URL,params={'serviceKey':key,'type':'json','pageNo':1,'numOfRows':30,'search1':country_name,'search2':'화장품'})
        try:
            obj=json.loads(raw);response=obj.get('response',obj);header=response.get('header',{});body=response.get('body',{})
            code=str(header.get('resultCode',''))
            items=body.get('itemList',{});items=items.get('item',[]) if isinstance(items,dict) else items
        except (ValueError,TypeError,AttributeError):
            try:
                root=ET.fromstring(raw);code=root.findtext('.//resultCode');items=[{c.tag:c.text or '' for c in item} for item in root.findall('.//item')]
            except ET.ParseError: raise IntegrationError('KOTRA 응답을 읽을 수 없습니다.') from None
        if code not in ('00','0','0000','NORMAL_SERVICE'): raise IntegrationError('KOTRA API 인증키와 이용 승인을 확인해 주세요.')
        if isinstance(items,dict): items=[items]
        if not isinstance(items,list): raise IntegrationError('KOTRA 기사 목록 형식을 확인할 수 없습니다.')
        result=[]
        for item in items:
            title=item.get('newsTitl');url=item.get('kotraNewsUrl')
            if title and str(url).startswith(('http://','https://')):
                result.append({'title':re.sub('<[^>]+>','',title),'url':url,'source':'KOTRA 해외시장뉴스','published_at':item.get('othbcDt',''),'country':item.get('natn'),'license':item.get('dataType','')})
        result.sort(key=lambda row:row['published_at'],reverse=True)
        return {'state':'ready' if result else 'data_pending','message':'' if result else '선택한 목적국의 화장품 기사가 없습니다.','items':result[:12]}
    return cached('kotra',[key,country_name],load)
