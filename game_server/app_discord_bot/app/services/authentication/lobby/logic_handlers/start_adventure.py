# game_server/app_discord_bot/app/services/authentication/lobby/logic_handlers/start_adventure.py

import inject
import discord
import logging
from typing import Union

from .select_character import SelectCharacterHandler

from .create_character_handler import CreateCharacterHandler


from game_server.app_discord_bot.core.contracts.handler_response_dto import AdventureStartedDTO, CharacterSelectionDTO
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager
from game_server.app_discord_bot.transport.websocket_client.ws_manager import WebSocketManager
from game_server.app_discord_bot.app.services.utils.error_handlers import handle_flow_errors

# Исправленные импорты
from game_server.contracts.dtos.system.commands import GetCharacterListForAccountCommandDTO # Предполагаем, что этот DTO тоже будет исправлен
from game_server.contracts.api_models.character.responses import CharacterListResponseData
from game_server.contracts.shared_models.base_responses import ResponseStatus
from game_server.contracts.shared_models.websocket_base_models import WebSocketResponsePayload


class StartAdventureHandler:
    """
    Оркестратор для флоу "Начать приключение". 
    Вызывает другие обработчики для создания или выбора персонажа.
    """
    @inject.autoparams()
    def __init__(
        self,
        account_data_manager: IAccountDataManager,
        ws_manager: WebSocketManager,
        logger: logging.Logger,
        # Инжектируем другие обработчики
        create_character_handler: CreateCharacterHandler,
        select_character_handler: SelectCharacterHandler
    ):
        self.account_data_manager = account_data_manager
        self.ws_manager = ws_manager
        self.logger = logger
        self.create_character_handler = create_character_handler
        self.select_character_handler = select_character_handler

    @handle_flow_errors
    async def execute(self, payload: str, interaction: discord.Interaction) -> Union[AdventureStartedDTO, CharacterSelectionDTO]:
        user = interaction.user
        guild = interaction.guild
        self.logger.info(f"Запускается оркестратор 'Начать приключение' для {user.name} (ID: {user.id}).")

        account_id_str = await self.account_data_manager.get_account_id_by_discord_id(user.id)
        if not account_id_str:
            raise ValueError("Ваш игровой аккаунт не найден. Пройдите регистрацию.")
        account_id = int(account_id_str)

        # 1. Проверяем, есть ли уже персонажи
        # TODO: Эту логику тоже можно вынести в отдельный 'ShowCharactersHandler'
        get_chars_command_dto = GetCharacterListForAccountCommandDTO(account_id=account_id) # Ожидаем, что этот DTO тоже будет исправлен
        response, _ = await self.ws_manager.send_command(
            command_type=get_chars_command_dto.command,
            command_payload=get_chars_command_dto.model_dump(),
            domain="system",
            discord_context={"user_id": user.id, "guild_id": guild.id}
        )
        response_payload = WebSocketResponsePayload(**response.get('payload', {}))
        if response_payload.status != ResponseStatus.SUCCESS:
            raise RuntimeError(f"Ошибка при проверке списка персонажей: {response_payload.message}")

        character_list_data = CharacterListResponseData(**response_payload.data)
        
        # 2. Принимаем решение на основе наличия персонажей
        if character_list_data.characters:
            # Сценарий А: Персонажи есть -> Показываем выбор
            self.logger.info(f"У аккаунта {account_id} найдены персонажи. Показываем выбор.")
            return CharacterSelectionDTO(
                type="character_selection_view",
                characters=character_list_data.characters
            )
        else:
            # Сценарий Б: Персонажей нет -> Создаем и сразу логиним
            self.logger.info(f"Персонажей не найдено. Запускаем флоу создания и логина.")
            
            # Шаг 1: Вызываем обработчик создания
            new_character_id = await self.create_character_handler.execute(
                account_id=account_id,
                user=user,
                guild=guild
            )
            # Шаг 2: Вызываем обработчик логина, имитируя нажатие кнопки
            # Формируем payload-строку, которую ожидает SelectCharacterHandler
            login_payload_str = f"enter_world:{new_character_id}"
            return await self.select_character_handler.execute(login_payload_str, interaction)