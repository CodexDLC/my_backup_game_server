from pydantic import UUID4, BaseModel, Field, field_serializer
from typing import Annotated, List, Optional
from datetime import datetime

class DiscordBindingBase(BaseModel):
    guild_id: int = Field(..., description="ID Discord-сервера (гильдии).")
    world_id: UUID4 = Field(..., description="ID мира, к которому привязана запись.")
    access_key: str = Field(..., description="Уникальный ключ доступа.")
    permissions: int = Field(..., description="Уровень разрешений.")
    created_at: Annotated[datetime, Field(..., description="Дата создания.")]
    updated_at: Annotated[datetime, Field(..., description="Дата обновления.")]
    category_id: Optional[int] = Field(None, description="ID Discord-категории.")
    channel_id: Optional[int] = Field(None, description="ID Discord-канала.")

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }

    @field_serializer("created_at", "updated_at")
    def serialize_datetime_to_iso(self, dt: datetime) -> str:
        return dt.isoformat() + "Z"

class DiscordBindingResponse(DiscordBindingBase):
    pass

class GetAllBindingsResponse(BaseModel):
    status: str = Field(..., description="Статус запроса.")
    data: List[DiscordBindingResponse] = Field(..., description="Список привязок.")

class StateEntitiesDiscordBase(BaseModel):
    world_id: UUID4 = Field(..., description="ID мира.")
    access_code: int = Field(..., description="Код доступа.")
    role_name: str = Field(..., description="Название роли.")
    role_id: int = Field(..., description="ID роли.")
    permissions: int = Field(0, description="Битовая маска разрешений.")

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }

class StateEntitiesDiscordCreateUpdateRequest(StateEntitiesDiscordBase):
    guild_id: int = Field(..., description="ID гильдии.")

class StateEntitiesDiscordResponse(StateEntitiesDiscordBase):
    guild_id: int = Field(..., description="ID гильдии.")
    created_at: Annotated[datetime, Field(..., description="Дата создания.")]
    updated_at: Annotated[datetime, Field(..., description="Дата обновления.")]

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }

class StateEntitiesBase(BaseModel):
    access_code: int = Field(..., description="Код доступа.")
    code_name: str = Field(..., description="Название кода.")
    ui_type: str = Field(..., description="Тип UI.")
    description: Optional[str] = Field("", description="Описание.")
    is_active: Optional[bool] = Field(True, description="Активность.")

    model_config = {
        "from_attributes": True
    }

class WorldDataV4(BaseModel):
    world_id: UUID4 = Field(..., description="ID мира.")
    world_name: str = Field(..., min_length=1, max_length=255, description="Название мира.")
    is_static: bool = Field(..., description="Статичность мира.")

    model_config = {
        "from_attributes": True
    }

class WorldCreateUpdateRequestV4(WorldDataV4):
    pass

class WorldResponseV4(WorldDataV4):
    pass
