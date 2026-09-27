"""사용자 제공 일본 배열형 JSON 호환. 자유 문장 조건은 추론하지 않습니다."""
import re
import unicodedata
from collections import Counter
from .ingredient_parser import normalize_row, percentage
from .regulation_loader import load_regulations

def norm(value):
    return " ".join(unicodedata.normalize("NFKC",str(value or "")).casefold().split())

def matches(row,rule):
    if row["cas_no"] and rule.get("cas_no"):
        return norm(row["cas_no"])==norm(rule["cas_no"])
    names=[rule.get("inci_name"),rule.get("kr_name")]+rule.get("aliases",[])
    return bool(row["inci_name"]) and norm(row["inci_name"]) in {norm(v) for v in names if v}

def scope_applies(rule,scope):
    if rule.get("product_type_scope")=="ALL":
        return True
    scopes=rule.get("applicable_product_scopes")
    if isinstance(scopes,list) and scopes and scope:
        return scope in scopes
    return None

def evaluate_rule(row,rule,prohibited,scope):
    applies=scope_applies(rule,scope)
    if applies is False:
        return None
    if applies is None:
        return "확인 필요","제품 범위·용도 확인 필요"
    if re.search(r"\b(except|other than|total|salts|derivatives)\b",rule.get("inci_name",""),re.I):
        return "확인 필요","성분군·예외·합계량 원문 확인 필요"
    # 공통 면책 문구를 특정 조건으로 혼동하지 않되 원본 일본 금지 규칙도 보수적으로 처리.
    conditions=rule.get("conditions") or rule.get("conditions_kr")
    if conditions and rule.get("conditions_verified") is not True:
        return "확인 필요","서술형 조건을 검토해야 합니다. 원문과 적용 범위를 확인해 주세요."
    if prohibited:
        return "부적합","등록된 적용 범위의 금지 규칙에 해당"
    if rule.get("max_concentration") is None:
        return "확인 필요","숫자 한도 미등록 · 원문 확인 필요"
    if rule.get("limit_basis") not in {None,"individual_percent"}:
        return "확인 필요","합계량 또는 단위 환산 검토 필요"
    if row["concentration"] is None:
        return "확인 필요","최종 제품 내 배합량(%) 입력 필요"
    try:
        cap=percentage(rule["max_concentration"])
    except ValueError:
        return "확인 필요","한도 값 형식 확인 필요"
    if row["concentration"]>cap:
        return "부적합",f"등록 한도 {cap:g}% 초과"
    return "적합",f"등록 한도 {cap:g}% 이내"

def screen_rows(ingredients,prohibited,restricted,product_scope=None):
    results=[]
    normalized=[normalize_row(r) for r in ingredients]
    name_counts=Counter(norm(r["inci_name"]) for r in normalized if r["inci_name"])
    cas_counts=Counter(norm(r["cas_no"]) for r in normalized if r["cas_no"])
    priority={"부적합":3,"확인 필요":2,"적합":1}
    for row in normalized:
        decisions=[]
        matched=[]
        types=[]
        for is_prohibited,rules in ((True,prohibited),(False,restricted)):
            for rule in rules:
                if matches(row,rule):
                    decision=evaluate_rule(row,rule,is_prohibited,product_scope)
                    if decision:
                        decisions.append(decision)
                        matched.append(rule)
                        types.append("금지" if is_prohibited else "제한")
        if name_counts.get(norm(row["inci_name"]),0)>1 or cas_counts.get(norm(row["cas_no"]),0)>1:
            decisions.append(("확인 필요","중복 성분 입력 · 같은 성분의 함량을 합쳐 한 행으로 입력해 주세요."))
        status,reason=max(decisions,key=lambda d:priority[d[0]]) if decisions else ("해당 없음","등록 JSON에서 일치하는 적용 항목 없음")
        results.append({**row,"result":status,"reason":reason,"regulation_type":" / ".join(dict.fromkeys(types)) or "—","matched_rules":matched})
    return results

def analyze(country,ingredients,product_scope=None,data_root=None):
    dataset=load_regulations(country,data_root)
    meta=dataset["metadata"]
    source=meta.get("source") or ("일본 후생노동성 「Standards for Cosmetics」" if country=="jp" else "출처 미등록")
    return {"state":dataset["state"],"message":dataset["message"],"data_hash":dataset.get("data_hash"),
            "data_version":meta.get("version"),"reviewed_at":meta.get("reviewed_at"),"notice":f"스크리닝은 등록된 규제 {source} 기준입니다.",
            "results":screen_rows(ingredients,dataset["prohibited"],dataset["restricted"],product_scope) if dataset["state"]=="ready" else []}
