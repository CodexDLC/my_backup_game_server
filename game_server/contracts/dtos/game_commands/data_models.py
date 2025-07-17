# game_server/contracts/dtos/game_commands/data_models.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field # <--- ИЗМЕНЕНО: Импортируем BaseModel и Field



class LocationDynamicSummaryDTO(BaseModel): # <--- ИЗМЕНЕНО: Наследуемся от BaseModel
    """
    DTO для возврата краткой динамической информации о локации,
    например, для футера или кратких сводок.
    """
    players_in_location: int = Field(default=0, description="Количество игроков в текущей локации.")
    npcs_in_location: int = Field(default=0, description="Количество NPC в текущей локации.")
    last_update: str = Field(default="", description="Время последнего обновления динамических данных локации (ISO формат даты).")
    # Можно добавить другие поля по мере необходимости, например, items_on_ground_count, effects_count и т.д.