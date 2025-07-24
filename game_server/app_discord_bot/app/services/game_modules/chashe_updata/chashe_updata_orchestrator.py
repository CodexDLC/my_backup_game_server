# game_server/app_discord_bot/app/services/game_modules/cache_update/cache_update_orchestrator.py

import inject
import logging
from typing import Dict, Any

from game_server.app_discord_bot.app.services.game_modules.chashe_updata.chashe_updata_config import CACHE_UPDATE_HANDLER_MAP



class CacheUpdateOrchestrator:
    """
    Оркестратор для фоновых задач по обновлению кэша дискорд-бота.
    """
    @inject.autoparams()
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.handlers: Dict[str, Any] = {
            command_name: inject.instance(handler_class)
            for command_name, handler_class in CACHE_UPDATE_HANDLER_MAP.items()
        }
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован с {len(self.handlers)} обработчиками.")

    async def process(self, command_str: str, interaction, response_message_object=None):
        """
        Основной метод-диспетчер. Разбирает команду, извлекает данные
        и вызывает нужный обработчик с чистыми данными.
        """
        try:
            # --- ✅ НОВАЯ ЛОГИКА РАЗБОРА КОМАНДЫ ---
            parts = command_str.split(':')
            command_name = parts[0]  # 'update_location'
            
            # Находим обработчик по имени команды
            handler = self.handlers.get(command_name)
            if not handler:
                self.logger.warning(f"Для команды обновления кэша '{command_name}' не найден обработчик.")
                return

            # Извлекаем параметры из оставшихся частей
            # В данном случае, location_id - это вторая часть
            location_id = parts[1] if len(parts) > 1 else None
            
            # Собираем чистые данные для передачи в обработчик
            data_to_execute = {
                "location_id": location_id
            }
            # --- КОНЕЦ НОВОЙ ЛОГИКИ ---

            self.logger.info(f"Передаю команду '{command_name}' в обработчик {handler.__class__.__name__}.")
            # Передаем в execute только чистые, нужные данные
            await handler.execute(data_to_execute)

        except Exception as e:
            self.logger.critical(f"Критическая ошибка в CacheUpdateOrchestrator: {e}", exc_info=True)