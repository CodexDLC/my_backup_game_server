# contracts/api_models/discord/config_management_requests.py

from typing import Literal, Optional, Dict, Any
from pydantic import Field

from game_server.contracts.shared_models.base_requests import BaseRequest

# Импортируем BaseRequest из новой общей папки


class GuildConfigSyncRequest(BaseRequest):
    """
    Модель для отправки полной конфигурации гильдии из кэша бота на бэкенд.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    command: Literal["discord:sync_config_from_bot"] = Field(
        "discord:sync_config_from_bot",
        description="Имя команды для синхронизации полной конфигурации с бота на бэкенд."
    )
    guild_id: int
    config_data: Dict[str, Any] = Field(..., description="Полное содержимое Hash конфигурации из Redis")
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).")

class GuildConfigDeleteRequest(BaseRequest):
    """
    Модель для отправки команды на удаление полной конфигурации гильдии из кэша на бэкенде.
    Перенесено из game_server/common_contracts/api_models/discord_api.py
    """
    command: Literal["discord:delete_config_from_bot"] = Field(
        "discord:delete_config_from_bot",
        description="Имя команды для удаления полной конфигурации гильдии с бота на бэкенд."
    )
    guild_id: int = Field(..., description="ID Discord-гильдии, конфигурацию которой нужно удалить.")
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).")

