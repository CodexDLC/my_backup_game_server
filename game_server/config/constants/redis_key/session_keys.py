# game_server/config/constants/redis/session_keys.py

# Шаблон для ключа сессии.
# Пример: global:session:some-secure-token
KEY_SESSION = "global:session:{token}"

# Время жизни сессии в секундах
SESSION_TTL_SECONDS = 86400  # 24 часа