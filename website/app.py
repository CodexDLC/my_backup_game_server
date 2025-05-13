from flask import Flask, render_template, request
import subprocess  # Для вызова внешнего скрипта
import logging  # Для логирования

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WebsiteMain")

# 🔹 Регистрируем маршруты
from website.routes import register_routes
register_routes(app)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/callback')
def oauth_callback():
    code = request.args.get("code")
    state = request.args.get("state")
    return f"OAuth callback успешно вызван. Code: {code}, State: {state}"

def check_and_update_tables():
    """Запуск create_tables.py для проверки и обновления таблиц"""
    try:
        logger.info("Проверка и обновление таблиц начато...")
        subprocess.run(["python3", "/opt/new_order_rpg/database/create_tables.py"], check=True)
        logger.info("Таблицы успешно проверены и обновлены.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Ошибка при проверке и обновлении таблиц: {e}")

if __name__ == "__main__":
    check_and_update_tables()
    app.run(host='0.0.0.0', port=5000, debug=True)
