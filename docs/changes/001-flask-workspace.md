# 001 — Flask 로컬 실행 프로젝트

이전 `beauty_team_starter`와 `deliverables/readme.md`는 수정하지 않고 새 프로젝트로 구현했습니다.

- 4개 전용 모듈을 Blueprint로 연결. Flask factory와 최소 app.py 진입점.
- 라벤더·화이트 화면, SVG 개략 지도·연결선·국가 버튼, 상단 탭, 가로 로드맵.
- SQLite, 비밀번호 scrypt 해시, 세션, CSRF, 소유권 검사, 로그인 시도 제한, 안전한 내부 리다이렉트.
- 계정별 프로젝트·복수 제품·수정·재분석 스냅샷·체크·메모·관심 정보·JSON 내보내기.
- 국가 변경은 새 프로젝트로 제품 입력만 복사. 이전 분석을 덮어쓰지 않음.
- 빈 국가별 JSON, 사용자 제공 일본 원본 설치 명령, 부분 준비/손상 상태 분리.
- CSV 쉼표 이름, 비정상 함량, CAS 매칭, 서술형 조건, null 한도, 중복 성분 처리.
- 관세·통관·환율 및 시장 그래프·유통사·기사의 JSON 연결 함수.
- 외부 API는 확장 파일과 미연결 상태만 제공. 가상의 실데이터를 포함하지 않음.
- VS Code 실행 설정, 팀 문서, 데이터·HTTP 계약, 테스트 및 CI 틀 추가.

주요 생성 파일: 루트 app.py·실행 설정·README, platform_core의 factory/routes/services/templates/static, 각 tab의 routes/services/integrations/templates/static/data/tests, docs의 설계·계약·검증 문서. 상세 전체 목록은 `docs/file_manifest.txt`에 있습니다.

제한 사항: 공식 자료의 최신성·법적 적용 확정, 외부 API 실제 연결, 서비스 배포, 팀 공유, 이메일 인증·복구는 후속 작업. 지도는 Portflow 연동 전 SVG 구현입니다.
