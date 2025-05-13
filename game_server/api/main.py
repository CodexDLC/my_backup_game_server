import os
import sys
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from game_server.Logic.DataAccessLogic.db_instance import get_db_session
from game_server.services.logging_config import logger  # Импорт глобального логера
from game_server.api.routers.random_pool import router as random_pool_router

# Загрузка переменных из `.env`
root_env = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '.env')
)
load_dotenv(root_env)


# Импорт маршрутов (роутеров)
from game_server.api.routers.discord import *
from game_server.api.routers.system import *

import asyncio

# Описание тегов для Swagger UI
tags_metadata = [
    {"name": "Discord", "description": "API для управления Discord-функциями"},
    {"name": "System", "description": "API для игровых систем и структуры мира"},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Открываем сессию с помощью get_db_session
    async with get_db_session() as session:
        logger.info("База данных подключена")
        yield {}  # Передаем пустой словарь, так как FastAPI ожидает именно его для lifespan

    logger.info("DB connection closed")

# Создание FastAPI приложения с тегами
app = FastAPI(
    title="Game Server API",
    description="Документация API",
    openapi_tags=tags_metadata,
    lifespan=lifespan
)
@app.get("/")
async def root():
    return {"message": "FastAPI работает!"}

# Подключаем все роуты
app.include_router(discord_bindings_router, prefix="/discord/bindings", tags=["Discord"])
logger.info("Роут /discord/bindings успешно подключен")

app.include_router(discord_roles_router, prefix="/discord/roles", tags=["Discord"])
logger.info("Роут /discord/roles успешно подключен")

app.include_router(discord_permissions_router, prefix="/discord/permissions", tags=["Discord"])
logger.info("Роут /discord/permissions успешно подключен")

app.include_router(system_gameworld_router, prefix="/system/gameworld", tags=["System"])
logger.info("Роут /system/gameworld успешно подключен")

app.include_router(system_entities_router, prefix="/system/entities", tags=["System"])
logger.info("Роут /system/entities успешно подключен")

app.include_router(system_mapping_router, prefix="/system/mapping", tags=["System"])
logger.info("Роут /system/mapping успешно подключен")

app.include_router(random_pool_router, prefix="/random", tags=["Random"])
logger.info("Роут /random успешно подключен")