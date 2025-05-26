

import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from game_server.api.routers_config import ROUTERS_CONFIG
from game_server.services.logging.logging_setup import logger  # Импорт глобального логера
from prometheus_fastapi_instrumentator import Instrumentator



# Загрузка переменных из `.env`
root_env = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '.env')
)

load_dotenv(root_env)

required_env_vars = [
    "REDIS_URL", 
]

required_env_vars = ["REDIS_URL"]  # Добавьте свои переменные
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    error_msg = f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}"
    logger.critical(error_msg)
    raise EnvironmentError(error_msg)

# Описание тегов для Swagger UI
tags_metadata = [
    {"name": "Discord", "description": "API для управления Discord-функциями"},
    {"name": "System", "description": "API для игровых систем и структуры мира"},
    {"name": "Random", "description": "API для получения случайных чисел"},
    {"name": "Character", "description": "API для синхронизации персонажей"},
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Сервер запущен!")  # 🔥 Единственная операция в lifespan
    yield  # Оставляем точку входа, но без инициализации сервисов




app = FastAPI(
    title="Game Server API",
    description="Документация API",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)


# Настройка сбора метрик Prometheus
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

@app.get("/")
async def root():
    """Проверка работоспособности API"""
    return {
        "message": "Game Server API работает",
        "status": "OK",
        "version": os.getenv("APP_VERSION", "dev")
    }

# Подключение роутеров из конфига
logger.info("⌛ Начинаю подключение роутеров...")
for router_cfg in ROUTERS_CONFIG:
    try:
        app.include_router(
            router_cfg["router"],
            prefix=router_cfg["prefix"],
            tags=router_cfg["tags"]
        )
        logger.success(
            f"✅ Роут {router_cfg['prefix']} подключен | "
            f"Теги: {router_cfg['tags']} | "
            f"Описание: {router_cfg.get('description', '')}"
        )
    except Exception as e:
        logger.critical(
            f"❌ Ошибка подключения роута {router_cfg['prefix']}: {str(e)}",
            exc_info=True
        )
        raise

logger.info(f"🎯 Всего подключено {len(ROUTERS_CONFIG)} роутеров")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Проверка здоровья сервиса"""
    return {
        "status": "healthy",
        "services": ["discord", "system", "character", "random"],
        "redis": "connected" if hasattr(app.state, 'rp_manager') and app.state.rp_manager.redis else "disconnected"
    }





