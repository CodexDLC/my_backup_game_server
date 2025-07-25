# game_server\app_discord_bot\config\router_config.py

# Импортируем существующие оркестраторы


# Карта, которая связывает имя сервиса (из custom_id) с классом его оркестратора
from game_server.app_discord_bot.app.services.game_modules.authentication.authentication_orchestrator import AuthenticationOrchestrator
from game_server.app_discord_bot.app.services.game_modules.character.character_orchestrator import CharacterOrchestrator
from game_server.app_discord_bot.app.services.game_modules.chashe_updata.chashe_updata_orchestrator import CacheUpdateOrchestrator
from game_server.app_discord_bot.app.services.game_modules.inspection.inspection_orchestrator import InspectionOrchestrator
from game_server.app_discord_bot.app.services.game_modules.lobby.lobby_orchestrator import LobbyOrchestrator
from game_server.app_discord_bot.app.services.game_modules.navigation.navigation_orchestrator import NavigationOrchestrator
from game_server.app_discord_bot.app.services.game_modules.system.system_orchestrator import SystemOrchestrator


SERVICE_MAP = {
    "authentication": AuthenticationOrchestrator,
    "lobby": LobbyOrchestrator,
    
    # --- НОВОЕ: Добавляем сюда новые сервисы ---
    "character": CharacterOrchestrator,
    "navigation": NavigationOrchestrator,
    "system": SystemOrchestrator,
    "inspection": InspectionOrchestrator,
    "cache": CacheUpdateOrchestrator
}