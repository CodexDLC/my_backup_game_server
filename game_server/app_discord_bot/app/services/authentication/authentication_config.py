# Импорты с правильными именами
from .logic_handlers.login_start import LoginStartHandler
from .presentation_handlers.initial_lobby_setup import InitialLobbySetupPresenter

# Карта логики
AUTH_LOGIC_HANDLER_MAP = {
    "start_login": LoginStartHandler,
}

# Карта представления
AUTH_PRESENTATION_HANDLER_MAP = {
    "initial_lobby_setup": InitialLobbySetupPresenter,
}