# game_server/common_contracts/dtos/auth_dtos.py

import uuid # Для uuid.UUID
from typing import Literal, Union, Optional, Dict, Any, TypeAlias

from pydantic import BaseModel, Field

# Импортируем базовые DTO из common_contracts.dtos
from game_server.common_contracts.dtos.base_dtos import BaseCommandDTO, BaseResultDTO
# Импортируем BaseModel, Field, ErrorDetail из общего файла моделей



class DiscordShardLoginCommandDTO(BaseCommandDTO): # Теперь наследует от BaseCommandDTO
    """
    DTO для команды входа пользователя Discord с шарда.
    """
    command: Literal["discord_shard_login"] = Field("discord_shard_login", description="Идентификатор команды для входа с шарда.")
    discord_user_id: str = Field(..., description="Глобальный ID пользователя Discord.")
    # correlation_id, trace_id, span_id, timestamp - наследуются от BaseCommandDTO


class HubRoutingCommandDTO(BaseCommandDTO): # Теперь наследует от BaseCommandDTO
    """
    DTO для команды маршрутизации пользователя из хаба.
    """
    command: Literal["discord_hub_login"] = Field("discord_hub_login", description="Идентификатор команды для маршрутизации из хаба.")
    discord_user_id: str = Field(..., description="Глобальный ID пользователя Discord.")
    guild_id: str = Field(..., description="ID Discord-сервера (хаба), откуда пришел запрос.")
    avatar: Optional[str] = Field(None, description="URL аватара пользователя Discord.")
    locale: Optional[str] = Field(None, description="Локаль пользователя Discord.")
    # correlation_id, trace_id, span_id, timestamp - наследуются от BaseCommandDTO


# --- DTO для РЕЗУЛЬТАТОВ работы сервисов ---

class SessionResultData(BaseModel):
    """
    DTO с данными результата успешного создания сессии.
    Это 'data' для BaseResultDTO.
    """
    auth_token: str = Field(..., description="Временный сессионный токен из Redis.")


class HubRoutingResultData(BaseModel):
    """
    DTO с данными результата успешной маршрутизации.
    Это 'data' для BaseResultDTO.
    """
    account_id: int = Field(..., description="ID созданного или найденного игрового аккаунта.")
    shard_id: str = Field(..., description="ID шарда, на который следует направить игрока.")


class SessionResultDTO(BaseResultDTO[SessionResultData]): # Наследует от BaseResultDTO и типизирует data
    """
    Результат операции создания сессии.
    """
    # correlation_id, trace_id, span_id, success, message - наследуются от BaseResultDTO
    # data: SessionResultData - уже типизировано через Generic[T]


class HubRoutingResultDTO(BaseResultDTO[HubRoutingResultData]): # Наследует от BaseResultDTO и типизирует data
    """
    Результат операции маршрутизации.
    """
    # correlation_id, trace_id, span_id, success, message - наследуются от BaseResultDTO
    # data: HubRoutingResultData - уже типизировано через Generic[T]


# ErrorResultDTO удаляется, так как BaseResultDTO теперь может содержать ErrorDetail
# Типы для возвращаемых значений из обработчиков адаптированы под новые DTO
type ShardLoginResult = HubRoutingResultDTO # DiscordShardLoginDTO -> HubRoutingResultDTO, т.к. это путь логина
type HubRoutingResult = HubRoutingResultDTO # HubRoutingDTO -> HubRoutingResultDTO