# 뷰우티 대시보드

> 화장품의 해외 진출 준비에 필요한 규제·관세·무역 통계·시장 정보를 한곳에서 확인하는 Flask 대시보드입니다.

[GitHub 저장소](https://github.com/kijoojootopia/beauty_dashboard) · [실행 방법](#1-바로-실행하기--windows--vs-code) · [데이터 출처](#데이터-출처) · [기능](#2-구현-상태)

<p align="center">
  <img src="docs/screenshots/2026-09-28%20204749.png" alt="대시보드 메인 화면" width="100%">
</p>

<p align="center"><sub>메인 화면 미리보기 · 통계는 API 연결 및 데이터 설정에 따라 달라집니다.</sub></p>

## 프로젝트 목표

국가별 화장품 성분 규제와 수출 준비 항목을 제품·프로젝트별로 관리하고, 관세·환율·무역 통계·시장 정보를 함께 살펴 수출 준비를 돕는 Python·Flask 기반 4인 팀 프로젝트입니다. [Render 데모 주소](https://beauty-dashboard-fjxq.onrender.com/)에서 확인할 수 있으며, 로컬 실행 방법도 아래에 안내합니다.

## 데이터 출처

서비스는 **외부 API에서 실행 시 받아오는 데이터**와 **팀이 국가별 자료를 확인해 저장소에 등록한 데이터**를 함께 사용합니다.

### 외부 API

| 제공처 / API | 사용 데이터 | 설정 키 |
|---|---|---|
| [관세청 품목별 수출입실적(GW)](https://www.data.go.kr/data/15101609/openapi.do) | 한국의 품목별 수출액·연도별 추이 | `CUSTOMS_API_KEY` |
| [관세청 품목별 국가별 수출입실적(GW)](https://www.data.go.kr/data/15100475/openapi.do) | 국가별 한국 수출 시장 현황 | `CUSTOMS_COUNTRY_API_KEY` |
| [UN Comtrade 개발자 포털](https://comtradedeveloper.un.org/) | 목적국이 보고한 한국산 화장품 수입액·점유율·연도별 추이 | `COMTRADE_API_KEY` |
| [대한무역투자진흥공사(KOTRA) 해외시장뉴스](https://www.data.go.kr/data/15034831/openapi.do) | 목적국별 해외시장 기사 | `KOTRA_API_KEY` |
| [OpenAI API](https://platform.openai.com/api-keys) | 유통사 후보 웹 검색, 사용자가 선택한 경우 CSV 열 분류 | `OPENAI_API_KEY` |
| [ExchangeRate-API](https://www.exchangerate-api.com/) | Tab 2 환율 조회·환산 | `EXCHANGE_API_KEY` |

관세청 API는 품목별 합계와 국가별 상세 조회에 두 서비스를 사용합니다. 서비스별 신청·승인과 키 설정은 [API 설정 안내](docs/api_setup.md)를 참고하세요. API 키가 없으면 연결 API 대신 저장소의 등록 데이터를 사용하거나 `데이터 준비 중`으로 표시합니다.

### 국가별 1차 자료와 저장 위치

규제 성분·수출 준비 로드맵은 아래 국가별 폴더의 JSON으로 관리합니다. 각 폴더에는 성분 금지·제한 목록, 로드맵, 데이터 상태 파일이 포함됩니다. 화면의 상세 근거는 해당 JSON의 출처 필드에서 확인할 수 있습니다.

| 국가 / 권역 | 참고하는 1차 자료 | 저장소 데이터 |
|---|---|---|
| 러시아(EAEU) | [EAEU 기술규정 포털](https://eec.eaeunion.org/), TR TS 009/2011 향수·화장품 안전 기술규정 | [`tab1_regulation/data/eac/`](tab1_regulation/data/eac/) |
| 유럽연합(EU) | [화장품 규정 (EC) No 1223/2009](https://eur-lex.europa.eu/eli/reg/2009/1223/oj), [CosIng 성분 데이터베이스](https://single-market-economy.ec.europa.eu/sectors/cosmetics/cosmetic-ingredient-database_en) | [`tab1_regulation/data/eu/`](tab1_regulation/data/eu/) |
| UAE | 화면 자료 목록의 CosIng Annex II·III 및 [GSO 표준 포털](https://www.gso.org.sa/)의 GCC 화장품 표준 GSO 1943:2024 | [`tab1_regulation/data/uae/`](tab1_regulation/data/uae/) |
| 미국 | [FDA 금지·제한 성분 안내](https://www.fda.gov/cosmetics/cosmetics-laws-regulations/prohibited-restricted-ingredients-cosmetics), [색소 허용 목록](https://www.fda.gov/cosmetics/cosmetic-ingredient-names/color-additives-permitted-use-cosmetics), MoCRA 자료 및 California Proposition 65 목록 | [`tab1_regulation/data/us/`](tab1_regulation/data/us/) |
| 일본 | 팀이 정리한 일본 화장품 원문·성분 목록과 수출 로드맵 자료 | [`tab1_regulation/data/jp/`](tab1_regulation/data/jp/) |
| 중국 | 팀이 등록한 화장품안전기술규범 성분 자료 | [`tab1_regulation/data/cn/`](tab1_regulation/data/cn/) |
| ASEAN | [태국 FDA의 ASEAN 화장품 조화 자료](https://cosmetic.fda.moph.go.th/asean-cosmetic-harmonization/) 및 ASEAN Cosmetic Directive 부속서 | [`tab1_regulation/data/asean/`](tab1_regulation/data/asean/) |

관세율과 통관 로드맵은 [국가별 Tab 2 JSON](tab2_customs/data/)에서 관리하며, 화면에 등록된 출처는 각 항목의 URL을 표시합니다. 현재 규제 데이터의 일부 `metadata.json`에는 출처 URL·검토일이 등록되지 않았습니다. 따라서 저장소의 데이터가 최신 공식 규정 전체를 반영한다고 보장하지 않으며, 실제 수출 전에는 링크된 원문과 최신 개정 여부를 확인해야 합니다. 데이터 파일 구조는 [데이터 계약](docs/data_contracts.md), 파일별 경로는 [국가 코드와 데이터 위치](#5-7개-국가-코드와-데이터-넣는-위치)를 참고하세요.

## 목차

- [바로 실행하기](#1-바로-실행하기--windows--vs-code)
- [구현 상태](#2-구현-상태)
- [사용 순서](#3-사용하는-순서)
- [데이터 파일 위치](#5-7개-국가-코드와-데이터-넣는-위치)
- [운영 범위와 제한](#8-운영-범위와-후속-작업)

회원가입·로그인·저장·3개 탭이 연결되어 있습니다. 규제·관세 데이터는 팀이 관리하고, 수출·수입 통계·환율·시장 기사·유통사 검색은 로컬 `.env` 또는 배포 환경 변수에 설정한 API 키로 조회합니다.

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
- 기본 로컬 실행에서는 계정과 작업 내용이 `instance/beauty.sqlite3`에 저장됩니다. `DATABASE_URL`을 설정하면 PostgreSQL을 사용합니다. **로컬 SQLite 파일을 지우면 그 파일에 저장된 내용이 사라집니다.**
- 회원가입 후 사용할 수 있으며 기본 관리자·공용 테스트 계정은 없습니다.
- VS Code Python 확장에서 `junior` 인터프리터를 선택하면 `F5 → 뷰우티 · Flask`로 실행할 수 있습니다.
- 5000번 포트가 사용 중이면 명령 끝에 `--port 5001`을 붙이고 주소의 포트도 바꾸세요.
- 가상환경을 활성화하지 않아도 위의 `junior\Scripts\python.exe` 방식으로 실행할 수 있습니다.

## 2. 구현 상태

| 영역 | 현재 구현된 기능 | 남은 작업 |
|---|---|---|
| 첫 화면 | SVG 세계 지도와 목적지 선택, 관세청 API 기반 한국 수출 통계·국가별 순위·추이 표시 | 배포 환경의 키·승인·API 응답 상태 점검 |
| 계정·저장 | 회원가입·로그인·로그아웃, 비밀번호 해시, CSRF 보호, 사용자별 접근 검사. 로컬 SQLite와 `DATABASE_URL` 기반 PostgreSQL 사용 지원 | 이메일 인증·비밀번호 재설정, 배포 DB 백업·복구 절차 확인 |
| 프로젝트·제품 | 프로젝트 및 제품 저장, EU·ASEAN 실제 회원국 선택, 다른 국가로 프로젝트 복사, JSON 내보내기, 프로젝트 삭제 | JSON 가져오기·복원, 여러 사용자의 팀 공유 |
| Tab 1 · 성분·수출 준비 | 성분 직접 입력·CSV 열 자동 인식·미리보기, 선택형 OpenAI 열 분류, 등록 규칙 기반 판정과 분석 이력, 로드맵 단계·문서 체크, 메모 저장 | 국가별 규제 원문·검토일 보완, 공식 규제 변경 자동 수집 |
| Tab 2 · 관세·통관 | 팀이 등록한 국가별 JSON으로 일반·FTA 관세율과 통관 로드맵 표시, ExchangeRate-API 환율 조회·환산 | 국가별 자료의 최신성·출처 검토 및 누락 자료 보완 |
| Tab 3 · 시장 정보 | UN Comtrade 수입 통계, KOTRA 해외시장뉴스, OpenAI 웹 검색 기반 유통사 후보 연동 | 배포 환경의 API 이용 승인·키·호출 한도 확인, 검색 후보의 담당자 검토 |
| 관심 정보 | 유통사 후보·기사·규제 공지를 사용자별로 저장·해제 | 저장 정보를 팀 계정 간 공유하는 기능 |

앱은 [Render 데모 주소](https://beauty-dashboard-fjxq.onrender.com/)로 배포되어 있습니다. 이 저장소에는 해당 배포의 환경 변수, 실제 DB 연결 방식, 백업 설정이 포함되어 있지 않으므로 배포 환경의 운영 상태는 별도로 확인해야 합니다. 외부 API 연동은 구현되어 있으며, 배포 환경에 유효한 키와 이용 승인이 설정된 경우 조회합니다. 키가 없으면 기능에 따라 저장소 JSON을 사용하거나 `데이터 준비 중`으로 표시하고, 오류 응답은 오류로 표시합니다. 앱은 규제나 통계를 임의로 만들어 채우지 않습니다.

규제 JSON은 국가별 원문 전체 및 최신 개정이 모두 검토되었다는 의미가 아닙니다. 특히 원문 링크나 검토일이 비어 있는 자료는 실제 수출 판단 전에 공식 출처에서 다시 확인해야 합니다. 화면 지도는 개략 SVG이며, 글꼴은 자체 포함한 Pretendard Variable을 사용합니다([라이선스](platform_core/static/fonts/pretendard/LICENSE.txt)).

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
| 1번 | `platform_core/` | 공통 디자인·지도·계정·프로젝트·DB(SQLite/PostgreSQL)·통합 |
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

이 프로젝트는 **로컬 개발 실행과 Render 데모 배포**를 제공합니다. 로컬의 `--debug` 서버는 개발용이므로 외부에 공개하지 마세요. 앱은 `DATABASE_URL`로 PostgreSQL 연결을 지원하지만, 배포 환경에서 실제 사용 중인 DB·영속성·백업 여부는 이 저장소만으로 확인할 수 없습니다. 정식 운영 전에는 HTTPS 쿠키 설정(`COOKIE_SECURE=true`), DB 백업·복구, 접근·요청 제한, 계정 복구 절차를 점검해야 합니다.

공식 규제의 최신성 검토와 관세 자료 관리는 팀에서 수행합니다. 통계·환율·기사·AI API 연동 코드는 구현되어 있으며, 실제 표시 여부는 배포 환경의 키·이용 승인·호출 한도에 달려 있습니다. 환율 API는 실제 키 응답과 환산을 확인했으며, 다른 API는 모의 응답으로 요청·오류 처리를 검증했습니다. 배포 환경에서 각 API 키의 현재 유효성과 승인 상태까지 확인한 것은 아닙니다. 규제 공지 자동 수집은 아직 구현되지 않았습니다.

**기본 통계 범위는 HS 3304입니다.** 한국 화장품 전체 범위와 동일하다고 가정하지 않습니다. 팀이 사용할 화장품 HS 목록을 `COSMETICS_HS_CODES`에 설정하면 수출과 수입 통계가 같은 범위로 바뀝니다. 기본 기간은 최근 완료된 5개년이며 화면에 기간·단위·범위를 표시합니다.

총수입비용·관세액 계산, 실시간 통관 진행 조회, JSON 자동 법령 개정, 유통사 자동 연락은 포함하지 않습니다.

원래 합의한 상세 설계는 [설계 기준안](docs/design-baseline.md)에 원문으로 보존했습니다. 현재 구현 여부는 이 README를 기준으로 확인하세요.
