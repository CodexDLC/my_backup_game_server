# game_server/api_fast/api_models/discord_api.py

from pydantic import BaseModel, ConfigDict, Field, conlist
from typing import Optional, List, Dict, Any
from datetime import datetime
from typing_extensions import Annotated # Импортируем Annotated

# Импортируем стандартизированные модели ответов из вашего файла
from .response_api import APIResponse, ErrorModel, create_success_response, create_error_response


# --- Модели для DiscordEntity ---

class DiscordEntityBase(BaseModel):
    """Базовая модель для сущности Discord (категории, канала).
    Соответствует полям таблицы DiscordEntity."""
    guild_id: int = Field(..., description="ID Discord-сервера, на котором находится сущность.")
    entity_type: str = Field(..., max_length=50, description="Тип сущности: 'category', 'text_channel', 'forum', 'news', 'voice', и т.д.")
    name: str = Field(..., max_length=100, description="Имя сущности, как оно отображается в Discord.")
    parent_id: Optional[int] = Field(None, description="Discord ID родительской категории (если это канал).")
    permissions: Optional[str] = Field(None, description="Специальные разрешения для канала (например, 'read_only').")
    description: Optional[str] = Field(None, description="Описание канала (для документации или использования в Discord).")


class DiscordEntityCreateRequest(DiscordEntityBase):
    """Модель для запроса создания новой сущности Discord.
    discord_id не включаем, так как он присваивается Discord'ом или бэкендом после создания."""
    pass


class DiscordEntityAPIResponse(DiscordEntityBase):
    """
    Модель ответа API для одной сущности Discord,
    включающая ID из нашей базы данных и Discord ID.
    """
    id: int = Field(..., description="Уникальный ID сущности в нашей базе данных.")
    discord_id: int = Field(..., description="Уникальный ID сущности в Discord.")
    created_at: datetime = Field(..., description="Время создания записи.")

    class Config:
        from_attributes = True


# --- Модели запросов/ответов для операций ---

class DiscordEntitySyncItem(DiscordEntityBase):
    """
    Элемент для пакетной синхронизации.
    discord_id может быть опциональным, если это новая сущность,
    или обязательным, если это обновление существующей.
    """
    discord_id: Optional[int] = Field(None, description="Уникальный ID сущности в Discord (опционально для создания, обязательно для обновления).")


class DiscordEntitySyncRequest(BaseModel):
    """
    Модель запроса для пакетной синхронизации сущностей Discord.
    Принимает список сущностей для создания/обновления.
    """
    # Исправлено: использование Annotated для conlist
    entities: Annotated[List[DiscordEntitySyncItem], Field(min_length=1)] = Field(..., description="Список сущностей Discord для синхронизации.")


class DiscordEntitySyncDetails(BaseModel):
    """Модель деталей ответа для пакетной синхронизации."""
    created_count: int = Field(..., description="Количество успешно созданных сущностей.")
    updated_count: int = Field(..., description="Количество успешно обновленных сущностей.")
    deleted_count: int = Field(0, description="Количество удаленных сущностей (если purge_existing=True).")
    errors: List[Dict[str, Any]] = Field([], description="Список ошибок, возникших в процессе синхронизации.")
    processed_entities: List[DiscordEntityAPIResponse] = Field([], description="Детали всех успешно обработанных сущностей (созданных/обновленных).")


class DiscordEntityBatchDeleteRequest(BaseModel):
    """Модель запроса для пакетного удаления сущностей Discord."""
    guild_id: int = Field(..., description="ID Discord-сервера, с которого удаляются сущности.")
    # Исправлено: использование Annotated для conlist
    discord_ids: Annotated[List[int], Field(min_length=1)] = Field(..., description="Список Discord ID сущностей для удаления.")


class DiscordEntityBatchDeleteResponseData(BaseModel):
    """Модель данных для ответа на пакетное удаление."""
    deleted_count: int = Field(..., description="Количество успешно удаленных сущностей.")


class DiscordEntityGetByGuildResponseData(BaseModel):
    """Модель данных для ответа на получение списка сущностей по guild_id."""
    entities: List[DiscordEntityAPIResponse] = Field(..., description="Список сущностей Discord для указанного сервера.")
    


class StateEntityDiscordBase(BaseModel):
    """Базовая модель для сущности StateEntityDiscord."""
    guild_id: int = Field(..., description="ID Discord-сервера.")
    role_id: int = Field(..., description="Discord ID роли.")
    
    access_code: Optional[str] = Field(None, description="Буквенно-цифровой код состояния/уровня доступа (опционально).")
    role_name: str = Field(..., max_length=255, description="Имя роли в Discord.")
    permissions: Optional[str] = Field(None, description="Опциональный строковый флаг разрешений (например, 'read_only', 'admin_only').")


class StateEntityDiscordCreateUpdateRequest(StateEntityDiscordBase): # <--- ВОТ ЭТА МОДЕЛЬ
    """Модель для создания/обновления одной записи StateEntityDiscord."""
    pass


class StateEntityDiscordAPIResponse(StateEntityDiscordBase):
    """Модель ответа API для одной сущности StateEntityDiscord."""
    created_at: datetime = Field(..., description="Время создания записи.")
    updated_at: datetime = Field(..., description="Время последнего обновления записи.")

    model_config = ConfigDict(from_attributes=True) # Позволяет создавать из ORM объектов


class StateEntityDiscordBatchCreateUpdateRequest(BaseModel):
    roles: Annotated[List[StateEntityDiscordCreateUpdateRequest], Field(min_length=1)] = Field(..., description="Список ролей Discord для массового создания/обновления.")


class StateEntityDiscordBatchDeleteRequest(BaseModel):
    """Модель для массового удаления записей StateEntityDiscord по role_id."""
    guild_id: int = Field(..., description="ID Discord-сервера, с которого удаляются роли.")
    role_ids: Annotated[List[int], Field(min_length=1)] = Field(..., description="Список Discord ID ролей для удаления.")


class StateEntityDiscordBatchDeleteResponseData(BaseModel):
    """Модель данных для ответа на массовое удаление записей StateEntityDiscord."""
    deleted_count: int = Field(..., description="Количество успешно удаленных записей.")
