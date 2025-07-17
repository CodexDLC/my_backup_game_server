# game_server/app_discord_bot/app/services/utils/request_helper.py

import asyncio
import logging
import uuid
from typing import Any, Dict, Optional, Callable, Awaitable, Tuple

from pydantic import BaseModel
import inject

# 1. Добавляем прямой импорт имени бота
from game_server.app_discord_bot.config.discord_settings import BOT_NAME_FOR_GATEWAY
from game_server.app_discord_bot.transport.pending_requests import PendingRequestsManager
from game_server.app_discord_bot.transport.http_client.http_manager import HTTPManager


class RequestHelper:
    @inject.autoparams()
    def __init__(
        self,
        # 2. Убираем bot_name_for_gateway из аргументов
        pending_requests_manager: PendingRequestsManager,
        http_client_gateway: HTTPManager,
        logger: logging.Logger
    ):
        self.pending_requests_manager = pending_requests_manager
        self.http_client_gateway = http_client_gateway
        self.logger = logger
        # 3. Устанавливаем ID клиента напрямую из импортированного значения
        self.client_id = BOT_NAME_FOR_GATEWAY

        # Проверяем, что client_id не пустой, чтобы избежать ошибок в будущем
        if not self.client_id:
            raise ValueError("BOT_NAME_FOR_GATEWAY не может быть пустым.")

        self.logger.info("✅ RequestHelper инициализирован.")

    async def send_and_await_response(
        self,
        api_method: Callable[[BaseModel, Optional[Dict[str, str]]], Awaitable[Tuple[Optional[int], Optional[Dict[str, Any]]]]],
        request_payload: BaseModel,
        correlation_id: uuid.UUID,
        timeout: int = 60,
        headers: Optional[Dict[str, str]] = None,
        discord_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        
        self.logger.debug(f"RequestHelper: Вход в send_and_await_response. Correlation ID: {correlation_id}")

        request_context = {
            "correlation_id": str(correlation_id),
            "endpoint_info": str(api_method),
            "payload_preview": request_payload.model_dump_json(exclude_none=True)[:200],
            "command": getattr(request_payload, 'command', 'N/A_Command')
        }
        if discord_context:
            request_context.update(discord_context)

        # 4. Формируем заголовки и добавляем X-Client-ID
        request_headers = headers if headers is not None else {}
        request_headers['X-Client-ID'] = self.client_id
        self.logger.debug(f"RequestHelper: Подготовлены заголовки: {request_headers}")

        try:
            self.logger.debug("RequestHelper: Вызов api_method для отправки HTTP запроса...")
            http_status, http_response_body = await api_method(
                request_payload,
                headers=request_headers
            )
            
            self.logger.debug(f"RequestHelper: api_method вернул статус: {http_status}")

            if http_status is None:
                self.logger.error(f"RequestHelper: HTTP-запрос к Gateway не был отправлен. Correlation ID: {correlation_id}.")
                self.pending_requests_manager._timeout_request(correlation_id)
                raise RuntimeError(f"Не удалось отправить запрос к Gateway (Correlation ID: {correlation_id}).")

            if not (200 <= http_status < 300):
                error_msg = http_response_body.get('detail', 'Неизвестная ошибка HTTP')
                self.logger.error(f"RequestHelper: HTTP-запрос завершился ошибкой Gateway: Status={http_status}, Body={http_response_body}. Correlation ID: {correlation_id}")
                self.pending_requests_manager._timeout_request(correlation_id)
                raise RuntimeError(f"Gateway вернул ошибку {http_status}: {error_msg}")

            self.logger.debug(f"RequestHelper: HTTP-запрос отправлен. Ожидаем асинхронный ответ. Correlation ID: {correlation_id}")

            response_future = await self.pending_requests_manager.create_request(correlation_id, request_context)
            
            self.logger.debug(f"RequestHelper: Ожидаем результат Future для ID {correlation_id} с таймаутом {timeout}...")
            actual_response_payload, retrieved_context_from_future = await asyncio.wait_for(response_future, timeout=timeout)
            
            self.logger.debug(f"RequestHelper: Future успешно разрешен. Получен ответ для запроса {correlation_id}.")
            return actual_response_payload, retrieved_context_from_future

        except asyncio.CancelledError as e:
            self.logger.info(f"RequestHelper: Запрос {correlation_id} отменен: {e}")
            self.pending_requests_manager._timeout_request(correlation_id)
            raise
        except Exception as e:
            self.logger.critical(f"RequestHelper: Критическая ошибка при вызове API: {e}", exc_info=True)
            self.pending_requests_manager._timeout_request(correlation_id)
            raise