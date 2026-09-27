# HTTP 계약 v1

대부분의 쓰기는 Jinja HTML form + POST + redirect 방식입니다. JSON 본문을 받는 쓰기 API는 현재 없습니다. 모든 변경 요청에는 세션과 일치하는 `csrf_token` 폼 필드 또는 `X-CSRF-Token` 헤더가 필요합니다. GET 요청은 상태를 변경하지 않습니다.

| Method | 경로 | 의미 |
|---|---|---|
| GET | `/beauty` | 국가 선택·첫 화면 |
| GET/POST | `/register`, `/login` | 계정 생성·로그인, 내부 경로 `next`만 허용 |
| POST | `/logout` | 로그아웃 |
| GET/POST | `/projects` | 소유 프로젝트 목록·생성 |
| GET | `/beauty/<country>/regulation` | Tab 1 |
| GET/POST | `/beauty/<country>/customs` | Tab 2 및 환율 환산 |
| GET | `/beauty/<country>/market` | Tab 3 |
| POST | `/projects/<id>/products/analyze` | 제품 등록/수정과 분석 이력 추가 |
| POST | `/products/<id>/reanalyze` | 현재 입력·규칙으로 새 분석 이력 |
| POST | `/products/<id>/tasks` | `task_id`, `completed` 1/0 저장 |
| POST | `/products/<id>/notes` | `notes`를 메모 목록에 추가; JSON 응답 지원 |
| POST | `/projects/<id>/delete` | 소유 프로젝트 및 연결 제품·이력·메모·체크·관심 정보 삭제 |
| POST | `/api/ingredients/preview` | 인증·CSRF 후 CSV 열 인식/AI 보조/매핑 미리보기, DB 저장 없음 |
| POST | `/projects/<id>/copy` | `name`, `country`, `member_state`로 복사 |
| GET | `/projects/<id>/export` | 소유 프로젝트 JSON 다운로드 |
| GET/POST | `/projects/<id>/bookmarks` | 목록/관심 정보 저장 |
| POST | `/projects/<id>/bookmarks/<id>/delete` | 관심 정보 해제 |
| GET | `/api/projects/<id>` | 인증·소유권 확인 후 프로젝트 JSON |
| GET | `/api/market/<country>/summary` | 공개 국가 시장 JSON |
| GET | `/api/exports/overview` | 공개 한국 수출 JSON |

화면 query: `project_id`, `product_id`, `member_state`. EU·ASEAN의 프로젝트가 없을 때도 `member_state`로 실제 목적국을 선택합니다. 프로젝트가 있으면 저장된 목적국을 사용합니다. Tab 1 `edit=<product_id>`는 수정 폼. project_id 없이 정보 둘러보기가 가능합니다. 인증되지 않은 HTML 프로젝트 요청은 로그인으로 이동하고 JSON API는 401, 타인의 객체는 404, CSRF 오류는 400입니다. 제품 폼 검증 오류는 400이며 DB를 변경하지 않습니다.

제품 저장: `name`, `product_type`, `hs_code` 선택, `product_id` 수정 시 선택. 입력 우선순위는 `ingredients_csv` multipart → `ingredients_text` → 반복된 `inci_name`, `cas_no`, `concentration`. 업로드는 최대 2 MiB, 제품 성분은 1~500개입니다.

시장 응답 `state`: `ready`, `data_pending`, `data_error`. 준비 중/오류에서는 실제 0이나 적합 결과를 만들지 않습니다. 관세 조회에서 등록 데이터가 있으나 조건이 일치하지 않으면 `no_match`입니다.

## 추가 응답과 비동기 화면

메모 POST는 `Accept: application/json`일 때 `{note: {id, product_id, content, created_at}}`를 반환합니다. 실패는 `{message}`와 400입니다. HTML 요청은 제품 화면의 `#product-notes`로 이동합니다. 메모는 1~5000자이며 공백만 있는 입력을 거부합니다.

CSV preview는 multipart `ingredients_csv`, 선택 `use_ai=1`, 수동 매핑 시 `mapping` JSON(0부터 시작하는 열 번호 또는 null)·`has_header=1/0`을 받습니다. 응답은 `has_header`, `mapping`, `columns`, `ingredients`, `sample`, `message`입니다. 인식한 행을 사용자가 확인·적용한 후 기존 분석 저장 경로를 사용합니다.

| GET 경로 | HTML 조각 |
|---|---|
| `/api/exports/fragment` | 수출액·성장률·연도별 선그래프 |
| `/api/exports/rank-card` | 수출 상위 국가 막대그래프 |
| `/api/exports/rankings-fragment` | 전체 국가별 수출 표 |
| `/api/market/<country>/<section>/fragment` | `statistics`, `distributors`, `news`; 실제 목적국·제품 문맥 반영 |

외부 API가 연결되면 서버에서만 키를 사용합니다. 요청 형식·캐시·키별 연결은 [API 설정](api_setup.md)을 따릅니다. 인증 오류/부분 통계는 0으로 대신하지 않고 화면에 상태를 표시합니다. 미구현인 규제 공지 자동 수집과 관세 API 스텁은 호출하지 않습니다.
