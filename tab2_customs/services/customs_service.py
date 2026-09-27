import re
from decimal import Decimal, InvalidOperation
from flask import current_app
from platform_core.services.data_loader import read_data, read_file

def lookup_tariffs(country,origin,hs_code):
    if not re.fullmatch(r"\d{6,12}",hs_code):
        raise ValueError("HS 코드는 6~12자리 숫자로 입력해 주세요.")
    if not re.fullmatch(r"[A-Z]{2}",origin):
        raise ValueError("원산지는 KR, CN처럼 국가 코드 두 글자로 입력해 주세요.")
    from flask import g
    if country in {"eu","asean"} and not getattr(g,"destination_member",""):
        return {"state":"data_pending","message":"실제 목적 회원국을 선택해 주세요.","items":[]}
    dataset=read_data(current_app.config["CUSTOMS_DATA_ROOT"],country,"tariffs.json")
    items=[]
    for row in dataset["data"]:
        # 6자리 검색은 세부 코드 후보를 보여주지만 자동으로 동일 품목으로 단정하지 않습니다.
        code=str(row.get("hs_code",""))
        if row.get("origin")==origin and (code==hs_code or (len(hs_code)==6 and code.startswith(hs_code))):
            value=row.get("rate")
            if value is not None:
                try:
                    number=Decimal(str(value))
                    if not number.is_finite() or number<0:
                        raise ValueError()
                except (ValueError,InvalidOperation):
                    return {"state":"data_error","message":"관세율 데이터의 숫자를 확인해 주세요.","items":[]}
            items.append(row)
    return {"state":dataset["state"] if dataset["state"]!="ready" else ("ready" if items else "no_match"),"items":items,
        "message":dataset["message"] or ("조회 조건에 맞는 등록 데이터가 없습니다." if not items else "")}

def load_customs(country):
    data=read_data(current_app.config["CUSTOMS_DATA_ROOT"],country,"customs_roadmap.json")
    return {**data,"steps":data["data"]}

def convert_currency(amount,source_rate_krw,target_rate_krw,source_unit=1,target_unit=1):
    try:
        a,s,t,su,tu=[Decimal(str(v)) for v in (amount,source_rate_krw,target_rate_krw,source_unit,target_unit)]
    except InvalidOperation:
        raise ValueError("금액·환율·고시 단위는 숫자로 입력해 주세요.") from None
    if not all(v.is_finite() for v in (a,s,t,su,tu)) or a<0 or min(s,t,su,tu)<=0:
        raise ValueError("금액은 0 이상, 환율과 고시 단위는 양수여야 합니다.")
    if a>Decimal("1e15") or any(v>Decimal("1e12") or v<Decimal("1e-12") for v in (s,t,su,tu)):
        raise ValueError("금액 또는 환율의 지원 범위를 초과했습니다.")
    return a*(s/su)/(t/tu)

def rates_dataset():
    from platform_core.integrations.http_client import setting,IntegrationError
    if setting("EXCHANGE_API_KEY"):
        from ..integrations.exchange_client import fetch
        try: return fetch()
        except IntegrationError as error: return {"state":"data_error","message":str(error),"data":{}}
    return read_file(current_app.config["CUSTOMS_DATA_ROOT"]/"exchange_rates.json",dict)

def calculate_exchange(amount,source,target):
    data=rates_dataset()
    if data["state"]=="data_error":
        raise ValueError(data["message"])
    payload=data["data"]
    rows=payload.get("rates",[])
    if not isinstance(rows,list) or any(not isinstance(r,dict) for r in rows):
        raise ValueError("환율 데이터 구조를 확인해 주세요.")
    rates={r.get("currency"):r for r in rows}
    rates["KRW"]={"krw_rate":1,"unit":1}
    if not payload.get("as_of") or not payload.get("source"):
        raise ValueError("환율 데이터 준비 중 · 기준일과 출처를 등록해 주세요.")
    if source not in rates or target not in rates:
        raise ValueError("선택한 통화의 환율이 아직 등록되지 않았습니다.")
    try:
        s,t=rates[source],rates[target]
        result=convert_currency(amount,s["krw_rate"],t["krw_rate"],s["unit"],t["unit"])
        rate=convert_currency(1,s["krw_rate"],t["krw_rate"],s["unit"],t["unit"])
    except KeyError:
        raise ValueError("환율과 고시 단위를 확인해 주세요.") from None
    return {"amount":format(result,".2f"),"rate":str(rate),"from":source,"to":target,"as_of":payload["as_of"],"source":payload["source"],"source_url":payload.get("source_url")}
