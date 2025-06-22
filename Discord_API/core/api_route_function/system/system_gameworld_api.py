# Discord_API/core/api_route_function/spec_route/system_gameworld_api.py

from typing import Any, Dict, List, Optional
import aiohttp

# Импортируем наш централизованный логгер бота
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
logger = bot_logger.getChild(__name__) # Получаем дочерний логгер

from Discord_API.discord_settings import API_URL


BASE_PATH_GAMEWORLD = "/system/gameworld" # Определяем базовый путь для роутов игрового мира

class SystemGameworldAPIClient:
    """
    Клиент для взаимодействия с API игрового мира (World, Regions, Subregions).
    """
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self):
        """Возвращает или создает сессию aiohttp."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _request(self, method: str, endpoint: str, data: Any = None, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Вспомогательный метод для выполнения HTTP-запросов.
        endpoint должен быть полным путём, начиная, например, с "/system/gameworld/..."
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        logger.info(f"Отправляем запрос: {method} {url}")

        try:
            async with session.request(method, url, json=data, params=params) as response:
                logger.info(f"Получен HTTP-ответ со статусом: {response.status}")
                response.raise_for_status() # Вызовет исключение для ошибок 4xx/5xx

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
    
    async def get_current_world(self) -> Dict[str, Any]:
        """Получить текущий мир."""
        logger.info("Запрос текущего игрового мира.")
        try:
            return await self._request("GET", f"{BASE_PATH_GAMEWORLD}/world")
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"Ошибка при получении текущего мира: {e}", exc_info=True)
            raise # Пробрасываем ошибку для обработки на уровне сервиса/команды

    async def get_all_regions(self) -> Dict[str, Any]:
        """Получить все регионы."""
        logger.info("Запрос всех регионов.")
        try:
            return await self._request("GET", f"{BASE_PATH_GAMEWORLD}/regions")
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"Ошибка при получении всех регионов: {e}", exc_info=True)
            raise

    async def get_all_subregions(self) -> Dict[str, Any]:
        """Получить все подрегионы."""
        logger.info("Запрос всех подрегионов.")
        try:
            return await self._request("GET", f"{BASE_PATH_GAMEWORLD}/subregions")
        except (ConnectionError, ValueError, RuntimeError) as e:
            logger.error(f"Ошибка при получении всех подрегионов: {e}", exc_info=True)
            raise

    async def close_session(self):
        """Закрывает сессию aiohttp."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None