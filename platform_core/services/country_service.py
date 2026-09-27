import json
from pathlib import Path

COUNTRIES = json.loads((Path(__file__).parents[1] / "data/countries.json").read_text(encoding="utf-8"))
EU_MEMBERS = {
 "AT":"오스트리아", "BE":"벨기에", "BG":"불가리아", "HR":"크로아티아",
 "CY":"키프로스", "CZ":"체코", "DK":"덴마크", "EE":"에스토니아",
 "FI":"핀란드", "FR":"프랑스", "DE":"독일", "GR":"그리스", "HU":"헝가리",
 "IE":"아일랜드", "IT":"이탈리아", "LV":"라트비아", "LT":"리투아니아",
 "LU":"룩셈부르크", "MT":"몰타", "NL":"네덜란드", "PL":"폴란드",
 "PT":"포르투갈", "RO":"루마니아", "SK":"슬로바키아", "SI":"슬로베니아",
 "ES":"스페인", "SE":"스웨덴"
}

def get_country(code):
    for country in COUNTRIES:
        if country["code"] == code:
            return country
    raise ValueError("지원하지 않는 국가입니다.")


ASEAN_MEMBERS = {"TH":"태국","VN":"베트남","ID":"인도네시아","SG":"싱가포르","MY":"말레이시아","PH":"필리핀","BN":"브루나이","MM":"미얀마","KH":"캄보디아","LA":"라오스"}
MEMBER_GROUPS = {"eu": EU_MEMBERS, "asean": ASEAN_MEMBERS}
MEMBER_NAMES = {**EU_MEMBERS, **ASEAN_MEMBERS}
MEMBER_CURRENCIES = {"TH":"THB","VN":"VND","ID":"IDR","SG":"SGD","MY":"MYR","PH":"PHP","BN":"BND","MM":"MMK","KH":"KHR","LA":"LAK"}

def destination(country, member_state=""):
    item = dict(get_country(country))
    members = MEMBER_GROUPS.get(country,{})
    if member_state:
        if member_state not in members:
            raise ValueError("선택한 권역의 목적국을 확인해 주세요.")
        item.update(iso=member_state, name=members[member_state], currency=MEMBER_CURRENCIES.get(member_state,item["currency"]))
    return item

