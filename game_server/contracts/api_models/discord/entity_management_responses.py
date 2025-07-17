# contracts/api_models/discord/entity_management_responses.py

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
# Импортируем APIResponse из новой общей папки
from game_server.contracts.shared_models.base_responses import APIResponse
# Импортируем DTOs из dtos/discord/results.py (будет создана позже)
# from game_server.contracts.dtos.discord.results import DiscordDeleteResultDTO, DiscordSyncResultDTO, GetDiscordEntitiesResultDTO # Пока закомментировано, т.к. файл еще не создан
# from game_server.contracts.dtos.discord.data_models import DiscordEntityDTO # Пока закомментировано, т.к. файл еще не создан


class SingleEntityAPIResponse(APIResponse[BaseModel]): # Временно BaseModel, будет DiscordEntityDTO
    """
    Ответ API, содержащий одну сущность Discord.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    pass

class EntityListAPIResponse(APIResponse[BaseModel]): # Временно BaseModel, будет GetDiscordEntitiesResultDTO
    """
    Ответ API, содержащий список сущностей Discord.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    pass

class SyncAPIResponse(APIResponse[BaseModel]): # Временно BaseModel, будет DiscordSyncResultDTO
    """
    Ответ API на операцию синхронизации.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    pass

class DeleteAPIResponse(APIResponse[BaseModel]): # Временно BaseModel, будет DiscordDeleteResultDTO
    """
    Ответ API на операцию удаления.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    pass

