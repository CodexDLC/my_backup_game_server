# game_server/Logic/InfrastructureLogic/app_cache/services/task_queue/redis_batch_store.py

import msgpack
import json
import logging
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod # Добавлено

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient

# Обновленный импорт логгера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # Изменено

# Импортируем новый интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_redis_batch_store import IRedisBatchStore # Добавлено


# Изменяем класс RedisBatchStore, чтобы он наследовал от IRedisBatchStore
class RedisBatchStore(IRedisBatchStore): # Изменено
    """
    Универсальный класс для низкоуровневого сохранения и загрузки данных батчей в Redis.
    Использует Redis HASH для хранения.
    - Сложные объекты (dict, list) сериализуются с MsgPack.
    - Простые типы (int, float, bool, str) сохраняются как строки Redis.
    """
    def __init__(self, redis_client: CentralRedisClient):
        self.redis = redis_client
        logger.info("✅ RedisBatchStore инициализирован.") # Изменено: используем logger

    async def save_batch(self, key_template: str, batch_id: str, batch_data: Dict[str, Any], ttl_seconds: int) -> bool:
        redis_key = key_template.format(batch_id=batch_id)

        try:
            async with self.redis.pipeline_raw() as pipe:
                for field, value in batch_data.items():
                    field_bytes = field.encode('utf-8')

                    if field == "specs":
                        value_bytes = msgpack.packb(value, use_bin_type=True, default=str)
                    elif isinstance(value, (dict, list)):
                        value_bytes = msgpack.packb(value, use_bin_type=True, default=str)
                    else:
                        value_bytes = str(value).encode('utf-8')

                    pipe.hset(redis_key, field_bytes, value_bytes)

                pipe.expire(redis_key, ttl_seconds)
                await pipe.execute()

            logger.debug(f"Батч '{batch_id}' сохранен в Redis (HASH + MsgPack/string) по ключу '{redis_key}'. TTL: {ttl_seconds}s.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении батча '{batch_id}' в Redis: {e}", exc_info=True)
            return False

    async def load_batch(self, key_template: str, batch_id: str) -> Optional[Dict[str, Any]]:
        redis_key = key_template.format(batch_id=batch_id)
        try:
            raw_data_dict_bytes = await self.redis.hgetall_raw(redis_key)

            if not raw_data_dict_bytes:
                logger.debug(f"Батч '{batch_id}' по ключу '{redis_key}' не найден или пуст в Redis.")
                return None

            loaded_data: Dict[str, Any] = {}
            for field_bytes, value_bytes in raw_data_dict_bytes.items():
                field = field_bytes.decode('utf-8')

                if field == "specs":
                    try:
                        value = msgpack.unpackb(value_bytes, raw=False)
                    except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackException) as e:
                        logger.error(f"Ошибка распаковки MsgPack для поля 'specs' в батче '{redis_key}': {e}", exc_info=True)
                        value = value_bytes.decode('utf-8')
                    except Exception as e:
                        logger.error(f"Неожиданная ошибка десериализации 'specs' для батча '{redis_key}': {e}", exc_info=True)
                        value = value_bytes
                else:
                    try:
                        value = value_bytes.decode('utf-8')
                        if field in ["target_count_in_chunk", "generated_count_in_chunk", "timestamp"]:
                            try:
                                value = int(value)
                            except ValueError:
                                pass
                    except UnicodeDecodeError:
                        logger.warning(f"Ошибка декодирования UTF-8 для поля '{field}' в батче '{redis_key}'.")
                        value = value_bytes

                loaded_data[field] = value

            logger.debug(f"Батч '{batch_id}' загружен из Redis (HASH + MsgPack/string) по ключу '{redis_key}'.")
            return loaded_data
        except Exception as e:
            logger.error(f"Ошибка при загрузке батча '{batch_id}' из Redis: {e}", exc_info=True)
            raise

    async def increment_field(self, key_template: str, batch_id: str, field: str, increment_by: int = 1) -> Optional[int]:
        redis_key = key_template.format(batch_id=batch_id)
        try:
            return await self.redis.hincrby_raw(redis_key, field.encode('utf-8'), increment_by)
        except Exception as e:
            logger.error(f"Ошибка hincrby для ключа '{redis_key}', поля '{field}': {e}", exc_info=True)
            raise

    async def update_fields(self, key_template: str, batch_id: str, fields: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
        redis_key = key_template.format(batch_id=batch_id)
        try:
            async with self.redis.pipeline_raw() as pipe:
                for field, value in fields.items():
                    field_bytes = field.encode('utf-8')
                    if field == "specs":
                        value_bytes = msgpack.packb(value, use_bin_type=True, default=str)
                    elif isinstance(value, (dict, list)):
                        value_bytes = msgpack.packb(value, use_bin_type=True, default=str)
                    else:
                        value_bytes = str(value).encode('utf-8')
                    pipe.hset(redis_key, field_bytes, value_bytes)

                if ttl_seconds is not None:
                    pipe.expire(redis_key, ttl_seconds)

                await pipe.execute()

            logger.debug(f"Поля батча '{batch_id}' обновлены в Redis: {redis_key}. Поля: {list(fields.keys())}.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении полей батча '{batch_id}' в Redis: {e}", exc_info=True)
            return False

    async def delete_batch(self, key_template: str, batch_id: str) -> bool:
        redis_key = key_template.format(batch_id=batch_id)
        try:
            result = await self.redis.delete(redis_key)
            if result > 0:
                logger.debug(f"Батч '{batch_id}' успешно удален из Redis: {redis_key}.")
                return True
            logger.debug(f"Батч '{batch_id}' по ключу '{redis_key}' не найден для удаления.")
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении батча '{batch_id}' из Redis: {e}", exc_info=True)
            return False