# game_server/common_contracts/dtos/base_dtos.py

import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Generic, TypeVar

T = TypeVar('T')

# --- БАЗОВЫЕ МОДЕЛИ ---

class BaseRequest(BaseModel):
    """Базовая модель для всех входящих HTTP-запросов от клиента."""
    correlation_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Уникальный идентификатор запроса для отслеживания, генерируемый клиентом или по умолчанию.")
    version: str = Field("1.0", description="Версия API, используемая клиентом для данного запроса.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Время отправки запроса клиентом (UTC).")
    trace_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Идентификатор трассировки для сквозного отслеживания операции.")
    span_id: Optional[uuid.UUID] = Field(None, description="Идентификатор текущей операции в рамках трассировки.")


class BaseCommandDTO(BaseModel):
    """Базовая модель для всех команд, отправляемых по шине сообщений."""
    command: str = Field(..., description="Имя команды.")
    correlation_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Уникальный идентификатор команды, генерируемый отправителем.")    
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Время отправки команды (UTC).")
    trace_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Идентификатор трассировки.")
    span_id: Optional[uuid.UUID] = Field(None, description="Идентификатор текущей операции в рамках трассировки.")
    payload: Optional[Dict[str, Any]] = Field(None, description="Полезная нагрузка команды.")
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал команду (для маршрутизации ответа).") # <--- ДОБАВЛЕНО


class BaseResultDTO(BaseModel, Generic[T]):
    """Базовая модель для всех результатов, возвращаемых микросервисами."""
    correlation_id: uuid.UUID = Field(..., description="ID корреляции с оригинальным запросом.")
    trace_id: Optional[uuid.UUID] = Field(None, description="ID трассировки.")
    span_id: Optional[uuid.UUID] = Field(None, description="ID span.")
    success: bool = Field(..., description="Успешно ли выполнена операция.")
    message: str = Field(..., description="Человекочитаемое сообщение о результате.")
    data: Optional[T] = Field(None, description="Дополнительные данные результата.")
    error: Optional[Dict[str, Any]] = Field(None, description="Детали ошибки, если успех = False.")
    client_id: Optional[str] = Field(None, description="ID клиента, которому должен быть доставлен результат (для Gateway).")

