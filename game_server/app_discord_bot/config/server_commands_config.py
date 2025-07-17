# game_server/app_discord_bot/app/configs/server_commands_config.py

from typing import Callable, Dict, Any # Добавил Any для ленивого импорта
# from game_server.app_discord_bot.transport.websocket_client.handlers.system_command_handlers import WSSystemCommandHandlers # <-- Эту строку мы удаляли для решения циклического импорта

def get_system_command_handlers(handler_instance: Any) -> Dict[str, Callable]: # <-- Это функция
    """
    Возвращает маппинг имен команд сервера на методы-обработчики.
    """
    # Этот импорт был добавлен ВНУТРИ функции для решения циклического импорта
    from game_server.app_discord_bot.transport.websocket_client.handlers.system_command_handlers import WSSystemCommandHandlers

    if not isinstance(handler_instance, WSSystemCommandHandlers):
        raise TypeError("handler_instance must be an instance of WSSystemCommandHandlers")

    return {
        "UPDATE_CONFIG": handler_instance.handle_update_config,
        "SHUTDOWN": handler_instance.handle_shutdown_command,
        "RELOAD_MODULE": handler_instance.handle_reload_module,
        "SYNC_TIME": handler_instance.handle_sync_time,
        "NOTIFY_ADMINS": handler_instance.handle_notify_admins,
        # Добавьте другие команды здесь
    }