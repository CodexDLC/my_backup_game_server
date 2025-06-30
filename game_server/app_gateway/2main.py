# game_server/app_gateway/main.py

# 🔥 МИНИМАЛЬНЫЕ ИМПОРТЫ ДЛЯ ТЕСТА
import json
import logging
import asyncio # Для asynccontextmanager, если он используется
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware # Для CORS


# Настраиваем базовый логгер, чтобы видеть вывод
logging.basicConfig(level=logging.INFO)
simple_logger = logging.getLogger("SimpleGatewayDebug")


# 🔥 ВРЕМЕННО: Пустой lifespan для минимальной конфигурации
import contextlib # Импортируем contextlib для asynccontextmanager

@contextlib.asynccontextmanager
async def empty_lifespan(app: FastAPI):
    simple_logger.info("Minimal lifespan started for debug.")
    yield
    simple_logger.info("Minimal lifespan finished for debug.")

# 🔥 Инициализация FastAPI приложения
app = FastAPI(
    title="Minimal WebSocket Debug Gateway",
    version="0.0.1",
    lifespan=empty_lifespan # Используем пустой lifespan
)

# 🔥 Настраиваем CORS максимально широко, чтобы исключить его как причину 403
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все источники
    allow_credentials=True,
    allow_methods=["*"],  # Разрешаем все HTTP-методы (GET, POST, OPTIONS, HEAD, PUT, PATCH, DELETE)
    allow_headers=["*"],  # Разрешаем все заголовки
)


# 🔥 САМЫЙ ПРОСТОЙ WEBSOCKET ЭНДПОИНТ (БЕЗ Depends, БЕЗ ТОКЕНОВ, БЕЗ СЛОЖНОЙ ЛОГИКИ)
@app.websocket("/debug_simple_ws")
async def debug_simple_websocket_endpoint(websocket: WebSocket):
    simple_logger.info(f"*** DEBUG: NEW CONNECTION AT /debug_simple_ws FROM {websocket.client.host}:{websocket.client.port} ***")
    try:
        await websocket.accept()
        simple_logger.info(f"*** DEBUG: CONNECTION ACCEPTED ON /debug_simple_ws FROM {websocket.client.host} ***")
        
        # 🔥 ИЗМЕНЕНИЕ ЗДЕСЬ: Отправляем простое JSON-сообщение
        await websocket.send_json({"status": "connected", "message": "Hello from DEBUG WebSocket!"})
        simple_logger.info("*** DEBUG: Sent initial JSON message. ***")

        # Просто эхо-сервер: ждем сообщения и отправляем обратно
        while True:
            received_data = await websocket.receive_text() # Получаем текст
            simple_logger.info(f"*** DEBUG: MESSAGE RECEIVED ON /debug_simple_ws: {received_data} ***")
            
            # 🔥 ИЗМЕНЕНИЕ ЗДЕСЬ: Пытаемся распарсить полученное сообщение как JSON
            try:
                parsed_json = json.loads(received_data)
                response_message = {"echo": parsed_json}
            except json.JSONDecodeError:
                response_message = {"echo_text": received_data} # Если не JSON, отправляем как текст
            
            await websocket.send_json(response_message) # Отправляем JSON-ответ

    except WebSocketDisconnect:
        simple_logger.info(f"*** DEBUG: Client disconnected from /debug_simple_ws. ***")
    except Exception as e:
        simple_logger.error(f"*** DEBUG: Error on /debug_simple_ws: {e}", exc_info=True)
    finally:
        simple_logger.info(f"*** DEBUG: Connection on /debug_simple_ws closed. ***")

# ... (остальной код файла) ...


# 🔥 БЛОК ЗАПУСКА FastAPI с Uvicorn (если вы запускаете его этим файлом)
if __name__ == "__main__":
    import uvicorn
    simple_logger.info("Attempting to run Uvicorn for debug Gateway...")
    # Убедитесь, что 'app' - это имя вашей переменной FastAPI
    uvicorn.run(app, host="0.0.0.0", port=8000)