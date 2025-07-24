# game_server/app_discord_bot/app/services/game_modules/inspection/inspection_dtos.py

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# --- DTO для первого шага (выбор категории) ---

@dataclass
class InspectionCategoryDTO:
    """
    DTO для описания одной категории объектов для осмотра.
    """
    display_name: str  # Имя для отображения на кнопке (например, "Игроки")
    count: int         # Количество объектов в категории
    category_key: str  # Уникальный ключ для использования в custom_id (например, "players")

@dataclass
class InspectionCategoriesDTO:
    """
    DTO для передачи списка категорий, доступных для осмотра в локации.
    """
    categories: List[InspectionCategoryDTO] = field(default_factory=list)
    type: str = field(default="DISPLAY_INSPECTION_CATEGORIES")


# --- DTO для второго шага (отображение списка) ---

@dataclass
class InspectedEntityDTO:
    """
    DTO для описания одного объекта в списке (для Select Menu).
    """
    entity_id: str
    label: str  # Текст, который будет показан в списке (например, "Player123 [Ур. 10]")
    description: Optional[str] = None # Краткое описание под текстом

@dataclass
class PaginationInfoDTO:
    """
    DTO для хранения информации о пагинации.
    """
    current_page: int
    total_pages: int
    category_key: str

@dataclass
class InspectionListDTO:
    """
    DTO для передачи списка сущностей для отображения.
    """
    title: str # Заголовок для эмбеда (например, "Игроки в локации")
    entities: List[InspectedEntityDTO] = field(default_factory=list)
    pagination: Optional[PaginationInfoDTO] = None
    type: str = field(default="DISPLAY_INSPECTION_LIST")

# --- DTO для обзора локации (Уровень 1) ---

@dataclass
class LookAroundResultObjectDTO:
    """
    DTO для представления одного объекта, найденного при обзоре,
    с информацией, необходимой для отображения.
    """
    category_key: str
    display_name: str
    count: int
    description_key: str
    embed_group: str

@dataclass
class LookAroundResultDTO:
    """
    DTO для передачи полной информации об обзоре локации.
    Содержит списки объектов, сгруппированных по типу эмбеда.
    """
    dynamic_entities: List[LookAroundResultObjectDTO] = field(default_factory=list)
    environmental_objects: List[LookAroundResultObjectDTO] = field(default_factory=list)
    type: str = field(default="DISPLAY_OVERVIEW") # Новый тип для презентера обзора


# --- DTO для третьего шага (детальный осмотр сущности) ---

@dataclass
class ActionDTO:
    """
    Data Transfer Object для описания одного действия (кнопки).
    """
    key: str
    label: str
    style: str
    disabled: bool
    # Шаблон для формирования кастомного ID. 
    # Например: "trade:initiate:{entity_id}"
    custom_id_template: Optional[str] = None

@dataclass
class EntityDetailsDTO:
    """
    DTO для передачи детальной информации о конкретной сущности.
    Теперь включает список доступных действий (кнопок).
    """
    entity_id: str
    category_key: str
    title: str  # Заголовок для эмбеда (например, "Детали: Shadow")
    description: str # Основное описание сущности
    fields: List[Dict[str, Any]] = field(default_factory=list) # Дополнительные поля для эмбеда (например, HP, Уровень)
    image_url: Optional[str] = None # URL изображения сущности
    actions: List[ActionDTO] = field(default_factory=list) # Список кнопок действий для этой сущности
    type: str = field(default="DISPLAY_ENTITY_DETAILS") # Новый тип для презентера детального осмотра

