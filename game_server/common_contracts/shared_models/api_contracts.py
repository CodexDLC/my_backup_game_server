# game_server/shared_models/api_contracts.py

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List, Union, Generic, TypeVar
from pydantic import BaseModel, Field
from typing_extensions import Literal

# --- 1. Базовые модели для HTTP-запросов и ответов (Gateway <-> Клиент) ---


class BaseRequest(BaseModel):
    """Базовая модель для всех входящих HTTP-запросов от клиента."""
    correlation_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Уникальный идентификатор запроса для отслеживания, генерируемый клиентом или по умолчанию.")
    version: str = Field("1.0", description="Версия API, используемая клиентом для данного запроса.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Время отправки запроса клиентом (UTC).")
    trace_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Идентификатор трассировки для сквозного отслеживания операции.")
    span_id: Optional[uuid.UUID] = Field(None, description="Идентификатор текущей операции в рамках трассировки.")
    
    
T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Универсальная модель для HTTP-ответов FastAPI (используется для 202 Accepted)."""
    success: bool = Field(..., description="Индикатор успешности операции.")
    message: Optional[str] = Field(None, description="Сообщение о статусе операции.")
    data: Optional[T] = Field(None, description="Полезная нагрузка ответа.")

class SuccessResponse(BaseModel):
    """Модель данных для успешных 202 Accepted HTTP-ответов."""
    correlation_id: uuid.UUID = Field(..., description="Уникальный идентификатор запроса, полученный от клиента.")

# --- 2. Модели для WebSocket-взаимодействия (Gateway <-> Клиент) ---

# 2.1. Статусы и Детализация ошибок (общие для WS-payload)
class ResponseStatus(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"

class ErrorDetail(BaseModel):
    code: str = Field(..., description="Код ошибки (например, 'VALIDATION_ERROR', 'PERMISSION_DENIED').")
    message: str = Field(..., description="Человекочитаемое сообщение об ошибке.")
    context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст ошибки.")

# 2.2. Payload-ы для WebSocketMessage (специфичные для типов сообщений)
# 🔥 ИЗМЕНЕНИЕ: WebSocketResponsePayload адаптирован под формат 'request_id'
class WebSocketResponsePayload(BaseModel):
    """Payload для ответа на КОМАНДУ клиента."""
    request_id: uuid.UUID = Field(..., description="ID запроса, к которому относится ответ.")
    status: ResponseStatus = Field(..., description="Статус выполнения запроса.")
    message: str = Field(..., description="Человекочитаемое сообщение о результате.")
    data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные ответа.")
    error: Optional[ErrorDetail] = Field(None, description="Детали ошибки, если статус FAIL.")

# 🔥 ИЗМЕНЕНИЕ: WebSocketEventPayload адаптирован под формат 'event_id' и 'type' в корне payload
class WebSocketEventPayload(BaseModel):
    """Payload для асинхронных СОБЫТИЙ от сервера клиенту."""
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Уникальный ID события, генерируемый сервером.")
    type: str = Field(..., description="Тип события (например, 'PLAYER_MOVED', 'INVENTORY_UPDATED').")
    payload: Dict[str, Any] = Field(..., description="Данные, связанные с событием.") # Поле 'payload' внутри payload

# 🔥 НОВОЕ: Payload для КОМАНДЫ от клиента к серверу через WebSocket
class WebSocketCommandFromClientPayload(BaseModel):
    """Payload для КОМАНДЫ от клиента к серверу через WebSocket."""
    command_id: uuid.UUID = Field(..., description="Уникальный ID команды.")
    type: str = Field(..., description="Тип команды (например, 'hub_login').")
    payload: Dict[str, Any] = Field(..., description="Полезная нагрузка команды.")


# 🔥 ИЗМЕНЕНИЕ: WebSocketSystemCommandPayload переименован в WebSocketSystemCommandToClientPayload
# чтобы подчеркнуть, что это команда ОТ СЕРВЕРА К СИСТЕМНОМУ КЛИЕНТУ.
# Его структура соответствует вашим примерам.
class WebSocketSystemCommandToClientPayload(BaseModel):
    """Payload для СИСТЕМНОЙ КОМАНДЫ от сервера к системному клиенту."""
    command_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Уникальный идентификатор системной команды, генерируется сервером.")
    command_name: Literal["UPDATE_CONFIG", "SHUTDOWN", "RELOAD_MODULE", "SYNC_TIME", "NOTIFY_ADMINS"] = Field(..., description="Имя системной команды.")
    command_data: Dict[str, Any] = Field(..., description="Данные для выполнения системной команды (должны быть строго типизированы в конкретных случаях).")

# 2.3. Универсальная обертка для всех WebSocket-сообщений
# 🔥 ИЗМЕНЕНИЕ: WebSocketMessage теперь объединяет новые Payload-ы
class WebSocketMessage(BaseModel):
    """Универсальная модель-обертка для всех сообщений, отправляемых по WebSocket."""
    # Эти поля на уровне корневого "конверта" WebSocket
    type: Literal["RESPONSE", "EVENT", "COMMAND", "SYSTEM_COMMAND", "AUTH_CONFIRM"] = Field(..., description="Тип WebSocket-сообщения.") # COMMAND для команд от клиента, SYSTEM_COMMAND для команд от сервера к системному клиенту
    correlation_id: uuid.UUID = Field(..., description="ID для корреляции запросов/ответов.")
    trace_id: Optional[uuid.UUID] = Field(None, description="ID для трассировки запроса (опционально).")
    span_id: Optional[uuid.UUID] = Field(None, description="ID для span в трассировке (опционально).")
    payload: Dict[str, Any] = Field(..., description="Основная полезная нагрузка сообщения.")
    # � КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ: Добавляем client_id на верхний уровень WebSocketMessage
    client_id: Optional[str] = Field(None, description="ID клиента, которому адресовано или от которого пришло сообщение.")
    target_audience: Optional[Literal["ADMIN_PANEL", "DISCORD_BOT", "PLAYER", "ALL"]] = Field(None, description="Целевая аудитория для широковещательных системных команд.")

    
    # Payload теперь строго типизирован, основываясь на 'type'
    payload: Union[WebSocketResponsePayload, WebSocketEventPayload, WebSocketCommandFromClientPayload, WebSocketSystemCommandToClientPayload, Dict[str, Any]] = Field(..., description="Основная полезная нагрузка сообщения.")

    # Дополнительные поля для маршрутизации/идентификации клиента
    player_id: Optional[str] = Field(None, description="ID игрока/аккаунта, если сообщение адресовано конкретному игроку (для игровых WS).")
    target_audience: Optional[Literal["PLAYER", "ADMIN_PANEL", "DISCORD_BOT", "ALL"]] = Field(
        "PLAYER", description="Целевая аудитория сообщения (для системных WS).")
    specific_client_ids: Optional[List[uuid.UUID]] = Field(None, description="Список ID конкретных клиентов для точечной рассылки (для системных WS).")

# 2.4. Модель подтверждения получения WebSocket-сообщения (WebSocketAck)
class WebSocketAck(BaseModel):
    """Модель для подтверждения получения WebSocket-сообщения клиентом (через WebSocket)."""
    message_id: uuid.UUID = Field(..., description="Идентификатор сообщения (correlation_id/event_id/command_id), которое было получено.")
    processing_status: Literal["received", "processing", "completed", "error"] = Field(..., description="Статус обработки сообщения клиентом.")
    error_details: Optional[str] = Field(None, description="Детали ошибки, если статус 'error'.")
    received_at: datetime = Field(default_factory=datetime.utcnow, description="Время получения сообщения клиентом (UTC).")

# 2.5. Модель для аутентификации системных соединений
class SystemConnectionAuth(BaseModel):
    """Модель для аутентификации системных WebSocket-соединений."""
    api_key: str = Field(..., min_length=64, max_length=64, description="Уникальный API-ключ для аутентификации.")
    client_type: Literal["ADMIN_PANEL", "MONITORING", "BOT_CONTROLLER"] = Field(..., description="Тип системного клиента.")
    permissions: List[str] = Field(..., description="Список разрешений для данного системного клиента.")

# --- 3. Модели для HTTP ACK от системных клиентов (/{command_id}/ack) ---
# 🔥 НОВОЕ: SystemCommandHttpAckRequest
class SystemCommandHttpAckRequest(BaseModel):
    """Модель для HTTP POST ACK запроса от системного клиента."""
    command_id: uuid.UUID = Field(..., description="Уникальный идентификатор команды, которую системный клиент подтверждает.")
    status: Literal["success", "failed"] = Field(..., description="Статус выполнения команды системным клиентом.")
    error_details: Optional[str] = Field(None, description="Детали ошибки, если статус 'failed'.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Время отправки ACK клиентом (UTC).")
    # Можно добавить trace_id, span_id если системный клиент их поддерживает в ACK