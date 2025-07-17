# contracts/dtos/discord/commands.py

from typing import Literal, Optional, List, Dict, Any
from pydantic import Field, BaseModel
from typing_extensions import Annotated

# Импортируем BaseCommandDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO
# Импортируем DiscordEntityDTO из data_models в этом же домене
from .data_models import DiscordEntityDTO


class DiscordEntitiesSyncCommand(BaseCommandDTO):
    """
    Команда для массовой синхронизации (создания/обновления) сущностей Discord.
    Перенесено из game_server/common_contracts/dtos/discord_dtos.py
    """
    command: Literal["system:sync_discord_entities"] = "system:sync_discord_entities"
    guild_id: int = Field(..., description="ID Discord-гильдии.")

    class SyncItem(BaseModel):
        """Под-модель для одного элемента синхронизации."""
        discord_id: int = Field(..., description="ID сущности в Discord.")
        guild_id: int = Field(..., description="ID Discord-гильдии.")
        entity_type: Literal["category", "text_channel", "voice_channel", "role", "user", "guild", "news", "forum"] = Field(..., description="Тип сущности ('ROLE', 'CHANNEL', 'CATEGORY').")
        name: str = Field(..., description="Имя сущности.")
        parent_id: Optional[int] = Field(None, description="ID родительской сущности.")
        permissions: Optional[str] = Field(None, description="Строка разрешений.")
        access_code: Optional[str] = Field(None, description="Универсальный код доступа.")
        description: Optional[str] = Field(None, description="Описание сущности.")
    entities_data: List[SyncItem] = Field(..., description="Список данных сущностей для синхронизации.")

class DiscordEntitiesDeleteCommand(BaseCommandDTO):
    """
    Команда для массового удаления сущностей Discord.
    Перенесено из game_server/common_contracts/dtos/discord_dtos.py
    """
    command: Literal["discord:delete_entities"] = "discord:delete_entities"
    guild_id: int = Field(..., description="ID Discord-гильдии.")
    discord_ids: Annotated[List[int], Field(min_length=1, description="Список ID Discord сущностей для удаления.")]


class DiscordEntityCreateCommand(BaseCommandDTO):
    """
    Команда для создания одной сущности Discord.
    Перенесено из game_server/common_contracts/dtos/discord_dtos.py
    """
    command: Literal["discord:create_single_entity"] = "discord:create_single_entity"
    guild_id: int = Field(..., description="ID Discord-гильдии.")
    discord_id: int = Field(..., description="ID сущности в Discord.")
    entity_type: Literal["category", "text_channel", "voice_channel", "role", "user", "guild"] = Field(..., description="Тип сущности ('ROLE', 'CHANNEL', 'CATEGORY').")
    name: str = Field(..., description="Имя сущности.")
    description: Optional[str] = Field(None, description="Описание сущности.")
    parent_id: Optional[int] = Field(None, description="ID родительской сущности.")
    permissions: Optional[str] = Field(None, description="Строка разрешений.")
    access_code: Optional[str] = Field(None, description="Универсальный код доступа.")


class GetDiscordEntitiesCommandDTO(BaseCommandDTO):
    """
    Команда для получения списка сущностей Discord.
    Перенесено из game_server/common_contracts/dtos/discord_dtos.py
    """
    command: Literal["discord:get_entities"] = Field("discord:get_entities", description="Идентификатор команды.")
    guild_id: int = Field(..., description="ID Discord-гильдии.")
    entity_type: Optional[Literal["category", "text_channel", "voice_channel", "role", "user", "guild"]] = Field(None, description="Опциональный фильтр по типу сущности.")
    discord_id: Optional[int] = Field(None, description="Конкретный Discord ID сущности для получения (опционально).")

