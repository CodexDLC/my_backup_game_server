# api_models/character_api.py
from pydantic import BaseModel, Field
from typing import Literal, Optional

# --- Модели для Character Creation ---

class CharacterCreateRequest(BaseModel):
    discord_id: str = Field(..., description="Discord ID пользователя.")

class CharacterCreateData(BaseModel):
    """Модель данных для успешного ответа при создании персонажа."""
    character_id: int
    name: str

# --- Модели для Auto Session ---

ActionType = Literal["start", "stop", "status", "update"]
IdentifierType = Literal["id", "name", "discord_id"]
CategoryType = Literal["Crafting", "General", "Exploration", "Trade"]

class AutoSessionRequest(BaseModel):
    """Модель для запроса на управление авто-сессией."""
    action: ActionType
    identifier_type: IdentifierType
    identifier_value: str = Field(min_length=1)
    category: Optional[CategoryType] = None

class AutoSessionData(BaseModel):
    """Модель данных для успешного ответа от авто-сессии."""
    status: str
    message: str
    session_details: Optional[dict] = None