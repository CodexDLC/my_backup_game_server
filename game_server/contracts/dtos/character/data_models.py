# contracts/dtos/character/data_models.py



from typing import Optional
from pydantic import BaseModel, Field


class CharacterDTO(BaseModel):
    """
    DTO для представления данных персонажа на экране выбора.
    """
    character_id: int = Field(..., description="Уникальный ID персонажа.") # Остается int
    name: str = Field(..., description="Имя персонажа.")
    surname: Optional[str] = Field(None, description="Фамилия персонажа (если есть).")
    creature_type_id: int = Field(..., description="ID типа существа (расы/класса) персонажа.")
    status: str = Field(..., description="Текущий статус персонажа (online, offline, in_game).")
    clan_id: Optional[int] = Field(None, description="ID клана персонажа (если состоит в клане).")
    

class CharacterCreatedDTO(BaseModel):
    """
    DTO с информацией о созданном персонаже.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    character_id: int
    account_id: int

