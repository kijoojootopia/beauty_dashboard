"""질문에 필요한 공통 등록 자료만 공개 조회 함수로 읽습니다."""
import json
import re
from flask import g
from platform_core.services.country_service import destination
from tab3_market.services.market_service import market_summary, overview
from tab3_market.services.news_service import load_news
from tab3_market.services.distributor_service import candidates
from tab1_regulation.services.regulation_loader import load_regulations
from tab1_regulation.services.roadmap_service import load_roadmap
from tab2_customs.services.customs_service import lookup_tariffs, load_customs


def _bounded(value):
    """긴 자료는 구조를 유지하며 제한하고 생략 여부를 명시합니다."""
    if isinstance(value, dict):
        return {str(k): _bounded(v) for k, v in value.items()
                if k not in {"charts", "chart", "data_hash"}}
    if isinstance(value, list):
        rows = [_bounded(v) for v in value[:30]]
        if len(value) > 30:
            rows.append({"omitted_count": len(value) - 30})
        return rows
    if isinstance(value, str):
        return value if len(value) <= 3000 else value[:3000] + " [이후 생략]"
    return value


def load_context(plan):
    topic = plan["topic"]
    if topic in {"general", "usage"}:
        return {"state": "not_requested", "usage": (
            "국가 선택 → 내 프로젝트 → 제품 등록. "
            "Tab 1 규제·수출 준비, Tab 2 관세·통관, Tab 3 시장·유통사. "
            "챗봇은 공통 등록 자료를 조회하며 개인 프로젝트를 변경하지 않습니다.")}
    country, member = plan["country"], plan["member_state"]
    if topic == "overview":
        result = overview(live=False, include_rankings=True)
        return {"dataset": "한국 화장품 수출 개요(등록 자료)", "data": _bounded(result)}
    if not country:
        return {"state": "clarify", "message": "조회할 국가를 알려 주세요."}
    target = destination(country, member)
    if country in {"eu", "asean"} and not member and topic in {"market", "tariffs", "customs", "news", "distributors"}:
        return {"state": "clarify", "message": "실제 목적 회원국을 알려 주세요."}
    # 기존 공개 조회 함수의 EU/ASEAN 회원국 선택 계약을 따릅니다.
    previous = getattr(g, "destination_member", None)
    g.destination_member = member
    try:
        if topic == "market":
            result = market_summary(country, member, live=False)
            result["share_definition"] = "한국 전체 화장품 수출액 중 해당국 수출액 비중(%)"
            result["amount_definition"] = "amount는 억 달러, amount_usd는 달러"
        elif topic == "regulations":
            term = plan["ingredient"].strip()
            if not term:
                return {"state": "clarify", "message": "조회할 성분명(INCI) 또는 CAS 번호를 알려 주세요."}
            result = load_regulations(country)
            needle = term.casefold()
            for key in ("prohibited", "restricted"):
                rows = result.get(key, [])
                result[key] = [row for row in rows if needle in json.dumps(
                    {k: row.get(k) for k in ("inci_name", "kr_name", "cas_no", "aliases")},
                    ensure_ascii=False).casefold()]
            result["lookup_note"] = "검색 결과가 없다는 것은 허용 또는 적합 판정이 아닙니다."
        elif topic == "roadmap":
            if country == "us" and not plan["product_type"]:
                return {"state": "clarify", "message": "일반 화장품인지 선케어 제품인지 알려 주세요."}
            result = load_roadmap(country, plan["product_type"] or None)
        elif topic == "tariffs":
            if not re.fullmatch(r"\d{6,12}", plan["hs_code"]) or not re.fullmatch(r"[A-Z]{2}", plan["origin"]):
                return {"state": "clarify", "message": "HS 코드(6~12자리)와 원산지 국가를 알려 주세요."}
            result = lookup_tariffs(country, plan["origin"], plan["hs_code"])
        elif topic == "customs":
            result = load_customs(country)
        elif topic == "news":
            result = load_news(country, member, live=False)
        elif topic == "distributors":
            result = candidates(country, None, member, live=False)
        else:
            raise ValueError("지원하지 않는 자료 유형입니다.")
        return {"dataset": topic, "country": target["name"], "data": _bounded(result)}
    finally:
        if previous is None:
            g.pop("destination_member", None)
        else:
            g.destination_member = previous

def direct_market_answer(question, history):
    """짧은 통계 질문과 후속 질문을 등록 자료로 직접 답합니다."""
    from platform_core.services.country_service import COUNTRIES, MEMBER_GROUPS
    compact = re.sub(r"\s+", "", question).lower()
    # 혼합/비통계 요청은 범위 분류 단계로 보냅니다.
    if any(word in compact for word in (
        "아이폰", "주식", "정치", "대통령", "코딩", "파이썬", "여행", "무시", "프롬프트",
        "수입시장", "수입점유", "전체산업", "전산업", "반도체", "자동차")):
        return None
    aliases = {"미국": ("us", ""), "일본": ("jp", ""), "중국": ("cn", ""),
               "러시아": ("eac", ""), "아랍에미리트": ("uae", ""), "uae": ("uae", "")}
    for group, members in MEMBER_GROUPS.items():
        for code, name in members.items():
            aliases[name.lower()] = (group, code)
    targets = list(dict.fromkeys(value for name, value in aliases.items() if name in compact))
    metric = "share" if any(w in compact for w in ("비중", "비율", "점유율", "퍼센트", "%")) else (
        "amount" if any(w in compact for w in ("수출액", "수출금액", "얼마수출")) else "")
    previous = ""
    recent_target = ""
    recent_year = ""
    for item in reversed(history):
        if item.get("role") == "user":
            candidate = re.sub(r"\s+", "", item["content"]).lower()
            if not recent_target and any(name in candidate for name in aliases):
                recent_target = candidate
            if not recent_year:
                year_match = re.search(r"20\d{2}", candidate)
                recent_year = year_match.group(0) if year_match else ""
            if any(w in candidate for w in ("비중", "비율", "점유율", "수출액", "수출금액")):
                previous = candidate
                break
    # 생략형 후속 질문만 과거 통계 문맥을 이어받습니다.
    remainder = compact
    for name in aliases:
        remainder = remainder.replace(name, "")
    remainder = re.sub(r"20\d{2}", "", remainder)
    for word in ("그럼", "그러면", "그리고", "작년", "올해", "전년", "년도", "년", "은", "는", "도", "요", "?", ".", "!"):
        remainder = remainder.replace(word, "")
    followup = not remainder and bool(targets or re.search(r"20\d{2}|작년|올해|전년", compact))
    if not metric and previous and followup:
        metric = "share" if any(w in previous for w in ("비중", "비율", "점유율")) else "amount"
    if not targets and metric and previous and followup:
        targets = list(dict.fromkeys(value for name, value in aliases.items() if name in (recent_target or previous)))
    if not metric or len(targets) != 1:
        return None
    # 요청이 길거나 여러 의도가 있으면 AI가 허용 질문을 먼저 추출합니다.
    if len(compact) > 70 or any(w in compact for w in ("추천", "만들어", "작성", "번역")):
        return None
    country, member = targets[0]
    data = market_summary(country, member, live=False)
    target = destination(country, member)["name"]
    if data["state"] != "ready":
        return f"{target}의 등록 시장 자료를 확인할 수 없습니다. " + data.get("message", "자료 준비 중입니다.")
    years = re.findall(r"(?<!\d)(20\d{2})(?!\d)", question)
    if len(set(years)) > 1:
        return None
    rows = [row for row in data.get("series", []) if row.get("period")]
    if data.get("current"):
        rows.append(data["current"])
    year = years[0] if years else (recent_year if followup and recent_year else None)
    if not year and ("작년" in compact or "전년" in compact):
        from datetime import date
        year = str(date.today().year - 1)
    if not year and "올해" in compact:
        from datetime import date
        year = str(date.today().year)
    # 임의 월/분기 요청을 최신 누계로 바꾸지 않습니다.
    if any(w in compact for w in ("분기", "상반기", "하반기", "월")) and not any(
            w in compact for w in ("1~8월", "1-8월", "1월부터8월")):
        return None
    available = [row for row in rows if row.get(metric if metric == "share" else "amount_usd") is not None]
    selected = next((row for row in rows if row["period"] == year), None) if year else (
        max(available, key=lambda row: row["period"]) if available else None)
    if not selected or selected.get(metric if metric == "share" else "amount_usd") is None:
        return f"{target}의 {year or '요청한 기간'} 수출 통계 값은 등록 자료에 없습니다."
    if "연간" in compact and selected.get("coverage") != "연간":
        return f"{target}의 {selected['period']}년 연간 자료는 없습니다. 등록 자료는 {selected.get('coverage', '기간 확인 필요')} 기준입니다."
    period = f"{selected['period']}년 {selected.get('coverage', '집계기간 확인 필요')}"
    if metric == "share":
        reply = f"한국 화장품 전체 수출 중 {target} 비중은 {selected['share']:g}%입니다.\n기준: {period}."
    else:
        reply = f"한국의 {target} 화장품 수출액은 {selected['amount_usd']:,.0f}달러입니다.\n기준: {period}."
    if not years:
        reply += " 연도를 지정하지 않아 등록된 최신 자료로 안내했습니다."
    if selected.get("basis"):
        reply += "\n통계 기준: " + selected["basis"]
    if selected.get("source_url"):
        reply += "\n출처: " + selected["source_url"]
    return reply
