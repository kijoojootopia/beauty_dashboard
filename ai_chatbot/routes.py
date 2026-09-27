"""챗봇 API. 공통 로그인 및 CSRF 검사를 그대로 사용합니다."""
from flask import Blueprint, request
from platform_core.integrations.http_client import IntegrationError
from platform_core.services.auth_service import login_required

from .service import answer, validate_payload

bp = Blueprint("ai_chatbot", __name__, static_folder="static",
               static_url_path="/chatbot-assets")


@bp.post("/api/chatbot/message")
@login_required
def message():
    if request.content_length and request.content_length > 200_000:
        return {"message": "대화 내용이 너무 깁니다. 새 대화를 시작해 주세요."}, 413
    try:
        question, history = validate_payload(request.get_json(silent=True))
    except ValueError as error:
        return {"message": str(error)}, 400
    try:
        return {"reply": answer(question, history)}
    except IntegrationError as error:
        return {"message": str(error)}, 503