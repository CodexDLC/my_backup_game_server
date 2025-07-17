# contracts/dtos/admin/commands.py

import uuid
from typing import Literal
from pydantic import Field

# Импортируем BaseCommandDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO

class ReloadCacheCommandDTO(BaseCommandDTO):
    """
    DTO для команды перезагрузки кэша администратором.
    Перенесено из game_server/common_contracts/dtos/Admin_dtos.py
    """
    command: Literal["admin:reload_cache"] = Field("admin:reload_cache", description="Идентификатор команды.")
    cache_type: str = Field(..., description="Тип кэша для перезагрузки (например, 'location_connections', 'items_data').")

