# game_server/app_discord_bot/storage/cache/managers/game_world_data_manager.py
# Version: 0.003 # Увеличиваем версию

from datetime import datetime
import inject
import redis.asyncio as redis
import json
from typing import Dict, Any, Optional

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.storage.cache.interfaces.game_world_data_manager_interface import IGameWorldDataManager
from game_server.app_discord_bot.storage.cache.constant.constant_key import RedisKeys
from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient


class GameWorldDataManager(IGameWorldDataManager):
    """
    Менеджер данных игрового мира, реализующий IGameWorldDataManager.
    Взаимодействует с Redis для хранения и получения статического скелета мира,
    а также динамических данных о локациях.
    """
    @inject.autoparams()
    def __init__(self, redis_client: DiscordRedisClient):
        self._redis = redis_client
        logger.info("GameWorldDataManager инициализирован.")

    async def set_hash_field(self, key: str, field: str, value: str) -> None:
        """
        Устанавливает значение поля в хеше Redis. (Для статических данных мира)
        """
        try:
            await self._redis.hset(key, field, value)
            logger.debug(f"Redis: Установлено поле '{field}' в хеше '{key}'.")
        except Exception as e:
            logger.error(f"Ошибка при установке поля '{field}' в хеше '{key}' Redis: {e}", exc_info=True)

    async def delete_hash(self, key: str) -> None:
        """
        Удаляет весь хеш по заданному ключу.
        """
        try:
            await self._redis.delete(key)
            logger.info(f"Redis: Хеш '{key}' успешно удален.")
        except Exception as e:
            logger.error(f"Ошибка при удалении хеша '{key}' Redis: {e}", exc_info=True)

    async def get_hash_field(self, key: str, field: str) -> Optional[str]:
        """Получает значение поля из хеша."""
        try:
            return await self._redis.hget(key, field)
        except Exception as e:
            logger.error(f"Ошибка Redis HGET для хеша '{key}', поля '{field}': {e}", exc_info=True)
            return None

    async def get_all_hash_fields(self, key: str) -> Dict[str, str]:
        """Получает все поля и значения из хеша."""
        try:
            return await self._redis.hgetall(key)
        except Exception as e:
            logger.error(f"Ошибка Redis HGETALL для хеша '{key}': {e}", exc_info=True)
            return {}

    # 🔥 НОВЫЕ МЕТОДЫ для работы с динамическими данными локаций (Redis String) 🔥

    # 🔥 ИСПРАВЛЕННЫЙ МЕТОД: используем HMSET для динамических данных
    async def set_dynamic_location_data(self, location_id: str, data: Dict[str, Any]) -> None:
        """
        Сохраняет динамические данные о локации в Redis Hash.
        Ключ хеша формируется из GLOBAL_GAME_WORLD_DYNAMIC_LOCATION_DATA.
        Поля хеша: players_in_location, npcs_in_location, last_update.

        Args:
            location_id (str): ID локации.
            data (Dict[str, Any]): Динамические данные локации (например, players_in_location, npcs_in_location, last_update).
        """
        hash_key = RedisKeys.GLOBAL_GAME_WORLD_DYNAMIC_LOCATION_DATA.format(location_id=location_id)
        try:
            processed_data = {}
            for k, v in data.items():
                if isinstance(v, datetime):
                    processed_data[k] = v.isoformat().replace('+00:00', 'Z') # Сериализуем datetime в ISO строку
                elif isinstance(v, (int, float, bool)): # Числа и булевы можно напрямую
                    processed_data[k] = str(v)
                else: # Остальное (например, строки)
                    processed_data[k] = v

            # 🔥🔥🔥 ВОТ ЗДЕСЬ КЛЮЧЕВОЕ ИЗМЕНЕНИЕ: ИСПОЛЬЗУЕМ HMSET 🔥🔥🔥
            await self._redis.hmset(hash_key, processed_data) # <--- ИСПОЛЬЗУЕМ HMSET
            logger.debug(f"Redis: Динамические данные для локации '{location_id}' сохранены в хеше.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении динамических данных для локации '{location_id}' в Redis: {e}", exc_info=True)

    # 🔥 НОВЫЙ/ИСПРАВЛЕННЫЙ МЕТОД: получаем данные из Redis Hash
    async def get_dynamic_location_data(self, location_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает динамические данные о локации из Redis Hash.

        Args:
            location_id (str): ID локации.

        Returns:
            Optional[Dict[str, Any]]: Динамические данные локации или None, если не найдены.
        """
        hash_key = RedisKeys.GLOBAL_GAME_WORLD_DYNAMIC_LOCATION_DATA.format(location_id=location_id)
        try:
            raw_data = await self._redis.hgetall(hash_key)
            if not raw_data:
                return None

            parsed_data = {}
            for k, v in raw_data.items():
                # raw_data.keys() могут быть байтами, если decode_responses=False в redis-клиенте
                key_str = k.decode('utf-8') if isinstance(k, bytes) else k
                value_str = v.decode('utf-8') if isinstance(v, bytes) else v

                if key_str == "players_in_location" or key_str == "npcs_in_location":
                    parsed_data[key_str] = int(value_str) if value_str.isdigit() else 0
                elif key_str == "last_update":
                    try:
                        # last_update_str должен быть в формате ISO 8601 для datetime.fromisoformat
                        parsed_data[key_str] = value_str # Оставляем как строку, так как DTO ожидает строку
                        # Если DTO ожидает datetime, то: datetime.fromisoformat(value_str.replace('Z', '+00:00'))
                    except ValueError:
                        parsed_data[key_str] = None
                else:
                    parsed_data[key_str] = value_str

            return parsed_data
        except Exception as e:
            logger.error(f"Ошибка при получении динамических данных для локации '{location_id}' из Redis: {e}", exc_info=True)
            return None