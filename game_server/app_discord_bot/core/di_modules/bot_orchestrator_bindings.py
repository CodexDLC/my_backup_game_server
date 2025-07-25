# game_server/app_discord_bot/core/di_modules/bot_orchestrator_bindings.py

import inject

from game_server.app_discord_bot.app.services.game_modules.authentication.authentication_orchestrator import AuthenticationOrchestrator
from game_server.app_discord_bot.app.services.game_modules.character.character_orchestrator import CharacterOrchestrator

from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_orchestrator import InspectionOrchestrator
from game_server.app_discord_bot.app.services.game_modules.lobby.lobby_orchestrator import LobbyOrchestrator
from game_server.app_discord_bot.app.services.game_modules.navigation.navigation_orchestrator import NavigationOrchestrator
from game_server.app_discord_bot.app.services.game_modules.system.system_orchestrator import SystemOrchestrator
# ✅ НОВЫЙ ИМПОРТ
from game_server.app_discord_bot.app.services.game_modules.chashe_updata.chashe_updata_orchestrator import CacheUpdateOrchestrator


def configure_bot_orchestrators(binder):
    """
    Конфигурирует привязки для всех оркестраторов сервисов бота.
    """
    binder.bind("lobby", LobbyOrchestrator)
    binder.bind("auth", AuthenticationOrchestrator)
    binder.bind("character", CharacterOrchestrator)
    binder.bind("navigation", NavigationOrchestrator)
    binder.bind("system", SystemOrchestrator)
    binder.bind("inspection", InspectionOrchestrator)
    
    # ✅ НОВАЯ ПРИВЯЗКА для нашего сервиса обновления кэша
    binder.bind("cache", CacheUpdateOrchestrator)