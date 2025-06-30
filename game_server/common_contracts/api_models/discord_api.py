# game_server/common_contracts/api_models/discord_api.py

from typing import Literal, Optional, List, Dict, Any
from pydantic import Field
from typing_extensions import Annotated

from game_server.common_contracts.dtos.discord_dtos import DiscordDeleteResultDTO, DiscordEntityDTO, DiscordSyncResultDTO, GetDiscordEntitiesResultDTO
from game_server.common_contracts.shared_models.api_contracts import APIResponse, BaseRequest


# --- Модели для ЗАПРОСОВ к API ---
class UnifiedEntityCreateRequest(BaseRequest):
    """
    Универсальная модель для запроса на создание ОДНОЙ сущности (роли, канала и т.д.).
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
    """
    command: Literal["system:sync_discord_entities"] = Field(
        "system:sync_discord_entities",
        description="Имя команды для SystemServices."
    )
    guild_id: int = Field(..., description="ID гильдии Discord, для которой производится синхронизация.")
    entities_data: List[DiscordEntityDTO] = Field(..., description="Список данных сущностей Discord для синхронизации.")
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).")


class UnifiedEntityBatchDeleteRequest(BaseRequest):
    """
    Универсальная модель для запроса на МАССОВОЕ УДАЛЕНИЕ.
    """
    command: Literal["discord:batch_delete_entities"] = Field( # 🔥 ДОБАВЛЕНО: Поле command
        "discord:batch_delete_entities",
        description="Имя команды для массового удаления сущностей Discord."
    )
    guild_id: int = Field(..., description="ID гильдии Discord, для которой производится синхронизация.")
    discord_ids: Annotated[List[int], Field(min_length=1)]
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).") # 🔥 ДОБАВЛЕНО: Для обратной маршрутизации


# --- Модели для ОТВЕТОВ от API ---
class SingleEntityAPIResponse(APIResponse[DiscordEntityDTO]):
    """Ответ API, содержащий одну сущность Discord."""
    pass

class EntityListAPIResponse(APIResponse[GetDiscordEntitiesResultDTO]):
    """Ответ API, содержащий список сущностей Discord."""
    pass

class SyncAPIResponse(APIResponse[DiscordSyncResultDTO]):
    """Ответ API на операцию синхронизации."""
    pass

class DeleteAPIResponse(APIResponse[DiscordDeleteResultDTO]):
    """Ответ API на операцию удаления."""
    pass

class GetDiscordEntitiesRequest(BaseRequest):
    """
    Модель запроса для получения сущностей Discord по гильдии и типу.
    """
    command: Literal["discord:get_entities"] = Field( # 🔥 ДОБАВЛЕНО: Поле command
        "discord:get_entities",
        description="Имя команды для получения сущностей Discord."
    )
    guild_id: int = Field(..., description="ID Discord-гильдии.")
    entity_type: Optional[str] = Field(None, description="Опциональный фильтр по типу сущности (ROLE, CHANNEL и т.д.).")


class GuildConfigSyncRequest(BaseRequest):
    """
    Модель для отправки полной конфигурации гильдии из кэша бота на бэкенд.
    """
    command: Literal["discord:sync_config_from_bot"] = Field(
        "discord:sync_config_from_bot",
        description="Имя команды для синхронизации полной конфигурации с бота на бэкенд."
    )
    guild_id: int
    config_data: Dict[str, Any] = Field(..., description="Полное содержимое Hash конфигурации из Redis")
    # НОВОЕ: Добавляем поле client_id
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).")

class GuildConfigDeleteRequest(BaseRequest):
    """
    Модель для отправки команды на удаление полной конфигурации гильдии из кэша на бэкенде.
    """
    command: Literal["discord:delete_config_from_bot"] = Field(
        "discord:delete_config_from_bot",
        description="Имя команды для удаления полной конфигурации гильдии с бота на бэкенд."
    )
    guild_id: int = Field(..., description="ID Discord-гильдии, конфигурацию которой нужно удалить.")
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).")
