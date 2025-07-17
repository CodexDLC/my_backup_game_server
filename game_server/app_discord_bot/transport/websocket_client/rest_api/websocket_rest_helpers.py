# game_server/app_discord_bot/transport/websocket_client/websocket_rest_helpers.py

import aiohttp
import asyncio
import logging
from typing import Any, Dict, Optional

# Получаем логгер для этого модуля
logger = logging.getLogger(__name__)
# ИЛИ, если вы хотите использовать центральный app_logger:
# from game_server.config.logging.logging_setup import app_logger as logger

# Важно: Эти функции будут принимать необходимые зависимости (logger, session, config_params) как аргументы.

async def request_auth_token(
    logger_instance: logging.Logger,
    session: aiohttp.ClientSession,
    auth_token_rest_endpoint: str,
    api_key: str,
    bot_name: str
) -> Optional[str]:
    """
    Запрашивает токен аутентификации через REST API Gateway.
    Это вынесенная функция из _request_auth_token ws_manager.py.
    """
    logger_instance.info(f"WSManager: Запрос токена аутентификации по URL: {auth_token_rest_endpoint}")

    payload = {
        "command": "issue_auth_token",
        "grant_type": "discord_bot",
        "client_type": "DISCORD_BOT",
        "bot_name": bot_name,
        "bot_secret": api_key
    }

    logger_instance.debug(f"DEBUG: Отправляю REST-запрос на получение токена: {payload}")
        
    try:
        # Убедимся, что сессия активна. Если она закрыта, создадим новую.
        # (Эта логика дублируется из WSManager, можно было бы сделать ensure_session_open в WSManager)
        if session.closed:
            logger_instance.debug("DEBUG: Предоставленная aiohttp.ClientSession закрыта, создаю новую.")
            session = aiohttp.ClientSession()

        async with session.post(auth_token_rest_endpoint, json=payload, timeout=10) as response:
            logger_instance.debug(f"DEBUG: Получен HTTP-ответ от REST-запроса токена, статус: {response.status}")
            if response.status == 200:
                response_data = await response.json()
                logger_instance.debug(f"DEBUG: Тело ответа REST-запроса токена: {response_data}")
                if response_data.get("success") and response_data.get("data") and response_data["data"].get("token"):
                    token = response_data["data"]["token"]
                    logger_instance.info(f"WSManager: ✅ Токен аутентификации успешно получен: ...{token[-6:]}")
                    return token
                else:
                    error_msg = response_data.get("message", "Неизвестная ошибка от сервера")
                    logger_instance.error(f"WSManager: Сервер отклонил запрос токена: {response.status} - {error_msg}")
                    return None
            else:
                error_text = await response.text()
                logger_instance.error(f"WSManager: Ошибка REST запроса токена: HTTP {response.status} - {error_text}")
                return None
    except asyncio.TimeoutError:
        logger_instance.error("WSManager: Таймаут при запросе токена через REST API.")
        return None
    except aiohttp.ClientError as e:
        logger_instance.error(f"WSManager: Ошибка HTTP клиента при запросе токена: {e}", exc_info=True)
        return None
    except Exception as e:
        logger_instance.critical(f"WSManager: Непредвиденная ошибка при запросе токена: {e}", exc_info=True)
        return None
