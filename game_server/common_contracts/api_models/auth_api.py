# game_server\common_contracts\api_models\auth_api.py

# BaseModel и Field теперь импортируем из shared_models.api_contracts



from typing import Literal, Optional
from pydantic import BaseModel, Field

from game_server.common_contracts.shared_models.api_contracts import BaseRequest


# --- Модели для ЗАПРОСА к API ---

class DiscordShardLoginRequest(BaseRequest): # Наследуем от BaseRequest
    """
    Модель для валидации входящего JSON-запроса на Роут №2.
    """
    discord_user_id: str = Field(..., description="Глобальный ID пользователя Discord.")


# --- Модель для УСПЕШНОГО ответа от API (Data Payload) ---
# Эти модели будут вкладываться в универсальную обертку APIResponse.data
class SessionSuccessData(BaseModel):
    """
    Модель данных для успешного ответа Роута №2.
    """
    auth_token: str = Field(..., description="Временный сессионный токен из Redis.")
    
    
class HubRoutingRequest(BaseRequest): # Наследуем от BaseRequest
    """
    API-модель запроса для Роута №1 (инициация и маршрутизация из хаба).
    """
    discord_user_id: str = Field(..., description="Глобальный ID пользователя Discord.")
    guild_id: str = Field(..., description="ID Discord-сервера (хаба), откуда пришел запрос.")
    avatar: str | None = None
    locale: str | None = None

class RoutingSuccessData(BaseModel):
    """
    Модель данных для успешного ответа Роута №1.
    """
    account_id: int = Field(..., description="ID созданного или найденного игрового аккаунта.")
    shard_id: str = Field(..., description="ID шарда, на который следует направить игрока.")


class AuthRequest(BaseModel):
    """
    Универсальная модель запроса для аутентификации и получения токена.
    """
    client_type: Literal["DISCORD_BOT", "PLAYER", "ADMIN"] = Field(
        ..., description="Тип клиента, запрашивающего токен."
    )
    # Поля для бота
    bot_name: Optional[str] = Field(None, description="Имя Discord-бота (для типа DISCORD_BOT).")
    bot_secret: Optional[str] = Field(None, description="Секрет Discord-бота (для типа DISCORD_BOT).")
    
    # Поля для игрока (пример)
    username: Optional[str] = Field(None, description="Имя пользователя (для типа PLAYER).")
    password: Optional[str] = Field(None, description="Пароль пользователя (для типа PLAYER).")
    
    # Можно добавить другие поля для других типов клиентов

class AuthResponse(BaseModel):
    """
    Универсальная модель ответа с токеном аутентификации.
    """
    token: str = Field(..., description="Выданный токен аутентификации.")
    expires_in: Optional[int] = Field(None, description="Срок действия токена в секундах (если применимо).")

