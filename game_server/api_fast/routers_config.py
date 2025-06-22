# api_fast/routers_config.py

# ===================================================================
# 1. ИМПОРТИРУЕМ ГОТОВЫЕ СПИСКИ ИЗ КАЖДОГО ДОМЕНА
# ===================================================================

from .rest_routers.system.system_config import system_routers
from .rest_routers.discord.discord_config import discord_routers
from .rest_routers.character.character_config import character_routers

# --- ИСПРАВЛЕНИЕ: Добавляем недостающие импорты ---
from .rest_routers.utils_route.utils_config import utils_routers  # <-- ДОБАВЛЕНО
from .rest_routers.health_config import health_routers            # <-- ДОБАВЛЕНО
from .rest_routers.gateway.gateway_config import gateway_routers  # <-- ДОБАВЛЕНО
# ... и так далее для всех остальных (test, random_pool и т.д.)
# ----------------------------------------------------


# ===================================================================
# 2. СОБИРАЕМ ВСЕ КОНФИГУРАЦИИ В ОДИН ОБЩИЙ СПИСОК
# ===================================================================

ROUTERS_CONFIG = (
    system_routers +
    discord_routers +
    character_routers +
    utils_routers +
    health_routers +
    gateway_routers
)