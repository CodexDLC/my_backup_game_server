# contracts/api_models/system/requests.py

from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from game_server.contracts.shared_models.base_requests import BaseRequest

# Импортируем BaseRequest из новой общей папки


class DiscordShardLoginRequest(BaseRequest):
    """
    API-модель запроса для HTTP-запроса Discord Shard Login.
    Перенесено из game_server/common_contracts/api_models/auth_api.py
    """
    command: Literal["discord_shard_login"] = Field("discord_shard_login", description="Идентификатор команды для входа с шарда.")
    account_id: int = Field(..., description="Внутренний ID аккаунта пользователя.")

class HubRoutingRequest(BaseRequest):
    """
    API-модель запроса для инициации и маршрутизации из хаба.
    Перенесено из game_server/common_contracts/api_models/auth_api.py
    """
    command: Literal["discord_hub_registered"] = Field("discord_hub_registered", description="Имя команды для AuthService (регистрация/первичный вход).")
    discord_user_id: str = Field(..., description="Глобальный ID пользователя Discord.")
    guild_id: int = Field(..., description="ID Discord-сервера (хаба), откуда пришел запрос.")
    client_id: Optional[str] = Field(None, description="ID клиента, который инициировал запрос (для маршрутизации ответа).")

class CreateNewCharacterRequest(BaseRequest):
    """
    API-модель запроса для команды create_new_character.
    Обновлена, чтобы соответствовать новой, уточненной ответственности.
    """

    command: Literal["create_new_character"] = Field("create_new_character")
    account_id: int = Field(..., description="ID аккаунта, для которого создается персонаж.")
    discord_user_id: int = Field(..., description="ID пользователя Discord.")
    guild_id: int = Field(..., description="ID Discord-сервера, с которого пришел запрос.")
    client_id: Optional[str] = Field(None, description="ID клиента для маршрутизации ответа.")

class LoginCharacterByIdRequest(BaseRequest):
    """
    API-модель запроса для команды character_login_by_id.
    Перенесено из game_server/common_contracts/api_models/auth_api.py
    """
    command: Literal["character_login_by_id"] = Field("character_login_by_id")
    character_id: int = Field(..., description="ID персонажа, которого нужно залогинить и закэшировать.")
    client_id: Optional[str] = Field(None, description="ID клиента для маршрутизации ответа.")

class GetStateEntityByKeyRequest(BaseRequest):
    """
    Модель запроса для получения сущности состояния по ключу.
    Перенесено из game_server/common_contracts/api_models/system_api.py
    """
    command: Literal["state_entity:get_by_key"] = Field(
        "state_entity:get_by_key",
        description="Имя команды для получения сущности состояния по ключу."
    )
    key: str = Field(..., description="Уникальный ключ сущности состояния.")

class GetAllStateEntitiesRequest(BaseRequest):
    """
    Модель запроса для получения всех сущностей состояния с опциональными фильтрами.
    Используется для команды 'system:get_all_state_entities'.
    Перенесено из game_server/common_contracts/api_models/system_api.py
    """
    command: Literal["system:get_all_state_entities"] = Field(
        "system:get_all_state_entities",
        description="Имя команды для SystemServices."
    )
    guild_id: int = Field(..., description="ID Discord-гильдии, для которой запрашиваются сущности.")
    entity_type: Optional[str] = Field(None, description="Опциональный фильтр по типу сущности (e.g., 'role', 'channel').")

