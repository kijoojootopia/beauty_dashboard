# 규제·수출 준비

CSV/텍스트/입력 행 파싱, 규제 로딩·판정, 공식 공지 수동 등록·제품 매칭, 가로 로드맵을 관리합니다.

## 기준·산식

함량은 완제품 질량%. 자연어·성분군·합계량·중복 성분은 확인 필요. 미일치는 해당 없음. 데이터 누락은 별도 준비 상태.

## 담당 범위

이 모듈 내부만 수정하고 공통 변경은 1번 담당자에게 요청합니다. 앱 실행은 루트 README를 따르세요. 기존 제공 데이터를 보존하며 새 외부 연결과 설정은 [API 설정](../docs/api_setup.md)을 따릅니다.

## 계약·기록

- [데이터 계약](../docs/data_contracts.md)
- [HTTP 계약](../docs/api_contracts.md)
- [공개 저장 서비스](../platform_core/docs/integration_contract.md)
- [최초 변경 기록](docs/changes/001-initial.md)

## 주요 생성 파일

- `__init__.py`
- `import_japan.py`
- `integrations/__init__.py`
- `integrations/eu_source.py`
- `integrations/jp_source.py`
- `integrations/other_sources.py`
- `integrations/us_source.py`
- `routes.py`
- `services/__init__.py`
- `services/ingredient_parser.py`
- `services/regulation_feed.py`
- `services/regulation_loader.py`
- `services/roadmap_service.py`
- `services/screening_service.py`
- `static/css/tab1.css`
- `static/js/tab1.js`
- `templates/tab1_regulation/index.html`
- `templates/tab1_regulation/ingredient_form.html`
- `templates/tab1_regulation/input_error.html`
- `templates/tab1_regulation/roadmap.html`
- `templates/tab1_regulation/screening_table.html`
- `tests/__init__.py`
- `tests/test_screening.py`


## 이번 수정

고정 헤더 없는 CSV 열 인식·선택적 AI 보조·수동 미리보기, 기본으로 열린 일괄 입력, 금지 확인 필요의 빨간색 표시, 로드맵 글자 확대, 별도 메모 목록을 연결했습니다. ASEAN 공통 규제는 사용자 제공 as 자료를 보존해 적용합니다.

[UI·ASEAN·API 변경 기록](docs/changes/002-requested-updates.md)
