# game_server\Logic\ApplicationLogic\auth_service\utils\account_helpers.py
import secrets
import re
from typing import List
from datetime import datetime, timedelta, timezone

async def generate_auth_token() -> str:
    """Генерирует криптографически стойкий шестнадцатеричный токен для аутентификации."""
    return secrets.token_hex(32)

async def generate_next_guest_username(existing_guest_usernames: List[str]) -> str:
    """
    Генерирует следующий уникальный номер для имени пользователя в формате 'ГостьXXXXX'.
    Ищет максимальный числовой суффикс среди существующих "Гость" имен.
    :param existing_guest_usernames: Список всех существующих имен пользователей, начинающихся с "Гость".
    :return: Сгенерированное уникальное имя пользователя.
    """
    max_suffix = 0
    guest_pattern = re.compile(r"^Гость(\d+)$")

    for username in existing_guest_usernames:
        match = guest_pattern.match(username)
        if match:
            try:
                suffix = int(match.group(1))
                max_suffix = max(max_suffix, suffix)
            except ValueError:
                continue # Пропускаем имена, которые не соответствуют ожидаемому шаблону
    
    return f"Гость{max_suffix + 1:05d}" # Форматируем с ведущими нулями, например, Гость00001

def get_linking_token_expiry_time(minutes: int = 30) -> datetime:
    """Возвращает время истечения срока действия токена привязки."""
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)