# game_server/app_discord_bot/transport/websocket_client/handlers/event_handlers.py

import inject
import logging
from discord.ext import commands
from typing import Dict, Any

# ✅ Импортируем нашу новую карту
from ....config.event_to_custom_id_config import EVENT_TO_CUSTOM_ID_MAP


class WSEventHandlers:
    """
    Получает события от бэкенда, преобразует их в custom_id с помощью карты
    и имитирует внутреннее событие 'нажатия кнопки' для InteractionRouter.
    """
    @inject.autoparams()
    def __init__(self, bot: commands.Bot, logger: logging.Logger):
        self.bot = bot
        self.logger = logger
        self.handlers_map = EVENT_TO_CUSTOM_ID_MAP # ✅ Используем новую карту
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован с {len(self.handlers_map)} правилами.")

    async def handle_event(self, event_payload_data: dict):
        """
        Основной метод. Распаковывает событие, находит правило в карте и генерирует
        внутреннее событие для роутера.
        """
        try:
            event_name = event_payload_data.get("type")
            if not event_name:
                self.logger.warning("Получено событие без поля 'type'.")
                return

            # Распаковываем до чистых данных
            clean_data = event_payload_data.get('payload', {})
            while isinstance(clean_data, dict) and 'payload' in clean_data:
                clean_data = clean_data['payload']

            # --- ✅ НОВАЯ ЛОГИКА С ИСПОЛЬЗОВАНИЕМ КАРТЫ ---
            
            # Ищем правило для этого события в нашей карте
            rule = self.handlers_map.get(event_name)

            if rule:
                custom_id_format = rule.get("custom_id_format")
                if not custom_id_format:
                    self.logger.error(f"Для события '{event_name}' в конфиге не указан 'custom_id_format'.")
                    return

                # Формируем custom_id, подставляя в шаблон значения из данных
                try:
                    custom_id = custom_id_format.format(**clean_data)
                    self.logger.info(f"Событие '{event_name}' преобразовано в custom_id '{custom_id}'. Генерирую внутреннее событие 'on_backend_event'.")
                    
                    # Генерируем кастомное событие, которое поймает другой слушатель
                    self.bot.dispatch("backend_event", custom_id, clean_data)
                except KeyError as e:
                    self.logger.error(f"Не удалось создать custom_id для '{event_name}': в данных не хватает ключа {e}.")

            else:
                self.logger.warning(f"Для события '{event_name}' не найдено правило в EVENT_TO_CUSTOM_ID_MAP.")

        except Exception as e:
            self.logger.critical(f"Ошибка в WSEventHandlers: {e}", exc_info=True)