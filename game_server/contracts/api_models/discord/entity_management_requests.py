# contracts/api_models/discord/entity_management_requests.py

from typing import Literal, Optional, List, Dict, Any
from pydantic import Field
from typing_extensions import Annotated

from game_server.contracts.shared_models.base_requests import BaseRequest

# Импортируем BaseRequest из новой общей папки

# Импортируем DiscordEntityDTO из dtos/discord/data_models.py (будет создана позже)
# from game_server.contracts.dtos.discord.data_models import DiscordEntityDTO # Пока закомментировано, т.к. файл еще не создан

class UnifiedEntityCreateRequest(BaseRequest):
    """
    Универсальная модель для запроса на создание ОДНОЙ сущности (роли, канала и т.д.).
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    guild_id: int
    discord_id: int
    entity_type: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    permissions: Optional[str] = None
    access_code: Optional[str] = None


class UnifiedEntitySyncRequest(BaseRequest):
    """
    Модель запроса для синхронизации сущностей Discord.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    command: Literal["system:sync_discord_entities"] = Field(
        "system:sync_discord_entities",
        description="Имя команды для SystemServices."
    )
    guild_id: int = Field(..., description="ID гильдии Discord, для которой производится синхронизация.")
    # entities_data: List[DiscordEntityDTO] = Field(..., description="Список данных сущностей Discord для синхронизации.") # Зависит от DiscordEntityDTO
    entities_data: List[Dict[str, Any]] = Field(..., description="Список данных сущностей Discord для синхронизации.") # Временно Dict[str, Any]
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).")


class UnifiedEntityBatchDeleteRequest(BaseRequest):
    """
    Универсальная модель для запроса на МАССОВОЕ УДАЛЕНИЕ.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    command: Literal["discord:batch_delete_entities"] = Field(
        "discord:batch_delete_entities",
        description="Имя команды для массового удаления сущностей Discord."
    )
    guild_id: int = Field(..., description="ID гильдии Discord, для которой производится синхронизация.")
    discord_ids: Annotated[List[int], Field(min_length=1)]
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).")


class GetDiscordEntitiesRequest(BaseRequest):
    """
    Модель запроса для получения сущностей Discord по гильдии и типу.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    command: Literal["discord:get_entities"] = Field(
        "discord:get_entities",
        description="Имя команды для получения сущностей Discord."
    )
    guild_id: int = Field(..., description="ID Discord-гильдии.")
    entity_type: Optional[str] = Field(None, description="Опциональный фильтр по типу сущности (ROLE, CHANNEL и т.д.).")

