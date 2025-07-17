# game_server/app_discord_bot/app/services/system/system_config.py

# --- Импорты Логических Обработчиков ---
# from .logic_handlers.show_settings import ShowSettingsHandler
from .logic_handlers.logout_handler import LogoutHandler

# --- Импорты Презентеров ---
# from .presentation_handlers.display_settings import DisplaySettingsPresenter

LOGIC_HANDLER_MAP = {
    # "show_settings": ShowSettingsHandler,
    "logout": LogoutHandler,
}

PRESENTATION_HANDLER_MAP = {
    # "settings_view": DisplaySettingsPresenter,
}