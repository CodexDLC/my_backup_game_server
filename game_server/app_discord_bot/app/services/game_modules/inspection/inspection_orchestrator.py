# game_server/app_discord_bot/app/services/game_modules/inspection/inspection_orchestrator.py

import inject
import discord
import logging

# Импортируем карты маршрутов из нашего собственного конфига
from .inspection_config import LOGIC_HANDLER_MAP, PRESENTATION_HANDLER_MAP
from game_server.app_discord_bot.app.services.utils.interaction_response_manager import InteractionResponseManager

class InspectionOrchestrator:
    """Оркестратор для сервиса Inspection (Осмотр)."""
    @inject.autoparams()
    def __init__(self, interaction_response_manager: InteractionResponseManager, logger: logging.Logger):
        self.interaction_response_manager = interaction_response_manager
        self.logger = logger
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def process(self, command_str: str, interaction: discord.Interaction, response_message_object: discord.Message | None = None):
        """
        Обрабатывает входящую команду, находит нужный обработчик и передает ему управление.
        response_message_object: Объект сообщения-индикатора, отправленного InteractionRouter.
        """
        data_dto = None # Инициализируем для использования в finally

        try:
            # Отделяем имя команды от ее параметров (например, "look_around" из "inspection:look_around")
            command_parts = command_str.split(':', 1)
            command_name = command_parts[0]

            # Находим класс логического обработчика по имени команды
            LogicHandlerClass = LOGIC_HANDLER_MAP.get(command_name)
            if not LogicHandlerClass:
                self.logger.warning(f"Логический обработчик для команды '{command_name}' не найден в InspectionOrchestrator.")
                # Если здесь нет обработчика, то и DTO не будет.
                return

            # Создаем экземпляр обработчика и выполняем его
            logic_handler_instance = inject.instance(LogicHandlerClass)
            data_dto = await logic_handler_instance.execute(command_str, interaction)

            # Если обработчик ничего не вернул, завершаем работу
            if data_dto is None:
                self.logger.info(f"Логический обработчик для команды '{command_name}' вернул None.")
                return

            # Находим класс презентера по типу данных из DTO
            data_type = getattr(data_dto, 'type', None)
            PresentationHandlerClass = PRESENTATION_HANDLER_MAP.get(data_type)
            if not PresentationHandlerClass:
                self.logger.warning(f"Презентационный обработчик для типа '{data_type}' не найден в InspectionOrchestrator.")
                return

            # Создаем экземпляр презентера и отрисовываем результат
            presentation_handler_instance = inject.instance(PresentationHandlerClass)
            await presentation_handler_instance.execute(data_dto, interaction, helpers=None, response_message_object=response_message_object) # Передаем response_message_object, хотя презентер его не использует

        except Exception as e:
            self.logger.critical(f"Критическая ошибка в InspectionOrchestrator при обработке команды '{command_str}': {e}", exc_info=True)
            # В случае критической ошибки можно отправить пользователю эфемерное сообщение
            if not interaction.response.is_done():
                await interaction.followup.send("Произошла непредвиденная ошибка при выполнении действия.", ephemeral=True)
            elif response_message_object:
                # Если response_message_object есть, но основное сообщение не обновлено из-за ошибки
                # Можно изменить текст сообщения индикатора на ошибку, чтобы пользователь увидел
                await self.interaction_response_manager.edit_thinking_message(response_message_object, "Произошла ошибка при обработке. Пожалуйста, попробуйте снова или сообщите администратору.")
        finally:
            # Важно: Завершаем сообщение-индикатор в любом случае
            if response_message_object:
                await self.interaction_response_manager.complete_thinking_message(response_message_object)
                self.logger.info(f"Сообщение-индикатор ID {response_message_object.id} завершено оркестратором.")