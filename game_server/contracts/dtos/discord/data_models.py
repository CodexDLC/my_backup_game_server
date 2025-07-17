# contracts/dtos/discord/data_models.py

from typing import Literal, Optional
from pydantic import BaseModel, Field

class DiscordEntityDTO(BaseModel):
    """
    DTO для единого представления любой сущности Discord в системе.
    Перенесено из game_server/common_contracts/dtos/discord_dtos.py
    """
    discord_id: int = Field(..., description="Discord ID сущности.")
    entity_type: Literal["category", "text_channel", "voice_channel", "role", "user", "guild", "news", "forum"] = Field(..., description="Тип сущности Discord.")
    name: str = Field(..., description="Имя сущности.")
    description: Optional[str] = Field(None, description="Описание сущности.")
    parent_id: Optional[int] = Field(None, description="ID родительской сущности (для каналов/категорий).")
    permissions: Optional[str] = Field(None, description="Строковый ключ набора разрешений.")
    access_code: Optional[str] = Field(None, description="Код доступа.")
    guild_id: int = Field(..., description="ID гильдии.")

