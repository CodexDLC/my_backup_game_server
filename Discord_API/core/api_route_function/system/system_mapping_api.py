# Discord_API/core/api_route_function/system/system_mapping_api.py

from typing import Any, Dict, List, Optional
import aiohttp

# Импортируем наш централизованный логгер бота
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
logger = bot_logger.getChild(__name__)

from Discord_API.discord_settings import API_URL


# ИСПРАВЛЕНО: Определяем базовый путь для роутов state_entities
# Он должен соответствовать тому, как роутер подключен в routers_config.py
# В Swagger UI это /system/mapping, поэтому BASE_PATH_FOR_STATE_ENTITIES должен быть "/system/mapping"
BASE_PATH_FOR_STATE_ENTITIES = "/mapping" # <--- ИСПРАВЛЕНО


class SystemMappingAPIClient:
    """
    Клиент для взаимодействия с API бэкенда по управлению записями StateEntity.
    """
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _request(self, method: str, endpoint: str, data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Отправляем запрос: {method} {url}")
        
        # --- НОВОЕ ЛОГИРОВАНИЕ: Логируем данные, отправляемые в теле запроса ---
        if data:
            logger.info(f"Данные запроса (тело): {data}")
        # ---------------------------------------------------------------------

        try:
            async with session.request(method, url, json=data, params=params) as response:
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
    
    async def get_all_state_entities(self) -> Dict[str, Any]: # <--- ИЗМЕНЕН ВОЗВРАЩАЕМЫЙ ТИП!
        """Запрос на получение всех записей `state_entities` из API."""
        try:
            response_full = await self._request("GET", f"{BASE_PATH_FOR_STATE_ENTITIES}/state-entities")
            
            if response_full.get("success") is True:
                logger.debug(f"API-ответ get_all_state_entities успешно получен и содержит 'success': True.")
                return response_full
            else:
                logger.warning(
                    f"⚠️ API-ответ get_all_state_entities имеет статус 'error' или 'success' не True. "
                    f"Получили: {response_full}"
                )
                return response_full 

        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"❌ Ошибка при получении всех State Entities: {e}", exc_info=True)
            return {"success": False, "message": str(e), "code": "CLIENT_ERROR"}


    async def get_state_entity_by_access_code(self, access_code: str) -> Optional[Dict[str, Any]]:
        """Запрос на получение записи `state_entities` по `access_code`."""
        try:
            response_full = await self._request("GET", f"{BASE_PATH_FOR_STATE_ENTITIES}/state-entities/{access_code}")
            
            if response_full.get("success") is True:
                logger.debug(f"Получена State Entity по access_code '{access_code}'.")
                return response_full
            else:
                logger.warning(
                    f"⚠️ API-ответ get_state_entity_by_access_code для '{access_code}' имеет статус 'error' или 'success' не True. "
                    f"Получили: {response_full}"
                )
                return response_full
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"❌ Ошибка при получении State Entity по access_code '{access_code}': {e}", exc_info=True)
            return {"success": False, "message": str(e), "code": "CLIENT_ERROR"}
