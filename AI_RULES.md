# AI 작업 규칙

1. 작업 전 이 문서와 AGENTS.md를 읽고 한국어로 신규 파일 및 최소 변경 파일을 알립니다.
2. 기존 파일을 임의 삭제·이동·대체하거나 unrelated 리팩터링하지 않습니다. 신규 기능은 해당 담당 폴더에 둡니다.
3. platform_core는 1번, tab1_regulation은 2번, tab2_customs는 3번, tab3_market은 4번 담당입니다. 루트 및 .github/.vscode는 1번 담당입니다. 최초 통합 구축은 사용자 요청에 따라 전체 모듈을 생성합니다.
4. 다른 모듈의 데이터·DB에 직접 쓰지 말고 문서화한 공개 서비스를 호출합니다. 계산은 services, HTTP 처리는 routes, 외부 연동은 integrations에 둡니다.
5. 빈 데이터·연동 오류를 0이나 적합 판정으로 바꾸지 않습니다. 자연어 조건·합계량·예외를 검토 없이 확정하지 않습니다.
6. 변경 후 각 모듈 readme.md, docs/changes 및 루트 readme 요약을 갱신합니다.
7. .env·API 키·DB·업로드·고객 처방을 Git에 올리지 않습니다. 기능별 브랜치와 PR을 사용합니다.
