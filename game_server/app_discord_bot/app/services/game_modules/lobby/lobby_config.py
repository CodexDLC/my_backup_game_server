# game_server/app_discord_bot/app/services/authentication/lobby/lobby_config.py

# --- Импорты Логических Обработчиков ---

from game_server.app_discord_bot.app.services.game_modules.lobby.logic_handlers.create_character_handler import CreateCharacterHandler
from .logic_handlers.show_characters import ShowCharactersHandler
from .logic_handlers.show_deck import ShowDeckHandler
from .logic_handlers.logout_lobby import LogoutHandlerlobby
# 🔥 НОВЫЕ ИМПОРТЫ
from .logic_handlers.start_adventure import StartAdventureHandler
from .logic_handlers.select_character import SelectCharacterHandler


# --- Импорты Презентеров ---
from .presentation_handlers.display_character_selection import DisplayCharacterSelectionPresenter
from .presentation_handlers.display_deck_stub import DisplayDeckStubPresenter
from .presentation_handlers.display_game_interface_handler import DisplayGameInterfacePresenter


# --- Карта логики для сервиса Лобби ---
LOGIC_HANDLER_MAP = {
    "show_characters": ShowCharactersHandler,
    "show_deck": ShowDeckHandler,
    "logout_lobby": LogoutHandlerlobby,
    "start_adventure": StartAdventureHandler,
    "enter_world": SelectCharacterHandler, # <-- ОБЪЕКТ SelectCharacterHandler теперь доступен
    "create_character": CreateCharacterHandler, # <-- ВАША НОВАЯ КОМАНДА
}

# --- Карта представления для сервиса Лобби ---
PRESENTATION_HANDLER_MAP = {
    "character_selection_view": DisplayCharacterSelectionPresenter,
    "deck_view_stub": DisplayDeckStubPresenter,
    "display_initial_location": DisplayGameInterfacePresenter,
}


