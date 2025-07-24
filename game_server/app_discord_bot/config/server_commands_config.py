# game_server\app_discord_bot\config\server_commands_config.py

from typing import Dict, Any

from game_server.app_discord_bot.app.services.game_modules.chashe_updata.logic_handlers.location_updated_handler import LocationUpdatedHandler


def get_event_handlers(
    # Сюда будут автоматически внедрены экземпляры обработчиков через inject
    location_updated_handler: LocationUpdatedHandler,
    # chat_message_handler: ChatMessageHandler, # Пример для будущего
) -> Dict[str, Any]:
    """
    Возвращает словарь, сопоставляющий имена событий с их обработчиками.
    """
    return {
        "event.location.updated": location_updated_handler,

    }