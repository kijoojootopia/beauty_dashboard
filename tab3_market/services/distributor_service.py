from pathlib import Path
from flask import current_app
from platform_core.services.data_loader import read_file

def candidates(country, product, member_state="", live=True):
    from platform_core.services.country_service import destination
    destination(country, member_state)

    if country in {"eu", "asean"} and not member_state:
        return {"state": "data_pending", "items": [], "message": "실제 목적 회원국을 선택해 주세요."}

    root = Path(current_app.config["MARKET_DATA_ROOT"])
    path = root / country / "distributors.json"
    if country in {"asean", "eu"}:
        path = root / country / member_state / "distributors.json"
    data = read_file(path, expected=dict)
    if data["state"] != "ready":
        return {"state": data["state"], "items": [], "message": data["message"]}
    payload = data["data"]
    rows = payload.get("data")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        return {"state": "data_error", "items": [], "message": "유통사 JSON 구조가 올바르지 않습니다."}

    result = []
    for row in rows:
        if any(not isinstance(row.get(key, []), list) or any(not isinstance(v, str) for v in row.get(key, [])) for key in ("product_types", "channels", "brands")):
            return {"state": "data_error", "message": "유통사의 제품 유형·채널·브랜드는 문자열 배열이어야 합니다.", "items": []}
        if not row.get("name") or not row.get("source_url") or not row.get("verified_at"):
            continue
        categories = row.get("product_types", [])
        match = bool(product and product.get("product_type") in categories)
        result.append({**row, "matched": match, "reason": "등록 자료의 취급 제품 유형이 일치합니다." if match else "등록 자료를 바탕으로 검토할 후보입니다."})

    result.sort(key=lambda r: not r["matched"])
    return {"state": "ready" if result else "data_pending", "items": result, "message": payload.get("message", "")}
