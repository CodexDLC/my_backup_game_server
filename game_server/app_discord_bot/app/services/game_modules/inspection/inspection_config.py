# game_server/app_discord_bot/app/services/game_modules/inspection/inspection_config.py

# --- Импорты Логических Обработчиков ---

from game_server.app_discord_bot.app.services.game_modules.inspection.logic_handlers.look_around import LookAroundOverviewHandler
from .logic_handlers.list_category import ListCategoryHandler
from .logic_handlers.view_entity import ViewEntityHandler # НОВЫЙ ИМПОРТ

# --- Импорты Презентеров ---
from .presentation_handlers.display_inspection import DisplayInspectionListPresenter
from .presentation_handlers.display_overview import DisplayOverviewPresenter
from .presentation_handlers.display_entity_details import DisplayEntityDetailsPresenter # НОВЫЙ ИМПОРТ


# Карта для связи строковых команд с классами-обработчиками логики
LOGIC_HANDLER_MAP = {
    # Кнопка "Осмотреться" вызывает команду "inspection:look_around"
    "look_around": LookAroundOverviewHandler,
    # Кнопка категории вызывает "inspection:list_category:players"
    "list_category": ListCategoryHandler,
    # Кнопка "Осмотреть" на 2-м уровне вызывает "inspection:action:inspect:<entity_id>"
    # Команда "action" будет обрабатывать все действия с сущностями.
    "action": ViewEntityHandler, # НОВЫЙ ОБРАБОТЧИК ДЛЯ ДЕЙСТВИЙ
}

# Карта для связи типов DTO с классами-презентерами
PRESENTATION_HANDLER_MAP = {
    "DISPLAY_OVERVIEW": DisplayOverviewPresenter,
    "DISPLAY_INSPECTION_LIST": DisplayInspectionListPresenter,
    "DISPLAY_ENTITY_DETAILS": DisplayEntityDetailsPresenter, # НОВЫЙ ПРЕЗЕНТЕР ДЛЯ ДЕТАЛЕЙ СУЩНОСТИ
}

