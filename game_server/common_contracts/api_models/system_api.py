# game_server\common_contracts\api_models\system_api.py

from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, ConfigDict, Field

from game_server.common_contracts.shared_models.api_contracts import BaseRequest


class StateEntityAPIResponse(BaseModel):
    """Pydantic-модель для сущностей состояний (state_entities) для ответа API."""
    access_code: str = Field(..., description="Буквенно-цифровой код состояния/уровня доступа (теперь основной ID).")
    code_name: str = Field(..., description="Системное имя кода (например, ROLE_ADMIN, STATUS_ONLINE).")
    ui_type: str = Field(..., description="Тип сущности (access_level, status_flag).")
    description: str = Field(..., description="Описание сущности.")
    is_active: bool = Field(..., description="Статус активности сущности.")
    created_at: datetime = Field(..., description="Время создания записи.")

    model_config = ConfigDict(from_attributes=True)


class GetStateEntityByKeyRequest(BaseRequest):
    """
    Модель запроса для получения сущности состояния по ключу.
    """
    command: Literal["state_entity:get_by_key"] = Field(
        "state_entity:get_by_key",
        description="Имя команды для получения сущности состояния по ключу."
    )
    key: str = Field(..., description="Уникальный ключ сущности состояния.")


class GetAllStateEntitiesRequest(BaseRequest):
    """
    Модель запроса для получения всех сущностей состояния с опциональными фильтрами.
    Используется для команды 'system:get_all_state_entities'.
    """
    command: Literal["system:get_all_state_entities"] = Field(
        "system:get_all_state_entities",
        description="Имя команды для SystemServices."
    )
    guild_id: int = Field(..., description="ID Discord-гильдии, для которой запрашиваются сущности.")
    entity_type: Optional[str] = Field(None, description="Опциональный фильтр по типу сущности (e.g., 'role', 'channel').")



