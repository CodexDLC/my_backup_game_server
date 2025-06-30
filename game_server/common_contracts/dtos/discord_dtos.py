# game_server/common_contracts/dtos/discord_dtos.py

import uuid # Явно импортируем uuid, т.к. он используется в базовых DTO
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import Annotated

# Импортируем базовые DTO и BaseModel из общих контрактов
from game_server.common_contracts.dtos.base_dtos import BaseCommandDTO, BaseResultDTO


# --- 1. БАЗОВАЯ МОДЕЛЬ ДАННЫХ ---
# Единое представление любой сущности Discord в системе
class DiscordEntityDTO(BaseModel):
    """Единое представление любой сущности Discord в системе."""
    discord_id: int = Field(..., description="Discord ID сущности.")
    entity_type: Literal["category", "text_channel", "voice_channel", "role", "user", "guild", "news", "forum"] = Field(..., description="Тип сущности Discord.")
    name: str = Field(..., description="Имя сущности.")
    description: Optional[str] = Field(None, description="Описание сущности.")
    parent_id: Optional[int] = Field(None, description="ID родительской сущности (для каналов/категорий).")
    permissions: Optional[str] = Field(None, description="Строковый ключ набора разрешений.")
    access_code: Optional[str] = Field(None, description="Код доступа.")
    guild_id: int = Field(..., description="ID гильдии.")
    
    
# --- 2. КОМАНДЫ (Запросы к сервису) ---

# --- DTO для команды "discord:sync_entities" ---
class DiscordEntitiesSyncCommand(BaseCommandDTO):
    """Команда для массовой синхронизации (создания/обновления) сущностей Discord."""
    command: Literal["system:sync_discord_entities"] = "system:sync_discord_entities"
    
    guild_id: int = Field(..., description="ID Discord-гильдии.")

    class SyncItem(BaseModel):
        """Под-модель для одного элемента синхронизации."""
        discord_id: int = Field(..., description="ID сущности в Discord.")
        guild_id: int = Field(..., description="ID Discord-гильдии.")
        entity_type: Literal["category", "text_channel", "voice_channel", "role", "user", "guild", "news", "forum"] = Field(..., description="Тип сущности ('ROLE', 'CHANNEL', 'CATEGORY').") # Убедитесь, что Literal совпадает с DiscordEntityDTO
        name: str = Field(..., description="Имя сущности.")
        parent_id: Optional[int] = Field(None, description="ID родительской сущности.")
        permissions: Optional[str] = Field(None, description="Строка разрешений.")
        access_code: Optional[str] = Field(None, description="Универсальный код доступа.")
        description: Optional[str] = Field(None, description="Описание сущности.")
    entities_data: List[SyncItem] = Field(..., description="Список данных сущностей для синхронизации.")

# --- DTO для команды "discord:delete_entities" ---
class DiscordEntitiesDeleteCommand(BaseCommandDTO):
    """Команда для массового удаления сущностей Discord."""
    command: Literal["discord:delete_entities"] = "discord:delete_entities"
    
    guild_id: int = Field(..., description="ID Discord-гильдии.")
    discord_ids: Annotated[List[int], Field(min_length=1, description="Список ID Discord сущностей для удаления.")]


# --- DTO для команды "discord:create_single_entity" ---
class DiscordEntityCreateCommand(BaseCommandDTO):
    """Команда для создания одной сущности Discord."""
    command: Literal["discord:create_single_entity"] = "discord:create_single_entity"
    
    guild_id: int = Field(..., description="ID Discord-гильдии.")
    discord_id: int = Field(..., description="ID сущности в Discord.")
    entity_type: Literal["category", "text_channel", "voice_channel", "role", "user", "guild"] = Field(..., description="Тип сущности ('ROLE', 'CHANNEL', 'CATEGORY').") # Убедитесь, что Literal совпадает с DiscordEntityDTO
    name: str = Field(..., description="Имя сущности.")
    description: Optional[str] = Field(None, description="Описание сущности.")
    parent_id: Optional[int] = Field(None, description="ID родительской сущности.")
    permissions: Optional[str] = Field(None, description="Строка разрешений.")
    access_code: Optional[str] = Field(None, description="Универсальный код доступа.")


# --- DTO для команды "discord:get_entities" ---
# ИСПРАВЛЕНИЕ: GetDiscordEntitiesCommandDTO теперь наследуется от BaseCommandDTO и имеет поле 'command'
class GetDiscordEntitiesCommandDTO(BaseCommandDTO): # ИЗМЕНЕНО: Наследуется от BaseCommandDTO
    """Команда для получения списка сущностей Discord."""
    command: Literal["discord:get_entities"] = "discord:get_entities" # Добавлено поле command
    
    guild_id: int = Field(..., description="ID Discord-гильдии.")
    entity_type: Optional[Literal["category", "text_channel", "voice_channel", "role", "user", "guild"]] = Field(None, description="Опциональный фильтр по типу сущности.")
    discord_id: Optional[int] = Field(None, description="Конкретный Discord ID сущности для получения (опционально).")


# --- 3. РЕЗУЛЬТАТЫ (Ответы от сервиса) ---

class DiscordSyncResultDTO(BaseModel):
    """Результат массовой синхронизации сущностей Discord."""
    created_count: int = Field(0, description="Количество созданных сущностей.")
    updated_count: int = Field(0, description="Количество обновленных сущностей.")
    errors: List[Dict[str, Any]] = Field([], description="Список деталей ошибок при обработке.")
    processed_entities: List[DiscordEntityDTO] = Field([], description="Список обработанных сущностей.")


class DiscordDeleteResultDTO(BaseModel):
    """Результат массового удаления сущностей Discord."""
    deleted_count: int = Field(..., description="Количество удаленных сущностей.")


# ИСПРАВЛЕНИЕ: GetDiscordEntitiesResultDTO НЕ должен наследоваться от BaseResultDTO.
# Это DTO для поля 'data' в BaseResultDTO.
class GetDiscordEntitiesResultDTO(BaseModel): # ИЗМЕНЕНО: Наследуется от BaseModel
    """Результат получения списка сущностей Discord."""
    # Поле должно быть 'entities', чтобы соответствовать использованию
    entities: List[DiscordEntityDTO] = Field([], description="Список найденных сущностей Discord.")
