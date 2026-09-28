import csv
import math
from pathlib import Path
from flask import current_app
from platform_core.services.country_service import destination
from platform_core.integrations.http_client import setting, IntegrationError
from platform_core.services.data_loader import read_file

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

# CSV는 국가별 행을 추가하는 방식으로 확장합니다. 공통 화면과 기존 수출 개요는 독립적으로 유지합니다.
MARKET_CSV_COLUMNS = {
    "amount": "한국화장품_수입액_한국측수출통계_천달러",
    "share": "한국전체화장품수출중_해당국가점유율_퍼센트",
    "achievement": "2026년_1~8월_전년도연간실적대비달성률_퍼센트",
}


def csv_number(value):
    if value is None or not value.strip():
        return None
    return finite_number(float(value.strip()))


def market_summary(country, member_state="", live=True):
    # live 인자는 기존 페이지/조각 호출과 호환하며, 시장 통계는 항상 등록 CSV를 읽습니다.
    target = destination(country, member_state)
    history = [{"period": str(year), "amount": None, "share": None, "source_url": ""}
               for year in range(2021, 2026)]
    result = {
        "state": "data_pending", "message": "해당 국가의 CSV 자료가 아직 등록되지 않았습니다.",
        # Tab 1 시장 요약에서 사용하는 기존 필드. 새 달성률/수출 비중과 구분합니다.
        "korean_imports": None, "total_imports": None,
        "growth": None, "share": None, "latest": None,
        "series": history, "current": None, "amount_eok": None,
        "achievement": None, "achievement_fill": None, "export_share": None,
        "previous_amount_eok": None, "current_period": "2026년 1~8월",
        "charts": [market_chart(history, "amount"), market_chart(history, "share")],
    }
    if country in {"eu", "asean"} and not member_state:
        return {**result, "message": "시장 자료를 볼 목적 회원국을 선택해 주세요."}
    names = {target["name"], target["iso"]}
    if country == "uae":
        names.add("아랍에미리트 연합")
    elif country == "eac":
        names.add("러시아")
    path = Path(current_app.config["MARKET_DATA_ROOT"]) / "market_statistics.csv"
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            required = {"국가", "사이트_국가명", "연도", "집계기간", "금액_통계기준",
                        "점유율_분모", "출처_URL", *MARKET_CSV_COLUMNS.values()}
            if not required.issubset(reader.fieldnames or []):
                raise ValueError("시장 CSV의 필수 열이 누락되었습니다.")
            selected = [row for row in reader
                        if (row.get("국가") or "").strip() in names
                        or (row.get("사이트_국가명") or "").strip() in names]
        if not selected:
            return result
        by_year = {}
        for raw in selected:
            year = int(raw["연도"])
            if year not in range(2021, 2027):
                continue
            if year in by_year:
                raise ValueError("동일 국가·연도의 시장 CSV 자료가 중복되었습니다.")
            coverage = (raw["집계기간"] or "").strip()
            if coverage != ("1~8월 누계" if year == 2026 else "연간"):
                raise ValueError("2021~2025년은 연간, 2026년은 1~8월 누계 자료가 필요합니다.")
            if (raw["점유율_분모"] or "").strip() != "한국의 전체 화장품 수출액":
                raise ValueError("점유율의 분모가 한국의 전체 화장품 수출액인지 확인해 주세요.")
            amount = csv_number(raw[MARKET_CSV_COLUMNS["amount"]])
            share = csv_number(raw[MARKET_CSV_COLUMNS["share"]])
            achievement = csv_number(raw[MARKET_CSV_COLUMNS["achievement"]])
            if share is not None and share > 100:
                raise ValueError("해당국 수출 비중은 100%를 넘을 수 없습니다.")
            by_year[year] = {
                "period": str(year), "coverage": coverage,
                "amount": amount / 100000 if amount is not None else None,
                "amount_usd": amount * 1000 if amount is not None else None,
                "share": share, "achievement": achievement,
                "basis": raw["금액_통계기준"], "source_url": raw["출처_URL"],
            }
        if not by_year:
            return result
        history = [by_year.get(year, row) for year, row in zip(range(2021, 2026), history)]
        current = by_year.get(2026)
        previous = by_year.get(2025, {}).get("amount")
        achievement = None
        if current:
            achievement = current["achievement"]
            if achievement is None and current["amount"] is not None and previous:
                achievement = current["amount"] / previous * 100
        has_values = any(row["amount"] is not None or row["share"] is not None
                         for row in by_year.values())
        return {
            **result, "state": "ready" if has_values else "data_pending",
            "message": "" if has_values else result["message"],
            "series": history, "current": current,
            "korean_imports": current["amount_usd"] if current else None,
            "latest": {
                "period": result["current_period"], "unit": "USD",
                "source": f"KCII · {current['basis']}",
            } if current else None,
            "amount_eok": current["amount"] if current else None,
            "export_share": current["share"] if current else None,
            "achievement": achievement,
            "achievement_fill": min(achievement, 100) if achievement is not None else None,
            "previous_amount_eok": previous,
            "charts": [market_chart(history, "amount"), market_chart(history, "share")],
        }
    except FileNotFoundError:
        return result
    except (OSError, UnicodeError, csv.Error, ValueError, TypeError, KeyError) as error:
        return {**result, "state": "data_error", "message": f"시장 CSV를 확인해 주세요. {error}"}


def market_chart(rows, key):
    values = [row[key] for row in rows if row[key] is not None]
    maximum = max(values) if values else 0
    if maximum:
        magnitude = 10 ** math.floor(math.log10(maximum))
        maximum = math.ceil(maximum / magnitude) * magnitude
    else:
        maximum = 1
    points, segments, segment = [], [], []
    for index, row in enumerate(rows):
        if row[key] is None:
            if segment:
                segments.append(" ".join(segment))
                segment = []
            continue
        x = 90 + index * 116
        y = 216 - row[key] / maximum * 160
        points.append({"x": x, "y": y, "height": 216-y,
                       "label": row["period"], "value": row[key]})
        segment.append(f"{x:.2f},{y:.2f}")
    if segment:
        segments.append(" ".join(segment))
    return {
        "key": key, "title": "한국 화장품 수입액" if key == "amount" else "한국 화장품 수출 중 해당국 비중",
        "unit": "억 달러" if key == "amount" else "%",
        "points": points, "segments": segments,
        "ticks": [{"y": 216-i*40, "value": maximum*i/4} for i in range(5)],
        "years": [{"x": 90+i*116, "label": str(year)} for i, year in enumerate(range(2021, 2026))],
    }


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
