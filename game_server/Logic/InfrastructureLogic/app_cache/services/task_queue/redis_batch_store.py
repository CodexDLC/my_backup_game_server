# game_server/Logic/InfrastructureLogic/app_cache/services/task_queue/redis_batch_store.py

import inject
import msgpack
# import json # Больше не нужен, если все в MsgPack
import logging
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_redis_batch_store import IRedisBatchStore


class RedisBatchStore(IRedisBatchStore):
    """
    Универсальный класс для низкоуровневого сохранения и загрузки данных батчей в Redis.
    Использует Redis HASH для хранения, сериализуя ВСЕ значения с MsgPack.
    """
    @inject.autoparams()
    def __init__(self, redis_client: CentralRedisClient, logger: logging.Logger):
        self.redis = redis_client
        self.logger = logger
        self.logger.info("✅ RedisBatchStore инициализирован.")

    async def save_batch(self, key_template: str, batch_id: str, batch_data: Dict[str, Any], ttl_seconds: int) -> bool:
        redis_key = key_template.format(batch_id=batch_id)

        try:
            async with self.redis.pipeline_raw() as pipe:
                msgpack_mapping_bytes = {}
                for field, value in batch_data.items():
                    # 🔥 ИЗМЕНЕНИЕ: ВСЕ значения сериализуются в MsgPack
                    # Добавляем default=str для обработки UUID и datetime, если они встречаются
                    value_bytes = msgpack.packb(value, use_bin_type=True, default=str)
                    msgpack_mapping_bytes[field.encode('utf-8')] = value_bytes

                # Используем hset с mapping для эффективной массовой записи
                await pipe.hset(redis_key.encode('utf-8'), mapping=msgpack_mapping_bytes) # Ключ хэша тоже кодируем

                pipe.expire(redis_key.encode('utf-8'), ttl_seconds)
                await pipe.execute()

            logger.debug(f"Батч '{batch_id}' сохранен в Redis (HASH + MsgPack) по ключу '{redis_key}'. TTL: {ttl_seconds}s.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении батча '{batch_id}' в Redis (MsgPack): {e}", exc_info=True)
            return False

    async def load_batch(self, key_template: str, batch_id: str) -> Optional[Dict[str, Any]]:
        redis_key = key_template.format(batch_id=batch_id)
        try:
            # 🔥 ИСПРАВЛЕНИЕ: Используем hgetall_msgpack, который возвращает уже десериализованные данные
            loaded_data = await self.redis.hgetall_msgpack(redis_key)
            
            if not loaded_data:
                logger.debug(f"Батч '{batch_id}' по ключу '{redis_key}' не найден или пуст в Redis.")
                return None

            # 🔥 ИЗМЕНЕНИЕ: Поскольку hgetall_msgpack уже все десериализовал, просто возвращаем данные
            logger.debug(f"Батч '{batch_id}' загружен из Redis (HASH + MsgPack) по ключу '{redis_key}'.")
            return loaded_data
        except Exception as e:
            logger.error(f"Ошибка при загрузке батча '{batch_id}' из Redis (MsgPack): {e}", exc_info=True)
            raise # Перебрасываем исключение, как было в оригинале

    async def increment_field(self, key_template: str, batch_id: str, field: str, increment_by: int = 1) -> Optional[int]:
        redis_key = key_template.format(batch_id=batch_id)
        try:
            # 🔥 ИЗМЕНЕНИЕ: Используем redis_raw.hincrby
            # hincrby работает с байтами, field и key должны быть закодированы
            return await self.redis.redis_raw.hincrby(redis_key.encode('utf-8'), field.encode('utf-8'), increment_by)
        except Exception as e:
            logger.error(f"Ошибка hincrby для ключа '{redis_key}', поля '{field}': {e}", exc_info=True)
            raise

    async def update_fields(self, key_template: str, batch_id: str, fields: Dict[str, Any], ttl_seconds: Optional[int] = None) -> bool:
        redis_key = key_template.format(batch_id=batch_id)
        try:
            async with self.redis.pipeline_raw() as pipe:
                msgpack_mapping_bytes = {}
                for field, value in fields.items():
                    # 🔥 ИЗМЕНЕНИЕ: ВСЕ значения сериализуются в MsgPack
                    value_bytes = msgpack.packb(value, use_bin_type=True, default=str)
                    msgpack_mapping_bytes[field.encode('utf-8')] = value_bytes
                
                await pipe.hset(redis_key.encode('utf-8'), mapping=msgpack_mapping_bytes) # Используем hset с mapping

                if ttl_seconds is not None:
                    pipe.expire(redis_key.encode('utf-8'), ttl_seconds)

                await pipe.execute()

            logger.debug(f"Поля батча '{batch_id}' обновлены в Redis (MsgPack): {redis_key}. Поля: {list(fields.keys())}.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при обновлении полей батча '{batch_id}' в Redis (MsgPack): {e}", exc_info=True)
            return False

    async def delete_batch(self, key_template: str, batch_id: str) -> bool:
        redis_key = key_template.format(batch_id=batch_id)
        try:
            # 🔥 ИЗМЕНЕНИЕ: Используем redis_raw.delete
            result = await self.redis.redis_raw.delete(redis_key.encode('utf-8'))
            if result > 0:
                logger.debug(f"Батч '{batch_id}' успешно удален из Redis: {redis_key}.")
                return True
            logger.debug(f"Батч '{batch_id}' по ключу '{redis_key}' не найден для удаления.")
            return False
        except Exception as e:
            logger.error(f"Ошибка при удалении батча '{batch_id}' из Redis: {e}", exc_info=True)
            return False