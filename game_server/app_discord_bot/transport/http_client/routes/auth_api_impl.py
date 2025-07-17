# game_server/app_discord_bot/transport/http_client/routes/auth_api_impl.py
import aiohttp
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel


from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.transport.http_client.interfaces.i_auth_api import IAuthAPIRoutes
from game_server.contracts.api_models.system.requests import DiscordShardLoginRequest, HubRoutingRequest


class AuthAPIRoutesImpl(IAuthAPIRoutes):
    def __init__(self, session: aiohttp.ClientSession, base_url: str, client_id: str):
        self._session = session
        self._base_url = f"{base_url}/auth"
        self._client_id = client_id # Сохраняем client_id

    async def _send_request(self, method: str, path: str, data: BaseModel, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        payload_data = data.model_dump(mode='json', by_alias=True)

        request_headers = headers if headers is not None else {}
        if self._client_id:
            request_headers['X-Client-ID'] = self._client_id
        else:
            logger.warning("AuthAPIRoutesImpl: client_id не установлен, заголовок X-Client-ID не будет отправлен.")

        full_url = f"{self._base_url}{path}"
        logger.debug(f"DEBUG_HTTP_CLIENT: Отправка запроса: {method} {full_url}")
        logger.debug(f"DEBUG_HTTP_CLIENT: Заголовки: {request_headers}")
        logger.debug(f"DEBUG_HTTP_CLIENT: Тело запроса (payload_data): {payload_data}")


        try:
            async with self._session.request(
                method, full_url, json=payload_data, headers=request_headers
            ) as response:
                logger.debug(f"DEBUG_HTTP_CLIENT: Получен ответ. Статус: {response.status}, Headers: {response.headers}")
                response_text = await response.text()
                logger.debug(f"DEBUG_HTTP_CLIENT: Тело ответа (text): {response_text}")

                response_json = None
                try:
                    response_json = await response.json()
                    logger.debug(f"DEBUG_HTTP_CLIENT: Тело ответа (JSON): {response_json}")
                except aiohttp.ContentTypeError:
                    if not (200 <= response.status < 300):
                        logger.error(f"HTTP запрос {method} {path} завершился ошибкой: {response.status}, не-JSON ответ: {response_text}")
                        return response.status, {"detail": response_text}
                    pass

                return response.status, response_json if response_json is not None else {}
                
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка клиента aiohttp для запроса {method} {path}: {e}", exc_info=True)
            return None, None
        except Exception as e:
            logger.critical(f"Критическая ошибка при отправке HTTP запроса {method} {path}: {e}", exc_info=True)
            return None, None

    # ИЗМЕНЕНО: Имя метода возвращено на hub_login, но путь изменен на /hub-registered
    async def hub_login(self, data: HubRoutingRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """Инициировать регистрацию/первичный вход через Хаб.""" # ИЗМЕНЕНО: Docstring обновлен
        return await self._send_request("POST", "/hub-registered", data, headers=headers) # ИЗМЕНЕНО: Путь

    async def session_login(self, data: DiscordShardLoginRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """Инициировать создание игровой сессии."""
        return await self._send_request("POST", "/session-login", data, headers=headers)