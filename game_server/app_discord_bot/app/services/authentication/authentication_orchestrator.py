# game_server/app_discord_bot/app/services/authentication/authentication_orchestrator.py

import inject
import discord # 🔥 НОВОЕ: Добавляем импорт discord

from .authentication_config import AUTH_LOGIC_HANDLER_MAP, AUTH_PRESENTATION_HANDLER_MAP
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager # 🔥 НОВОЕ: Импортируем менеджер ответов

class AuthenticationOrchestrator:
    """Оркестратор для сервиса Аутентификации."""
    @inject.autoparams() # Добавим декоратор для инъекции зависимостей
    def __init__(self, interaction_response_manager: InteractionResponseManager): # 🔥 НОВОЕ: Инжектируем менеджер
        self.interaction_response_manager = interaction_response_manager

    # 🔥 ГЛАВНОЕ ИЗМЕНЕНИЕ: Добавляем response_message_object в сигнатуру метода
    async def process(self, command_str: str, interaction: discord.Interaction, response_message_object: discord.Message | None = None):
        command_parts = command_str.split(':', 1)
        command_name = command_parts[0]
        payload = command_parts[1] if len(command_parts) > 1 else None
        
        LogicHandlerClass = AUTH_LOGIC_HANDLER_MAP.get(command_name)
        if not LogicHandlerClass:
            # Если обработчик не найден, удаляем индикатор
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
            return

        logic_handler_instance = inject.instance(LogicHandlerClass)
        # 🔥 ИЗМЕНЕНИЕ: Передаем response_message_object в логический обработчик
        data_dto = await logic_handler_instance.execute(payload, interaction, response_message_object=response_message_object)
        
        # 🔥 НОВОЕ: Если обработчик логики вернул None, значит, дальнейшие действия не требуются.
        # Удаляем индикатор.
        if data_dto is None:
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
            return

        data_type = data_dto.type # Используем data_dto вместо data для единообразия
        PresentationHandlerClass = AUTH_PRESENTATION_HANDLER_MAP.get(data_type)
        if not PresentationHandlerClass:
            # Если презентер не найден, удаляем индикатор
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object, delete_delay=0)
            return

        presentation_handler_instance = inject.instance(PresentationHandlerClass)
        # 🔥 ИЗМЕНЕНИЕ: Передаем response_message_object в презентационный обработчик
        await presentation_handler_instance.execute(data_dto, interaction, helpers=None, response_message_object=response_message_object)