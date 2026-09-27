import math
from flask import current_app
from platform_core.services.country_service import get_country, destination
from platform_core.integrations.http_client import setting, IntegrationError
from platform_core.services.data_loader import read_data,read_file

def finite_number(value):
    if value is None:
        return None
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError("통계 값은 0 이상의 유한한 숫자여야 합니다.")
    return value

def growth_rate(current,previous):
    current,previous=finite_number(current),finite_number(previous)
    return None if current is None or previous is None or previous==0 else (current-previous)/previous*100

def import_share(korean_imports,total_imports):
    korean_imports,total_imports=finite_number(korean_imports),finite_number(total_imports)
    if korean_imports is None or total_imports is None or total_imports==0:
        return None
    if korean_imports>total_imports:
        raise ValueError("한국산 수입액이 전체 수입액보다 큽니다.")
    return korean_imports/total_imports*100

def market_summary(country,member_state="",live=True):
    target=destination(country,member_state)
    data=read_data(current_app.config["MARKET_DATA_ROOT"],country,"trade_statistics.json",dict)
    if country in {"eu","asean"} and member_state:
        data=read_file(current_app.config["MARKET_DATA_ROOT"]/country/member_state/"trade_statistics.json",dict)
    if live and setting("COMTRADE_API_KEY"):
        from ..integrations.comtrade_client import fetch
        try:
            external=fetch(target["iso"])
            data={"state":external["state"],"message":external.get("message",""),"data":{"series":external["series"]}}
        except IntegrationError as error:
            data={"state":"data_error","message":str(error),"data":{}}
    result={"state":data["state"],"message":data["message"],"series":[],"total_imports":None,"korean_imports":None,"growth":None,"share":None}
    if data["state"]=="data_error":
        return result
    try:
        rows=data["data"].get("series",[])
        if not isinstance(rows,list):
            raise ValueError("series는 배열이어야 합니다.")
        seen=set()
        for raw in rows:
            required=["period","reporter","hs_scope","hs_version","unit","source","coverage"]
            if not isinstance(raw,dict) or any(not raw.get(k) for k in required):
                raise ValueError("통계에 기간·보고국·HS 범위·버전·단위·출처·집계 범위가 필요합니다.")
            if raw["reporter"]!=target["iso"]:
                raise ValueError("목적국이 보고한 수입 통계를 사용해 주세요. 러시아는 RU, EU 집계는 EU입니다.")
            if raw["period"] in seen:
                raise ValueError("동일 기간의 중복 통계를 확인해 주세요.")
            seen.add(raw["period"])
            row=dict(raw)
            for key in ("total_imports","korean_imports","korea_exports"):
                row[key]=finite_number(raw.get(key))
            if row["korea_exports"] is not None and (raw.get("export_reporter")!="KR" or not raw.get("export_source")):
                raise ValueError("한국 수출액에는 export_reporter=KR과 export_source가 필요합니다.")
            row["share"]=import_share(row["korean_imports"],row["total_imports"])
            result["series"].append(row)
        result["series"].sort(key=lambda r:r["period"])
        if not rows:
            return {**result,"state":"data_pending","message":"시장 통계 데이터 준비 중"}
        comparators=("reporter","hs_scope","hs_version","unit","coverage")
        available=[r for r in result["series"] if r["korean_imports"] is not None or r["total_imports"] is not None]
        if not available:
            return {**result,"state":"data_pending","message":"해당 목적국의 통계가 아직 제공되지 않았습니다."}
        latest=available[-1]
        if any(any(r[k]!=latest[k] for k in comparators) for r in result["series"]):
            raise ValueError("추이 비교의 보고국·품목·단위·집계 범위가 일치하지 않습니다.")
        previous=next((r for r in result["series"] if r["period"]==latest.get("previous_period")),None)
        # 성장률은 데이터가 비교 기간을 명시한 경우에만 계산합니다.
        growth=growth_rate(latest["korean_imports"],previous["korean_imports"]) if previous and latest.get("previous_period")==previous["period"] else None
        result.update(state="ready",total_imports=latest["total_imports"],korean_imports=latest["korean_imports"],growth=growth,share=latest["share"],latest=latest)
        result["charts"]=[chart(result["series"],"total_imports","화장품 수입액",latest["unit"]),chart(result["series"],"korean_imports","한국 화장품 수입액",latest["unit"]),chart(result["series"],"share","한국산 수입 점유율","%")]
        return result
    except (ValueError,TypeError,KeyError) as error:
        return {**result,"series":[],"state":"data_error","message":str(error)}

def chart(rows,key,title,unit):
    values=[r[key] for r in rows if r[key] is not None]
    maximum=max(values) if values else 1
    maximum=maximum or 1
    points=[]
    segments=[]
    current=[]
    for i,row in enumerate(rows):
        if row[key] is None:
            if current:
                segments.append(" ".join(current))
                current=[]
            continue
        x=50+i*640/max(len(rows)-1,1)
        y=180-row[key]/maximum*135
        current.append(f"{x:.1f},{y:.1f}")
        points.append({"x":x,"y":y,"label":row["period"],"value":row[key]})
    if current:
        segments.append(" ".join(current))
    return {"title":title,"unit":unit,"segments":segments,"points":points,"maximum":maximum,"key":key}

def overview(live=True,include_rankings=False):
    data=read_file(current_app.config["MARKET_DATA_ROOT"]/"korea/export_overview.json",dict)
    if live and setting("CUSTOMS_API_KEY"):
        from ..integrations.customs_export_client import fetch
        try:
            external=fetch(include_rankings=include_rankings)
            data={"state":external["state"],"message":external.get("message",""),"data":external}
        except IntegrationError as error:
            data={"state":"data_error","message":str(error),"data":{}}
    result={"state":"data_pending","total_exports":None,"growth":None,"rankings":[],"series":[],"period":None,"unit":"USD","message":data.get("message",""),"hs_scope":str(setting("COSMETICS_HS_CODES","3304"))}
    if data["state"]=="data_error":
        return {**result,"state":"data_error"}
    payload=data["data"]
    try:
        total=finite_number(payload.get("total_exports"))
        previous=finite_number(payload.get("previous_exports"))
        if total is None or not payload.get("period") or not payload.get("source"):
            return result
        rankings=payload.get("rankings",[])
        if not isinstance(rankings,list) or any(not isinstance(r,dict) or not r.get("country") for r in rankings):
            raise ValueError()
        for r in rankings:
            finite_number(r.get("value"))
        series=payload.get("series",[])
        if not isinstance(series,list) or any(not isinstance(r,dict) or not r.get("period") for r in series):
            raise ValueError()
        for r in series:
            finite_number(r.get("value"))
        return {**result,**payload,"state":"ready","growth":growth_rate(total,previous) if payload.get("previous_period") else None,"chart":chart(series,"value","한국 화장품 수출 추이","USD")}
    except (ValueError,TypeError):
        return {**result,"state":"data_error"}
