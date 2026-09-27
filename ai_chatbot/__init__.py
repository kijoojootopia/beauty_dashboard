"""기존 템플릿을 변경하지 않고 챗봇 자산을 연결합니다."""
import hashlib

from flask import g, render_template_string, request
from platform_core.services.auth_service import csrf_token

from .routes import bp


def init_app(app):
    if "ai_chatbot" in app.extensions:
        return
    app.register_blueprint(bp)
    app.extensions["ai_chatbot"] = True

    @app.after_request
    def attach_chatbot(response):
        if (request.method != "GET" or response.status_code != 200
                or response.mimetype != "text/html" or response.is_streamed
                or response.direct_passthrough
                or response.headers.get("Content-Disposition")
                or response.headers.get("Content-Encoding")):
            return response
        html = response.get_data(as_text=True)
        if 'class="rail-links"' not in html or 'id="ai-chatbot-loader"' in html:
            return response
        if "</head>" not in html:
            return response
        token = csrf_token()
        signed_in = g.get("user") is not None
        storage_id = hashlib.sha256(token.encode()).hexdigest()[:24] if signed_in else "guest"
        assets = render_template_string("""
<link rel="stylesheet" href="{{ url_for('ai_chatbot.static', filename='chatbot.css') }}">
<script id="ai-chatbot-loader" defer
 src="{{ url_for('ai_chatbot.static', filename='chatbot.js') }}"
 data-api="{{ url_for('ai_chatbot.message') }}"
 data-csrf="{{ token }}" data-session="{{ storage_id }}"
 data-authenticated="{{ 'true' if signed_in else 'false' }}"
 data-login="{{ url_for('platform_core.login', next=request.full_path) }}"></script>
""", token=token, storage_id=storage_id, signed_in=signed_in)
        response.set_data(html.replace("</head>", assets + "</head>", 1))
        response.headers.pop("ETag", None)
        response.headers["Cache-Control"] = "no-store"
        return response