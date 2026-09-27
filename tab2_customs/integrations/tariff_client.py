"""국가별 관세 데이터 연동 확장 위치. 실제 연결은 아직 구현되지 않았습니다."""

def fetch(**query):
    return {"state": "integration_pending", "provider": "국가별 관세 데이터",
            "items": [], "message": "제공처·이용조건·인증·지원 범위 확인 후 연결이 필요합니다."}
