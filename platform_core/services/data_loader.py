"""공개 JSON 읽기 계약. 누락·빈 값·손상을 구별합니다."""
import json
from pathlib import Path
from .country_service import get_country
from flask import g, has_request_context

def read_data(root, country, filename, expected=list):
    get_country(country)
    path=Path(root)/country/filename
    member=getattr(g,"destination_member","") if has_request_context() else ""
    if country in {"eu","asean"} and member:
        specific=Path(root)/country/member/filename
        # ASEAN 성분 규제는 공통 규칙, 관세/통관/시장 자료는 목적국별 자료입니다.
        common_rules=filename in {"prohibited_ingredients.json","restricted_ingredients.json","metadata.json","regulation_updates.json","pipeline_checklist.json"}
        if (country=="asean" and not common_rules) or (specific.exists() and country=="eu"):
            path=specific
    return read_file(path, expected)

def read_file(path, expected=list):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        return {"state":"data_pending", "data":expected(), "message":"데이터 준비 중 · 파일 미등록"}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"state":"data_error", "data":expected(), "message":"데이터 파일을 읽을 수 없습니다. JSON 형식을 확인하세요."}
    if not isinstance(value, expected) or (expected is list and any(not isinstance(r,dict) for r in value)):
        return {"state":"data_error", "data":expected(), "message":"JSON 구조가 데이터 계약과 다릅니다."}
    return {"state":"ready" if value else "data_pending", "data":value,
            "message":"" if value else "데이터 준비 중"}
