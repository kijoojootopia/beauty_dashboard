# 최신 검증: 2026-09-26

요청한 UI·ASEAN·CSV·API 연결 변경을 검증했습니다.

- Python 3.10.21: `python -m pytest -q` — **49 passed**
- Python 3.12.14: 같은 테스트 — **49 passed**
- 루트 requirements와 requirements-lock 버전을 사용했습니다. 추가 런타임 패키지는 없습니다. Windows cmd 실행 명령을 제공하며 실제 Windows 머신에서는 실행하지 않았습니다.
- 기존 기능 회귀 검사와 함께 ASEAN 10개국·기존 VN/TH 이관·선택 유지, 프로젝트 소유권/CSRF/연결 데이터 삭제, 메모 목록·기존 메모의 1회 이관, 금지/제한 색상, 유연한 CSV·AI 열 선택을 검증했습니다.
- API 검증은 관세청 XML 페이지/합계/전 세계 국가 코드, Comtrade 보고국·파트너·수입액 성장률/점유율, 환율 고시 단위·이전 영업일, KOTRA 응답 필드, 웹 검색 근거 없는 유통사 제외, 오류/누락 처리와 캐시를 포함합니다. 모의 응답만 사용했습니다.

## 브라우저

임시 DB·합성 통계로 Chromium/Playwright에서 확인했습니다. 운영 파일은 변경하지 않았습니다.

- Pretendard Variable 적용, 지도 목적지 7개, 연도별 수출 선그래프와 상위 국가 막대그래프 렌더링
- 데스크톱·768px·390px 첫 화면에서 페이지 가로 넘침 없음
- 지구본/폴더의 선택 표시 전환
- 제품 메모 저장 전후 스크롤 위치 유지(2379px), 목록 추가, 입력칸 초기화
- 재배열된 CSV 열의 미리보기와 성분 2개 적용
- ASEAN 선택 후 베트남 목적국 유지, 프로젝트 삭제 확인 취소 시 보존
- JavaScript 오류 0건

실제 인증키의 승인/한도 및 외부 제공처의 실응답은 확인하지 않았습니다. 해당 연결 확인 방법은 [API 설정](api_setup.md)에 있습니다. 사용자 원본의 `.env`, DB, 로컬 키와 기존 규제·관세 JSON은 바이트 비교로 보존을 확인했습니다. 첫 실행에 기존 프로젝트/메모를 새 구조로 이관합니다.

---

## 이전 버전 검증 기록 (2026-09-24)

아래는 초기 버전의 역사적 기록입니다. 현재 데이터·폰트·API 연결 상태는 위 최신 기록과 루트 README를 따릅니다.


검증일: 2026-09-24. Python 3.12, Flask 3.1.3, pytest 9.1.1 환경에서 실행했습니다. Windows 실제 머신에서는 실행하지 않았으며 Windows cmd 명령·VS Code debugpy 설정을 포함했습니다.

## 자동 검증

`python -m pytest -q` — **31 passed**

- 8개 국가 × 3개 탭의 렌더링 및 잘못된 국가 처리
- 회원가입·해시 비밀번호·CSRF·안전한 로그인 이동
- 계정 간 프로젝트·제품·메모·이력·내보내기 접근 차단
- 제품 수정 후 이전 스냅샷 불변, 복수 제품, 다른 국가 복사
- 앱 재생성·재로그인 후 데이터 유지
- 제품별 로드맵·문서 체크, 메모, 관심 정보 중복 저장 방지
- CSV 쉼표 성분명, malformed CSV, NaN/무한/음수/100 초과 함량 거부
- CAS 우선 매칭, 제품 범위, null 한도, 자연어 조건·중복 성분의 보수적 판정
- 빈 규칙/부분 준비/손상/누락 구별
- 환율 고시 단위 환산, 음수·비정상 값 거부, 누락과 실제 관세율 0 구별
- 수입 점유율·성장률, 통계 보고국·단위·비교 기간·출처 확인
- 실제 값을 채운 합성 테스트 자료로 홈·공지·관세·환율·시장 그래프·유통사·기사 렌더링

테스트의 합성 자료는 임시 폴더에만 기록합니다. 운영 data 폴더는 빈 틀로 남아 있습니다.

## 사용자 제공 일본 JSON 호환 검증

첨부 원본을 임시 검증 폴더에 설치했습니다.

- 금지 성분 79개
- 제한 성분 190개
- 수출 준비 로드맵 7단계
- 원본 필드·문서 문자열 보존
- 자연어 조건이 있는 제한 성분을 `확인 필요`로 표시

이는 최신 법령의 정확성·완전성을 검증했다는 뜻이 아닙니다. 실제 배포 데이터에는 원본을 자동 포함하지 않았으며 사용자가 import_japan 명령으로 설치할 수 있습니다.

## 브라우저 검증

로컬 Chromium + Playwright에서 회원가입 → 프로젝트 생성 → 제품 입력·분석 → 메모 저장 → 로드맵 완료 → Tab 2/3 이동을 실행했습니다.

- JavaScript 오류 0건
- 화면 콘솔 오류 0건
- 데스크톱 1440×1000 확인
- 모바일 390×844에서 홈·Tab 1 문서 폭 390px: 페이지 가로 넘침 없음
- 성분 표와 가로 타임라인은 내부 가로 스크롤 사용
- Noto Sans KR 자체 호스팅 글꼴 적용 확인

[첫 화면](screenshots/home-desktop.png) · [Tab 1](screenshots/tab1-desktop.png) · [Tab 2](screenshots/tab2-desktop.png) · [Tab 3](screenshots/tab3-desktop.png) · [모바일 첫 화면](screenshots/home-mobile.png)

Tab 1 스크린샷은 **화면 검증용 제품 + 첨부 일본 데이터**를 임시 DB에 사용했습니다. 스크린샷의 계정·제품·DB는 실행 패키지에 포함하지 않습니다. 최초 실행은 빈 프로젝트·데이터 상태입니다.

## 확인하지 않은 범위

외부 API 실제 연결, 최신 공식 규정 내용, 운영 배포·다중 서버·이메일 전송은 이번 검증에 포함하지 않습니다. 현재 앱의 구현 범위는 루트 README에 기록했습니다.

구현 참고: [Flask Application Factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/), [Testing](https://flask.palletsprojects.com/en/stable/testing/), [Security Considerations](https://flask.palletsprojects.com/en/stable/web-security/).
