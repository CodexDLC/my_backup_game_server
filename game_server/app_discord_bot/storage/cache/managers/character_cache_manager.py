# character_cache_manager.py

import inject
import logging
import json
from typing import Optional, Dict, Any

from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.storage.cache.interfaces.character_cache_manager_interface import ICharacterCacheManager

class CharacterCacheManagerImpl(ICharacterCacheManager):
    """
    Реализация менеджера кэша для сессий персонажей.
    Адаптировано под новую, гибридную структуру хранения сессии в Redis.
    """
    @inject.autoparams()
    def __init__(self, redis_client: DiscordRedisClient, logger: logging.Logger):
        self._redis = redis_client
        self._logger = logger
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def cache_login_session(
        self,
        character_data: Dict[str, Any],
        user_id: int,
        guild_id: int,
        account_id: int
    ) -> None:
        """
        Кэширует сессию, раскладывая полный документ персонажа
        на логические блоки в хэш Redis.
        """
        character_id = character_data.get("_id")
        if not character_id:
            raise ValueError("Отсутствует '_id' в данных персонажа для кэширования.")

        # --- 1. Кэшируем детальные данные персонажа (НОВАЯ ЛОГИКА) ---
        char_session_key = RedisKeys.CHARACTER_SESSION_HASH.format(guild_id=guild_id, character_id=character_id)
        
        # Определяем логические блоки для "нарезки"
        logical_blocks = [
            "core", "location", "vitals", "stats", "derived_stats",
            "abilities", "items", "skills", "quests", "reputation", "session"
        ]

        # Собираем данные для хэша, где каждое поле - это JSON-строка
        redis_hash_data = {}
        for block_name in logical_blocks:
            if block_name in character_data:
                block_data_dict = character_data[block_name]
                redis_hash_data[block_name] = json.dumps(block_data_dict)
        
        if redis_hash_data:
            await self._redis.hmset(char_session_key, redis_hash_data)
            self._logger.info(f"Структурированный кэш персонажа {character_id} сохранен в {char_session_key}.")

        # --- 2. Устанавливаем активную сессию (логика не изменилась) ---
        active_session_key = RedisKeys.ACTIVE_USER_SESSION_HASH.format(discord_id=user_id)
        active_session_data = {
            RedisKeys.FIELD_SESSION_ACCOUNT_ID: str(account_id),
            RedisKeys.FIELD_SESSION_CHARACTER_ID: str(character_id)
        }
        await self._redis.hmset(active_session_key, active_session_data)
        self._logger.info(f"Установлена активная сессия для {user_id}: персонаж {character_id}, аккаунт {account_id}.")

        # --- 3. Добавляем в глобальный список онлайн (логика не изменилась) ---
        await self._redis.sadd(RedisKeys.GLOBAL_ONLINE_PLAYERS_SET, str(character_id))
        self._logger.info(f"Персонаж {character_id} добавлен в глобальный список онлайн.")

    async def get_active_character_id(self, user_id: int) -> Optional[int]:
        # Этот метод не требует изменений
        active_session_key = RedisKeys.ACTIVE_USER_SESSION_HASH.format(discord_id=user_id)
        char_id_str = await self._redis.hget(active_session_key, RedisKeys.FIELD_SESSION_CHARACTER_ID)
        return int(char_id_str) if char_id_str else None

    async def get_character_session(self, character_id: int, guild_id: int) -> Optional[Dict[str, Any]]:
        """
        Читает структурированный хэш из Redis и собирает из него
        полный документ персонажа.
        """
        char_session_key = RedisKeys.CHARACTER_SESSION_HASH.format(guild_id=guild_id, character_id=character_id)
        
        # Получаем все поля хэша (core, vitals, и т.д.)
        structured_hash = await self._redis.hgetall(char_session_key)
        if not structured_hash:
            return None
        
        # Собираем полный документ, декодируя каждое поле из JSON
        reassembled_document = {}
        for block_name, json_string in structured_hash.items():
            try:
                reassembled_document[block_name] = json.loads(json_string)
            except (json.JSONDecodeError, TypeError):
                # На случай, если какое-то поле не является JSON
                reassembled_document[block_name] = json_string
        
        # Добавляем ID обратно в документ для полноты
        reassembled_document["_id"] = character_id
        # account_id можно будет получить из active_session, если потребуется

        return reassembled_document

    async def clear_login_session(self, user_id: int, guild_id: int) -> None:
        # Этот метод не требует изменений
        character_id = await self.get_active_character_id(user_id)
        if not character_id:
            self._logger.warning(f"Попытка выхода для {user_id}, но активная сессия не найдена.")
            return

        await self._redis.srem(RedisKeys.GLOBAL_ONLINE_PLAYERS_SET, str(character_id))
        await self._redis.delete(RedisKeys.ACTIVE_USER_SESSION_HASH.format(discord_id=user_id))
        await self._redis.delete(RedisKeys.CHARACTER_SESSION_HASH.format(guild_id=guild_id, character_id=character_id))
        self._logger.info(f"Сессия для персонажа {character_id} (пользователь {user_id}) была полностью очищена.")