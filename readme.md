# 뷰우티 대시보드

**VS Code + Python + Flask로 실행하는 4인 팀 프로젝트**입니다. 국가별 성분 스크리닝·수출 준비·관세·시장 정보를 프로젝트와 제품 단위로 관리합니다.

이번 버전은 **로컬 실행 가능한 앱**입니다. 회원가입·로그인·저장·3개 탭이 연결되어 있습니다. 규제·관세 데이터는 팀이 관리하고, 수출·수입 통계·환율·시장 기사·유통사 검색은 `.env`의 API 키로 연결합니다.

## 1. 바로 실행하기 — Windows / VS Code

Python 3.10 이상을 설치하고, VS Code에서 압축을 푼 `beauty_dashboard` 폴더를 여세요. 터미널이 `app.py`와 같은 폴더인지 확인합니다.

**Python 3.10을 계속 사용할 수 있습니다.** 첨부 requirements와 현재 코드에 3.11 전용 의존성은 없습니다. 모듈별 requirements가 비어 있는 상태에서 루트 의존성과 잠금 버전으로 검증합니다.

이미 `junior`를 사용 중이면 Windows 명령 프롬프트(cmd)에서 해당 환경을 활성화하고 아래 명령을 실행하세요. Conda 환경이라면 `conda activate junior`로 활성화합니다.

```bat
python --version
python -m pip install -r requirements.txt -c requirements-lock.txt
if not exist .env copy .env.example .env
python -m flask --app app run --debug
```

새 venv를 만들 때만 다음 명령을 사용합니다. 이 경우 `python`이 3.10인지 먼저 확인하세요.

```bat
python -m venv junior
.\junior\Scripts\python.exe -m pip install -r requirements.txt
if not exist .env copy .env.example .env
.\junior\Scripts\python.exe -m flask --app app run --debug
```

브라우저에서 **http://127.0.0.1:5000/beauty** 를 여세요. 종료는 터미널에서 `Ctrl+C`입니다.

가상환경을 활성화하는 기존 방식도 지원합니다.

```bat
.\junior\Scripts\activate.bat
python -m flask --app app run --debug
```

Mac/Linux:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
[ -e .env ] || cp .env.example .env
.venv/bin/python -m flask --app app run --debug
```

- 첫 실행에 API 키가 필요하지 않습니다. `.env.example`의 인증키는 비어 있고 품목·모델 등 기본 설정만 포함합니다. 키 입력과 화면별 연결은 [API 설정](docs/api_setup.md)을 보세요.
- `SECRET_KEY`를 비워 두면 `instance/secret.key`에 무작위 키를 생성하고 다음 실행에도 재사용합니다.
- 계정과 작업 내용은 `instance/beauty.sqlite3`에 저장됩니다. **이 파일을 지우면 저장 내용이 사라집니다.**
- 회원가입 후 사용할 수 있으며 기본 관리자·공용 테스트 계정은 없습니다.
- VS Code Python 확장에서 `junior` 인터프리터를 선택하면 `F5 → 뷰우티 · Flask`로 실행할 수 있습니다.
- 5000번 포트가 사용 중이면 명령 끝에 `--port 5001`을 붙이고 주소의 포트도 바꾸세요.
- 가상환경을 활성화하지 않아도 위의 `junior\Scripts\python.exe` 방식으로 실행할 수 있습니다.

## 2. 구현 상태

| 영역 | 이번 버전에서 동작하는 기능 | 후속 연결 |
|---|---|---|
| 첫 화면 | 지도·7개 목적지, 관세청 한국 수출액·비교 성장률·연도별 선그래프·주요 수출 시장 막대그래프·전체 국가 표 | 서비스 활용 승인·키 입력 |
| 계정·저장 | 회원가입·로그인·로그아웃, 비밀번호 해시, CSRF, 소유권 검사, SQLite 영속 저장 | 이메일 인증·비밀번호 복구·운영 인프라 |
| 프로젝트 | EU·ASEAN 목적 회원국 선택, 여러 제품, 다른 국가로 복사, JSON 내보내기·프로젝트 삭제 | 내보낸 JSON의 자동 복원·팀 공유 |
| Tab 1 | CSV 열 자동 인식·선택적 AI 분류·미리보기, 판정, 분석 이력, 확대된 로드맵, 문서·단계 체크, 별도 메모 목록·화면 이동 없는 저장 | 국가별 규칙 검토·입력, 공식 공지 자동 수집 |
| Tab 2 | 팀 JSON 기반 일반·FTA 관세율 조회·통관 단계, ExchangeRate-API 환율 계산 | 국가별 관세·통관 데이터 입력 |
| Tab 3 | UN Comtrade 한국산 수입액·성장률·수입 점유율·추이, OpenAI 웹 검색 유통사 후보, KOTRA 기사 | 제공처 키 입력·실제 계정 승인 확인 |
| 관심 정보 | 유통사·기사·규제 공지 저장과 저장 해제 | 제공처별 데이터 확보 |

**사용자가 제공한 기존 규제·데이터를 보존합니다.** API 키가 없으면 등록 JSON을 사용하며, 값이 없으면 `데이터 준비 중`, 손상되거나 API 연결에 실패하면 오류를 표시합니다. 임의의 규제나 통계를 만들지 않습니다. 화면 상단 Tab 1에는 KPI 카드를 두지 않고 시장 요약을 오른쪽에 배치했습니다.

Portflow의 정확한 도구는 확인되지 않아 외부 키가 필요 없는 SVG 개략 지도를 사용합니다. 별도의 지도 CDN·프런트 빌드·Node.js 설치가 필요하지 않습니다. 글꼴은 Pretendard Variable로 통일하고 자체 포함했습니다. [글꼴 라이선스](platform_core/static/fonts/pretendard/LICENSE.txt)를 함께 배포합니다.

## 3. 사용하는 순서

1. 지도 마커 또는 국가 카드에서 목적국을 선택합니다.
2. EU·ASEAN은 실제 목적 회원국을 선택합니다. `프로젝트 시작`을 누르고 회원가입 또는 로그인합니다.
3. 프로젝트를 만들고 `제품 추가`에서 제품명·제품 유형·성분을 입력합니다. CSV는 열 인식 미리보기에서 성분명·CAS·배합 비율을 확인하고 입력칸에 적용합니다. 고정 헤더나 `aliases` 배열은 필요하지 않습니다.
4. `저장하고 분석하기`를 누릅니다. 데이터가 아직 없어도 제품은 저장됩니다.
5. 국가별 규칙 JSON을 등록한 후 `현재 데이터로 재분석`을 누릅니다.
6. 제품별 카드에서 최신 결과와 분석 이력을 확인합니다. 전체 제품·선택 제품 보기를 전환할 수 있습니다.
7. 제품을 선택하고 로드맵의 문서·단계를 체크하거나 메모를 저장합니다. 저장 메모는 별도 목록에 누적되며 입력칸이 비워지고 현재 위치를 유지합니다.
8. Tab 2·3에서도 선택 프로젝트와 제품이 유지됩니다.
9. 내 프로젝트에서 다시 열거나 `내보내기`로 입력·이력·체크 상태·메모·관심 정보를 JSON으로 내려받습니다. `삭제하기`는 확인 후 해당 프로젝트와 연결된 제품·기록을 삭제합니다.

다른 국가로 복사하면 제품 입력만 새 프로젝트로 복사합니다. 분석 이력·체크 상태는 원래 프로젝트에 보존하며 새 국가 기준으로 다시 시작합니다. 다운로드 JSON에는 제품 처방이 포함되므로 팀의 Git 저장소에 넣지 마세요.

## 4. 4인 독립 작업 구역

| 담당자 | 전용 폴더 | 책임 |
|---|---|---|
| 1번 | `platform_core/` | 공통 디자인·지도·계정·프로젝트·SQLite·통합 |
| 2번 | `tab1_regulation/` | 성분·판정·규제 피드·수출 로드맵 |
| 3번 | `tab2_customs/` | 관세·통관·환율 |
| 4번 | `tab3_market/` | 시장·수출·유통사·기사 |

루트 실행·설정·문서·`.github/`·`.vscode/`는 1번 담당자가 관리합니다. 실제 GitHub 계정은 `.github/CODEOWNERS`의 주석을 수정해 등록하세요. CODEOWNERS만으로 파일 수정이 차단되지는 않으므로 브랜치 보호와 필수 리뷰를 함께 설정합니다.

```text
beauty_dashboard/
├── app.py                       # 실행 진입점
├── requirements.txt             # 공통 + 모듈별 의존성
├── requirements-lock.txt        # 실행 검증한 라이브러리 버전
├── requirements-dev.txt         # 테스트 의존성
├── readme.md
├── AI_RULES.md / AGENTS.md
├── .env.example / .gitignore
├── .vscode/                     # F5 실행 설정
├── .github/                     # 리뷰·PR·테스트 설정
├── platform_core/
│   ├── app_factory.py / routes.py
│   ├── services/                # 계정·DB·프로젝트·공개 저장 서비스
│   ├── data/countries.json
│   ├── templates/platform_core/
│   ├── static/css/ / static/js/
│   ├── docs/ / tests/
│   └── requirements.txt / readme.md
├── tab1_regulation/
│   ├── routes.py / import_japan.py
│   ├── services/ / integrations/
│   ├── data/{eac,eu,uae,us,jp,cn,asean}/
│   ├── templates/tab1_regulation/
│   ├── static/css/ / static/js/
│   ├── docs/ / tests/
│   └── requirements.txt / readme.md
├── tab2_customs/                 # 같은 모듈 구조
├── tab3_market/                  # 같은 모듈 구조, data/export/ 사용
├── docs/                        # 구조·입력 계약·변경 이력
├── uploads/                     # Git 제외, 원본 CSV 영구 저장은 하지 않음
└── instance/                    # Git 제외, DB·로컬 키
```

계산은 각 `services/`, 요청 처리는 `routes.py`, 외부 연결은 `integrations/`에 둡니다. 각 모듈의 화면과 정적 파일은 Blueprint 경로로 분리했습니다. 다른 모듈의 DB·파일에 직접 쓰지 않고 [공개 연결 계약](platform_core/docs/integration_contract.md)을 호출합니다.

## 5. 7개 국가 코드와 데이터 넣는 위치

| 화면 표시 | 코드 | 무역 통계 보고국 |
|---|---|---|
| 러시아(EAEU) | `eac` | `RU` — 러시아 통계, EAEU 전체 합계와 구분 |
| 유럽(EU) | `eu` | `EU` — 권역 코드, 실제 목적 회원국은 프로젝트에 별도 저장하며 API는 해당 회원국 기준 |
| UAE | `uae` | `AE` |
| 미국 | `us` | `US` |
| 일본 | `jp` | `JP` |
| 중국 | `cn` | `CN` |
| ASEAN | `asean` | `ASEAN` — 권역 코드, 실제 목적 회원국은 프로젝트에 별도 저장하며 API는 해당 회원국 기준 |

ASEAN 목적국은 요청한 10개국(태국·베트남·인도네시아·싱가포르·말레이시아·필리핀·브루나이·미얀마·캄보디아·라오스)입니다. 권역을 선택한 뒤 국가를 선택하며, 시장·관세·기사·유통사는 선택 국가를 사용합니다. 기존 `vn`/`th` 프로젝트는 첫 실행에 ASEAN + `VN`/`TH`로 이관되고 이전 URL도 연결됩니다.

- 규제: `tab1_regulation/data/<코드>/prohibited_ingredients.json`, `restricted_ingredients.json`
- 수출 로드맵: 같은 폴더의 `pipeline_checklist.json`
- 규제 공지: 같은 폴더의 `regulation_updates.json`
- 관세·통관: `tab2_customs/data/<코드>/tariffs.json`, `customs_roadmap.json`
- 환율: `tab2_customs/data/exchange_rates.json`
- 시장: `tab3_market/data/export/<코드>/trade_statistics.json`, `distributors.json`, `news.json`
- 첫 화면 API 키가 없을 때 읽는 한국 수출 자료: `tab3_market/data/export/korea/export_overview.json`
- ASEAN 공통 성분·로드맵: `tab1_regulation/data/asean/` (사용자가 제공한 `as/` 자료 적용)
- ASEAN 목적국별 관세·통관: `tab2_customs/data/asean/<ISO>/`; 목적국별 시장·유통사·기사: `tab3_market/data/export/asean/<ISO>/`
- EU 목적 회원국 자료도 각 `eu/<ISO>/` 경로로 구분합니다. 규제는 공통 자료를 사용할 수 있습니다.
- 각 국가의 `metadata.json`: 규제/자료 버전·검토일·출처·수집일

상세 필드·빈 데이터 처리·입력 예시는 [데이터 계약](docs/data_contracts.md)을 보세요. 각 담당자가 자기 폴더의 JSON만 편집합니다. 파일 변경 후 새로고침하면 반영되지만 **저장된 분석 이력은 자동 변경되지 않습니다.**

### 첨부했던 일본 JSON 적용

파일 3개를 별도의 폴더에 모은 뒤 아래처럼 실행합니다.

```bat
.\junior\Scripts\python.exe -m tab1_regulation.import_japan --source-dir "C:\경로\일본_JSON"
```

| 원본 파일명 | 적용 파일 |
|---|---|
| `japan_prohibit.json` | `tab1_regulation/data/jp/prohibited_ingredients.json` |
| `japan_restrict.json` | `tab1_regulation/data/jp/restricted_ingredients.json` |
| `japan_cosmetics_export_roadmap.json` | `tab1_regulation/data/jp/pipeline_checklist.json` |

원본 내용과 배열형 구조를 그대로 보존합니다. 기존 데이터가 있으면 기본적으로 중단하며, 본인이 교체를 결정했을 때만 `--replace`를 붙입니다. 최신 규정 검토를 수행한 것으로 표시하지 않습니다.

## 6. 판정과 산식

- 금지 조건 적용 또는 제한 한도 초과: `부적합`
- 자동 판정 가능한 제한 규칙 충족: `적합`
- 등록된 적용 규칙 미일치: `해당 없음`
- 함량·제품 범위·자연어 조건·합계량·중복 입력·예외 등 확인 부족: `확인 필요`
- 파일 누락·부분 준비: `데이터 준비 중`; JSON 손상: `데이터 오류`

일본 원본에 포함된 자연어 조건은 자동으로 법적 의미를 추론하지 않습니다. 전문 검토 후 구조화된 `conditions_verified`, `limit_basis`, `applicable_product_scopes`를 보완하는 방식은 데이터 계약에 설명했습니다. 검토 표시를 일괄 추가하지 마세요.

금지·제한 목록 중 하나가 비어 있으면 준비 중입니다. 실제로 빈 목록임을 확인한 경우에만 metadata의 해당 `complete_lists`를 `true`로 표시합니다. `max_concentration: null`은 무제한·0이 아닙니다.

- 성장률 = `(현재 − 이전) / 이전 × 100`; 이전이 0·누락이면 계산하지 않음. 첫 화면은 한국 수출액, Tab 3은 목적국의 한국산 수입액 기준
- 한국산 수입 비중 = `목적국 보고 한국산 수입액 / 같은 목적국 보고 전체 수입액 × 100`
- 환산액 = `금액 × (기준통화 KRW 환율 / 고시 단위) / (대상통화 KRW 환율 / 고시 단위)`

통계의 보고국·기간·품목·HS 버전·단위·집계 범위를 일치시킵니다. 한국 수출액은 별도 지표이며 한국산 수입 비중의 분자로 사용하지 않습니다. 성장률은 비교 기간을 데이터에 명시한 경우에만 계산합니다.

## 7. 테스트와 개발 규칙

```bat
.\junior\Scripts\python.exe -m pip install -r requirements-dev.txt
.\junior\Scripts\python.exe -m pytest -q
```

검증 범위와 결과는 [검증 기록](docs/validation.md), 이번 변경 내역은 [UI·ASEAN·API 수정 기록](docs/changes/002-dashboard-api-asean.md), 초기 내역은 [최초 구현 기록](docs/changes/001-flask-workspace.md)에 있습니다. 데이터 형식·인증·보안 관련 테스트는 임시 DB와 **합성 테스트 데이터**를 사용하며 운영 데이터에 쓰지 않습니다.

1. AI 작업 전 `AI_RULES.md`를 읽고 한국어로 신규·수정 파일을 보고합니다.
2. 각자 담당 폴더와 기능 브랜치에서 작업합니다. `main`에 직접 개발하지 않습니다.
3. 공통 변경은 1번 담당자에게 요청합니다. API·서비스 연결은 문서에 먼저 기록합니다.
4. 기능별 PR에 기능·파일·검증·실제 데이터/API 여부·제한 사항을 적습니다.
5. 각 모듈 README와 변경 기록을 갱신하고, 1번이 루트 README를 반영합니다.
6. `.env`, `junior/`, DB·키·업로드·실제 고객 처방은 Git에서 제외합니다.

## 8. 운영 범위와 후속 작업

이 패키지는 팀의 **로컬 개발 실행용**입니다. `--debug` 서버를 외부에 공개하지 마세요. 서비스 배포 시 HTTPS, 영속 DB/백업, 운영 서버, 접근·요청 제한, 계정 복구 정책을 별도 구성해야 합니다. `COOKIE_SECURE=true`는 HTTPS 환경에서 설정합니다.

공식 규제 최신성 검토와 관세 데이터 제작은 팀에서 수행합니다. 이번에 연결한 통계·환율·기사·AI API는 유효한 키를 `.env`에 넣고 새로고침하면 조회합니다. 환율은 실제 키로 응답을 확인했으며, 나머지 API의 발급 계정 승인·한도는 공식 요청 형식과 모의 응답으로만 검증했습니다. 규제 공지 자동 수집 확장 지점은 아직 미구현입니다.

**기본 통계 범위는 HS 3304입니다.** 한국 화장품 전체 범위와 동일하다고 가정하지 않습니다. 팀이 사용할 화장품 HS 목록을 `COSMETICS_HS_CODES`에 설정하면 수출과 수입 통계가 같은 범위로 바뀝니다. 기본 기간은 최근 완료된 5개년이며 화면에 기간·단위·범위를 표시합니다.

총수입비용·관세액 계산, 실시간 통관 진행 조회, JSON 자동 법령 개정, 유통사 자동 연락은 포함하지 않습니다.

원래 합의한 상세 설계는 [설계 기준안](docs/design-baseline.md)에 원문으로 보존했습니다. 현재 구현 여부는 이 README를 기준으로 확인하세요.