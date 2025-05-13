from flask import Flask, request

app = Flask(__name__)

@app.route('/')
def home():
    return "Привет, это наш сайт!"  # Главная страница

# Новый маршрут для обработки OAuth2 callback
@app.route('/callback')
def oauth_callback():
    # Получаем параметры, переданные в query (например, 'code' и 'state')
    code = request.args.get("code")
    state = request.args.get("state")
    # Здесь можно добавить обработку: обмен кода на токен и т.д.
    return f"OAuth callback успешно вызван. Code: {code}, State: {state}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
