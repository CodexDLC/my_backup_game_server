# game_server\app_discord_bot\config\router_config.py

# Импортируем существующие оркестраторы
from game_server.app_discord_bot.app.services.authentication.authentication_orchestrator import AuthenticationOrchestrator
from game_server.app_discord_bot.app.services.authentication.lobby.lobby_orchestrator import LobbyOrchestrator

# --- НОВОЕ: Импортируем оркестраторы для новых сервисов ---
from game_server.app_discord_bot.app.services.character.character_orchestrator import CharacterOrchestrator
from game_server.app_discord_bot.app.services.navigation.navigation_orchestrator import NavigationOrchestrator
from game_server.app_discord_bot.app.services.system.system_orchestrator import SystemOrchestrator


# Карта, которая связывает имя сервиса (из custom_id) с классом его оркестратора
SERVICE_MAP = {
    "authentication": AuthenticationOrchestrator,
    "lobby": LobbyOrchestrator,
    
    # --- НОВОЕ: Добавляем сюда новые сервисы ---
    "character": CharacterOrchestrator,
    "navigation": NavigationOrchestrator,
    "system": SystemOrchestrator,
}