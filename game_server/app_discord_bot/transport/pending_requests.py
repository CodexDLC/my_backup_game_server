# game_server/app_discord_bot/transport/pending_requests.py

import asyncio
import uuid
import json
from typing import Dict, Optional, Any, Tuple
from game_server.config.logging.logging_setup import app_logger as logger

from game_server.app_discord_bot.storage.cache.managers.pending_request_manager import PendingRequestManager as RedisPendingRequestManager


class PendingRequestsManager:
    def __init__(self, redis_pending_request_manager: RedisPendingRequestManager, timeout: float = 60.0):
        self._pending: Dict[uuid.UUID, asyncio.Future] = {}
        self._timeout_handles: Dict[uuid.UUID, asyncio.Handle] = {} 
        self._redis_pending_request_manager = redis_pending_request_manager
        self._timeout = timeout
        # Этот лог может оставаться INFO, так как это инициализация менеджера
        logger.info(f"PendingRequestsManager инициализирован (управляет Futures и Redis). Таймаут: {timeout}с.")

    async def create_request(self, request_id: uuid.UUID, context_data: Dict[str, Any]) -> asyncio.Future:
        # Этот лог может оставаться INFO, так как это вход в публичный метод
        logger.info(f"PendingRequestsManager: create_request ВХОД для ID: {request_id}")
        if request_id in self._pending:
            logger.warning(f"PendingRequestsManager: Запрос с ID {request_id} уже существует в памяти (_pending). Перезапись.")
        
        future = asyncio.get_running_loop().create_future()
        
        logger.debug(f"PendingRequestsManager: Добавление Future для ID {request_id} в _pending. Текущий размер: {len(self._pending)}. Тип ключа: {type(request_id)}") # NEW LOG
        self._pending[request_id] = future

        logger.debug(f"PendingRequestsManager: Сохранение контекста в Redis для ID: {request_id}")
        await self._redis_pending_request_manager.store_request(str(request_id), context_data)
        logger.debug(f"PendingRequestsManager: Контекст сохранен в Redis для ID: {request_id}.")
        
        handle = asyncio.get_running_loop().call_later(
            self._timeout, self._timeout_request, request_id
        )
        self._timeout_handles[request_id] = handle
        
        logger.debug(f"PendingRequestsManager: Запланирован таймаут для ID: {request_id}. Текущий размер _timeout_handles: {len(self._timeout_handles)}")
        # Этот лог может оставаться INFO, так как это выход из публичного метода
        logger.info(f"PendingRequestsManager: create_request ВЫХОД для ID: {request_id}. Future создан и таймаут запланирован.")
        return future

    async def resolve_request(self, request_id: uuid.UUID, response_payload: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
        # Этот лог может оставаться INFO, так как это вход в публичный метод
        logger.info(f"PendingRequestsManager: resolve_request ВХОД для ID: {request_id}. Тип входящего ID: {type(request_id)}") # NEW LOG
        
        if isinstance(request_id, str):
            try:
                request_id = uuid.UUID(request_id)
                logger.debug(f"PendingRequestsManager: Входящий request_id преобразован в UUID: {request_id}") # NEW LOG
            except ValueError:
                logger.error(f"PendingRequestsManager: Получен невалидный строковый request_id: {request_id}. Невозможно преобразовать в UUID.")
                return False, None

        logger.debug(f"PendingRequestsManager: Попытка извлечь Future для ID {request_id} из _pending. Текущий размер: {len(self._pending)}. Тип ключа для поиска: {type(request_id)}") # NEW LOG
        future = self._pending.pop(request_id, None)
        logger.debug(f"PendingRequestsManager: Future извлечен: {future is not None}. Новый размер _pending: {len(self._pending)}")

        logger.debug(f"PendingRequestsManager: Попытка извлечь handle для ID {request_id} из _timeout_handles. Текущий размер: {len(self._timeout_handles)}. Тип ключа для поиска: {type(request_id)}") # NEW LOG
        handle = self._timeout_handles.pop(request_id, None) 
        if handle:
            handle.cancel()
            logger.debug(f"PendingRequestsManager: Таймаут handle для ID {request_id} отменен. Новый размер _timeout_handles: {len(self._timeout_handles)}")
        else:
            logger.warning(f"PendingRequestsManager: Таймаут handle для ID {request_id} не найден или уже отменен.")


        context_data = None
        
        if future and not future.done():
            logger.debug(f"PendingRequestsManager: Future для ID {request_id} найден и не завершен. Получение контекста из Redis.")
            context_data = await self._redis_pending_request_manager.retrieve_and_delete_request(str(request_id))
            
            future.set_result((response_payload, context_data))
            # 🔥 ИЗМЕНЕНО: Теперь этот лог будет уровня DEBUG
            logger.debug(f"PendingRequestsManager: Запрос с ID {request_id} успешно завершен. Контекст: {context_data}")
            return True, context_data
        elif future:
            logger.warning(f"PendingRequestsManager: Попытка завершить уже завершенный Future для ID: {request_id}. Future.done(): {future.done()}")
        else:
            logger.warning(f"PendingRequestsManager: Получен ответ для неизвестного или истекшего запроса с ID: {request_id}. Future не найден.")
            await self._redis_pending_request_manager.delete_request(str(request_id))
        # Этот лог может оставаться INFO, так как это выход из публичного метода
        logger.info(f"PendingRequestsManager: resolve_request ВЫХОД для ID: {request_id}.")
        return False, None

    def _timeout_request(self, request_id: uuid.UUID):
        # Этот лог может оставаться INFO, так как это вход в публичный метод/обработчик
        logger.info(f"PendingRequestsManager: _timeout_request ВХОД для ID: {request_id}.")
        
        handle = self._timeout_handles.pop(request_id, None) 
        if handle:
            handle.cancel()
            logger.debug(f"PendingRequestsManager: Таймаут handle для ID {request_id} отменен (из _timeout_request).")

        logger.debug(f"PendingRequestsManager: Попытка извлечь Future для ID {request_id} из _pending (в _timeout_request). Текущий размер: {len(self._pending)}")
        future = self._pending.pop(request_id, None)
        logger.debug(f"PendingRequestsManager: Future извлечен (в _timeout_request): {future is not None}. Новый размер _pending: {len(self._pending)}")

        if future and not future.done():
            error = asyncio.TimeoutError(f"Ответ на запрос {request_id} не получен в течение {self._timeout}с.")
            future.set_exception(error)
            logger.error(f"PendingRequestsManager: Тайм-аут для запроса с ID: {request_id}. Future помечен как исключение.")
            asyncio.create_task(self._redis_pending_request_manager.delete_request(str(request_id)))
        elif future:
            logger.warning(f"PendingRequestsManager: Тайм-аут сработал для уже завершенного Future: {request_id}. Future.done(): {future.done()}")
        else:
            logger.info(f"PendingRequestsManager: Тайм-аут сработал для уже отсутствующего Future: {request_id}.")
        # Этот лог может оставаться INFO, так как это выход из публичного метода/обработчика
        logger.info(f"PendingRequestsManager: _timeout_request ВЫХОД для ID: {request_id}.")

    def clear_all_pending(self):
        # Этот лог может оставаться INFO, так как это высокоуровневая операция
        logger.info("PendingRequestsManager: Очистка всех ожидающих запросов и их таймаутов.")
        for request_id, future in list(self._pending.items()):
            if not future.done():
                future.cancel("Manager is shutting down.")
            self._pending.pop(request_id, None)
        for handle in list(self._timeout_handles.values()):
            handle.cancel()
        self._timeout_handles.clear()
        # Этот лог может оставаться INFO, так как это завершение высокоуровневой операции
        logger.info("PendingRequestsManager: Очистка всех ожидающих запросов завершена.")

    async def startup(self):
        # Эти логи могут оставаться INFO
        logger.info("PendingRequestsManager: Запуск...")
        logger.info("PendingRequestsManager: Запущен.")

    async def shutdown(self):
        # Эти логи могут оставаться INFO
        logger.info("PendingRequestsManager: Завершение работы...")
        self.clear_all_pending()
        logger.info("PendingRequestsManager: Завершение работы завершено.")
