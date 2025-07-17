# contracts/dtos/game_world/data_models.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class WorldLocationExitDTO(BaseModel):
    """
    DTO для одного выхода из локации.
    Перенесено из game_server/common_contracts/dtos/game_world_dtos.py
    """
    label: str
    target_location_id: str

class WorldLocationPresentationDTO(BaseModel):
    """
    DTO для валидации структуры 'presentation' в YAML-файлах
    и для использования в StaticLocationData.
    Перенесено из game_server/common_contracts/dtos/game_world_dtos.py
    """
    image_url: Optional[str] = None
    icon_emoji: Optional[str] = None

class WorldLocationDataDTO(BaseModel):
    """
    Pydantic DTO для статических данных одной локации,
    передаваемых от бэкенда к боту.
    Полностью соответствует финализированному слепку статической локации.
    Перенесено из game_server/common_contracts/dtos/game_world_dtos.py
    """
    location_id: str 
    parent_id: Optional[str] = None
    type: str # ИЗМЕНЕНИЕ: Поле 'type' (бывшее location_type)
    name: str
    description: str
    
    exits: List[WorldLocationExitDTO] = [] 

    child_location_ids: Optional[List[str]] = [] 
    rules: Optional[Dict[str, Any]] = {}         
    interactions: Optional[Dict[str, Any]] = {} 

    unified_display_type: Optional[str] = None 
    specific_category: Optional[str] = None    
    presentation: Optional[WorldLocationPresentationDTO] = None 
    entry_point_location_id: Optional[str] = None 
    flavor_text_options: List[str] = [] 
    tags: List[str] = []                 

    class Config:
        populate_by_name = True
        extra = 'ignore'

