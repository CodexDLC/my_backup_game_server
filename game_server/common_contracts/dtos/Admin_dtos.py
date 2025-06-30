# game_server/common_contracts/dtos/admin_dtos.py

import uuid
from typing import Optional, Literal # Добавлен Literal

from pydantic import Field

from game_server.common_contracts.dtos.base_dtos import BaseCommandDTO, BaseResultDTO


class ReloadCacheCommandDTO(BaseCommandDTO):
    """
    DTO для команды перезагрузки кэша администратором.
    """
    # 🔥 ИЗМЕНЕНО: Использование Literal для команды
    command: Literal["admin:reload_cache"] = Field("admin:reload_cache", description="Идентификатор команды.")
    # correlation_id, trace_id, span_id, timestamp - наследуются

    cache_type: str = Field(..., description="Тип кэша для перезагрузки (например, 'location_connections', 'items_data').")
    # Дополнительные поля, если нужны для уточнения команды, могут быть добавлены здесь


class AdminOperationResultDTO(BaseResultDTO[None]):
    """
    DTO для результата административной операции.
    """
    # correlation_id, success, message, trace_id, span_id, timestamp - наследуются
    # data: Optional[None] - уже типизировано через Generic[T]

    # Дополнительные поля результата, если нужны для административных операций
    # например, affected_records_count: Optional[int] = Field(None, description="Количество затронутых записей.")
