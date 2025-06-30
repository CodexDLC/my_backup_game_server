# transport/http_client/routes/shard_api_impl.py

import aiohttp
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel # Импортируем BaseModel для универсальности

# 🔥 ИЗМЕНЕНИЕ: Импортируем SaveShardCommandDTO вместо RegisterGameShardRequest
from game_server.common_contracts.dtos.shard_dtos import SaveShardCommandDTO # ИЛИ game_server.common_contracts.api_models.system_api.RegisterGameShardRequest, если SaveShardCommandDTO будет использоваться как команда

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.app_discord_bot.transport.http_client.interfaces.i_shard_api import IShardAPIRoutes


class ShardAPIRoutesImpl(IShardAPIRoutes):
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self._session = session
        self._base_url = f"{base_url}/shards"

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


    # 🔥 ИЗМЕНЕНИЕ: Метод register теперь принимает SaveShardCommandDTO
    async def register(self, data: SaveShardCommandDTO, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        Регистрирует игровой шард на бэкенде.
        Возвращает кортеж (HTTP_статус, тело_ответа_FastAPI)
        """
        return await self._send_request("POST", "/register", data, headers=headers)
