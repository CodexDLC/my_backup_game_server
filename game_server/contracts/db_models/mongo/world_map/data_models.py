# contracts/db_models/mongo/world_map/data_models.py

from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# Импортируем LocationExit и LocationPresentationData из contracts/dtos/orchestrator/data_models
# Если они используются здесь и являются общими, а не только для YAML-парсинга
# from game_server.contracts.dtos.orchestrator.data_models import LocationExitData, LocationPresentationData # Пока закомментировано, если не уверены

class LocationExit(BaseModel):
    """
    DTO для одного выхода из локации.
    Перенесено из game_server/common_contracts/dtos_mongo/world_map_generation/world_map_dtos.py
    """
    label: str
    target_location_id: str

class LocationPresentationData(BaseModel):
    """
    Pydantic DTO для валидации структуры 'presentation' в YAML-файлах
    и для использования в StaticLocationData.
    Перенесено из game_server/common_contracts/dtos_mongo/world_map_generation/world_map_dtos.py
    """
    image_url: Optional[str] = None
    icon_emoji: Optional[str] = None

class StaticLocationData(BaseModel):
    """
    DTO для статических данных одной локации, готовых к сохранению в MongoDB.
    Перенесено из game_server/common_contracts/dtos_mongo/world_map_generation/world_map_dtos.py
    """
    location_id: str 
    parent_id: Optional[str] = None
    type: str 
    name: str
    description: str
    unified_display_type: Optional[str] = None
    exits: List[LocationExit] = [] # Используем Local LocationExit
    entry_point_location_id: Optional[str] = None
    presentation: Optional[LocationPresentationData] = None # Используем Local LocationPresentationData
    flavor_text_options: List[str] = []
    tags: List[str] = []                 

    class Config:
        populate_by_name = True
        extra = 'ignore' 

class WorldRegionDocument(BaseModel):
    """
    DTO для финального документа-региона, который будет сохранен в MongoDB.
    Перенесено из game_server/common_contracts/dtos_mongo/world_map_generation/world_map_dtos.py
    """
    id: str = Field(..., alias="_id")
    name: str
    locations: Dict[str, StaticLocationData]

    class Config:
        populate_by_name = True
        json_encoders = {}


class ActiveLocationDocument(BaseModel):
    """
    DTO для динамических данных одной активной локации.
    Это документ, который будет храниться в коллекции active_locations.
    Перенесено из game_server/common_contracts/dtos_mongo/world_map_generation/world_map_dtos.py
    """
    id: str = Field(..., alias="_id")
    last_update: datetime = Field(default_factory=datetime.utcnow)
    world_instance_id: Optional[str] = None

    players: List[Dict[str, Any]] = []
    npcs: List[Dict[str, Any]] = []
    items_on_ground: List[Dict[str, Any]] = []
    resource_nodes: List[Dict[str, Any]] = []
    location_effects: List[Dict[str, Any]] = []

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" if v else None
        }

