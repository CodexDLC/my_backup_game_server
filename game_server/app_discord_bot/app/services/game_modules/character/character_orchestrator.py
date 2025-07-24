# game_server/app_discord_bot/app/services/character/character_orchestrator.py

import inject
import discord
import logging

from .character_config import LOGIC_HANDLER_MAP, PRESENTATION_HANDLER_MAP
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager

class CharacterOrchestrator:
    """Оркестратор для сервиса Character."""
    @inject.autoparams()
    def __init__(self, interaction_response_manager: InteractionResponseManager, logger: logging.Logger):
        self.interaction_response_manager = interaction_response_manager
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def process(self, command_str: str, interaction: discord.Interaction, response_message_object: discord.Message | None = None):
        command_parts = command_str.split(':', 1)
        command_name = command_parts[0]

        LogicHandlerClass = LOGIC_HANDLER_MAP.get(command_name)
        if not LogicHandlerClass:
            self.logger.warning(f"Логический обработчик для команды '{command_name}' не найден в CharacterOrchestrator.")
            return

        logic_handler_instance = inject.instance(LogicHandlerClass)
        data_dto = await logic_handler_instance.execute(command_str, interaction)

        if data_dto is None:
            self.logger.info(f"Логический обработчик для команды '{command_name}' вернул None.")
            return

        data_type = data_dto.type
        PresentationHandlerClass = PRESENTATION_HANDLER_MAP.get(data_type)
        if not PresentationHandlerClass:
            self.logger.warning(f"Презентационный обработчик для типа '{data_type}' не найден в CharacterOrchestrator.")
            return

        presentation_handler_instance = inject.instance(PresentationHandlerClass)
        await presentation_handler_instance.execute(data_dto, interaction, helpers=None, response_message_object=response_message_object)