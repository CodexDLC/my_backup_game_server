# contracts/shared_models/websocket_base_models.py

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field
from typing_extensions import Literal

# Импортируем ErrorDetail и ResponseStatus из base_responses
from .base_responses import ErrorDetail, ResponseStatus

class WebSocketResponsePayload(BaseModel):
    """Payload для ответа на КОМАНДУ клиента."""
    request_id: uuid.UUID = Field(..., description="ID запроса, к которому относится ответ.")
    status: ResponseStatus = Field(..., description="Статус выполнения запроса.")
    message: str = Field(..., description="Человекочитаемое сообщение о результате.")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные ответа.")
    error: Optional[ErrorDetail] = Field(None, description="Детали ошибки, если статус FAIL.")

class WebSocketEventPayload(BaseModel):
    """Payload для асинхронных СОБЫТИЙ от сервера клиенту."""
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Уникальный ID события, генерируемый сервером.")
    type: str = Field(..., description="Тип события (например, 'PLAYER_MOVED', 'INVENTORY_UPDATED').")
    payload: Dict[str, Any] = Field(..., description="Данные, связанные с событием.")

class WebSocketCommandFromClientPayload(BaseModel):
    """Payload для КОМАНДЫ от клиента к серверу через WebSocket."""
    command_id: uuid.UUID = Field(..., description="Уникальный ID команды.")
    type: str = Field(..., description="Тип команды (например, 'hub_login').")
    domain: str = Field(..., description="Целевой домен/сервис для команды (например, 'auth', 'system').")
    payload: Dict[str, Any] = Field(..., description="Полезная нагрузка команды.")

class WebSocketSystemCommandToClientPayload(BaseModel):
    """Payload для СИСТЕМНОЙ КОМАНДЫ от сервера к системному клиенту."""
    command_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Уникальный идентификатор системной команды, генерируется сервером.")
    command_name: Literal["UPDATE_CONFIG", "SHUTDOWN", "RELOAD_MODULE", "SYNC_TIME", "NOTIFY_ADMINS"] = Field(..., description="Имя системной команды.")
    command_data: Dict[str, Any] = Field(..., description="Данные для выполнения системной команды (должны быть строго типизированы в конкретных случаях).")

class WebSocketMessage(BaseModel):
    """Универсальная модель-обертка для всех сообщений, отправляемых по WebSocket."""
    type: Literal["RESPONSE", "EVENT", "COMMAND", "SYSTEM_COMMAND", "AUTH_CONFIRM"] = Field(..., description="Тип WebSocket-сообщения.")
    correlation_id: uuid.UUID = Field(..., description="ID для корреляции запросов/ответов.")
    trace_id: Optional[uuid.UUID] = Field(None, description="ID для трассировки запроса (опционально).")
    span_id: Optional[uuid.UUID] = Field(None, description="ID для span в трассировке (опционально).")
    client_id: Optional[str] = Field(None, description="ID клиента, которому адресовано или от которого пришло сообщение.")
    target_audience: Optional[Literal["ADMIN_PANEL", "DISCORD_BOT", "PLAYER", "ALL"]] = Field(None, description="Целевая аудитория для широковещательных системных команд.")
    
    payload: Union[WebSocketResponsePayload, WebSocketEventPayload, WebSocketCommandFromClientPayload, WebSocketSystemCommandToClientPayload, Dict[str, Any]] = Field(..., description="Основная полезная нагрузка сообщения.")

    player_id: Optional[str] = Field(None, description="ID игрока/аккаунта, если сообщение адресовано конкретному игроку (для игровых WS).")
    specific_client_ids: Optional[List[uuid.UUID]] = Field(None, description="Список ID конкретных клиентов для точечной рассылки (для системных WS).")

class WebSocketAck(BaseModel):
    """Модель для подтверждения получения WebSocket-сообщения клиентом (через WebSocket)."""
    message_id: uuid.UUID = Field(..., description="Идентификатор сообщения (correlation_id/event_id/command_id), которое было получено.")
    processing_status: Literal["received", "processing", "completed", "error"] = Field(..., description="Статус обработки сообщения клиентом.")
    error_details: Optional[str] = Field(None, description="Детали ошибки, если статус 'error'.")
    received_at: datetime = Field(default_factory=datetime.utcnow, description="Время получения сообщения клиентом (UTC).")

