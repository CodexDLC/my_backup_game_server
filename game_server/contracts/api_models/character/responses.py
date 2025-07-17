import uuid # <--- Добавьте этот импорт

from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

# Убедитесь, что CharacterDTO импортирован
from game_server.contracts.dtos.character.data_models import CharacterDTO

# Убедитесь, что BaseResultDTO импортирован
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
from game_server.contracts.shared_models.base_responses import ErrorDetail # Для HubRoutingResultDTO


class CharacterListResponseData(BaseModel):
    """
    DTO для данных ответа, содержащих список персонажей.
    Используется в GetCharacterListForAccountResultDTO.
    """
    characters: List[CharacterDTO] = Field(..., description="Список персонажей аккаунта.")


class GetCharacterListForAccountResultDTO(BaseResultDTO):
    """
    DTO для результата команды получения списка персонажей для аккаунта.
    """
    success: bool = Field(..., description="Статус выполнения операции.")
    message: Optional[str] = Field(None, description="Сообщение о результате операции.")
    data: Optional[CharacterListResponseData] = Field(None, description="Данные ответа (список персонажей) при успешном выполнении.")
    error: Optional[ErrorDetail] = Field(None, description="Детали ошибки при неуспешном выполнении.")

    # Добавляем поля из BaseCommandDTO, если они не наследуются или нужны явно
    correlation_id: uuid.UUID # <--- ИЗМЕНЕНО НА uuid.UUID
    trace_id: Optional[uuid.UUID] = None # <--- ИЗМЕНЕНО НА uuid.UUID
    span_id: Optional[str] = Field(None, description="ID спана трассировки.")
    client_id: Optional[str] = Field(None, description="ID клиента, инициировавшего запрос.")