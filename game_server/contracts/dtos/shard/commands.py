# contracts/dtos/shard/commands.py

import uuid
from typing import Literal
from pydantic import Field

# Импортируем BaseCommandDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO

class SaveShardCommandDTO(BaseCommandDTO):
    """
    DTO для команды сохранения/регистрации игрового шарда.
    Перенесено из game_server/common_contracts/dtos/shard_dtos.py
    """
    command: Literal["system:save_shard"] = "system:save_shard" 
    discord_guild_id: int = Field(..., description="ID Discord-гильдии, связанной с шардом.")
    shard_name: str = Field(..., description="Уникальное имя игрового шарда.")
    max_players: int = Field(200, description="Максимальное количество игроков, которое может вместить шард.")
    is_system_active: bool = Field(False, description="Статус активности шарда в системе.")

class NotifyAdminsCommandDTO(BaseCommandDTO):
    """
    DTO для команды уведомления администраторов.
    Перенесено из game_server/common_contracts/dtos/shard_dtos.py
    """
    command: Literal["system:notify_admins"] = "system:notify_admins"
    reason: str = Field(..., description="Причина уведомления (e.g., 'SHARDS_FULL').")
    message: str = Field(..., description="Полный текст сообщения для администраторов.")

