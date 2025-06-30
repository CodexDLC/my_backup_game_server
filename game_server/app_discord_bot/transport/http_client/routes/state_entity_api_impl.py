# game_server/app_discord_bot/transport/http_client/routes/state_entity_api_impl.py

import aiohttp
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel # Импортируем BaseModel для универсальности
from game_server.config.logging.logging_setup import app_logger as logger

# 🔥 ВАЖНО: Убедитесь, что IStateEntityAPIRoutes импортирован
from game_server.app_discord_bot.transport.http_client.interfaces.i_state_entity_api import IStateEntityAPIRoutes

# 🔥 ВАЖНО: Убедитесь, что GetStateEntityByKeyRequest (и другие модели, если используются здесь)
# импортированы из правильного "common_contracts" пути после перемещения файлов
from game_server.common_contracts.api_models.system_api import GetStateEntityByKeyRequest


# 🔥 ВОЗВРАЩАЕМ НАСЛЕДОВАНИЕ ОТ IStateEntityAPIRoutes
class StateEntityAPIRoutesImpl(IStateEntityAPIRoutes):
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self._session = session
        self._base_url = f"{base_url}/state-entities"

    # Тип возвращаемого значения: Tuple[Optional[int], Optional[Dict[str, Any]]]
    async def _send_request(self, method: str, path: str, data: BaseModel, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        payload_data = data.model_dump(mode='json', by_alias=True)

        try:
            async with self._session.request(
                method, f"{self._base_url}{path}", json=payload_data, headers=headers
            ) as response:
                response_json = None
                try:
                    response_json = await response.json()
                except aiohttp.ContentTypeError:
                    if not (200 <= response.status < 300):
                         logger.error(f"HTTP запрос {method} {path} завершился ошибкой: {response.status}, не-JSON ответ: {await response.text()}")
                         return response.status, {"detail": await response.text()}
                    pass 

                return response.status, response_json if response_json is not None else {}
                
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка клиента aiohttp для запроса {method} {path}: {e}", exc_info=True)
            return None, None
        except Exception as e:
            logger.critical(f"Критическая ошибка при отправке HTTP запроса {method} {path}: {e}", exc_info=True)
            return None, None

    # Методы должны соответствовать интерфейсу IStateEntityAPIRoutes
    # Используем BaseModel для data, так как все наши запросы являются BaseModel
    async def get_all(self, data: BaseModel, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        return await self._send_request("POST", "/get-all", data, headers=headers)

    async def get_by_key(self, data: BaseModel, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        return await self._send_request("POST", "/get-by-key", data, headers=headers)