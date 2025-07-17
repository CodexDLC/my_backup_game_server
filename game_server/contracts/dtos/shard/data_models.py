# contracts/dtos/shard/data_models.py

from typing import Optional
from pydantic import Field, BaseModel
from datetime import datetime

class ShardDataDTO(BaseModel):
    """
    Модель данных для информации о шарде (ORM-подобная структура).
    Перенесено из game_server/common_contracts/dtos/shard_dtos.py
    """
    id: Optional[int] = None
    shard_name: str = Field(..., description="Уникальное имя игрового шарда.")
    discord_guild_id: int = Field(..., description="ID Discord-гильдии, связанной с шардом.")
    current_players: int = Field(0, description="Текущее количество игроков.")
    is_admin_enabled: bool = Field(False, description="Админский мастер-переключатель.")
    is_system_active: bool = Field(False, description="Серверный флаг активности/сна.")
    created_at: Optional[datetime] = Field(None, description="Время создания записи (UTC).")
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления (UTC).")

