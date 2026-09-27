# 공통 플랫폼

회원가입·로그인·프로젝트·제품·스냅샷·체크·메모·관심 정보·JSON 내보내기와 공통 디자인을 관리합니다.

## 기준·산식

첫 화면 수출 요약은 Tab 3 공개 서비스를 사용합니다. 자체 통계를 중복 보유하지 않습니다.

## 담당 범위

이 모듈 내부만 수정하고 공통 변경은 1번 담당자에게 요청합니다. 앱 실행은 루트 README를 따르세요. 기존 제공 데이터를 보존하며 새 외부 연결과 설정은 [API 설정](../docs/api_setup.md)을 따릅니다.

## 계약·기록

- [데이터 계약](../docs/data_contracts.md)
- [HTTP 계약](../docs/api_contracts.md)
- [공개 저장 서비스](../platform_core/docs/integration_contract.md)
- [최초 변경 기록](docs/changes/001-initial.md)

## 주요 생성 파일

- `__init__.py`
- `app_factory.py`
- `integrations/__init__.py`
- `routes.py`
- `services/__init__.py`
- `services/auth_service.py`
- `services/country_service.py`
- `services/data_loader.py`
- `services/database.py`
- `services/project_service.py`
- `services/workspace_service.py`
- `static/css/home.css`
- `static/css/theme.css`
- `static/js/app.js`
- `templates/platform_core/auth.html`
- `templates/platform_core/base.html`
- `templates/platform_core/bookmarks.html`
- `templates/platform_core/error.html`
- `templates/platform_core/home.html`
- `templates/platform_core/macros.html`
- `templates/platform_core/projects.html`
- `templates/platform_core/workspace.html`
- `tests/__init__.py`
- `tests/test_workflows.py`


## 이번 수정

프로젝트 삭제·메모 목록과 기존 데이터 이관, EU/ASEAN 목적국 검증, 사이드바 선택 상태, Pretendard 자체 호스팅, 비동기 수출 카드·전체 국가 표, 공통 HTTP/AI 클라이언트를 추가했습니다.

[UI·ASEAN·API 변경 기록](docs/changes/002-requested-updates.md)

로그인·회원가입 화면의 시장 수를 현재 7개 국가·지역에 맞추고, 템플릿 줄바꿈을 정리했습니다.
