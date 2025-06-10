import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI
from game_server.api_rest.routers_config import ROUTERS_CONFIG
from game_server.services.logging.logging_setup import logger  # Импорт глобального логера


# 🔥 ИЗМЕНЕНИЕ: Импортируем новый health роут
from game_server.api_rest.routers.health import router as health_router


# Загрузка переменных из `.env`
root_env = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '.env')
)

load_dotenv(root_env)

required_env_vars = [
    "REDIS_URL", 
    "APP_VERSION" # Добавил APP_VERSION, так как вы его используете в роуте
]

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
    {"name": "utils_route", "description": "API утилиты для работы с сервером"},
    {"name": "Health Check", "description": "API для проверки состояния сервиса"} # 🔥 Добавил тег для health check
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Заглушка для управления жизненным циклом FastAPI.
    Здесь можно инициализировать соединения, кэши, и т.д.
    """
    logger.info("🚀 Сервер запущен! Выполняются операции запуска Lifespan...")
    # Здесь можно инициализировать Redis, подключиться к другим сервисам
    # Например, если у вас есть RedisManager, можно сделать:
    # app.state.rp_manager = await initialize_redis_manager() # Пример инициализации
    yield  # Приложение доступно для обработки запросов
    logger.info("👋 Сервер завершает работу! Выполняются операции завершения Lifespan...")
    # Здесь можно корректно закрыть соединения
    # Например:
    # if hasattr(app.state, 'rp_manager') and app.state.rp_manager:
    #     await app.state.rp_manager.close() # Пример закрытия Redis
    logger.info("✅ Операции завершения Lifespan выполнены.")


app = FastAPI(
    title="Game Server API",
    description="Документация API",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)


# Настройка сбора метрик Prometheus
#instrumentator = Instrumentator()
#instrumentator.instrument(app).expose(app)

@app.get("/", summary="Корневая точка доступа API")
async def root():
    """Проверка работоспособности API"""
    return {
        "message": "Game Server API работает",
        "status": "OK",
        "version": os.getenv("APP_VERSION", "dev")
    }



# Подключение остальных роутеров из конфига
logger.info("⌛ Начинаю подключение остальных роутеров из ROUTERS_CONFIG...")
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

logger.info(f"🎯 Всего подключено {len(ROUTERS_CONFIG) + 1} роутеров (включая health check)") # +1 для health_check