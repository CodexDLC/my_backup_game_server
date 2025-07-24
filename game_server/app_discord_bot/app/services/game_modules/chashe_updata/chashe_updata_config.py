# game_server/app_discord_bot/app/services/game_modules/cache_update/cache_update_config.py

from typing import Dict, Any

# Импортируем обработчик, который мы создадим на следующем шаге
from .logic_handlers.update_location_cache_handler import UpdateLocationCacheHandler

# Карта: "имя_команды" -> класс_обработчика
CACHE_UPDATE_HANDLER_MAP: Dict[str, Any] = {
    "update_location": UpdateLocationCacheHandler,
}