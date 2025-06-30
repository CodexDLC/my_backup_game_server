# game_server/app_discord_bot/storage/cache/managers/pending_request_manager.py

import json
from typing import Dict, Any, Optional


from game_server.app_discord_bot.storage.cache.discord_redis_client import DiscordRedisClient
from game_server.app_discord_bot.storage.cache.interfaces.pending_request_manager_interface import IPendingRequestManager
from game_server.config.logging.logging_setup import app_logger as logger

class PendingRequestManager(IPendingRequestManager): # Это ваш Redis-менеджер
    def __init__(self, redis_client: DiscordRedisClient, ttl: int = 300):
        self.redis_client = redis_client
        self.ttl = ttl
        self.KEY_PREFIX = "pending_request"
        logger.info("✨ PendingRequestManager инициализирован.")

    async def store_request(self, command_id: str, data: Dict[str, Any]) -> None:
        key = f"{self.KEY_PREFIX}:{command_id}"
        try:
            await self.redis_client.set_with_ttl(key, json.dumps(data), self.ttl)
            logger.debug(f"Запрос {command_id} сохранен в кеше с TTL {self.ttl}s.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении запроса {command_id} в кеше: {e}", exc_info=True)

    async def retrieve_and_delete_request(self, command_id: str) -> Optional[Dict[str, Any]]:
        key = f"{self.KEY_PREFIX}:{command_id}"
        try:
            data_str = await self.redis_client.get(key)
            if data_str:
                await self.redis_client.delete(key) # Удаляем после извлечения
                logger.debug(f"Запрос {command_id} извлечен и удален из кеша.")
                return json.loads(data_str)
            logger.warning(f"Запрос {command_id} не найден в кеше или истек.")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON для запроса {command_id}: {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Ошибка при извлечении/удалении запроса {command_id} из кеша: {e}", exc_info=True)
            return None

    def clear_all_pending(self):
        """Очищает все ожидающие Future в памяти (для корректного завершения работы)."""
        for request_id, future in list(self._pending.items()): # Итерируем по копии, чтобы безопасно удалять
            if not future.done():
                future.cancel("Manager shutting down")
                logger.debug(f"Pending request {request_id} cancelled during shutdown.")
            self._pending.pop(request_id, None)
        logger.info("Все ожидающие Future очищены.")
            
    # 🔥 ДОБАВЛЕНО: Метод для удаления запроса (используется при таймауте)
    async def delete_request(self, command_id: str) -> None:
        key = f"{self.KEY_PREFIX}:{command_id}"
        try:
            await self.redis_client.delete(key)
            logger.debug(f"Запрос {command_id} удален из кеша.")
        except Exception as e:
            logger.error(f"Ошибка при удалении запроса {command_id} из кеша: {e}", exc_info=True)