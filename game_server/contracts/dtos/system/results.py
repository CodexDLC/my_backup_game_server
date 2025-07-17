# contracts/dtos/system/results.py

from typing import Optional, List
from pydantic import BaseModel, Field

# Импортируем BaseResultDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
# Импортируем CharacterDTO из dtos/character/data_models
from game_server.contracts.dtos.character.data_models import CharacterDTO


class HubRoutingResultData(BaseModel):
    """
    DTO с данными результата успешной маршрутизации.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    account_id: int = Field(..., description="ID созданного или найденного игрового аккаунта.")
    shard_id: int = Field(..., description="ID шарда, на который следует направить игрока.")

class HubRoutingResultDTO(BaseResultDTO[HubRoutingResultData]):
    """
    Результат операции маршрутизации.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    pass

class DiscordShardLoginResponseData(BaseModel):
    """
    DTO с данными, возвращаемыми после успешного входа через Discord Shard Login.
    Предназначен для поля 'data' в WebSocketResponsePayload.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    characters: List[CharacterDTO] = Field(..., description="Список персонажей аккаунта.")

class DiscordShardLoginResultDTO(BaseResultDTO[DiscordShardLoginResponseData]):
    """
    Результат операции входа через Discord Shard Login.
    Перенесено из game_server/common_contracts/dtos/auth_dtos.py
    """
    pass

