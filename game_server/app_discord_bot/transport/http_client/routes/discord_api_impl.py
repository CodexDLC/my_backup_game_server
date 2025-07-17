# game_server/app_discord_bot/transport/http_client/routes/discord_api_impl.py

import aiohttp
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel # Импортируем BaseModel для универсальности
from game_server.app_discord_bot.transport.http_client.interfaces.i_discord_api import IDiscordAPIRoutes
# Добавляем импорт GuildConfigDeleteRequest

from game_server.config.logging.logging_setup import app_logger as logger
from game_server.contracts.api_models.discord.config_management_requests import GuildConfigDeleteRequest, GuildConfigSyncRequest
from game_server.contracts.api_models.discord.entity_management_requests import GetDiscordEntitiesRequest, UnifiedEntityBatchDeleteRequest, UnifiedEntitySyncRequest
from game_server.contracts.shared_models.base_requests import BaseRequest


class DiscordAPIRoutesImpl(IDiscordAPIRoutes):
    def __init__(self, session: aiohttp.ClientSession, base_url: str):
        self._session = session
        self._base_url = f"{base_url}/discord"

    async def _send_request(self, method: str, path: str, data: BaseRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        payload_data = data.model_dump(mode='json', by_alias=True)

        try:
            async with self._session.request(
                method, f"{self._base_url}{path}", json=payload_data, headers=headers
            ) as response:
                response_body = await response.json() if response.status != 204 else {}
                return response.status, response_body
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка клиента aiohttp для запроса {method} {path}: {e}", exc_info=True)
            return None, None
        except Exception as e:
            logger.critical(f"Критическая ошибка при отправке HTTP запроса {method} {path}: {e}", exc_info=True)
            return None, None

    async def sync_entities(self, data: UnifiedEntitySyncRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        return await self._send_request("POST", "/sync", data, headers=headers)

    async def get_entities(self, data: GetDiscordEntitiesRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        return await self._send_request("POST", "/get", data, headers=headers)

    async def batch_delete_entities(self, data: UnifiedEntityBatchDeleteRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        return await self._send_request("DELETE", "/batch-delete", data, headers=headers)

    async def sync_config_from_bot(self, data: GuildConfigSyncRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        Отправляет полную конфигурацию гильдии из кэша бота на бэкенд.
        """
        return await self._send_request("POST", "/guild-config/sync", data, headers=headers)

    # НОВЫЙ МЕТОД: Для вызова эндпоинта удаления конфигурации гильдии из бэкенд-Redis
    async def delete_config_from_bot(self, data: GuildConfigDeleteRequest, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[int], Optional[Dict[str, Any]]]:
        """
        Отправляет команду на удаление полной конфигурации гильдии из бэкенд-кэша.
        """
        return await self._send_request("POST", "/guild-config/delete", data, headers=headers) # Используем POST для команды
