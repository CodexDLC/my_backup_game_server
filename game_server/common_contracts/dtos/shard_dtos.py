# game_server/common_contracts/dtos/shard_dtos.py

import uuid
from typing import Dict, Optional, Any, Literal
from pydantic import Field, BaseModel
from datetime import datetime

from game_server.common_contracts.dtos.base_dtos import BaseCommandDTO, BaseResultDTO


class SaveShardCommandDTO(BaseCommandDTO):
    """
    DTO для команды сохранения/регистрации игрового шарда.
    Это унифицированная команда для операции "save_shard".
    """
    # 🔥 ИЗМЕНЕНИЕ: Команда теперь "system:save_shard"
    command: Literal["system:save_shard"] = "system:save_shard" 

    discord_guild_id: int = Field(..., description="ID Discord-гильдии, связанной с шардом.")
    shard_name: str = Field(..., description="Уникальное имя игрового шарда.")
    max_players: int = Field(200, description="Максимальное количество игроков, которое может вместить шард.")
    is_system_active: bool = Field(False, description="Статус активности шарда в системе.")


class ShardDataDTO(BaseModel):
    """Модель данных для информации о шарде (ORM-подобная структура)."""
    id: Optional[int] = None
    shard_name: str = Field(..., description="Уникальное имя игрового шарда.")
    discord_guild_id: int = Field(..., description="ID Discord-гильдии, связанной с шардом.")
    current_players: int = Field(0, description="Текущее количество игроков.")
    is_admin_enabled: bool = Field(False, description="Админский мастер-переключатель.")
    is_system_active: bool = Field(False, description="Серверный флаг активности/сна.")
    created_at: Optional[datetime] = Field(None, description="Время создания записи (UTC).")
    updated_at: Optional[datetime] = Field(None, description="Время последнего обновления (UTC).")


class ShardOperationResultDTO(BaseResultDTO[ShardDataDTO]):
    """
    DTO для результата операции с шардом (сохранение, обновление).
    """
    shard_data: Optional[ShardDataDTO] = Field(None, description="Данные о шарде после операции.")


class NotifyAdminsCommandDTO(BaseCommandDTO):
    """
    DTO для команды уведомления администраторов.
    """
    command: Literal["system:notify_admins"] = "system:notify_admins"
    reason: str = Field(..., description="Причина уведомления (e.g., 'SHARDS_FULL').")
    message: str = Field(..., description="Полный текст сообщения для администраторов.")

