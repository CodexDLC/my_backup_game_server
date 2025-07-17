# contracts/dtos/coordinator/commands.py

import uuid
from typing import List, Literal
from pydantic import Field

# Импортируем BaseCommandDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO

class ProcessAutoExploringDTO(BaseCommandDTO):
    """
    DTO для команды обработки автоматического исследования.
    Перенесено из game_server/common_contracts/dtos/coordinator_dtos.py
    """
    command: Literal["coordinator:process_auto_exploring"] = Field("coordinator:process_auto_exploring", description="Идентификатор команды.")
    character_ids: List[int] = Field(..., min_items=1, description="Список ID персонажей для обработки.")


class ProcessAutoLevelingDTO(BaseCommandDTO):
    """
    DTO для команды обработки автоматической прокачки уровня.
    Перенесено из game_server/common_contracts/dtos/coordinator_dtos.py
    """
    command: Literal["coordinator:process_auto_leveling"] = Field("coordinator:process_auto_leveling", description="Идентификатор команды.")
    character_ids: List[int] = Field(..., min_items=1, description="Список ID персонажей для обработки.")

