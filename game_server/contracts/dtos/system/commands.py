# contracts/dtos/system/commands.py

import uuid
from typing import Literal, Optional
from pydantic import BaseModel, Field

# Импортируем BaseCommandDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO
# Импортируем CharacterDTO из dtos/character/data_models



class GetCharacterListForAccountCommandDTO(BaseCommandDTO):
    """
    DTO для команды получения списка персонажей для аккаунта.
    Заменяет DiscordShardLoginCommandDTO, делая команду более универсальной.
    """
    command: Literal["get_character_list_for_account"] = Field("get_character_list_for_account", description="Идентификатор команды для получения списка персонажей.")
    account_id: int = Field(..., description="Внутренний ID аккаунта пользователя.")


# --- НОВОЕ: DTO для полезной нагрузки команды выхода ---
class LogoutCharacterPayload(BaseModel):
    """
    Полезная нагрузка для команды выхода персонажа.
    Содержит ID персонажа и ID аккаунта.
    """
    # ИЗМЕНЕНО: Тип character_id изменен на int
    character_id: int = Field(..., description="ID персонажа, который выходит из игры.")
    account_id: int = Field(..., description="Внутренний ID аккаунта пользователя, к которому принадлежит персонаж.")


class LogoutCharacterCommandDTO(BaseCommandDTO):
    """
    DTO для команды выхода из персонажа.
    Используется для отключения персонажа от игрового мира.
    """
    command: Literal["logout_character"] = Field("logout_character", description="Идентификатор команды для выхода из персонажа.")
    payload: LogoutCharacterPayload = Field(..., description="Полезная нагрузка команды выхода, содержащая ID персонажа и аккаунта.")

