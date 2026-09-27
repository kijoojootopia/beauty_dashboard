# 관세·통관

HS·원산지별 등록 관세율 비교, 통관 절차와 환율 환산을 제공합니다.

## 기준·산식

환산액 = 금액 × (기준 통화의 KRW 환율 / 고시 단위) / (대상 통화의 KRW 환율 / 고시 단위). 관세액 계산은 제공하지 않습니다.

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
- `integrations/exchange_client.py`
- `integrations/tariff_client.py`
- `routes.py`
- `services/__init__.py`
- `services/customs_service.py`
- `static/css/tab2.css`
- `templates/tab2_customs/index.html`
- `tests/__init__.py`
- `tests/test_customs.py`


## 이번 수정

관세·통관은 팀 JSON으로 유지하고 ASEAN 목적국별 경로를 읽습니다. 한국수출입은행 인증키로 환율을 조회하며 휴일 이전 영업일·100통화 고시 단위를 처리합니다.

[UI·ASEAN·API 변경 기록](docs/changes/002-requested-updates.md)
