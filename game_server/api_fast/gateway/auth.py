# api_fast/gateway/auth.py
import os
import hmac

from game_server.config.settings_core import GATEWAY_BOT_SECRET # Используется для безопасного сравнения строк

# Этот секрет должен быть установлен в переменных окружения
# и быть ОДИНАКОВЫМ для шлюза и для бота.
# Например, в .env файле: GATEWAY_BOT_SECRET="d4e8f10b..."


if not GATEWAY_BOT_SECRET:
    # Приложение не запустится, если секрет не задан. Это хорошо.
    raise ValueError("Переменная окружения GATEWAY_BOT_SECRET не установлена!")

async def validate_bot_token(token: str) -> bool:
    """
    Безопасно сравнивает предоставленный токен с секретом из переменных окружения.
    Использует hmac.compare_digest для защиты от атак по времени (Timing Attacks).
    """
    if not token:
        return False

    return hmac.compare_digest(token, GATEWAY_BOT_SECRET)