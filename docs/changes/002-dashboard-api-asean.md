# UI·ASEAN·외부 API 요청 수정

2026-09-26

## 변경 목적과 결과

1. 로드맵 단계/문서와 통관 단계의 글자를 키웠습니다.
2. 성분 CSV의 열 순서·이름·구분자·인코딩을 유연하게 인식하고, 선택적 OpenAI 열 분류·미리보기·열 수정을 추가했습니다. CSV에 aliases 배열을 요구하지 않습니다.
3. 금지 규칙의 확인 필요는 빨간색, 제한 규칙의 확인 필요는 노란색으로 표시합니다.
4. 확인 대화상자가 있는 프로젝트 삭제 버튼과 소유권·CSRF 검증, 연결 데이터 삭제를 추가했습니다.
5. 지구본/폴더 사이드바가 현재 화면에 맞게 선택 표시됩니다.
6. 상단의 ‘당신의 다음 시장을 만나는 곳’을 제거했습니다.
7. 목적지 VN/TH를 ASEAN으로 통합하고 EU처럼 요청한 10개국을 선택합니다. 기존 프로젝트·URL은 ASEAN으로 연결합니다.
8. 메모를 별도 목록에 누적하고 저장 후 입력창을 비우며 현재 스크롤 위치를 유지합니다. 이전 메모도 한 번만 이관합니다.
9. 성분 일괄 입력 영역을 처음부터 열어 둡니다.
10. Pretendard를 자체 호스팅하고 전체 화면에 적용했습니다.
11. 관세청 수출액·성장률·연도별 추이·전 세계 국가 순위를 홈에 연결했습니다. 국가 통계와 합계 통계는 따로 비동기 로딩합니다.
12. Tab 3은 실제 목적국의 Comtrade 한국산 수입액·성장률·수입 점유율·추이, OpenAI 검색 근거가 있는 유통사, KOTRA 기사를 연결했습니다.
13. 환율 계산기는 한국수출입은행 API, 관세는 팀의 국가별 JSON을 사용합니다.
14. .env.example, API·데이터·저장 계약, README와 cmd 명령을 갱신했습니다. Python 3.10 지원을 확인하고 CI에 3.10/3.12를 설정했습니다.

## 검증과 범위

Python 3.10.21/3.12.14에서 각각 49개 테스트를 통과했습니다. Chromium에서 반응형 화면·메모 위치·CSV 미리보기·선택 표시를 확인했습니다. 실제 API 키를 호출한 검증은 포함하지 않습니다. 상세 내용은 [검증 기록](../validation.md), 키별 연결·통계 범위는 [API 설정](../api_setup.md)을 참조하세요.

기본 통계 품목은 HS 3304이며 전체 화장품 정의와 동일하다고 가정하지 않습니다. 팀 HS 범위는 설정으로 변경합니다. 관세청 국가별 최초 조회는 수백 건이므로 캐시를 사용합니다. 미보고/미등록 국가·통화·관세에 임의 값을 넣지 않습니다.

사용자 원본 .env·DB·로컬 키와 기존 데이터 JSON은 보존했습니다. ASEAN 공통 자료는 제공된 as 자료를 복사하고 10개 목적국의 관세·통관·시장 자료용 빈 파일을 별도 경로에 준비했습니다. 이전 분석 스냅샷을 새 판정으로 덮어쓰지 않습니다. Git 저장소 연결이 없는 ZIP 작업이므로 커밋/PR 대신 이 기록과 수정 파일 목록을 제공합니다.

## 수정 파일

- `.env.example`
- `.github/workflows/tests.yml`
- `.gitignore`
- `docs/api_contracts.md`
- `docs/data_contracts.md`
- `docs/design-baseline.md`
- `docs/validation.md`
- `platform_core/app_factory.py`
- `platform_core/data/countries.json`
- `platform_core/docs/integration_contract.md`
- `platform_core/readme.md`
- `platform_core/routes.py`
- `platform_core/services/country_service.py`
- `platform_core/services/data_loader.py`
- `platform_core/services/database.py`
- `platform_core/services/project_service.py`
- `platform_core/services/workspace_service.py`
- `platform_core/static/css/home.css`
- `platform_core/static/css/theme.css`
- `platform_core/static/js/app.js`
- `platform_core/templates/platform_core/base.html`
- `platform_core/templates/platform_core/home.html`
- `platform_core/templates/platform_core/projects.html`
- `platform_core/templates/platform_core/workspace.html`
- `platform_core/tests/test_workflows.py`
- `readme.md`
- `tab1_regulation/.env.example`
- `tab1_regulation/integrations/other_sources.py`
- `tab1_regulation/readme.md`
- `tab1_regulation/routes.py`
- `tab1_regulation/services/ingredient_parser.py`
- `tab1_regulation/static/css/tab1.css`
- `tab1_regulation/static/js/tab1.js`
- `tab1_regulation/templates/tab1_regulation/index.html`
- `tab1_regulation/templates/tab1_regulation/ingredient_form.html`
- `tab1_regulation/templates/tab1_regulation/screening_table.html`
- `tab1_regulation/tests/test_screening.py`
- `tab2_customs/.env.example`
- `tab2_customs/integrations/exchange_client.py`
- `tab2_customs/readme.md`
- `tab2_customs/routes.py`
- `tab2_customs/services/customs_service.py`
- `tab2_customs/static/css/tab2.css`
- `tab2_customs/templates/tab2_customs/index.html`
- `tab3_market/.env.example`
- `tab3_market/integrations/comtrade_client.py`
- `tab3_market/integrations/kotra_client.py`
- `tab3_market/integrations/openai_client.py`
- `tab3_market/readme.md`
- `tab3_market/routes.py`
- `tab3_market/services/distributor_service.py`
- `tab3_market/services/market_service.py`
- `tab3_market/services/news_service.py`
- `tab3_market/templates/tab3_market/index.html`
- `tab3_market/tests/test_market.py`

## 신규 파일

- `docs/api_setup.md`
- `docs/changes/002-dashboard-api-asean.md`
- `platform_core/data/comtrade_reporters.json`
- `platform_core/data/customs_countries.json`
- `platform_core/docs/changes/002-requested-updates.md`
- `platform_core/integrations/http_client.py`
- `platform_core/integrations/openai_client.py`
- `platform_core/static/fonts/pretendard/LICENSE.txt`
- `platform_core/static/fonts/pretendard/PretendardVariable.woff2`
- `platform_core/static/fonts/pretendard/font.css`
- `platform_core/templates/platform_core/export_rank_card.html`
- `platform_core/templates/platform_core/export_rankings.html`
- `platform_core/templates/platform_core/export_stats.html`
- `platform_core/tests/test_requested_updates.py`
- `tab1_regulation/data/asean/metadata.json`
- `tab1_regulation/data/asean/pipeline_checklist.json`
- `tab1_regulation/data/asean/prohibited_ingredients.json`
- `tab1_regulation/data/asean/regulation_updates.json`
- `tab1_regulation/data/asean/restricted_ingredients.json`
- `tab1_regulation/docs/changes/002-requested-updates.md`
- `tab1_regulation/integrations/ingredient_ai.py`
- `tab1_regulation/tests/test_flexible_csv.py`
- `tab2_customs/data/asean/BN/customs_roadmap.json`
- `tab2_customs/data/asean/BN/metadata.json`
- `tab2_customs/data/asean/BN/tariffs.json`
- `tab2_customs/data/asean/ID/customs_roadmap.json`
- `tab2_customs/data/asean/ID/metadata.json`
- `tab2_customs/data/asean/ID/tariffs.json`
- `tab2_customs/data/asean/KH/customs_roadmap.json`
- `tab2_customs/data/asean/KH/metadata.json`
- `tab2_customs/data/asean/KH/tariffs.json`
- `tab2_customs/data/asean/LA/customs_roadmap.json`
- `tab2_customs/data/asean/LA/metadata.json`
- `tab2_customs/data/asean/LA/tariffs.json`
- `tab2_customs/data/asean/MM/customs_roadmap.json`
- `tab2_customs/data/asean/MM/metadata.json`
- `tab2_customs/data/asean/MM/tariffs.json`
- `tab2_customs/data/asean/MY/customs_roadmap.json`
- `tab2_customs/data/asean/MY/metadata.json`
- `tab2_customs/data/asean/MY/tariffs.json`
- `tab2_customs/data/asean/PH/customs_roadmap.json`
- `tab2_customs/data/asean/PH/metadata.json`
- `tab2_customs/data/asean/PH/tariffs.json`
- `tab2_customs/data/asean/SG/customs_roadmap.json`
- `tab2_customs/data/asean/SG/metadata.json`
- `tab2_customs/data/asean/SG/tariffs.json`
- `tab2_customs/data/asean/TH/customs_roadmap.json`
- `tab2_customs/data/asean/TH/metadata.json`
- `tab2_customs/data/asean/TH/tariffs.json`
- `tab2_customs/data/asean/VN/customs_roadmap.json`
- `tab2_customs/data/asean/VN/metadata.json`
- `tab2_customs/data/asean/VN/tariffs.json`
- `tab2_customs/data/asean/customs_roadmap.json`
- `tab2_customs/data/asean/metadata.json`
- `tab2_customs/data/asean/tariffs.json`
- `tab2_customs/docs/changes/002-requested-updates.md`
- `tab3_market/data/export/asean/BN/distributors.json`
- `tab3_market/data/export/asean/BN/metadata.json`
- `tab3_market/data/export/asean/BN/news.json`
- `tab3_market/data/export/asean/BN/trade_statistics.json`
- `tab3_market/data/export/asean/ID/distributors.json`
- `tab3_market/data/export/asean/ID/metadata.json`
- `tab3_market/data/export/asean/ID/news.json`
- `tab3_market/data/export/asean/ID/trade_statistics.json`
- `tab3_market/data/export/asean/KH/distributors.json`
- `tab3_market/data/export/asean/KH/metadata.json`
- `tab3_market/data/export/asean/KH/news.json`
- `tab3_market/data/export/asean/KH/trade_statistics.json`
- `tab3_market/data/export/asean/LA/distributors.json`
- `tab3_market/data/export/asean/LA/metadata.json`
- `tab3_market/data/export/asean/LA/news.json`
- `tab3_market/data/export/asean/LA/trade_statistics.json`
- `tab3_market/data/export/asean/MM/distributors.json`
- `tab3_market/data/export/asean/MM/metadata.json`
- `tab3_market/data/export/asean/MM/news.json`
- `tab3_market/data/export/asean/MM/trade_statistics.json`
- `tab3_market/data/export/asean/MY/distributors.json`
- `tab3_market/data/export/asean/MY/metadata.json`
- `tab3_market/data/export/asean/MY/news.json`
- `tab3_market/data/export/asean/MY/trade_statistics.json`
- `tab3_market/data/export/asean/PH/distributors.json`
- `tab3_market/data/export/asean/PH/metadata.json`
- `tab3_market/data/export/asean/PH/news.json`
- `tab3_market/data/export/asean/PH/trade_statistics.json`
- `tab3_market/data/export/asean/SG/distributors.json`
- `tab3_market/data/export/asean/SG/metadata.json`
- `tab3_market/data/export/asean/SG/news.json`
- `tab3_market/data/export/asean/SG/trade_statistics.json`
- `tab3_market/data/export/asean/TH/distributors.json`
- `tab3_market/data/export/asean/TH/metadata.json`
- `tab3_market/data/export/asean/TH/news.json`
- `tab3_market/data/export/asean/TH/trade_statistics.json`
- `tab3_market/data/export/asean/VN/distributors.json`
- `tab3_market/data/export/asean/VN/metadata.json`
- `tab3_market/data/export/asean/VN/news.json`
- `tab3_market/data/export/asean/VN/trade_statistics.json`
- `tab3_market/data/export/asean/distributors.json`
- `tab3_market/data/export/asean/metadata.json`
- `tab3_market/data/export/asean/news.json`
- `tab3_market/data/export/asean/trade_statistics.json`
- `tab3_market/docs/changes/002-requested-updates.md`
- `tab3_market/integrations/customs_export_client.py`
- `tab3_market/templates/tab3_market/distributors.html`
- `tab3_market/templates/tab3_market/news.html`
- `tab3_market/templates/tab3_market/statistics.html`
- `tab3_market/tests/test_integrations.py`
