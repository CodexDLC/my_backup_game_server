# game_server/app_discord_bot/transport/websocket_client/handlers/system_command_handlers.py (уже существующий файл)

import logging
from typing import Dict, Any
from discord.ext import commands # Если хендлер - это ког Discord.py

# Импортируем контракты
from game_server.app_discord_bot.config.server_commands_config import get_system_command_handlers
from game_server.contracts.shared_models.websocket_base_models import WebSocketSystemCommandToClientPayload


# Импортируем наш новый конфиг



class WSSystemCommandHandlers: # Или это может быть commands.Cog, если команды Discord
    def __init__(self, logger: logging.Logger, bot: commands.Bot):
        self.logger = logger
        self.bot = bot
        # Инициализируем маппинг команд после того, как все методы будут доступны
        self.command_map = get_system_command_handlers(self)
        self.logger.info("WSSystemCommandHandlers инициализирован.")

    async def handle_command(self, payload: Dict[str, Any]):
        """
        Основной метод для обработки входящих системных команд.
        """
        try:
            # Валидация payload с помощью Pydantic модели
            command_dto = WebSocketSystemCommandToClientPayload(**payload) #
            command_name = command_dto.command_name #
            command_data = command_dto.command_data #

            self.logger.info(f"Получена системная команда от сервера: '{command_name}'")
            self.logger.debug(f"Данные команды: {command_data}")

            # Используем маппинг для вызова нужного метода
            handler_method = self.command_map.get(command_name)
            if handler_method:
                await handler_method(command_data) # Передаем данные команды в обработчик
                self.logger.info(f"Системная команда '{command_name}' успешно обработана.")
            else:
                self.logger.warning(f"Получена неизвестная системная команда: '{command_name}'. Данные: {command_data}")

        except Exception as e:
            self.logger.error(f"Ошибка обработки системной команды: {e}", exc_info=True)

    # --- Примеры методов-обработчиков для различных команд ---

    async def handle_update_config(self, data: Dict[str, Any]):
        self.logger.info(f"Выполняю команду: Обновить конфигурацию. Данные: {data}")
        # Здесь будет логика обновления конфига бота
        pass

    async def handle_shutdown_command(self, data: Dict[str, Any]):
        self.logger.info(f"Выполняю команду: Отключение бота. Причина: {data.get('reason', 'Не указана')}")
        # Здесь будет логика корректного отключения бота
        await self.bot.close() # Например
        pass

    async def handle_reload_module(self, data: Dict[str, Any]):
        module_name = data.get("module_name")
        self.logger.info(f"Выполняю команду: Перезагрузить модуль: {module_name}")
        # Здесь будет логика перезагрузки модуля (аналогично CommandsManager.reload_cogs)
        pass
    
    async def handle_sync_time(self, data: Dict[str, Any]):
        self.logger.info(f"Выполняю команду: Синхронизация времени. Данные: {data}")
        # Логика синхронизации времени
        pass

    async def handle_notify_admins(self, data: Dict[str, Any]):
        message_to_send = data.get("message", "Сообщение для администраторов")
        self.logger.info(f"Выполняю команду: Уведомить администраторов. Сообщение: {message_to_send}")
        # Логика отправки сообщения в Discord администраторам
        pass