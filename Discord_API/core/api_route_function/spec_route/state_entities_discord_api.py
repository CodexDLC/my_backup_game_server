# Discord_API/core/api_route_function/spec_route/state_entities_discord_api.py

from typing import Any, Dict, List, Optional
import aiohttp

# Импортируем наш централизованный логгер бота
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
logger = bot_logger.getChild(__name__)

from Discord_API.discord_settings import API_URL


# Определяем базовый путь для роутов StateEntityDiscord
# ЭТО КРАЙНЕ ВАЖНО: УБЕДИТЕСЬ, ЧТО ЭТОТ ПУТЬ СОВПАДАЕТ С ВАШИМ ROUTERS_CONFIG.PY НА БЭКЕНДЕ
# Если ваш роутер discord_roles_mapping_router зарегистрирован под /discord/roles, то это верно.
BASE_PATH_ROLES = "/discord/roles" # <--- УБЕДИТЕСЬ, ЧТО ЭТОТ ПУТЬ СОВПАДАЕТ С ВАШИМ ROUTERS_CONFIG.PY НА БЭКЕНДЕ


class StateEntitiesDiscordAPIClient:
    """
    Клиент для взаимодействия с API бэкенда по управлению записями StateEntityDiscord.
    (Привязка ролей Discord к State Entities).
    """
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self):
        """Возвращает или создает сессию aiohttp."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _request(
        self,
        method: str,
        endpoint_path: str, # Это путь относительно base_url, например "/discord/roles/sync-batch"
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Вспомогательный асинхронный метод для выполнения HTTP-запросов.
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint_path}"
        logger.info(f"Отправляем запрос: {method} {url}")

        try:
            async with session.request(method, url, json=payload, params=params) as response:
                logger.info(f"Получен HTTP-ответ со статусом: {response.status}")
                response.raise_for_status()

                response_json = await response.json()
                logger.debug(f"API-ответ получен: {response_json}")
                return response_json

        except aiohttp.ClientConnectorError as e:
            logger.error(f"❌ Ошибка подключения к бэкенду по адресу {url}: {e}", exc_info=True)
            raise ConnectionError(f"Не удалось подключиться к бэкенду API: {e}")
        except aiohttp.ClientResponseError as e:
            error_details = await response.json() if response.content_type == 'application/json' else await response.text()
            logger.error(f"❌ Ошибка API {e.status} {e.message} от {url}: {error_details}", exc_info=True)
            raise ValueError(f"Ошибка API {e.status} {e.message}: {error_details}")
        except Exception as e:
            logger.error(f"❌ Непредвиденная ошибка при запросе к API {url}: {e}", exc_info=True)
            raise RuntimeError(f"Неизвестная ошибка при запросе к API: {e}")

    # --- Методы, соответствующие StateEntitiesDiscordLogic на бэкенде ---

    async def create_or_update_roles_batch(self, roles_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Массовое создание или обновление записей StateEntityDiscord.
        Соответствует: POST {BASE_PATH_ROLES}/sync-batch
        """
        # Бэкенд ожидает {"roles": [...]}, где [...] - список словарей.
        return await self._request("POST", f"{BASE_PATH_ROLES}/sync-batch", payload={"roles": roles_data})

    async def get_all_roles_for_guild(self, guild_id: int) -> Dict[str, Any]:
        """
        Получает все записи StateEntityDiscord для указанной гильдии.
        Соответствует: GET {BASE_PATH_ROLES}/guild/{guild_id}
        """
        # Путь роута на бэкенде был изменен с /guild/{guild_id}/all на /guild/{guild_id}
        return await self._request("GET", f"{BASE_PATH_ROLES}/guild/{guild_id}")

    async def get_role_by_pk(self, guild_id: int, role_id: int) -> Dict[str, Any]:
        """
        Получает одну запись StateEntityDiscord по ПК (guild_id, role_id).
        Соответствует: GET {BASE_PATH_ROLES}/guild/{guild_id}/role/{role_id}
        """
        # Путь роута на бэкенде был изменен (world_id и access_code удалены из пути)
        return await self._request("GET", f"{BASE_PATH_ROLES}/guild/{guild_id}/role/{role_id}")

    async def create_or_update_role_by_pk(self, guild_id: int, role_id: int, access_code: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        Создает или обновляет одну запись StateEntityDiscord по ПК (guild_id, role_id).
        Соответствует: PUT {BASE_PATH_ROLES}/guild/{guild_id}/role/{role_id}
        """
        payload = {
            "guild_id": guild_id,
            "discord_role_id": role_id,
            "access_code": access_code,
            "description": description
        }
        # Путь роута на бэкенде был изменен (world_id и access_code удалены из пути)
        return await self._request("PUT", f"{BASE_PATH_ROLES}/guild/{guild_id}/role/{role_id}", payload=payload)


    async def delete_roles_by_discord_ids(self, guild_id: int, discord_role_ids: List[int]) -> Dict[str, Any]:
        """
        Массовое удаление записей StateEntityDiscord по Discord role_id.
        Соответствует: DELETE {BASE_PATH_ROLES}/delete-batch
        """
        # Бэкенд ожидает {"guild_id": ..., "role_ids": [...]}
        payload = {"guild_id": guild_id, "role_ids": discord_role_ids}
        return await self._request("DELETE", f"{BASE_PATH_ROLES}/delete-batch", payload=payload)

    async def delete_role_by_pk(self, guild_id: int, role_id: int) -> Dict[str, Any]:
        """
        Удаление одной записи StateEntityDiscord по ПК (guild_id, role_id).
        Соответствует: DELETE {BASE_PATH_ROLES}/guild/{guild_id}/role/{role_id}
        """
        # Путь роута на бэкенде был изменен (world_id и access_code удалены из пути)
        return await self._request("DELETE", f"{BASE_PATH_ROLES}/guild/{guild_id}/role/{role_id}")
        
    async def close_session(self):
        """Закрывает сессию aiohttp."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None