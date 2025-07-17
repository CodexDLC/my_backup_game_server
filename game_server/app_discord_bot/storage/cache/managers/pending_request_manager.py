# game_server/app_discord_bot/storage/cache/managers/pending_request_manager.py

import json
import logging
from typing import Dict, Any, Optional
import inject

from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.storage.cache.interfaces.pending_request_manager_interface import IPendingRequestManager

class PendingRequestManager(IPendingRequestManager):
    """
    Менеджер кэша для хранения контекста ожидающих запросов в Redis.
    """
    @inject.autoparams()
    def __init__(self, redis_client: DiscordRedisClient, logger: logging.Logger):
        self.redis_client = redis_client
        self.logger = logger
        # Устанавливаем TTL жестко внутри класса
        self.ttl = 300
        self.KEY_PREFIX = "pending_request"
        self.logger.info(f"✨ PendingRequestManager (cache) инициализирован с TTL: {self.ttl}")

    async def store_request(self, request_id: str, data: Dict[str, Any]) -> None:
        """Сохраняет контекст запроса в Redis с указанным TTL."""
        key = f"{self.KEY_PREFIX}:{request_id}"
        try:
            # Теперь self.ttl гарантированно будет int
            await self.redis_client.set_with_ttl(key, json.dumps(data), self.ttl)
            self.logger.debug(f"Запрос {request_id} сохранен в кеше с TTL {self.ttl}s.")
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении запроса {request_id} в кеше: {e}", exc_info=True)

    async def retrieve_and_delete_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Извлекает и удаляет контекст запроса из Redis."""
        key = f"{self.KEY_PREFIX}:{request_id}"
        try:
            data_str = await self.redis_client.get(key)
            if data_str:
                await self.redis_client.delete(key) # Удаляем после извлечения
                self.logger.debug(f"Запрос {request_id} извлечен и удален из кеша.")
                return json.loads(data_str)
            self.logger.warning(f"Запрос {request_id} не найден в кеше или истек.")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка декодирования JSON для запроса {request_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при извлечении/удалении запроса {request_id} из кеша: {e}", exc_info=True)
            return None
            
    async def delete_request(self, request_id: str) -> None:
        """Удаляет запрос из кеша (используется при таймауте)."""
        key = f"{self.KEY_PREFIX}:{request_id}"
        try:
            await self.redis_client.delete(key)
            self.logger.debug(f"Запрос {request_id} удален из кеша (по таймауту).")
        except Exception as e:
            self.logger.error(f"Ошибка при удалении запроса {request_id} из кеша: {e}", exc_info=True)