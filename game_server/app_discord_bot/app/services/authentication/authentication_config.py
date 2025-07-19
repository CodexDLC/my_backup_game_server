# /services/authentication/authentication_config.py

# --- СТАРЫЕ ИМПОРТЫ ДЛЯ ЛОГИНА (ОСТАВЛЯЕМ) ---

from game_server.app_discord_bot.app.services.authentication.logic_handlers.Faq_handler import ShowFaqHandler
from game_server.app_discord_bot.app.services.authentication.logic_handlers.hub_registration_handler import HubRegistrationFlowHandler
from .logic_handlers.login_start import LoginStartHandler
from .presentation_handlers.initial_lobby_setup import InitialLobbySetupPresenter

# --- НОВЫЕ ИМПОРТЫ ДЛЯ РЕГИСТРАЦИИ (ДОБАВЛЯЕМ) ---

#
# --- Карта логики ---
#
AUTH_LOGIC_HANDLER_MAP = {
    # Короткие имена команд как ключи
    "start_registration": HubRegistrationFlowHandler,
    "start_login": LoginStartHandler,
    "show_faq": ShowFaqHandler,
}
#
# --- Карта представления ---
#
AUTH_PRESENTATION_HANDLER_MAP = {
    # --- ВАША РАБОЧАЯ НАСТРОЙКА ДЛЯ ЛОББИ (ОНА НА МЕСТЕ) ---
    "initial_lobby_setup": InitialLobbySetupPresenter,

}