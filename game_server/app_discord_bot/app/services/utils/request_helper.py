# game_server/app_discord_bot/app/services/utils/request_helper.py

import asyncio
import json
import uuid
from typing import Any, Dict, Optional, Tuple, Callable, Awaitable, Coroutine

from pydantic import BaseModel

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.transport.pending_requests import PendingRequestsManager
from game_server.app_discord_bot.transport.http_client.http_manager import HTTPManager


class RequestHelper:
    def __init__(self, pending_requests_manager: PendingRequestsManager, http_client_gateway: HTTPManager, bot_name: str):
        self.pending_requests_manager = pending_requests_manager
        self.http_client_gateway = http_client_gateway
        self.logger = logger

        self.logger.info("✅ RequestHelper инициализирован.")
        # ИЗМЕНЕНО: Переименовали _bot_name в bot_name_for_gateway для соответствия ожидаемому атрибуту
        self.bot_name_for_gateway = bot_name 

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
            "payload_preview": request_payload.model_dump_json()[:200],
            "command": getattr(request_payload, 'command', 'N/A_Command')
        }
        if discord_context:
            request_context.update(discord_context)

        request_headers = headers if headers is not None else {}
        # ИЗМЕНЕНО: Используем новое имя атрибута
        request_headers['X-Client-ID'] = self.bot_name_for_gateway 
        self.logger.debug(f"RequestHelper: Подготовлены заголовки: {request_headers}")

        http_response_body: Optional[Dict[str, Any]] = None
        http_status: Optional[int] = None
        try:
            self.logger.debug("RequestHelper: Вызов api_method для отправки HTTP запроса...")
            http_api_result = await api_method(
                request_payload,
                headers=request_headers
            )
            
            # Предполагаем, что http_api_result всегда Tuple[Optional[int], Optional[Dict[str, Any]]]
            # Поэтому извлекаем статус и тело ответа
            http_status, http_response_body = http_api_result
            
            self.logger.debug(f"RequestHelper: api_method вернул статус: {http_status}")

            if http_api_result is None or http_status is None: # Добавлена проверка http_status
                self.logger.error(f"RequestHelper: HTTP-запрос к Gateway не был отправлен или завершился сетевой ошибкой. Correlation ID: {correlation_id}. api_method вернул None.")
                self.pending_requests_manager._timeout_request(correlation_id)
                raise RuntimeError(f"Не удалось отправить запрос или соединиться с Gateway (Correlation ID: {correlation_id}).")

            if not (200 <= http_status < 300):
                error_msg = http_response_body.get('message', http_response_body.get('detail', 'Неизвестная ошибка HTTP'))
                self.logger.error(f"RequestHelper: HTTP-запрос завершился ошибкой Gateway: Status={http_status}, Body={http_response_body}. Correlation ID: {correlation_id}")
                self.pending_requests_manager._timeout_request(correlation_id)
                raise RuntimeError(f"Gateway вернул ошибку {http_status}: {error_msg}")

            self.logger.debug(f"RequestHelper: HTTP-запрос через API метод {str(api_method)} отправлен. Ожидаем асинхронный ответ. Correlation ID: {correlation_id}")

            self.logger.debug(f"RequestHelper: Вызов pending_requests_manager.create_request для ID {correlation_id}...")
            response_future = await self.pending_requests_manager.create_request(correlation_id, request_context)
            self.logger.debug(f"RequestHelper: Получен Future: {response_future}. Тип: {type(response_future)}")

            if not isinstance(response_future, asyncio.Future):
                self.logger.critical(f"RequestHelper: ОЖИДАЛСЯ asyncio.Future, ПОЛУЧЕН: {type(response_future)}. ЭТО СЕРЬЕЗНАЯ ПРОБЛЕМА.")
                self.pending_requests_manager._timeout_request(correlation_id)
                raise TypeError(f"Expected asyncio.Future from create_request, got {type(response_future)}")

            self.logger.debug(f"RequestHelper: Ожидаем результат Future для ID {correlation_id} с таймаутом {timeout}...")
            actual_response_payload, retrieved_context_from_future = await asyncio.wait_for(response_future, timeout=timeout)
            self.logger.debug(f"RequestHelper: Future успешно разрешен. Получен ответ: {actual_response_payload}. Тип: {type(actual_response_payload)}. Контекст: {retrieved_context_from_future}. Тип контекста: {type(retrieved_context_from_future)}")
            
            if actual_response_payload:
                if not isinstance(actual_response_payload, dict):
                    self.logger.critical(f"RequestHelper: ОЖИДАЛСЯ СЛОВАРЬ ОТВЕТА (после распаковки), ПОЛУЧЕН: {type(actual_response_payload)}. ЗНАЧЕНИЕ: {actual_response_payload}. ЭТО СЕРЬЕЗНАЯ ПРОБЛЕМА.")
                    raise TypeError(f"Expected dict as response payload after unpacking, got {type(actual_response_payload)}")

                self.logger.debug(f"RequestHelper: Получен асинхронный ответ для запроса {correlation_id}. Статус: {actual_response_payload.get('status')}")
                return actual_response_payload, retrieved_context_from_future
            else:
                self.logger.warning(f"RequestHelper: Запрос {correlation_id} отменен: Таймаут или не получен ответ.")
                raise asyncio.CancelledError(f"Запрос {correlation_id} отменен: Таймаут или не получен ответ.")

        except asyncio.CancelledError as e:
            self.logger.info(f"RequestHelper: Запрос {correlation_id} отменен: {e}")
            self.pending_requests_manager._timeout_request(correlation_id)
            raise
        except Exception as e:
            self.logger.critical(f"RequestHelper: Критическая ошибка при вызове API синхронизации: {e}", exc_info=True)
            self.pending_requests_manager._timeout_request(correlation_id)
            raise
