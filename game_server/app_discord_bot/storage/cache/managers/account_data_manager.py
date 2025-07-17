# game_server/app_discord_bot/storage/cache/managers/account_data_manager.py
import json
import logging
from typing import Dict, Any, Optional, List, Set # Добавлены List, Set для общих методов Redis
import inject

from redis.asyncio import Redis # Убедитесь, что Redis импортирован
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.storage.cache.interfaces.account_data_manager_interface import IAccountDataManager

class AccountDataManager(IAccountDataManager):
    """
    Менеджер кэша для хранения постоянных данных игровых аккаунтов.
    Использует PLAYER_ACCOUNT_DATA_HASH для данных аккаунта (ключ по discord_user_id).
    Использует GLOBAL_BACKEND_DISCORD_TO_ACCOUNT_MAPPING для глобального индекса discord_user_id -> account_id (как Hash).
    
    """
    @inject.autoparams()
    def __init__(self, redis_client: DiscordRedisClient, logger: logging.Logger):
        self.redis_client = redis_client
        self.logger = logger
        # Шаблон для основных данных аккаунта (по Discord ID)
        self.PLAYER_DATA_KEY_PATTERN = RedisKeys.PLAYER_ACCOUNT_DATA_HASH
        # Шаблон для глобального индекса Discord ID -> Account ID (Hash)
        self.GLOBAL_DISCORD_TO_ACCOUNT_KEY_PATTERN = RedisKeys.GLOBAL_BACKEND_DISCORD_TO_ACCOUNT_MAPPING
        # Шаблон для индекса Account ID -> Discord ID (String)       
        self.logger.info("✨ AccountDataManager инициализирован.")

    async def _get_player_data_key(self, shard_id: int, discord_user_id: int) -> str:
        """
        Формирует ключ Redis для хеша основных данных аккаунта игрока, используя discord_user_id.
        """
        return self.PLAYER_DATA_KEY_PATTERN.format(shard_id=shard_id, discord_user_id=discord_user_id)

    async def _get_global_discord_to_account_key(self, discord_user_id: int) -> str:
        """
        Формирует глобальный ключ Redis для индекса Discord ID -> Account ID.
        """
        return self.GLOBAL_DISCORD_TO_ACCOUNT_KEY_PATTERN.format(discord_user_id=discord_user_id)

    async def save_account_field(self, shard_id: int, discord_user_id: int, field_name: str, data: Dict[str, Any]) -> None:
        """
        Сохраняет или обновляет одно поле (например, general_info, linked_discord_meta)
        в хеше данных аккаунта, идентифицируемом по discord_user_id.
        Данные будут сериализованы в JSON.
        """
        key = await self._get_player_data_key(shard_id, discord_user_id)
        try:
            value = json.dumps(data)
            await self.redis_client.hset(key, field_name, value)
            self.logger.debug(f"Поле '{field_name}' для Discord пользователя {discord_user_id} на шарде {shard_id} сохранено в Redis.")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении поля '{field_name}' для Discord пользователя {discord_user_id} на шарде {shard_id}: {e}", exc_info=True)

    async def get_account_field(self, shard_id: int, discord_user_id: int, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Извлекает одно поле из хеша данных аккаунта, идентифицируемого по discord_user_id,
        и десериализует его из JSON.
        """
        key = await self._get_player_data_key(shard_id, discord_user_id)
        try:
            value = await self.redis_client.hget(key, field_name)
            if value:
                try:
                    return json.loads(value)
                except json.JSONDecodeError as e:
                    self.logger.error(f"Ошибка декодирования JSON для поля '{field_name}' Discord пользователя {discord_user_id} на шарде {shard_id}: {e}", exc_info=True)
                    return None
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении поля '{field_name}' для Discord пользователя {discord_user_id} на шарде {shard_id}: {e}", exc_info=True)
            return None

    async def get_all_account_data(self, shard_id: int, discord_user_id: int) -> Optional[Dict[str, Any]]:
        """
        Извлекает все данные для конкретного аккаунта (все поля хеша),
        идентифицируемого по discord_user_id.
        """
        key = await self._get_player_data_key(shard_id, discord_user_id)
        try:
            all_data = await self.redis_client.hgetall(key)
            if not all_data:
                self.logger.warning(f"Данные для Discord пользователя {discord_user_id} на шарде {shard_id} (ключ {key}) не найдены в кэше.")
                return None
            
            parsed_data = {}
            for field, value in all_data.items():
                try:
                    parsed_data[field] = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    parsed_data[field] = value
            return parsed_data
        except Exception as e:
            self.logger.error(f"Ошибка при получении всех данных для Discord пользователя {discord_user_id} на шарде {shard_id}: {e}", exc_info=True)
            return None

    async def delete_account_data(self, shard_id: int, discord_user_id: int) -> None:
        """
        Полностью удаляет хеш данных аккаунта из Redis, идентифицируемый по discord_user_id.
        """
        key = await self._get_player_data_key(shard_id, discord_user_id)
        try:
            await self.redis_client.delete(key)
            self.logger.info(f"Данные для Discord пользователя {discord_user_id} на шарде {shard_id} удалены из Redis.")
        except Exception as e:
            self.logger.error(f"Ошибка при удалении данных для Discord пользователя {discord_user_id} на шарде {shard_id}: {e}", exc_info=True)

    async def get_account_id_by_discord_id(self, discord_user_id: int) -> Optional[int]:
        """
        Извлекает account_id из глобального Redis Hash (поле 'account_id') по Discord User ID.
        """
        key = await self._get_global_discord_to_account_key(discord_user_id)
        try:
            account_id_str = await self.redis_client.hget(key, "account_id")
            if account_id_str:
                return int(account_id_str)
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении account_id для Discord пользователя {discord_user_id} из глобального индекса: {e}", exc_info=True)
            return None

    async def set_discord_account_mapping(self, discord_user_id: int, account_id: int) -> None:
        """
        Сохраняет соответствие Discord User ID к account_id в глобальном Redis Hash (поле 'account_id').
        """
        key = await self._get_global_discord_to_account_key(discord_user_id)
        try:
            await self.redis_client.hset(key, "account_id", str(account_id))
            self.logger.debug(f"Сохранено глобальное сопоставление Discord ID {discord_user_id} -> Account ID {account_id}.")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении глобального сопоставления Discord ID {discord_user_id} -> Account ID {account_id}: {e}", exc_info=True)

    # НОВОЕ: Реализация get_temp_field
    async def get_temp_field(self, user_id: int, field_name: str) -> Optional[str]:
        """
        Получает временное поле, связанное с пользователем, из Redis.
        Используется для временных данных, таких как выбранный персонаж.
        """
        key = RedisKeys.TEMP_USER_DATA_KEY.format(user_id=user_id, field_name=field_name)
        value = await self.redis_client.get(key)
        if value:
            self.logger.debug(f"DEBUG REDIS: Получено временное поле '{field_name}' для пользователя {user_id}.")
            return value.decode('utf-8')
        self.logger.debug(f"DEBUG REDIS: Временное поле '{field_name}' для пользователя {user_id} не найдено.")
        return None

    # НОВОЕ: Реализация set_temp_field
    async def set_temp_field(self, user_id: int, field_name: str, value: str, ttl: Optional[int] = None) -> None:
        """
        Устанавливает временное поле для пользователя в Redis.
        ttl (время жизни) в секундах.
        """
        key = RedisKeys.TEMP_USER_DATA_KEY.format(user_id=user_id, field_name=field_name)
        if ttl:
            await self.redis_client.setex(key, ttl, value)
            self.logger.debug(f"DEBUG REDIS: Установлено временное поле '{field_name}' для пользователя {user_id} с TTL {ttl}s.")
        else:
            await self.redis_client.set(key, value)
            self.logger.debug(f"DEBUG REDIS: Установлено временное поле '{field_name}' для пользователя {user_id} (без TTL).")

    # НОВОЕ: Общие методы для работы с хэшами
    async def set_hash_fields(self, key: str, data: Dict[str, Any]) -> None:
        """
        Устанавливает несколько полей в хеше Redis, делегируя это клиенту.
        """
        try:
            # Преобразуем все значения в строки для Redis
            string_data = {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) for k, v in data.items()}
            
            # 👇 ТЕПЕРЬ ВСЯ СЛОЖНОСТЬ СКРЫТА В КЛИЕНТЕ
            await self.redis_client.hmset(key, string_data)
            
            self.logger.debug(f"Установлены поля в хеше Redis для ключа '{key}'.")
        except Exception as e:
            self.logger.error(f"Ошибка при установке полей в хеше Redis для ключа '{key}': {e}", exc_info=True)
            raise

    async def get_hash_field(self, key: str, field: str) -> Optional[str]:
        """
        Получает одно поле из хеша Redis.
        """
        try:
            value = await self.redis_client.hget(key, field)
            return value # Просто возвращаем значение, оно уже является строкой

        except Exception as e:
            self.logger.error(f"Ошибка при получении поля '{field}' из хеша Redis для ключа '{key}': {e}", exc_info=True)
            raise

    async def add_to_set(self, key: str, member: str) -> None:
        """
        Добавляет элемент в Redis Set.
        """
        try:
            await self.redis_client.sadd(key, member)
            self.logger.debug(f"Элемент '{member}' добавлен в Redis Set '{key}'.")
        except Exception as e:
            self.logger.error(f"Ошибка при добавлении элемента '{member}' в Redis Set '{key}': {e}", exc_info=True)
            raise

    async def set_key(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """
        Устанавливает строковое значение по ключу в Redis, опционально с TTL.
        """
        try:
            if ttl:
                await self.redis_client.setex(key, ttl, value)
                self.logger.debug(f"Ключ '{key}' установлен в Redis с TTL {ttl}s.")
            else:
                await self.redis_client.set(key, value)
                self.logger.debug(f"Ключ '{key}' установлен в Redis.")
        except Exception as e:
            self.logger.error(f"Ошибка при установке ключа '{key}' в Redis: {e}", exc_info=True)
            raise

    async def get_key(self, key: str) -> Optional[str]:
        """
        Получает строковое значение по ключу из Redis.
        """
        try:
            value = await self.redis_client.get(key)
            if value:
                return value.decode('utf-8')
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении ключа '{key}' из Redis: {e}", exc_info=True)
            raise


    # ДОБАВЛЯЕМ НОВЫЙ МЕТОД ДЛЯ УСТАНОВКИ СЕССИИ
    async def set_active_session(self, discord_id: int, account_id: int, character_id: int) -> None:
        """Сохраняет ID аккаунта и персонажа в хэш активной сессии."""
        key = RedisKeys.ACTIVE_USER_SESSION_HASH.format(discord_id=discord_id)
        session_data = {
            RedisKeys.FIELD_SESSION_ACCOUNT_ID: str(account_id),
            RedisKeys.FIELD_SESSION_CHARACTER_ID: str(character_id)
        }
        # Используем исправленный set_hash_fields
        await self.set_hash_fields(key, session_data)

    # ДОБАВЛЯЕМ НОВЫЙ МЕТОД ДЛЯ ПОЛУЧЕНИЯ СЕССИИ
    async def get_active_session(self, discord_id: int) -> Optional[Dict[str, int]]:
        """Получает ID аккаунта и персонажа из хэша активной сессии."""
        key = RedisKeys.ACTIVE_USER_SESSION_HASH.format(discord_id=discord_id)
        session_data = await self.redis_client.hgetall(key)
        if not session_data:
            return None
        return {
            "account_id": int(session_data.get(RedisKeys.FIELD_SESSION_ACCOUNT_ID)),
            "character_id": int(session_data.get(RedisKeys.FIELD_SESSION_CHARACTER_ID))
        }