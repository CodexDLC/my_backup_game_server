# game_server/app_discord_bot/app/services/authentication/lobby/lobby_orchestrator.py

import inject
import discord
import logging
from discord.ext import commands

from .lobby_config import LOGIC_HANDLER_MAP, PRESENTATION_HANDLER_MAP
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager

class LobbyOrchestrator:
    """Оркестратор для сервиса Лобби."""
    @inject.autoparams()
    def __init__(self, interaction_response_manager: InteractionResponseManager, logger: logging.Logger):
        self.interaction_response_manager = interaction_response_manager
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def process(self, command_str: str, interaction: discord.Interaction, response_message_object: discord.Message | None = None):
        # command_str будет выглядеть как "enter_world:16" или "show_characters"
        
        command_parts = command_str.split(':', 1)
        command_name = command_parts[0]
        # 🔥 ИЗМЕНЕНО: Удалена строка, которая извлекала payload здесь для передачи в execute
        # payload = command_parts[1] if len(command_parts) > 1 else None 

        LogicHandlerClass = LOGIC_HANDLER_MAP.get(command_name)
        if not LogicHandlerClass:
            self.logger.warning(f"Логический обработчик для команды '{command_name}' не найден в LobbyOrchestrator.")
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
            return

        logic_handler_instance = inject.instance(LogicHandlerClass)
        
        self.logger.info(f"Передаю команду '{command_str}' логическому обработчику '{command_name}'.")

        try:
            # 🔥 ГЛАВНОЕ ИЗМЕНЕНИЕ: Передаем ПОЛНУЮ строку command_str в execute
            # Например, "enter_world:16" будет передан как payload в SelectCharacterHandler.execute()
            data_dto = await logic_handler_instance.execute(command_str, interaction) # ИЗМЕНЕНО: Передаем command_str как payload

            if data_dto is None:
                self.logger.info(f"Логический обработчик для команды '{command_name}' вернул None. Дальнейшие действия не требуются.")
                if response_message_object:
                    await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
                return

            data_type = data_dto.type
            PresentationHandlerClass = PRESENTATION_HANDLER_MAP.get(data_type)
            if not PresentationHandlerClass:
                self.logger.warning(f"Презентационный обработчик для типа данных '{data_type}' не найден в LobbyOrchestrator.")
                if response_message_object:
                    await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
                return

            presentation_handler_instance = inject.instance(PresentationHandlerClass)
            self.logger.info(f"Передаю данные типа '{data_type}' презентационному обработчику '{PresentationHandlerClass.__name__}'.")
            await presentation_handler_instance.execute(data_dto, interaction, helpers=None, response_message_object=response_message_object)
            self.logger.info(f"Презентационный обработчик '{PresentationHandlerClass.__name__}' успешно завершил работу.")

        except Exception as e:
            self.logger.error(f"Ошибка при выполнении логического обработчика для команды '{command_name}': {e}", exc_info=True)
            if not interaction.response.is_done():
                await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)
            elif response_message_object:
                await response_message_object.edit(content=f"Произошла ошибка: {e}", delete_after=None)

