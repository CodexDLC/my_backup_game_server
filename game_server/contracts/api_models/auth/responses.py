# contracts/api_models/auth/responses.py

from typing import Optional
from pydantic import BaseModel, Field

# Импортируем BaseRequest из новой общей папки




class AuthResponse(BaseModel):
    
    """
    Универсальная модель ответа с токеном аутентификации.
    Перенесено из game_server/common_contracts/api_models/auth_api.py
    """
    token: str = Field(..., description="Выданный токен аутентификации.")
    expires_in: Optional[int] = Field(None, description="Срок действия токена в секундах (если применимо).")

class SessionSuccessData(BaseModel):
    """
    Модель данных для успешного ответа сессии.
    Перенесено из game_server/common_contracts/api_models/auth_api.py
    """
    auth_token: str = Field(..., description="Временный сессионный токен из Redis.")

# RoutingSuccessResponse из старого response_api.py, теперь будет в system/responses.py
# SessionSuccessResponse из старого response_api.py, теперь будет здесь
class SessionSuccessResponse(BaseModel):
    """
    Модель успешного ответа для сессии, содержащая токен.
    Перенесено из game_server/common_contracts/api_models/response_api.py
    (Предполагается, что будет использоваться как 'data' в APIResponse)
    """
    auth_token: str = Field(..., description="Временный сессионный токен из Redis.")

