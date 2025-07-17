# contracts/db_models/mongo/character/data_models.py

from typing import Any, Dict
from pydantic import BaseModel

class CharacterCacheDTO(BaseModel):
    """
    DTO, содержащий полный документ персонажа из кэша MongoDB.
    Перенесено из game_server/common_contracts/dtos_mongo/character/character_dtos.py
    """
    character_document: Dict[str, Any]

