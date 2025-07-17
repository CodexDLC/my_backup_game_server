# contracts/dtos/game_world/results.py

from typing import Dict
from pydantic import BaseModel

# Импортируем WorldLocationDataDTO из data_models в этом же домене
from .data_models import WorldLocationDataDTO

class GetWorldDataResponseData(BaseModel):
    """
    DTO for the response data to the command requesting the static game world skeleton.
    Contains a dictionary of all locations by their ID.
    Перенесено из game_server/common_contracts/dtos/game_world_dtos.py
    """
    locations: Dict[str, WorldLocationDataDTO]

