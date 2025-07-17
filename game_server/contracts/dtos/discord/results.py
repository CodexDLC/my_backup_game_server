# contracts/dtos/discord/results.py

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

# Импортируем DiscordEntityDTO из data_models в этом же домене
from .data_models import DiscordEntityDTO

class DiscordSyncResultDTO(BaseModel):
    """
    Результат массовой синхронизации сущностей Discord.
    Перенесено из game_server/common_contracts/dtos/discord_dtos.py
    """
    created_count: int = Field(0, description="Количество созданных сущностей.")
    updated_count: int = Field(0, description="Количество обновленных сущностей.")
    errors: List[Dict[str, Any]] = Field([], description="Список деталей ошибок при обработке.")
    processed_entities: List[DiscordEntityDTO] = Field([], description="Список обработанных сущностей.")


class DiscordDeleteResultDTO(BaseModel):
    """
    Результат массового удаления сущностей Discord.
    Перенесено из game_server/common_contracts/dtos/discord_dtos.py
    """
    deleted_count: int = Field(..., description="Количество удаленных сущностей.")


class GetDiscordEntitiesResultDTO(BaseModel):
    """
    Результат получения списка сущностей Discord.
    Перенесено из game_server/common_contracts/dtos/discord_dtos.py
    """
    entities: List[DiscordEntityDTO] = Field([], description="Список найденных сущностей Discord.")

