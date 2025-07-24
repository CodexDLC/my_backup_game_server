# game_server/contracts/dtos/game_commands/cache_request_commands.py

from pydantic import BaseModel, Field
from typing import Dict, Any, Literal

# Импортируем базовые классы DTO
from ...shared_models.base_commands_results import BaseCommandDTO, BaseResultDTO


# --- DTO для команды GetLocationSummary ---

class GetLocationSummaryPayloadDTO(BaseModel):
    """
    Полезная нагрузка для команды получения сводки по локации из кэша.
    """
    location_id: str = Field(..., description="ID локации, для которой запрашивается сводка.")


class GetLocationSummaryCommandDTO(BaseCommandDTO):
    """
    DTO для команды получения сводки по локации, отправляемой на бэкенд.
    """
    command: Literal["get_location_summary"] = Field("get_location_summary", description="Идентификатор команды.")
    payload: GetLocationSummaryPayloadDTO = Field(..., description="Полезная нагрузка команды.")


class GetLocationSummaryResultDTO(BaseResultDTO[Dict[str, Any]]):
    """
    DTO для результата команды получения сводки по локации.
    В поле 'data' будет содержаться словарь с данными из кэша Redis.
    """
    pass

# Сюда можно будет добавлять DTO для других команд, работающих с кэшем