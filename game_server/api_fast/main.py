# api_fast/main.py

import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
import redis.asyncio as aioredis
from dotenv import load_dotenv

# --- Импорты ---
from game_server.api_fast.gateway.command_listener import CommandListener
from game_server.api_fast.gateway.connection_manager import ConnectionManager
from game_server.api_fast.routers_config import ROUTERS_CONFIG
from game_server.api_fast.ws_routers_config import WS_ROUTERS_CONFIG
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger
from game_server.config.settings_core import REDIS_URL, REDIS_PASSWORD, APP_VERSION

# --- ИЗМЕНЕНИЕ ЗДЕСЬ: Удален импорт глобальной переменной ---
from game_server.api_fast.dependencies import get_connection_manager # Только get_connection_manager

# --- Загрузка и проверка переменных окружения ---
root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(root_env)

required_env_vars = ["REDIS_URL", "REDIS_PASSWORD", "GATEWAY_BOT_SECRET"]
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    error_msg = f"Отсутствуют обязательные переменные окружения для шлюза: {', '.join(missing_vars)}"
    logger.critical(error_msg)
    raise EnvironmentError(error_msg)

# --- Описание тегов для Swagger UI ---
tags_metadata = [
    {"name": "Gateway REST", "description": "REST API для служебных операций шлюза (например, подтверждение команд)."},
    {"name": "Gateway WebSocket", "description": "WebSocket API для подключения бота и получения команд."},
    {"name": "Root", "description": "Проверка доступности сервиса."},
]

# --- Lifespan Manager: Управление жизненным циклом шлюза ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управляет запуском и остановкой фоновых сервисов шлюза.
    """
    logger.info("🚀 Шлюз команд (Command Gateway) запускается...")
    
    try:
        # 1. Подключение к основной БД Redis (db: 0), где лежат стримы команд
        redis_client = aioredis.from_url(REDIS_URL, password=REDIS_PASSWORD, decode_responses=False)
        await redis_client.ping()
        app.state.redis_client = redis_client
        logger.info(f"✅ Успешное подключение к Redis для шлюза: {REDIS_URL}")
        
        # 2. Инициализация синглтонов для шлюза
        # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Инициализируем и кладем в app.state ---
        app.state.connection_manager = ConnectionManager()
        logger.info("✅ ConnectionManager инициализирован.")

        app.state.command_listener = CommandListener(
            redis_client=app.state.redis_client,
            connection_manager=app.state.connection_manager # Берем из app.state
        )
        logger.info("✅ CommandListener инициализирован.")
        
        # 3. Запуск слушателя команд в фоновом режиме
        listener_task = asyncio.create_task(app.state.command_listener.listen_forever())
        app.state.listener_task = listener_task
        logger.info("✅ Слушатель команд Redis Stream запущен в фоновом режиме.")

    except Exception as e:
        logger.critical(f"🚨 Критическая ошибка на этапе запуска шлюза: {e}", exc_info=True)
        raise

    yield  # Шлюз готов к работе

    logger.info("👋 Шлюз команд завершает работу...")
    
    if hasattr(app.state, 'listener_task') and app.state.listener_task:
        if hasattr(app.state, 'command_listener'):
            app.state.command_listener.stop()
        app.state.listener_task.cancel()
        try:
            await app.state.listener_task
        except asyncio.CancelledError:
            logger.info("Фоновая задача слушателя успешно отменена.")

    if hasattr(app.state, 'redis_client'):
        await app.state.redis_client.close()
        logger.info("✅ Соединение шлюза с Redis закрыто.")
        
    # --- ИЗМЕНЕНИЕ ЗДЕСЬ: Очищаем app.state при завершении ---
    if hasattr(app.state, 'connection_manager'):
        del app.state.connection_manager
    # -------------------------------------------------------------------
        
    logger.info("✅ Операции завершения Lifespan выполнены.")


# --- Создание приложения FastAPI ---
app = FastAPI(
    title="Command Gateway API",
    description="Сервис-шлюз для асинхронной и безопасной коммуникации с Discord-ботом.",
    version=os.getenv("APP_VERSION", "1.0.0"),
    openapi_tags=tags_metadata,
    lifespan=lifespan
)

# --- Подключение REST роутеров ---
logger.info("Подключение REST роутеров шлюза...")
for router_config in ROUTERS_CONFIG:
    app.include_router(
        router_config["router"],
        prefix=router_config.get("prefix", ""),
        tags=router_config.get("tags", [])
    )
logger.info("✅ REST роутеры шлюза успешно подключены.")

# --- Подключение WebSocket роутеров ---
logger.info("Подключение WebSocket роутеров...")
for ws_router_config in WS_ROUTERS_CONFIG:
    app.include_router(
        ws_router_config["router"],
        prefix=ws_router_config.get("prefix", ""),
        tags=ws_router_config.get("tags", [])
    )
logger.info("✅ Все WebSocket роутеры успешно подключены.")

# --- Базовый роут ---
@app.get("/", tags=["Root"], status_code=status.HTTP_200_OK)
async def read_root():
    return {"message": "Command Gateway is alive"}