# /services/authentication/authentication_orchestrator.py

import inject
import discord
import logging

from .authentication_config import AUTH_LOGIC_HANDLER_MAP, AUTH_PRESENTATION_HANDLER_MAP
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager

class AuthenticationOrchestrator:
    """Оркестратор для сервиса Аутентификации."""
    @inject.autoparams()
    def __init__(self, interaction_response_manager: InteractionResponseManager, logger: logging.Logger):
        self.interaction_response_manager = interaction_response_manager
        self.logger = logger

    async def process(self, command_str: str, interaction: discord.Interaction, response_message_object: discord.Message | None = None):
        
        # Роутер уже отрезал сервис, command_str - это 'start_registration' или 'start_login'
        # Нам все еще нужно отделить payload, если он есть
        command_parts = command_str.split(':', 1)
        command_name = command_parts[0]
        payload = command_parts[1] if len(command_parts) > 1 else None
        
        # Ищем обработчик по короткому имени команды
        LogicHandlerClass = AUTH_LOGIC_HANDLER_MAP.get(command_name)
        
        if not LogicHandlerClass:
            self.logger.warning(f"Оркестратор не нашел обработчик для команды: '{command_name}'")
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
            return

        try:
            logic_handler_instance = inject.instance(LogicHandlerClass)
            
            # Передаем payload в execute. Для регистрации он будет None, для логина - то, что нужно.
            data_dto = await logic_handler_instance.execute(payload, interaction, response_message_object=response_message_object)
            
            if data_dto is None:
                if response_message_object:
                    await self.interaction_response_manager.complete_thinking_message(response_message_object)
                return

            # --- Обработка PresentationHandler (остается без изменений) ---
            data_type = data_dto.type
            PresentationHandlerClass = AUTH_PRESENTATION_HANDLER_MAP.get(data_type)
            if not PresentationHandlerClass:
                if response_message_object:
                    await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
                return

            presentation_handler_instance = inject.instance(PresentationHandlerClass)
            await presentation_handler_instance.execute(data_dto, interaction, helpers=None, response_message_object=response_message_object)

        except Exception as e:
            self.logger.critical(f"СБОЙ В ОРКЕСТРАТОРЕ ПРИ СОЗДАНИИ/ЗАПУСКЕ ОБРАБОТЧИКА для команды '{command_name}': {e}", exc_info=True)
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)