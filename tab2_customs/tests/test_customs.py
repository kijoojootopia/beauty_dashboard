from decimal import Decimal
import pytest
from conftest import write_json
from tab2_customs.services.customs_service import convert_currency,lookup_tariffs,calculate_exchange

def test_quoted_currency_units():
    assert convert_currency(100,900,1300,100,1)==Decimal(900)/Decimal(1300)
    assert convert_currency(1300,1,1300)==1
    assert convert_currency(0,1,1300)==0

@pytest.mark.parametrize("amount,rate",[("NaN",1),(-1,1),(10,0),(10,-1),(10,"Infinity")])
def test_invalid_exchange(amount,rate):
    with pytest.raises(ValueError):convert_currency(amount,1,rate)

def test_missing_rates_and_true_zero_tariff(app):
    with app.app_context():
        with pytest.raises(ValueError,match="선택한 통화의 환율이 아직 등록되지 않았습니다."):calculate_exchange(100,"KRW","ZZZ")
        # 실제 등록 데이터 대신 임시 복사본으로 빈 데이터 상태를 구성합니다.
        write_json(app.config["CUSTOMS_DATA_ROOT"]/"jp/tariffs.json",[])
        assert lookup_tariffs("jp","KR","330499")["state"]=="data_pending"
        write_json(app.config["CUSTOMS_DATA_ROOT"]/"jp/tariffs.json",[{"origin":"KR","hs_code":"3304990000","rate":0,"rate_type":"test-only","rate_unit":"%"}])
        result=lookup_tariffs("jp","KR","330499")
        assert result["state"]=="ready" and result["items"][0]["rate"]==0
        assert lookup_tariffs("jp","CN","330499")["state"]=="no_match"
