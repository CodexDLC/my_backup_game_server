# game_server/contracts/dtos/character/commands.py

from typing import Literal
from pydantic import BaseModel, Field

# Импортируем базовую модель команды
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO


# 1. Определяем модель для полезной нагрузки (payload)
class CreateNewCharacterPayload(BaseModel):
    """Данные для команды создания нового персонажа."""
    account_id: int = Field(..., description="ID учетной записи игрока, к которой привязан персонаж.")
    discord_user_id: int = Field(..., description="Discord ID пользователя, для связи с Discord.")
    guild_id: int = Field(..., description="ID Discord-сервера, на котором происходит создание.")
    # Сюда можно добавить и другие поля, если они нужны для создания, 
    # например, name, class_id и т.д.


# 2. Обновляем DTO команды, чтобы он использовал нашу модель payload
class CreateNewCharacterCommandDTO(BaseCommandDTO):
    """
    DTO для команды создания нового персонажа.
    Использует вложенную модель Payload для передачи данных.
    """
    command: Literal["create_new_character"] = Field("create_new_character")
    payload: CreateNewCharacterPayload