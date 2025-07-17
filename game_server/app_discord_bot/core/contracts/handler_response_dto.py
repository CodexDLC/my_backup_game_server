from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

from game_server.contracts.dtos.character.data_models import CharacterDTO


# --- 1. Базовый класс ---
@dataclass
class BaseHandlerResponseDTO:
    """Базовый DTO, гарантирующий наличие поля 'type' для маршрутизации."""
    type: str


@dataclass
class StubResponseDTO(BaseHandlerResponseDTO):
    """DTO для простого текстового ответа от заглушки."""
    message: str
    view_to_show: Optional[str] = None # Опциональное поле, чтобы указать, какой View показать
    


@dataclass
class InitialLobbySetupDTO(BaseHandlerResponseDTO):
    characters: List[CharacterDTO]
    # Плюс любые другие данные, которые могут понадобиться для отображения
    
    
    
# --- DTO для отображения экрана выбора персонажа ---
@dataclass
class CharacterSelectionDTO(BaseHandlerResponseDTO):
    """DTO с данными для экрана выбора персонажа."""
    characters: List[CharacterDTO]


@dataclass
class AdventureStartedDTO(BaseHandlerResponseDTO):
    """
    DTO, возвращаемый после успешного создания/выбора персонажа и входа в лобби.
    Сигнализирует о необходимости отрисовать основной игровой интерфейс.
    """
    discord_user_id: int


@dataclass
class LoginSuccessDTO(BaseHandlerResponseDTO):
    """
    DTO, возвращаемый после любого успешного входа в лобби (новый или существующий персонаж).
    Сигнализирует о необходимости отрисовать основной игровой интерфейс.
    """
    discord_user_id: int
    

