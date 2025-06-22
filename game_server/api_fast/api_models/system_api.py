# api_models/system_api.py
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

# --- Модели для Auth ---

class RegisterOrLoginRequest(BaseModel):
    identifier_type: str = Field(..., description="Тип идентификатора (e.g., 'discord_id').")
    identifier_value: str = Field(..., description="Значение идентификатора.")
    username: str
    avatar: Optional[str] = None
    locale: Optional[str] = None
    region: Optional[str] = None

class CharacterLoginSummary(BaseModel):
    """Краткая информация о персонаже для ответа при логине."""
    character_id: int
    name: str
    
    # ИЗМЕНЕНИЕ V2: Замена orm_mode на from_attributes
    model_config = ConfigDict(from_attributes=True)

class AuthData(BaseModel):
    """Данные, возвращаемые после успешной аутентификации."""
    account_id: int
    auth_token: str
    character_ids: List[CharacterLoginSummary] = []

class CharacterSummary(BaseModel):
    """Полная краткая информация о персонаже для списка."""
    character_id: int
    name: str
    surname: Optional[str]
    creature_type_id: int
    status: str
    
    # ИЗМЕНЕНИЕ V2: Замена orm_mode на from_attributes
    model_config = ConfigDict(from_attributes=True)

class PlayerData(BaseModel):
    """Полные данные игрока для ответа /player_data."""
    account_info: Dict[str, Any]
    characters: List[CharacterSummary]
    active_character_id: Optional[int]
    active_character_summary: Optional[CharacterSummary]

class LinkingUrlData(BaseModel):
    """Данные для сгенерированной ссылки привязки."""
    linking_token: str
    linking_url: str
    expires_at: str
    
    
class WorldData(BaseModel):
    """Pydantic-модель, описывающая данные об игровом мире."""
    world_id: uuid.UUID
    world_name: str
    is_static: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class RegionData(BaseModel):
    """Pydantic-модель для региона. Поля нужно будет адаптировать под вашу ORM-модель."""
    id: int # Пример
    name: str # Пример
    world_id: uuid.UUID # Пример

    model_config = ConfigDict(from_attributes=True)

class SubregionData(BaseModel):
    """Pydantic-модель для подрегиона."""
    id: int # Пример
    name: str # Пример
    region_id: uuid.UUID # Пример

    model_config = ConfigDict(from_attributes=True)

# --- НОВАЯ МОДЕЛЬ: StateEntityAPIResponse ---
class StateEntityAPIResponse(BaseModel):
    """Pydantic-модель для сущностей состояний (state_entities) для ответа API."""
    # Удаляем 'id' и вместо него используем 'access_code' как основной идентификатор
    # id: int = Field(..., description="Уникальный ID сущности в базе данных.") # Эту строку удаляем или комментируем

    access_code: str = Field(..., description="Буквенно-цифровой код состояния/уровня доступа (теперь основной ID).") # <--- ЭТО МЕНЯЕМ
    code_name: str = Field(..., description="Системное имя кода (например, ROLE_ADMIN, STATUS_ONLINE).")
    ui_type: str = Field(..., description="Тип сущности (access_level, status_flag).")
    description: str = Field(..., description="Описание сущности.")
    is_active: bool = Field(..., description="Статус активности сущности.")
    created_at: datetime = Field(..., description="Время создания записи.")

    model_config = ConfigDict(from_attributes=True) # Это оставляем, оно важно для работы с ORM объектами