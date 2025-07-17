# contracts/shared_models/base_responses.py

import uuid
from typing import Optional, Dict, Any, Generic, TypeVar
from pydantic import BaseModel, Field
from enum import Enum

T = TypeVar('T')

class ResponseStatus(str, Enum):
    """Статусы ответа для WebSocket-сообщений и других операций."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"

class ErrorDetail(BaseModel):
    """Детализация ошибки для стандартизированных ответов."""
    code: str = Field(..., description="Код ошибки (например, 'VALIDATION_ERROR', 'PERMISSION_DENIED').")
    message: str = Field(..., description="Человекочитаемое сообщение об ошибке.")
    context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст ошибки.")

class APIResponse(BaseModel, Generic[T]):
    """Универсальная модель для HTTP-ответов FastAPI (используется для 202 Accepted)."""
    success: bool = Field(..., description="Индикатор успешности операции.")
    message: Optional[str] = Field(None, description="Сообщение о статусе операции.")
    data: Optional[T] = Field(None, description="Полезная нагрузка ответа.")

class SuccessResponse(BaseModel):
    """Модель данных для успешных 202 Accepted HTTP-ответов (содержит только correlation_id)."""
    correlation_id: uuid.UUID = Field(..., description="Уникальный идентификатор запроса, полученный от клиента.")

