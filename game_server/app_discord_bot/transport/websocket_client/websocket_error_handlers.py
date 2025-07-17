# game_server/app_discord_bot/transport/websocket_client/websocket_error_handlers.py

import asyncio
import logging
from typing import Any, Dict
import aiohttp.client_exceptions # Для aiohttp.WSMsgType


# Получаем логгер для этого модуля
logger = logging.getLogger(__name__) 
# ИЛИ, если вы хотите использовать центральный app_logger:
# from game_server.config.logging.logging_setup import app_logger as logger


# --- Функции для обработки успешного подтверждения и различных ошибок ---

async def handle_auth_success(logger_instance: logging.Logger, client_id: str, client_type: str) -> None:
    """
    Обрабатывает успешное подтверждение аутентификации от сервера.
    """
    logger_instance.info(f"WSManager: Аутентификация подтверждена сервером. Client ID: {client_id}, Type: {client_type}")
    logger_instance.debug("DEBUG: Аутентификация успешно завершена. Перехожу к прослушиванию сообщений.")

async def handle_auth_error_response(logger_instance: logging.Logger, rpc_payload: Dict[str, Any]) -> None:
    """
    Обрабатывает ответ от сервера, указывающий на отклонение аутентификации.
    Выбрасывает ValueError, чтобы инициировать сброс токена.
    """
    error_detail = rpc_payload.get("error")
    error_code = error_detail.get("code", "UNKNOWN") if error_detail and isinstance(error_detail, dict) else "UNKNOWN_CODE"
    error_message = error_detail.get("message", "Неизвестная ошибка.") if error_detail and isinstance(error_detail, dict) else "Неизвестная ошибка."
    
    response_status_lower = rpc_payload.get("status", "N/A").lower()
    
    logger_instance.error(f"WSManager: Сервер отклонил аутентификацию. Статус: {response_status_lower}, Ошибка: {error_code} - {error_message}")
    raise ValueError(f"Server rejected WebSocket authentication: {error_message}")

async def handle_auth_invalid_data(logger_instance: logging.Logger, confirm_data: Any) -> None:
    """
    Обрабатывает случай, когда подтверждение аутентификации не содержит client_id/client_type.
    Выбрасывает ValueError, чтобы инициировать сброс токена.
    """
    logger_instance.error(f"WSManager: Подтверждение аутентификации не содержит client_id/client_type в поле 'data': {confirm_data}")
    raise ValueError("Server authentication confirmation missing client_id/client_type in data.")

async def handle_json_decode_error(logger_instance: logging.Logger, raw_data: Any) -> None:
    """
    Обрабатывает ошибку декодирования JSON в сообщении подтверждения аутентификации.
    """
    logger_instance.error(f"WSManager: Получено не-JSON подтверждение аутентификации: {raw_data}")
    raise ValueError("Invalid JSON in authentication confirmation.")

async def handle_non_text_message(logger_instance: logging.Logger, msg_type: aiohttp.WSMsgType) -> None:
    """
    Обрабатывает получение не текстового сообщения подтверждения аутентификации.
    """
    logger_instance.error(f"WSManager: Получено не текстовое сообщение подтверждения аутентификации: {msg_type}")
    raise ValueError("Non-text message received for authentication confirmation.")

# --- Функции для обработки общих ошибок подключения ---
async def handle_client_connector_error(logger_instance: logging.Logger, exception: aiohttp.client_exceptions.ClientConnectorError, host_url: str) -> None:
    """
    Обрабатывает ошибки подключения к серверу WebSocket (например, DNS, недоступность хоста).
    """
    message = f"Ошибка подключения к серверу WebSocket '{host_url}': {exception.oserror.strerror if exception.oserror else str(exception)}. Проверьте доступность хоста."
    logger_instance.error(f"WSManager: {message}")
    logger_instance.debug(f"DEBUG: Полная ошибка ClientConnectorError: {exception}", exc_info=False)

async def handle_timeout_error(logger_instance: logging.Logger, exception: asyncio.TimeoutError) -> None:
    """
    Обрабатывает таймауты при подключении к WebSocket или ожидании аутентификации.
    """
    message = "Таймаут при подключении к WebSocket или ожидании аутентификации."
    logger_instance.error(f"WSManager: {message}")
    logger_instance.debug(f"DEBUG: Таймаут произошел во время подключения или ожидания подтверждения WS.")