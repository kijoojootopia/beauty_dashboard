import pytest
import csv
from conftest import write_json
from tab3_market.services.market_service import growth_rate,import_share,market_summary
from tab3_market.services.distributor_service import candidates

def test_growth_share_and_unavailable():
    assert growth_rate(120,100)==20
    assert import_share(20,100)==20
    assert growth_rate(0,100)==-100
    assert growth_rate(100,0) is None
    assert import_share(None,100) is None
    assert import_share(0,100)==0
    with pytest.raises(ValueError):import_share(200,100)
    with pytest.raises(ValueError):import_share(float("nan"),100)

def test_reporting_units_period_and_source_validation(app, tmp_path):
    app.config["MARKET_DATA_ROOT"] = tmp_path / "isolated-market"
    app.config["MARKET_DATA_ROOT"].mkdir()
    target=app.config["MARKET_DATA_ROOT"] / "market_statistics.csv"
    columns=["국가", "사이트_국가명", "연도", "집계기간", "금액_통계기준",
             "점유율_분모", "출처_URL", "한국화장품_수입액_한국측수출통계_천달러",
             "한국전체화장품수출중_해당국가점유율_퍼센트",
             "2026년_1~8월_전년도연간실적대비달성률_퍼센트"]
    rows=[{"국가":"JP", "사이트_국가명":"일본", "연도":year, "집계기간":"연간",
           "금액_통계기준":"USD", "점유율_분모":"한국의 전체 화장품 수출액",
           "출처_URL":"https://example.test/market", columns[7]:amount,
           columns[8]:share, columns[9]:""}
          for year,amount,share in [(2024,100000,20),(2025,120000,24)]]
    def write_rows(values, header=columns):
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer=csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerows(values)

    with app.app_context():
        assert market_summary("jp")["state"]=="data_pending"
        write_rows(rows)
        data=market_summary("jp")
        assert data["state"]=="ready"
        assert data["series"][4]["amount"]==1.2
        assert data["series"][4]["share"]==24
        assert len(data["charts"])==2
        write_rows([{**rows[1], "집계기간":"1~8월 누계"}])
        assert market_summary("jp")["state"]=="data_error"
        write_rows([rows[0], rows[0]])
        assert market_summary("jp")["state"]=="data_error"
        write_rows([{**rows[0], columns[8]:101}])
        assert market_summary("jp")["state"]=="data_error"


def test_distributors_use_country_json_for_initial_and_live_views(app, monkeypatch):
    from tab3_market import routes as market_routes

    root = app.config["MARKET_DATA_ROOT"]
    row = {"name": "Synthetic Vietnam Distributor", "type": "Test distributor",
           "description": "합성 유통사 설명", "product_types": ["스킨케어"],
           "channels": ["Test channel"], "brands": ["Test brand"],
           "source_url": "https://example.test/distributor", "verified_at": "2026-01-01"}
    write_json(root/"asean"/"VN"/"distributors.json", {"state": "ready", "message": "베트남 자료", "data": [row]})
    write_json(root/"asean"/"SG"/"distributors.json", {"state": "ready", "message": "싱가포르 자료", "data": []})
    product = {"id": "test-product", "name": "테스트 제품", "product_type": "스킨케어"}
    with app.app_context():
        for live in (False, True):
            result = candidates("asean", product, "VN", live=live)
            assert result["state"] == "ready"
            assert [item["name"] for item in result["items"]] == [row["name"]]
            assert result["items"][0]["matched"] is True
        assert candidates("asean", product, "SG")["items"] == []

    monkeypatch.setattr(market_routes, "workspace_context", lambda country: {
        "country": {"code": country}, "project": None,
        "selected_product": product, "member_state": "VN"})
    response = app.test_client().get("/api/market/asean/distributors/fragment")
    assert response.status_code == 200
    assert row["name"] in response.text
    assert row["description"] in response.text
    assert row["type"] in response.text
    assert "스킨케어" in response.text
    assert "웹 검색 출처" not in response.text


def test_distributor_json_errors_and_missing_members(app, tmp_path):
    app.config["MARKET_DATA_ROOT"] = tmp_path / "isolated-market"
    app.config["MARKET_DATA_ROOT"].mkdir()
    root = app.config["MARKET_DATA_ROOT"]
    (root / "jp").mkdir()
    with app.app_context():
        assert candidates("asean", None)["state"] == "data_pending"
        assert candidates("eu", None, "FR")["state"] == "data_pending"
        write_json(root/"jp"/"distributors.json", {"state": "ready", "data": "invalid"})
        assert candidates("jp", None)["state"] == "data_error"


def test_eu_distributors_follow_selected_member(app, tmp_path):
    app.config["MARKET_DATA_ROOT"] = tmp_path / "isolated-market"
    app.config["MARKET_DATA_ROOT"].mkdir()
    root = app.config["MARKET_DATA_ROOT"] / "eu"
    (root / "FR").mkdir(parents=True)
    (root / "DE").mkdir()
    def row(name):
        return {"name": name, "source_url": "https://example.test/distributor",
                "verified_at": "2026-01-01", "product_types": ["스킨케어"],
                "channels": [], "brands": []}

    write_json(root / "FR" / "distributors.json", {"state": "ready", "data": [row("Synthetic France Distributor")]})
    write_json(root / "DE" / "distributors.json", {"state": "ready", "data": [row("Synthetic Germany Distributor")]})
    with app.app_context():
        for live in (False, True):
            france = candidates("eu", None, "FR", live=live)
            germany = candidates("eu", None, "DE", live=live)
            assert [item["name"] for item in france["items"]] == ["Synthetic France Distributor"]
            assert [item["name"] for item in germany["items"]] == ["Synthetic Germany Distributor"]
        assert candidates("eu", None, "ES")["state"] == "data_pending"


@pytest.mark.parametrize("section", ["distributors", "news"])
@pytest.mark.parametrize("country,member", [("jp", ""), ("eu", "FR")])
def test_bookmark_fragment_returns_to_market(monkeypatch, section, country, member):
    from html import unescape
    from pathlib import Path
    import re
    from urllib.parse import parse_qs, urlsplit
    from flask import Flask, g
    from platform_core import routes as core_routes
    from tab3_market import routes as market_routes

    # ?? ? ????DB??? ????? API ?? ??? ?? ? ??? ?????.
    root = Path(__file__).resolve().parents[2]
    app = Flask(__name__, template_folder=str(root / "platform_core/templates"))
    app.config.update(TESTING=True, SECRET_KEY="synthetic-test-only")
    app.register_blueprint(core_routes.bp)
    app.register_blueprint(market_routes.bp)
    app.jinja_env.filters["safe_url"] = lambda value: value
    app.jinja_env.globals["csrf_token"] = lambda: "synthetic-token"

    @app.before_request
    def synthetic_user():
        g.user = {"id": "test-user"}

    context = {"country": {"code": country}, "project": {"id": "test-project"},
               "selected_product": {"id": "test-product", "name": "?? ??"},
               "member_state": member}
    monkeypatch.setattr(market_routes, "workspace_context", lambda country: context)
    item = {"name": "?? ???", "title": "?? ??", "url": "https://example.test/news",
            "source_url": "https://example.test/company", "verified_at": "2025-01-01"}
    result = {"state": "ready", "items": [item], "message": ""}
    monkeypatch.setattr(market_routes, "candidates", lambda *args: result)
    monkeypatch.setattr(market_routes, "load_news", lambda *args: result)
    saved = []
    monkeypatch.setattr(core_routes.store, "save_bookmark", lambda *args: saved.append(args))

    client = app.test_client()
    response = client.get(f"/api/market/{country}/{section}/fragment")
    assert response.status_code == 200
    next_url = unescape(re.search(r'name="next" value="([^"]+)"', response.text).group(1))
    target = urlsplit(next_url)
    assert target.path == f"/beauty/{country}/market"
    expected = {"project_id": ["test-project"], "product_id": ["test-product"]}
    if member:
        expected["member_state"] = [member]
    assert parse_qs(target.query) == expected
    response = client.post("/projects/test-project/bookmarks", data={
        "kind": "news" if section == "news" else "distributor",
        "title": "?? ??", "url": item["url"], "next": next_url})
    assert response.status_code == 302 and response.location == next_url
    assert len(saved) == 1 and saved[0][:2] == ("test-user", "test-project")
