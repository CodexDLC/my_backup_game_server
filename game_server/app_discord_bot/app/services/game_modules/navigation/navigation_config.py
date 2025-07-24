# game_server/app_discord_bot/app/services/navigation/navigation_config.py

# --- Импорты Логических Обработчиков ---
from .logic_handlers.show_navigation import ShowNavigationHandler
from .logic_handlers.move_to_location import MoveToLocationHandler # <--- ДОБАВЛЕНО

# --- Импорты Презентеров ---
from .presentation_handlers.display_navigation import DisplayNavigationPresenter

LOGIC_HANDLER_MAP = {
    "show_navigation": ShowNavigationHandler,
    "move_to": MoveToLocationHandler, # <--- ДОБАВЛЕНО
    "back": MoveToLocationHandler,
}

PRESENTATION_HANDLER_MAP = {
    # 'LOCATION_DISPLAY' - это значение поля 'type' из NavigationDisplayDataDTO
    "LOCATION_DISPLAY": DisplayNavigationPresenter,
}