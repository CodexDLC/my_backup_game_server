# contracts/api_models/system/responses.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Импортируем APIResponse из новой общей папки
from game_server.contracts.shared_models.base_responses import APIResponse

class RoutingSuccessData(BaseModel):
    """
    Модель данных для успешного ответа API маршрутизации.
    Перенесено из game_server/common_contracts/api_models/auth_api.py
    """
    account_id: int = Field(..., description="ID созданного или найденного игрового аккаунта.")
    shard_id: str = Field(..., description="ID шарда, на который следует направить игрока.")

# RoutingSuccessResponse из старого response_api.py, теперь здесь
class RoutingSuccessResponse(BaseModel):
    """
    Модель успешного ответа для маршрутизации.
    Перенесено из game_server/common_contracts/api_models/response_api.py
    (Предполагается, что будет использоваться как 'data' в APIResponse)
    """
    account_id: int = Field(..., description="ID созданного или найденного игрового аккаунта.")
    shard_id: str = Field(..., description="ID шарда, на который следует направить игрока.")


class StateEntityAPIResponse(BaseModel):
    """
    Pydantic-модель для сущностей состояний (state_entities) для ответа API.
    Перенесено из game_server/common_contracts/api_models/system_api.py
    """
    access_code: str = Field(..., description="Буквенно-цифровой код состояния/уровня доступа (теперь основной ID).")
    code_name: str = Field(..., description="Системное имя кода (например, ROLE_ADMIN, STATUS_ONLINE).")
    ui_type: str = Field(..., description="Тип сущности (access_level, status_flag).")
    description: str = Field(..., description="Описание сущности.")
    is_active: bool = Field(..., description="Статус активности сущности.")
    created_at: datetime = Field(..., description="Время создания записи.")

    model_config = ConfigDict(from_attributes=True)

