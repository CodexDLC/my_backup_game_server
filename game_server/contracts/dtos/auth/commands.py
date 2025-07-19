# contracts/dtos/auth/commands.py

from typing import Literal, Optional
from pydantic import BaseModel, Field

# Импортируем BaseCommandDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO

class GetSessionDataCommandDTO(BaseCommandDTO):
    """
    DTO для команды запроса данных сессии (персонажей) для указанного аккаунта.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    command: str = "get_session_data"
    account_id: int
    
class IssueAuthTokenRpcCommandDTO(BaseCommandDTO):
    """
    DTO для внутренней RPC команды на выдачу токена, формируемой Gateway.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    command: Literal["issue_auth_token"] = Field("issue_auth_token", description="Идентификатор RPC команды.")
    client_type: Literal["DISCORD_BOT", "PLAYER", "ADMIN"] = Field(..., description="Тип клиента.")
    bot_name: Optional[str] = Field(None, description="Имя бота (для DISCORD_BOT).")
    bot_secret: Optional[str] = Field(None, description="Секрет бота (для DISCORD_BOT).")
    username: Optional[str] = Field(None, description="Имя пользователя (для PLAYER).")
    password: Optional[str] = Field(None, description="Пароль пользователя (для PLAYER).")

class ValidateTokenRpcCommandDTO(BaseCommandDTO):
    """
    DTO для внутренней RPC команды на валидацию токена, формируемой Gateway.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    command: Literal["validate_token_rpc"] = Field("validate_token_rpc", description="Идентификатор RPC команды.")
    token: str = Field(..., description="Токен для валидации.")
    client_type: Literal["DISCORD_BOT", "PLAYER", "ADMIN"] = Field(None, description="Тип клиента.")

# 1. Создайте новый класс для вложенных данных
class HubRoutingPayload(BaseModel):
    discord_user_id: str
    guild_id: str
    # Добавить поле 'command' сюда, чтобы оно дублировалось,
    # как в других работающих DTO.
    command: Literal["discord_hub_registered"] = Field("discord_hub_registered", description="Идентификатор команды.")

    
class HubRoutingRequest(BaseCommandDTO):
    command: str = "discord_hub_registered"
    payload: HubRoutingPayload


# 2. Обновленный DTO команды
class HubRoutingCommandDTO(BaseCommandDTO):
    """DTO для команды маршрутизации пользователя из хаба."""
    command: Literal["discord_hub_registered"] = Field("discord_hub_registered", description="Идентификатор команды.")
    payload: HubRoutingPayload
    
    

# 1. Модель для полезной нагрузки (payload)
class LoginCharacterByIdPayload(BaseModel):
    """Данные для команды логина персонажа по его ID."""
    character_id: int = Field(..., description="Уникальный ID персонажа для логина.")
    account_id: int = Field(..., description="ID аккаунта, которому принадлежит персонаж.")


# 2. Обновленный DTO команды
class LoginCharacterByIdCommandDTO(BaseCommandDTO):
    """Команда для логина персонажа по его ID."""
    command: Literal["character_login_by_id"] = "character_login_by_id"
    payload: LoginCharacterByIdPayload