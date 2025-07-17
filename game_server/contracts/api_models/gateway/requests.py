# contracts/api_models/gateway/requests.py

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field



class BotAcknowledgementRequest(BaseModel):
    """
    Модель для тела запроса ACK от бота, отправляемого по HTTP.
    Должен содержать command_id/correlation_id команды, которую он подтверждает.
    Перенесено из game_server/common_contracts/api_models/gateway_api.py
    """
    command_id: str = Field(..., description="ID команды, которую бот подтверждает.")
    status: str = Field(..., description="Статус выполнения команды (success, failed).")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки, если статус 'failed'.")

