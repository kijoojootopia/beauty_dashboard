"""VS Code / flask --app app run 진입점."""
from platform_core.app_factory import create_app

from ai_chatbot import init_app as init_chatbot

app = create_app()
init_chatbot(app)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
