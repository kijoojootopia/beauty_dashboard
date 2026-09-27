# 시장·유통사

등록 통계의 시장 요약·SVG 그래프·수치 표, 출처가 확인된 유통사 후보·기사 피드를 제공합니다.

## 기준·산식

성장률=(현재-이전)/이전×100. 한국산 수입 비중=목적국 보고 한국산 수입액/목적국 보고 전체 수입액×100. 한국 수출액을 분자로 사용하지 않습니다.

## 담당 범위

이 모듈 내부만 수정하고 공통 변경은 1번 담당자에게 요청합니다. 앱 실행은 루트 README를 따르세요. 기존 제공 데이터를 보존하며 새 외부 연결과 설정은 [API 설정](../docs/api_setup.md)을 따릅니다.

## 계약·기록

- [데이터 계약](../docs/data_contracts.md)
- [HTTP 계약](../docs/api_contracts.md)
- [공개 저장 서비스](../platform_core/docs/integration_contract.md)
- [최초 변경 기록](docs/changes/001-initial.md)

## 주요 생성 파일

- `__init__.py`
- `integrations/__init__.py`
- `integrations/comtrade_client.py`
- `integrations/kotra_client.py`
- `integrations/openai_client.py`
- `routes.py`
- `services/__init__.py`
- `services/distributor_service.py`
- `services/market_service.py`
- `services/news_service.py`
- `static/css/tab3.css`
- `templates/tab3_market/index.html`
- `tests/__init__.py`
- `tests/test_market.py`


## 이번 수정

관세청 전체 수출·전 세계 국가 순위, UN Comtrade 실제 목적국 한국산 수입액·성장률·점유율·추이, OpenAI 웹 검색 유통사 후보, KOTRA 화장품 기사를 연결했습니다.

[UI·ASEAN·API 변경 기록](docs/changes/002-requested-updates.md)
