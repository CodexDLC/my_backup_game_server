# game_server/common_contracts/dtos/state_entity_dtos.py

import uuid
from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import Annotated

# Импортируем базовые DTO
from game_server.common_contracts.dtos.base_dtos import BaseCommandDTO, BaseResultDTO


# --- 1. БАЗОВАЯ МОДЕЛЬ ДАННЫХ ---
class StateEntityDTO(BaseModel):
    """
    Единое представление сущности состояния (например, системная роль, статус игрока).
    """
    id: Optional[int] = Field(None, description="Внутренний ID сущности в БД (опционально).")
    access_code: str = Field(..., description="Уникальный код доступа, связанный с сущностью.")
    code_name: str = Field(..., description="Программное имя сущности (например, ROLE_ADMIN).")
    ui_type: Literal["access_level", "status_flag", "game_setting"] = Field(..., description="Тип сущности для UI/логики.")
    description: Optional[str] = Field(None, description="Описание для UI.")
    is_active: bool = Field(True, description="Активна ли сущность.")
    created_at: Optional[Any] = Field(None, description="Дата создания.")
    updated_at: Optional[Any] = Field(None, description="Дата последнего обновления.")


# --- 2. КОМАНДЫ (Запросы к сервису) ---

class GetAllStateEntitiesCommand(BaseCommandDTO):
    """Команда для получения всех сущностей состояния."""
    command: Literal["system:get_all_state_entities"] = "system:get_all_state_entities"
    guild_id: Optional[int] = Field(None, description="Опциональный ID гильдии для фильтрации.")
    entity_type: Optional[Literal["role", "channel", "category", "player_status"]] = Field(None, description="Опциональный фильтр по типу сущности.")


class GetStateEntityByKeyCommand(BaseCommandDTO):
    """Команда для получения сущности состояния по ключу."""
    command: Literal["state_entity:get_by_key"] = "state_entity:get_by_key"
    access_code: str = Field(..., description="Код доступа сущности.")


# --- 3. РЕЗУЛЬТАТЫ (Ответы от сервиса) ---

# ИСПРАВЛЕНИЕ: GetAllStateEntitiesResult теперь наследуется от BaseModel, а не BaseResultDTO.
# Это DTO для поля 'data' в BaseResultDTO.
class GetAllStateEntitiesResult(BaseModel):
    """Результат получения списка сущностей состояния."""
    entities: List[StateEntityDTO] = Field([], description="Список найденных сущностей состояния.")

# НОВОЕ: Добавляем определение StateEntityResult, который является результатом для GetStateEntityByKeyCommand
# Он должен быть BaseResultDTO, содержащим один StateEntityDTO в поле 'data'.
class StateEntityResult(BaseResultDTO[StateEntityDTO]): # Наследуется от BaseResultDTO
    """Результат получения одной сущности состояния."""
    # Поле 'data' уже определено в BaseResultDTO, его тип указан в [StateEntityDTO]
    # Если сущность не найдена, 'data' будет None, что соответствует Optional[StateEntityDTO] в BaseResultDTO.
    pass

