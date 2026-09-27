import pytest
from conftest import write_json
from tab3_market.services.market_service import growth_rate,import_share,market_summary

def test_growth_share_and_unavailable():
    assert growth_rate(120,100)==20
    assert import_share(20,100)==20
    assert growth_rate(0,100)==-100
    assert growth_rate(100,0) is None
    assert import_share(None,100) is None
    assert import_share(0,100)==0
    with pytest.raises(ValueError):import_share(200,100)
    with pytest.raises(ValueError):import_share(float("nan"),100)

def test_reporting_units_period_and_source_validation(app):
    row={"period":"2024","reporter":"JP","unit":"USD","hs_scope":"3304","hs_version":"2022","source":"TEST ONLY","coverage":"annual","total_imports":100,"korean_imports":20,"korea_exports":30,"export_reporter":"KR","export_source":"TEST ONLY"}
    target=app.config["MARKET_DATA_ROOT"]/"jp/trade_statistics.json"
    with app.app_context():
        assert market_summary("jp")["state"]=="data_pending"
        write_json(target,{"series":[row,{**row,"period":"2025","previous_period":"2024","total_imports":120,"korean_imports":24}]})
        data=market_summary("jp")
        assert data["growth"]==20 and data["share"]==24/120*100
        assert len(data["charts"])==3
        write_json(target,{"series":[row,{**row,"period":"2025","unit":"JPY"}]})
        assert market_summary("jp")["state"]=="data_error"
        write_json(target,{"series":[{**row,"reporter":"KR"}]})
        assert market_summary("jp")["state"]=="data_error"
        write_json(target,{"series":[{**row,"export_source":None}]})
        assert market_summary("jp")["state"]=="data_error"
