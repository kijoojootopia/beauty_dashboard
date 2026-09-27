# 모듈 연결 계약 v1

공통 저장 계층은 platform_core만 소유합니다. 각 함수는 Flask application/request context 안에서 사용합니다. 전달하는 user_id는 반드시 서버에서 인증한 `g.user['id']`여야 합니다. 사용자 요청의 user_id를 신뢰하지 않습니다.

| 호출 | 역할 |
|---|---|
| `project_service.project_for(user_id, project_id)` | 소유 프로젝트 조회, 타 소유면 404 |
| `products_for(user_id, project_id)` | 소유 프로젝트의 제품 목록 |
| `product_for(user_id, product_id)` | 소유 제품 조회 |
| `save_product_analysis(user_id, project_id, payload, snapshot, product_id=None)` | 제품과 새 분석 스냅샷을 한 DB 트랜잭션으로 저장 |
| `analyses_for(user_id, product_id)` | 최신순 분석 이력 |
| `tasks_for` / `save_task` | 제품별 단계·문서 상태 |
| `notes_for` / `save_notes` | 제품 메모 목록 조회 / 새 메모 추가·저장 행 반환 |
| `delete_project` | 소유권 확인 후 프로젝트와 연결 자료 트랜잭션 삭제 |
| `save_bookmark` / `bookmarks_for` | 프로젝트 관심 정보 |
| `copy_project` | 다른 국가의 새 프로젝트에 제품 입력만 복사 |
| `export_project` | 인증된 사용자의 프로젝트 내보내기 |

Tab 1은 입력 파싱·판정 후 공통 저장 함수를 호출합니다. Tab 2·3은 `workspace_service.workspace_context(country)`로 동일 프로젝트·제품 선택을 읽습니다. 국가와 프로젝트의 목적국 불일치는 404입니다. 공통 템플릿을 extend하고 각 Blueprint의 static endpoint를 사용합니다.

성분 및 계산 데이터는 같은 프로세스의 **공개 서비스 함수**로 연동합니다. 홈/Tab 1은 `tab3_market.services.market_service.overview()` / `market_summary(country, member_state="", live=True)`를 사용합니다. HTTP API도 제공하며 브라우저에서 추가 연결이 필요할 때 사용합니다. 다른 담당자의 데이터 파일을 복제하지 않습니다.

인증·CSRF·소유권 검사와 DB 스키마는 core 담당자만 변경합니다. 기능별 라이브러리는 각 모듈 requirements.txt에 추가하고 공통 의존성 변경은 통합 담당자에게 요청합니다.


## API·권역 연결

`workspace_context`가 프로젝트/쿼리의 `member_state`, `member_options`, `destination`과 `g.destination_member`를 설정합니다. ASEAN은 공통 규제와 목적국별 통계·관세를 구분합니다. `country_service.destination(country, member_state)`는 권역에 속하지 않는 목적국을 거부합니다.

공통 `integrations.http_client`가 설정·타임아웃·안전한 오류·UTF-8 디스크 캐시를 제공하며 외부 연결 실패는 `IntegrationError`로 전달합니다. `setting`은 요청 시 루트 `.env`를 다시 읽고, 테스트는 명시한 config 키만 사용합니다. 모듈은 운영 키나 HTTP 응답 원문을 화면에 노출하지 않습니다.

홈은 수출 합계와 전체 국가 순위를 따로 비동기 로딩합니다. `overview(include_rankings=True)`가 국가별 조회를 포함하며, Tab 3도 통계·유통사·기사 조각을 독립적으로 불러옵니다. HTML 초기에 쓰는 `live=False`는 등록된 JSON만 읽습니다.
