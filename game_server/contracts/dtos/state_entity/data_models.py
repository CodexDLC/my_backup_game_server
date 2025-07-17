# contracts/dtos/state_entity/data_models.py

from typing import Literal, Optional, Any
from pydantic import BaseModel, Field

class StateEntityDTO(BaseModel):
    """
    Единое представление сущности состояния (например, системная роль, статус игрока).
    Перенесено из game_server/common_contracts/dtos/state_entity_dtos.py
    """
    id: Optional[int] = Field(None, description="Внутренний ID сущности в БД (опционально).")
    access_code: str = Field(..., description="Уникальный код доступа, связанный с сущностью.")
    code_name: str = Field(..., description="Программное имя сущности (например, ROLE_ADMIN).")
    ui_type: Literal["access_level", "status_flag", "game_setting"] = Field(..., description="Тип сущности для UI/логики.")
    description: Optional[str] = Field(None, description="Описание для UI.")
    is_active: bool = Field(True, description="Активна ли сущность.")
    created_at: Optional[Any] = Field(None, description="Дата создания.")
    updated_at: Optional[Any] = Field(None, description="Дата последнего обновления.")

