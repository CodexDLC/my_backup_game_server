# contracts/dtos/state_entity/commands.py

from typing import Literal, Optional
from pydantic import Field

# Импортируем BaseCommandDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO

class GetAllStateEntitiesCommand(BaseCommandDTO):
    """
    Команда для получения всех сущностей состояния.
    Перенесено из game_server/common_contracts/dtos/state_entity_dtos.py
    """
    command: Literal["system:get_all_state_entities"] = "system:get_all_state_entities"
    guild_id: Optional[int] = Field(None, description="Опциональный ID гильдии для фильтрации.")
    entity_type: Optional[Literal["role", "channel", "category", "player_status"]] = Field(None, description="Опциональный фильтр по типу сущности.")


class GetStateEntityByKeyCommand(BaseCommandDTO):
    """
    Команда для получения сущности состояния по ключу.
    Перенесено из game_server/common_contracts/dtos/state_entity_dtos.py
    """
    command: Literal["state_entity:get_by_key"] = "state_entity:get_by_key"
    access_code: str = Field(..., description="Код доступа сущности.")

