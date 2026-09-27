# 데이터 입력 계약 v1

UTF-8 JSON을 사용합니다. `[]`는 아직 등록된 행이 없다는 뜻입니다. `null`을 0으로 바꾸지 않습니다. 다음 예시의 `TEST`·가상 이름·수치는 **구조 설명용 합성 예시이며 실제 규제·통계가 아닙니다**. 운영 폴더에는 들어 있지 않습니다.

## 공통 메타데이터

각 국가의 `metadata.json`:

```json
{
  "version": null,
  "reviewed_at": null,
  "source": null,
  "source_url": null,
  "last_collected_at": null
}
```

Tab 1은 추가로 `complete_lists: {"prohibited": false, "restricted": false}`를 사용합니다. 목록에 실제 행이 있으면 해당 목록을 읽을 수 있습니다. 비어 있는 목록은 검토 완료 플래그가 `true`여야 분석 준비 상태로 인정합니다. **파일 누락은 플래그와 관계없이 준비 중**입니다. 빈 목록이 최신 법령 전체에서 정말 비어 있다는 뜻인지 검토한 후 플래그를 설정하세요. 두 규제 파일과 메타데이터를 함께 SHA-256으로 해시하여 분석 이력에 보존합니다.

검토일과 수집일은 다릅니다. 규제·관세는 사람이 확인한 자료를 수동 등록합니다. 수출·수입·환율·기사·유통사 외부 연동은 제공처와 조회 시점을 별도로 표시합니다. `source_url`, `url`, `guide_url`, `website`는 http/https 주소만 링크로 표시합니다.

## Tab 1: 금지·제한 성분

최상위는 객체 배열입니다. 기존 일본 파일의 필드는 그대로 읽습니다.

| 필드 | 형식 | 설명 |
|---|---|---|
| `inci_name` | 문자열 | 원문 성분명. 이름 또는 CAS 중 하나 필수 |
| `cas_no` | 문자열 | 알려지지 않으면 빈 문자열. 양쪽 CAS가 있으면 CAS 우선 |
| `kr_name` | 문자열 | 선택 국문 이름 |
| `aliases` | 문자열 배열 | 검증한 동의어만 선택 추가 |
| `status` | 문자열 | 원본 상태 보존. 실제 금지/제한 분류는 파일 위치 기준 |
| `max_concentration` | 숫자 / null | 최종 제품 내 함량 %. null은 판단 불가 |
| `product_type_scope` | 문자열 | `ALL` 또는 원문. 자유 문장은 자동 판정하지 않음 |
| `conditions`, `conditions_kr` | 문자열 | 조건 원문/국문 |
| `regulation_source` | 문자열 | 조문·표·출처 등 근거 |
| `applicable_product_scopes` | 문자열 배열 | 검토한 적용 범위 구조화 값 |
| `conditions_verified` | true/false | 추가 조건 전체를 검토해 현재 수치 판정이 충분함을 확인한 경우만 true |
| `limit_basis` | 문자열 | 검토한 개별 질량%이면 `individual_percent`; 성분군 합계는 자동 판정하지 않음 |

제품 유형 코드는 `leave_on`, `rinse_off`, `lip`, `eye`, `sunscreen`, `other`입니다. 국가별 법적 분류를 이 유형 코드 하나로 확정하지 않습니다. 일본 원문의 긴 제품 범위는 명시적 매핑 전까지 확인 필요입니다.

CAS·이름을 모두 정규화해 정확히 일치시키며, 부분 문자열·유사도·모델 추정으로 성분군을 확장하지 않습니다. 식별되지 않은 이름은 `해당 없음`으로 표시하고 입력을 보존합니다. 조건이 있는 금지 성분도 검토 완료 표시가 없으면 확인 필요입니다. 동일 성분/CAS가 중복되면 함량 분할로 적합 판정을 받지 않도록 확인 필요로 처리합니다.

입력 CSV는 고정 헤더나 `aliases` 배열이 필요하지 않습니다. 열 제목·CAS 패턴·숫자/백분율을 함께 보고 성분명·CAS·배합 비율을 분류합니다. 열 순서가 달라도 되고, 헤더 없는 자료·UTF-8/BOM·CP949·UTF-16 BOM·쉼표/탭/세미콜론/파이프 구분을 지원합니다. 쉼표가 있는 이름·소수는 CSV 규칙에 따라 큰따옴표로 감쌉니다. 번호·가격·질량을 함량으로 쓰지 않도록 미리보기에서 확인하세요.

AI 보조는 선택 사항입니다. 체크했을 때만 첫 12행을 OpenAI로 보내 열 번호를 분류하며, 성분·CAS·함량이나 법적 판정을 생성하지 않습니다. 인식이 모호하면 직접 열을 선택합니다. 입력 후에는 기존 규제 DB의 검증된 CAS/이름/동의어로 분석합니다. 규제 JSON의 선택 필드 `aliases`는 기존 데이터 호환을 위해 유지합니다.

직접 입력은 한 줄 한 성분, CAS·함량은 탭으로 구분합니다. 0~100의 유한한 함량만 허용하고 제품 합계 100% 초과를 거부합니다. CSV는 500개 성분·30열까지 처리합니다.

## Tab 1: 로드맵

```json
[
  {
    "stage_step": 1,
    "task_id": "COUNTRY_TASK_ID",
    "task_name": "등록할 작업명",
    "required_doc": "문서 A, 문서 B(세부1, 세부2)",
    "estimated_days": null,
    "is_mandatory": true,
    "guide_url": null
  }
]
```

`task_id`는 국가 안에서 고유하고 변경하지 않는 값입니다. `required_doc`가 문자열이면 쉼표를 임의 분리하지 않고 한 문서 묶음으로 표시합니다. 개별 체크가 필요하면 `['문서 A','문서 B(세부1, 세부2)']` 형태의 **문자열 배열**로 직접 구조화하세요. 문서명 해시를 체크 키로 사용하므로 문서 내용이 달라지면 새 항목으로 취급됩니다. 단계 완료와 문서 완료는 각각 저장하며 자동으로 서로를 체크하지 않습니다.

## Tab 1: 공지

`regulation_updates.json` 객체 배열. 주요 필드:

```json
[
  {
    "title": "공식 공지 제목",
    "scope": "administrative",
    "ingredients": [],
    "product_types": [],
    "status": "상태 미확인",
    "published_at": null,
    "effective_at": null,
    "transition_end": null,
    "summary": "이용이 허용된 범위의 요약",
    "url": "https://example.org/official-source",
    "uncertain": true
  }
]
```

공통 행정이면 `scope=administrative`. 성분 연관이면 `ingredients`에 검증한 성분명 또는 CAS, 유형이면 `product_types`에 위 제품 유형 코드를 입력합니다. 원문에 없는 날짜·의무는 채우지 않습니다. 성분군 매핑은 사람이 검토해 추가해야 합니다.

## Tab 2: 관세

`tariffs.json` 객체 배열:

```json
[
  {
    "origin": "KR",
    "hs_code": "3304990000",
    "product_name": "자료상 품목명",
    "rate_type": "MFN",
    "rate": null,
    "rate_unit": "%",
    "agreement": null,
    "conditions": "원산지 조건과 필요 증빙",
    "as_of": null,
    "source": null,
    "source_url": null
  }
]
```

위 코드는 형식 예시입니다. 실제 대상국 품목 분류를 확인하세요. HS 코드는 **문자열**로 유지합니다. 일반·협정 세율을 각각 별도 행으로 입력합니다. 6자리 조회는 같은 접두어의 세부 코드 후보도 보여 줍니다. 자동으로 세부 코드·협정·원산지를 결정하지 않습니다. 실제 `rate=0`만 0으로 표시하고 null은 미확인입니다. 관세액은 계산하지 않습니다.

`customs_roadmap.json`: 객체 배열. `task_name`, `description`, `required_doc`(문자열/문자열 배열), `owner`, `guide_url`을 표시합니다. 배열 순서를 단계 순서로 사용합니다. 실제 진행 조회나 상태 자동 갱신은 없습니다.

## Tab 2: 환율

`data/exchange_rates.json`:

```json
{
  "as_of": null,
  "source": null,
  "source_url": null,
  "rates": []
}
```

각 rate는 `{"currency":"JPY", "krw_rate":900, "unit":100}`처럼 입력합니다. **이는 단위 설명용 합성 예시**로, 100 JPY당 900 KRW를 의미합니다. 모든 통화는 원화 기준 고시 값으로 통일합니다. KRW는 내부에서 환율 1/단위 1로 처리합니다. 실제 기준일·출처가 없거나 선택 통화가 누락되면 계산하지 않습니다. 휴일이면 실제 사용한 이전 영업일을 `as_of`에 기록합니다.

## Tab 3: 시장 통계

`trade_statistics.json` 최상위는 `{ "series": [] }`입니다. 기간순으로 정렬할 수 있는 `YYYY` 또는 `YYYY-MM`을 사용하며 한 파일에서 주기를 섞지 않습니다.

```json
{
  "series": [
    {
      "period": "2025",
      "previous_period": "2024",
      "reporter": "JP",
      "coverage": "annual, destination-reported imports",
      "hs_scope": "3304",
      "hs_version": "2022",
      "unit": "USD",
      "total_imports": null,
      "korean_imports": null,
      "source": "실제 자료 제공처",
      "source_url": null,
      "korea_exports": null,
      "export_reporter": "KR",
      "export_source": null,
      "export_source_url": null
    }
  ]
}
```

- `total_imports`와 `korean_imports`는 같은 행의 보고국·기간·품목·단위·집계 범위를 공유합니다.
- 한국 수출액은 `korea_exports`이며 반드시 `export_reporter=KR`와 수출액 출처를 기록합니다. 행의 기간·품목·통화 단위와 맞춰 정규화한 값을 넣습니다.
- `previous_period`가 바로 이전 등록 행의 기간과 같을 때만 성장률을 계산합니다. ‘전년 동기’와 단순 ‘직전 기간’을 구분해 입력하세요.
- EU·ASEAN에서 실제 목적국을 선택하면 `reporter`는 `DE`, `VN` 등 해당 국가 코드입니다. 권역 전체 자료는 별도 집계 자료임을 `coverage`에 명시하고 회원국 수치와 섞지 않습니다. API 연결은 선택 국가 기준이며 ASEAN 자체를 Comtrade 보고국으로 요청하지 않습니다. 러시아는 RU와 EAEU 전체 합계를 혼용하지 않습니다.
- 차트의 누락값은 선을 끊고 표에 `—`로 표시합니다. 0을 만들지 않습니다.
- 현재 한 파일은 하나의 품목·단위·집계 범위를 가집니다. 여러 HS나 서로 다른 단위를 비교하려면 별도 구조 확장이 필요합니다.

`korea/export_overview.json`: `period`, `previous_period`, `unit`, `source`, `source_url`, `total_exports`, `previous_exports`, `rankings`, `series`. 순위는 같은 기간/품목/단위 기준의 `[{"country":"jp","name":"일본","value":...}]`, 추이는 `[{"period":"2025","value":...}]`입니다. 첫 화면은 수출액 내림차순으로 국가 순위를 표시합니다. 숫자는 문자열이 아닌 유한한 숫자입니다.

## Tab 3: 유통사·기사

유통사 `distributors.json`: `name`, `website`, `contact`, `product_types`(배열), `channels`(배열), `brands`(배열), `source_url`, `verified_at`. 회사명·근거 URL·확인일이 있는 행만 후보로 표시합니다. 등록 유형이 선택 제품과 맞으면 우선 정렬하고 그 사실만 추천 근거로 표시합니다. OpenAI 연결 시 실제 웹 검색에 등장한 출처 URL이 있는 후보만 사용하며 근거 설명을 표시합니다. AI 검색 후보와 직접 등록 자료를 구분합니다. 연락처·거래 가능 여부는 담당자가 확인합니다.

기사 `news.json`: `title`, `source`, `published_at`, `url`. 기사 본문은 수집하지 않으며 제목과 원문 링크를 표시합니다. 제목 재사용 등 제공처 이용조건을 별도 확인하세요.


## 권역별 저장과 메모

서비스 목적지는 `eac`, `eu`, `uae`, `us`, `jp`, `cn`, `asean`입니다. 프로젝트의 `member_state`에 EU/ASEAN 실제 목적국 ISO 코드를 저장합니다. ASEAN의 규제·기본 로드맵은 `asean/`, 관세·통관·시장·기사·유통사는 `asean/<ISO>/`로 분리합니다. 다른 국가 자료로 빈 회원국 값을 대신하지 않습니다.

`product_notes`는 `id`, `product_id`, `content`, `created_at`를 저장하며 최신순으로 조회합니다. 기존 `products.notes` 값은 첫 실행에 한 번만 목록으로 이관합니다. 내보내기의 각 제품에 `note_list`가 포함됩니다. 프로젝트 삭제는 소유권을 확인하고 연결된 모든 작업 데이터를 한 트랜잭션으로 삭제합니다.
