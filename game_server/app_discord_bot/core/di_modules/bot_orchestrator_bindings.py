# game_server/app_discord_bot/core/di_modules/bot_orchestrator_bindings.py

import inject

# Существующие оркестраторы
from game_server.app_discord_bot.app.services.authentication.authentication_orchestrator import AuthenticationOrchestrator
from game_server.app_discord_bot.app.services.authentication.lobby.lobby_orchestrator import LobbyOrchestrator

# --- НОВОЕ: Импорты для новых сервисов ---
from game_server.app_discord_bot.app.services.character.character_orchestrator import CharacterOrchestrator
from game_server.app_discord_bot.app.services.navigation.navigation_orchestrator import NavigationOrchestrator
from game_server.app_discord_bot.app.services.system.system_orchestrator import SystemOrchestrator


def configure_bot_orchestrators(binder):
    """
    Конфигурирует привязки для всех оркестраторов сервисов бота.
    """
    # Старые привязки
    binder.bind("lobby", LobbyOrchestrator) # Изменен на строковый ключ для единообразия
    binder.bind("auth", AuthenticationOrchestrator)  # Изменен на строковый ключ

    # --- НОВОЕ: Привязки для новых оркестраторов ---
    binder.bind("character", CharacterOrchestrator)
    binder.bind("navigation", NavigationOrchestrator)
    binder.bind("system", SystemOrchestrator)