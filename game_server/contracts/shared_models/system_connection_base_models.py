# contracts/shared_models/system_connection_base_models.py

import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from typing_extensions import Literal

class SystemConnectionAuth(BaseModel):
    """Модель для аутентификации системных WebSocket-соединений."""
    api_key: str = Field(..., min_length=64, max_length=64, description="Уникальный API-ключ для аутентификации.")
    client_type: Literal["ADMIN_PANEL", "MONITORING", "BOT_CONTROLLER"] = Field(..., description="Тип системного клиента.")
    permissions: List[str] = Field(..., description="Список разрешений для данного системного клиента.")

class SystemCommandHttpAckRequest(BaseModel):
    """Модель для HTTP POST ACK запроса от системного клиента."""
    command_id: uuid.UUID = Field(..., description="Уникальный идентификатор команды, которую системный клиент подтверждает.")
    status: Literal["success", "failed"] = Field(..., description="Статус выполнения команды системным клиентом.")
    error_details: Optional[str] = Field(None, description="Детали ошибки, если статус 'failed'.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время отправки ACK клиентом (UTC).")

