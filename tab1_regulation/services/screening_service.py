"""사용자 제공 일본 배열형 JSON 호환. 자유 문장 조건은 추론하지 않습니다."""
import re
import unicodedata
from difflib import get_close_matches
from collections import Counter
from .ingredient_parser import normalize_row, percentage
from .regulation_loader import load_regulations

def norm(value):
    return " ".join(unicodedata.normalize("NFKC",str(value or "")).casefold().split())

def matches(row,rule):
    if row["cas_no"] and rule.get("cas_no"):
        if norm(row["cas_no"])!=norm(rule["cas_no"]):
            return False
        return not row["inci_name"] or not rule_names(rule) or norm(row["inci_name"]) in rule_names(rule)
    return bool(row["inci_name"]) and norm(row["inci_name"]) in rule_names(rule)


def rule_names(rule):
    return {norm(v) for v in [rule.get("inci_name"),rule.get("kr_name"),*(rule.get("aliases") or []),*(rule.get("synonyms") or [])] if v}

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
    all_rules=[*prohibited,*restricted]
    known_names={name for rule in all_rules for name in rule_names(rule)}
    for row in normalized:
        decisions=[]
        matched=[]
        types=[]
        cas_rules=[rule for rule in all_rules if row["cas_no"] and rule.get("cas_no") and norm(rule["cas_no"])==norm(row["cas_no"])]
        name_rules=[rule for rule in all_rules if row["inci_name"] and norm(row["inci_name"]) in rule_names(rule)]
        resolved_names={rule["inci_name"] for rule in cas_rules if rule.get("inci_name")}
        resolved_cases={rule["cas_no"] for rule in name_rules if rule.get("cas_no")}
        for is_prohibited,rules in ((True,prohibited),(False,restricted)):
            for rule in rules:
                if matches(row,rule):
                    decision=evaluate_rule(row,rule,is_prohibited,product_scope)
                    if decision:
                        decisions.append(decision)
                        matched.append(rule)
                        types.append("금지" if is_prohibited else "제한")
        conflict_reason=""
        if row["cas_no"] and row["inci_name"] and cas_rules and any(rule_names(rule) and norm(row["inci_name"]) not in rule_names(rule) for rule in cas_rules):
            conflict_reason="입력한 CAS와 성분명이 규제 목록에서 일치하지 않습니다. 두 식별자를 확인해 주세요."
        if row["cas_no"] and row["inci_name"] and name_rules and any(rule.get("cas_no") and norm(rule["cas_no"])!=norm(row["cas_no"]) for rule in name_rules):
            conflict_reason="입력한 성분명에 연결된 CAS가 다릅니다. 두 식별자를 확인해 주세요."
        if not row["inci_name"] and len({norm(name) for name in resolved_names})>1:
            decisions.append(("확인 필요","CAS에 연결된 성분명이 여러 개입니다. 표준 성분명을 확인해 주세요."))
        if not row["cas_no"] and len({norm(cas) for cas in resolved_cases})>1:
            decisions.append(("확인 필요","성분명에 연결된 CAS가 여러 개입니다. CAS를 확인해 주세요."))
        if row["inci_name"] and not row["cas_no"] and not name_rules:
            query=norm(row["inci_name"])
            suggestions=get_close_matches(query,known_names,n=3,cutoff=0.8) if len(query)>=4 else []
            if suggestions:
                decisions.append(("확인 필요","비슷한 규제 성분명이 있습니다. 후보를 확인해 주세요: "+", ".join(suggestions)))
        if name_counts.get(norm(row["inci_name"]),0)>1 or cas_counts.get(norm(row["cas_no"]),0)>1:
            decisions.append(("확인 필요","중복 성분 입력 · 같은 성분의 함량을 합쳐 한 행으로 입력해 주세요."))
        status,reason=max(decisions,key=lambda d:priority[d[0]]) if decisions else ("해당 없음","등록 JSON에서 일치하는 적용 항목 없음")
        if conflict_reason:
            status,reason="확인 필요",conflict_reason
        results.append({**row,"resolved_name":next(iter(resolved_names)) if len(resolved_names)==1 else "", "resolved_cas":next(iter(resolved_cases)) if len(resolved_cases)==1 else "", "result":status,"reason":reason,"regulation_type":" / ".join(dict.fromkeys(types)) or "—","matched_rules":matched})
    return results

def analyze(country,ingredients,product_scope=None,data_root=None):
    dataset=load_regulations(country,data_root)
    meta=dataset["metadata"]
    source=meta.get("source") or ("일본 후생노동성 「Standards for Cosmetics」" if country=="jp" else "출처 미등록")
    unidentified=dataset.get("unidentified",[])
    return {"state":dataset["state"],"message":dataset["message"],"unidentified":unidentified,"data_hash":dataset.get("data_hash"),
            "data_version":meta.get("version"),"reviewed_at":meta.get("reviewed_at"),"notice":f"스크리닝은 등록된 규제 {source} 기준입니다.",
            "results":screen_rows(ingredients,dataset["prohibited"],dataset["restricted"],product_scope) if dataset["state"]=="ready" else []}
