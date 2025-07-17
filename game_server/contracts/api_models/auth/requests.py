# contracts/api_models/auth/requests.py

from typing import Literal, Optional
from pydantic import BaseModel, Field

from game_server.contracts.shared_models.base_requests import BaseRequest

# Импортируем BaseRequest из новой общей папки


class AuthRequest(BaseRequest):
    """
    Универсальная модель запроса для аутентификации и получения токена.
    Перенесено из game_server/common_contracts/api_models/auth_api.py
    """
    command: Literal["issue_auth_token", "validate_token_rpc"] = Field(
        ..., description="Команда RPC операции (e.g., 'issue_auth_token', 'validate_token_rpc')."
    )
    client_type: Literal["DISCORD_BOT", "PLAYER", "ADMIN"] = Field(
        ..., description="Тип клиента, запрашивающего токен."
    )
    # Поля для бота
    bot_name: Optional[str] = Field(None, description="Имя Discord-бота (для типа DISCORD_BOT).")
    bot_secret: Optional[str] = Field(None, description="Секрет Discord-бота (для типа DISCORD_BOT).")

    # Поля для игрока (пример)
    username: Optional[str] = Field(None, description="Имя пользователя (для типа PLAYER).")
    password: Optional[str] = Field(None, description="Пароль пользователя (для типа PLAYER).")

