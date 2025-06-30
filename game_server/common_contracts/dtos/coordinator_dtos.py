# game_server/common_contracts/dtos/coordinator_dtos.py

import uuid
from typing import List, Optional, Literal # Добавлен Literal

from pydantic import Field

from game_server.common_contracts.dtos.base_dtos import BaseCommandDTO



class ProcessAutoExploringDTO(BaseCommandDTO):
    """
    DTO для команды обработки автоматического исследования.
    """
    # 🔥 ИЗМЕНЕНО: Использование Literal для команды
    command: Literal["coordinator:process_auto_exploring"] = Field("coordinator:process_auto_exploring", description="Идентификатор команды.")
    # correlation_id, trace_id, span_id, timestamp - наследуются

    character_ids: List[int] = Field(..., min_items=1, description="Список ID персонажей для обработки.")


class ProcessAutoLevelingDTO(BaseCommandDTO):
    """
    DTO для команды обработки автоматической прокачки уровня.
    """
    # 🔥 ИЗМЕНЕНО: Использование Literal для команды
    command: Literal["coordinator:process_auto_leveling"] = Field("coordinator:process_auto_leveling", description="Идентификатор команды.")
    # correlation_id, trace_id, span_id, timestamp - наследуются

    character_ids: List[int] = Field(..., min_items=1, description="Список ID персонажей для обработки.")
