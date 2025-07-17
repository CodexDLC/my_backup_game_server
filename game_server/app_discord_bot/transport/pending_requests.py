# game_server/app_discord_bot/transport/pending_requests.py

import asyncio
import uuid
import logging
from typing import Dict, Optional, Any, Tuple, Union
import inject

from game_server.app_discord_bot.storage.cache.interfaces.pending_request_manager_interface import IPendingRequestManager

class PendingRequestsManager:
    """
    Управляет жизненным циклом асинхронных запросов...
    """
    @inject.autoparams()
    def __init__(
        self,
        redis_pending_request_manager: IPendingRequestManager,
        logger: logging.Logger
    ):
        self._pending: Dict[uuid.UUID, asyncio.Future] = {}
        self._timeout_handles: Dict[uuid.UUID, asyncio.Handle] = {}
        self.redis_pending_request_manager = redis_pending_request_manager
        self.logger = logger
        self._timeout = 60.0
        self.logger.info(f"✨ PendingRequestsManager (transport) инициализирован. Таймаут: {self._timeout}с.")

    async def create_request(self, request_id: Union[str, uuid.UUID], context_data: Dict[str, Any]) -> asyncio.Future:
        """
        Создает Future для ожидания ответа, сохраняет контекст в Redis и устанавливает таймаут.
        """
        if isinstance(request_id, str):
            try:
                request_id = uuid.UUID(request_id)
            except ValueError:
                self.logger.error(f"Получен невалидный строковый request_id в create_request: {request_id}")
                raise

        # 🔥 ИЗМЕНЕНО: Уровень логирования изменен на DEBUG
        self.logger.debug(f"PendingRequestsManager: create_request для ID: {request_id}")
        if request_id in self._pending:
            self.logger.warning(f"Запрос с ID {request_id} уже существует в памяти. Перезапись.")
        
        future = asyncio.get_running_loop().create_future()
        self._pending[request_id] = future
        
        await self.redis_pending_request_manager.store_request(str(request_id), context_data)
        
        handle = asyncio.get_running_loop().call_later(
            self._timeout, self._timeout_request, request_id
        )
        self._timeout_handles[request_id] = handle
        
        self.logger.debug(f"Запланирован таймаут для ID: {request_id}.")

        return future

    async def resolve_request(self, request_id: uuid.UUID, response_payload: Any) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Находит соответствующий Future, завершает его с полученными данными
        и извлекает контекст из Redis.
        """
        # 🔥 ИЗМЕНЕНО: Уровень логирования изменен на DEBUG
        self.logger.debug(f"PendingRequestsManager: resolve_request для ID: {request_id}")
        
        if isinstance(request_id, str):
            try:
                request_id = uuid.UUID(request_id)
            except ValueError:
                self.logger.error(f"Получен невалидный строковый request_id: {request_id}")
                return False, None

        future = self._pending.pop(request_id, None)
        handle = self._timeout_handles.pop(request_id, None) 
        if handle:
            handle.cancel()

        context_data = None
        if future and not future.done():
            self.logger.debug(f"Future для ID {request_id} найден. Получение контекста из Redis.")
            context_data = await self.redis_pending_request_manager.retrieve_and_delete_request(str(request_id))
            future.set_result((response_payload, context_data))
            self.logger.debug(f"Запрос с ID {request_id} успешно завершен.")
            return True, context_data
        elif future:
            self.logger.warning(f"Попытка завершить уже завершенный Future для ID: {request_id}.")
        else:
            # 🔥 ИЗМЕНЕНО: Сообщение о неизвестном запросе лучше делать уровня INFO, чтобы его было видно
            self.logger.info(f"Получен ответ для неизвестного или истекшего запроса с ID: {request_id}.")
            await self.redis_pending_request_manager.delete_request(str(request_id))
        
        return False, None

    def _timeout_request(self, request_id: uuid.UUID):
        """Обработчик таймаута для запроса."""
        # 🔥 ИЗМЕНЕНО: Таймаут - это важное событие, его уровень лучше поднять до WARNING
        self.logger.warning(f"PendingRequestsManager: сработал таймаут для ID: {request_id}.")
        
        future = self._pending.pop(request_id, None)
        self._timeout_handles.pop(request_id, None)

        if future and not future.done():
            error = asyncio.TimeoutError(f"Ответ на запрос {request_id} не получен в течение {self._timeout}с.")
            future.set_exception(error)
            # Оставляем ошибку на уровне ERROR, это правильно
            self.logger.error(f"Тайм-аут для запроса с ID: {request_id}. Future помечен как исключение.")
            asyncio.create_task(self.redis_pending_request_manager.delete_request(str(request_id)))

    def clear_all_pending(self):
        """Отменяет все ожидающие запросы."""
        self.logger.info("Очистка всех ожидающих запросов.")
        for future in self._pending.values():
            if not future.done():
                future.cancel("Manager is shutting down.")
        self._pending.clear()
        
        for handle in self._timeout_handles.values():
            handle.cancel()
        self._timeout_handles.clear()

    async def shutdown(self):
        """Корректное завершение работы менеджера."""
        self.logger.info("PendingRequestsManager: Завершение работы...")
        self.clear_all_pending()
        self.logger.info("PendingRequestsManager: Завершение работы завершено.")