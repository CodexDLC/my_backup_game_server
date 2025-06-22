# game_server/common_contracts/discord_integration/discord_commands_and_events.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Annotated
import uuid

# --- DTO/Commands for DiscordEntity (сущности: категории, каналы, роли, пользователи) ---
class DiscordEntityDTO(BaseModel):
    id: Optional[int] = None
    discord_id: Optional[Annotated[int, Field(ge=0)]] = None
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии (сервера)")
    entity_type: str = Field(..., description="Тип сущности (CHANNEL, ROLE, USER, CATEGORY)")
    name: str = Field(..., description="Имя сущности")
    parent_id: Optional[Annotated[int, Field(ge=0)]] = None
    is_deleted: bool = Field(False, description="Флаг удаления")
    # Добавьте другие поля, если они есть в вашей модели DiscordEntity

class DiscordEntityCreateCommand(BaseModel):
    discord_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID сущности")
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии")
    entity_type: str = Field(..., description="Тип сущности (CHANNEL, ROLE, USER, CATEGORY)")
    name: str = Field(..., description="Имя сущности")
    parent_id: Optional[Annotated[int, Field(ge=0)]] = Field(None, description="Discord ID родительской сущности")

class DiscordEntityUpdateCommand(BaseModel):
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии")
    discord_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID сущности")
    updates: Dict[str, Any] = Field(..., description="Словарь полей для обновления")

class DiscordEntitiesSyncCommand(BaseModel):
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии")
    entities_data: Annotated[List[DiscordEntityCreateCommand], Field(min_length=1)] = Field(..., description="Список данных сущностей для синхронизации")

class DiscordEntitiesDeleteCommand(BaseModel):
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии")
    discord_ids: Annotated[List[Annotated[int, Field(ge=0)]], Field(min_length=1)] = Field(..., description="Список Discord ID сущностей для удаления")

class DiscordSyncResultDTO(BaseModel):
    created_count: int = 0
    updated_count: int = 0
    deleted_count: int = 0
    errors: List[Dict[str, Any]] = []
    processed_entities: List[DiscordEntityDTO] = []


# --- DTO/Commands for StateEntityDiscord (привязка ролей к игровым состояниям/сущностям) ---
# ПК теперь (guild_id, discord_role_id), access_code - атрибут
class StateEntityDiscordDTO(BaseModel):
    id: Optional[int] = None # Если есть суррогатный PK
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии")
    discord_role_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID роли")
    access_code: str = Field(..., description="Код доступа (название роли или флага)") # Теперь просто атрибут
    description: Optional[str] = None
    # Добавьте другие поля из StateEntityDiscord

# Для создания/обновления: все поля, но ПК (guild_id, discord_role_id)
class StateEntityDiscordCreateUpdateCommand(BaseModel):
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии")
    discord_role_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID роли")
    access_code: str = Field(..., description="Код доступа (название роли или флага)")
    description: Optional[str] = None

# Для обновления: идентифицируем по ПК (guild_id, discord_role_id), обновляем access_code/description
class StateEntityDiscordUpdateCommand(BaseModel):
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии")
    discord_role_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID роли")
    # Обновляемые поля
    access_code: Optional[str] = Field(None, description="Новый код доступа") # access_code теперь можно обновлять
    description: Optional[str] = Field(None, description="Новое описание")


# Для удаления: только ПК (guild_id, discord_role_id)
class StateEntityDiscordDeleteCommand(BaseModel):
    guild_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID гильдии")
    discord_role_id: Annotated[int, Field(ge=0)] = Field(..., description="Discord ID роли")
    # access_code: str = Field(..., description="Код доступа") # Удален из ПК для удаления

# Для массового создания/обновления, используется та же DTO
class StateEntitiesDiscordBatchCreateCommand(BaseModel):
    roles_batch: Annotated[List[StateEntityDiscordCreateUpdateCommand], Field(min_length=1)] = Field(..., description="Список данных ролей для создания/обновления")

# --- DTO/Commands for StateEntity (общие сущности состояния системы) ---
class StateEntityDTO(BaseModel):
    id: Optional[int] = None
    key: str = Field(..., description="Уникальный ключ сущности состояния (например, 'SERVER_STATUS', 'MAINTENANCE_MODE')")
    value: str = Field(..., description="Значение сущности состояния")
    description: Optional[str] = None
    is_active: bool = Field(True, description="Активна ли сущность состояния")

class StateEntityGetByAccessCodeCommand(BaseModel):
    access_code: str = Field(..., description="Код доступа для сущности состояния")

class StateEntityUpdateCommand(BaseModel):
    entity_id: Optional[int] = None
    key: Optional[str] = None
    updates: Dict[str, Any] = Field(..., description="Поля для обновления")