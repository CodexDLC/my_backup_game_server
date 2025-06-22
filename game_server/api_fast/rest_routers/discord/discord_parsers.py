# game_server/api_fast/rest_routers/discord/discord_parsers.py

from fastapi import Request, Body, Query # Добавил Body, Query
from typing import List, Optional, Any # Добавил Optional, Any
from game_server.api_fast.api_models.discord_api import (

    # Добавлены импорты для новых моделей
    DiscordEntityCreateRequest,
    DiscordEntitySyncRequest,
    DiscordEntityBatchDeleteRequest
)




# --- НОВЫЕ ПАРСЕРЫ ДЛЯ DISCORDENTITY (добавлены к существующим) ---

# Парсер для POST /discord-entities/sync
async def parse_sync_request(
    sync_request: DiscordEntitySyncRequest = Body(
        ...,
        example={
            "entities": [
                {
                    "guild_id": 1234567890,
                    "discord_id": 1122334455,
                    "entity_type": "category",
                    "name": "Категория: [ НАЧНИ ЗДЕСЬ ] 🏁",
                    "parent_id": None,
                    "description": "Полная структура для публичного Хаб-сервера."
                },
                {
                    "guild_id": 1234567890,
                    "discord_id": 9988776655,
                    "entity_type": "text_channel",
                    "name": "#👋-добро-пожаловать",
                    "parent_id": 1122334455,
                    "description": "Канал, где новых участников встречает бот."
                }
            ]
        }
    )
) -> DiscordEntitySyncRequest:
    """Парсит и валидирует запрос на синхронизацию Discord сущностей."""
    return sync_request

# Парсер для POST /discord-entities/create-one
async def parse_create_one_request(
    entity_data: DiscordEntityCreateRequest = Body(
        ...,
        example={
            "guild_id": 1234567890,
            "discord_id": 1234567891, # Здесь уже должен быть Discord ID
            "entity_type": "text_channel",
            "name": "новая-статья-по-лор",
            "parent_id": 1384956439428337755, # Discord ID категории "БИБЛИОТЕКА ЗНАНИЙ"
            "permissions": "read_only",
            "description": "Описание новой статьи про лор."
        }
    )
) -> DiscordEntityCreateRequest:
    """Парсит и валидирует запрос на создание одной Discord сущности."""
    return entity_data

# Парсер для DELETE /discord-entities/batch
async def parse_batch_delete_request(
    delete_request: DiscordEntityBatchDeleteRequest = Body(
        ...,
        example={
            "guild_id": 1234567890,
            "discord_ids": [1122334455, 9988776655, 7766554433]
        }
    )
) -> DiscordEntityBatchDeleteRequest:
    """Парсит и валидирует запрос на пакетное удаление Discord сущностей."""
    return delete_request

# Парсер для GET /discord-entities/{guild_id} (параметр пути)
# Для параметров пути парсер не требуется, они разбираются FastAPI автоматически,
# но если бы были Query параметры, они могли бы быть здесь.
# Например, если бы мы хотели фильтрацию по типу:
async def parse_get_by_guild_params(
    entity_type: Optional[str] = Query(None, description="Отфильтровать по типу сущности (например, 'category', 'text_channel').")
) -> Optional[str]:
    return entity_type