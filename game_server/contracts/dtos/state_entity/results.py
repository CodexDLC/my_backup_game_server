# contracts/dtos/state_entity/results.py

from typing import List
from pydantic import BaseModel, Field

# Импортируем BaseResultDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
# Импортируем StateEntityDTO из data_models в этом же домене
from .data_models import StateEntityDTO

class GetAllStateEntitiesResult(BaseModel):
    """
    Результат получения списка сущностей состояния.
    Перенесено из game_server/common_contracts/dtos/state_entity_dtos.py
    """
    entities: List[StateEntityDTO] = Field([], description="Список найденных сущностей состояния.")

class StateEntityResult(BaseResultDTO[StateEntityDTO]):
    """
    Результат получения одной сущности состояния.
    Перенесено из game_server/common_contracts/dtos/state_entity_dtos.py
    """
    pass

