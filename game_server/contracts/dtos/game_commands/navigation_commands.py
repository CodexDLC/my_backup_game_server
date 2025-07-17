# game_server/contracts/dtos/game_commands/navigation_commands.py

import uuid
from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field

# Импортируем BaseCommandDTO и BaseResultDTO из общей папки контрактов
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO, BaseResultDTO


class MoveToLocationPayloadDTO(BaseModel):
    """
    Полезная нагрузка для команды перемещения персонажа.
    """
    character_id: int = Field(..., description="ID персонажа, который перемещается.")
    account_id: int = Field(..., description="ID аккаунта, к которому принадлежит персонаж.")
    target_location_id: str = Field(..., description="ID локации, куда персонаж пытается переместиться.")


class MoveToLocationCommandDTO(BaseCommandDTO):
    """
    DTO для команды перемещения персонажа, отправляемой на бэкенд.
    """
    command: Literal["move_character_to_location"] = Field("move_character_to_location", description="Идентификатор команды для перемещения персонажа.")
    payload: MoveToLocationPayloadDTO = Field(..., description="Полезная нагрузка команды перемещения.")


class MoveToLocationResultDTO(BaseResultDTO):
    """
    DTO для результата выполнения команды перемещения персонажа,
    возвращаемого с бэкенда.
    """
    # BaseResultDTO уже имеет поле 'data'. Здесь оно будет использоваться для динамических данных.
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Дополнительные динамические данные, например, для обновления эмбиента. "
                    "Может включать 'ambient_footer_data' или другие специфичные данные."
    )