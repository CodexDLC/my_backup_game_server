# contracts/dtos/auth/results.py

from typing import Optional, Literal
from pydantic import BaseModel, Field

# Импортируем BaseResultDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
# Импортируем ErrorDetail из base_responses
from game_server.contracts.shared_models.base_responses import ErrorDetail
# Импортируем CharacterDTO из dtos/character/data_models (будет создана позже)
# from game_server.contracts.dtos.character.data_models import CharacterDTO # Пока закомментировано, если CharacterDTO еще не перенесено

class SessionResultData(BaseModel):
    """
    DTO с данными результата успешного создания сессии.
    Это 'data' для BaseResultDTO.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    auth_token: str = Field(..., description="Временный сессионный токен из Redis.")
    # characters: List[CharacterDTO] = Field(..., description="Список персонажей аккаунта.") # Если SessionResultData содержит список персонажей

class SessionResultDTO(BaseResultDTO[SessionResultData]):
    """
    Результат операции создания сессии.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    pass

class IssueAuthTokenRpcResponseDTO(BaseModel):
    """
    DTO для RPC ответа после выдачи токена.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    success: bool = Field(..., description="Индикатор успешности операции.")
    token: Optional[str] = Field(None, description="Выданный токен аутентификации.")
    expires_in: Optional[int] = Field(None, description="Срок действия токена в секундах.")
    error: Optional[str] = Field(None, description="Сообщение об ошибке.")


class ValidateTokenRpcResponseDTO(BaseModel):
    """
    DTO для RPC ответа после валидации токена.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    is_valid: bool = Field(..., description="Флаг валидности токена.")
    client_id: Optional[str] = Field(None, description="ID клиента, если токен валиден.")
    client_type: Literal["DISCORD_BOT", "PLAYER", "ADMIN"] = Field(None, description="Тип клиента, если токен валиден.")
    error: Optional[str] = Field(None, description="Сообщение об ошибке.")

