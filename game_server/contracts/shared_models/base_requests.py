# contracts/shared_models/base_requests.py

import uuid
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class BaseRequest(BaseModel):
    """Базовая модель для всех входящих HTTP-запросов от клиента."""
    correlation_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Уникальный идентификатор запроса для отслеживания, генерируемый клиентом или по умолчанию.")
    version: str = Field("1.0", description="Версия API, используемая клиентом для данного запроса.")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Время отправки запроса клиентом (UTC).")
    trace_id: uuid.UUID = Field(default_factory=uuid.uuid4, description="Идентификатор трассировки для сквозного отслеживания операции.")
    span_id: Optional[uuid.UUID] = Field(None, description="Идентификатор текущей операции в рамках трассировки.")

