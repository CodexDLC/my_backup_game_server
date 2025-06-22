import aiohttp
import json
from typing import Any, Dict, List, Optional

# Импортируем наш централизованный логгер бота
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
logger = bot_logger.getChild(__name__)

# Импортируем только API_URL из настроек
from Discord_API.discord_settings import API_URL


# Определяем базовый путь для роутов Discord сущностей (биндингов)
# Это должен быть префикс, который вы установите для этого роутера на бэкенде.
# Исходя из discord_entity.py, это /discord
BASE_PATH_ENTITIES = "/discord" # <--- УБЕДИТЕСЬ, ЧТО ЭТОТ ПУТЬ СОВПАДАЕТ С ВАШИМ ROUTERS_CONFIG.PY НА БЭКЕНДЕ


class DiscordBindingsAPI:
    """
    Клиент для взаимодействия с REST API бэкенда по управлению сущностями Discord (биндингами).
    Использует централизованный API_URL.
    """
    def __init__(self, base_url: str = API_URL):
        self.base_url = base_url
        self.session: Optional[aiohttp.ClientSession] = None # Сессия aiohttp будет инициализирована при первом использовании
        logger.info("✨ DiscordBindingsAPI клиент инициализирован.")

    async def _get_session(self) -> aiohttp.ClientSession:
        """Возвращает или создает сессию aiohttp."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
            logger.debug("Создана новая aiohttp.ClientSession.")
        return self.session

    async def _request(
        self,
        method: str,
        endpoint_path: str, # Это путь относительно BASE_PATH_ENTITIES
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Вспомогательный метод для выполнения HTTP-запросов.
        """
        session = await self._get_session()
        full_url = f"{self.base_url}{endpoint_path}" # Полный URL теперь формируется здесь
        logger.info(f"Отправляем запрос: {method} {full_url}")
        if payload:
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        try:
            async with session.request(method, full_url, json=payload, params=params) as response:
                logger.info(f"Получен HTTP-ответ со статусом: {response.status}")
                response.raise_for_status() # Выбрасывает исключение для статусов 4xx/5xx

                response_json = await response.json()
                logger.debug(f"API-ответ получен: {json.dumps(response_json, indent=2)}")
                return response_json
        except aiohttp.ClientConnectorError as e:
            logger.error(f"❌ Ошибка подключения к бэкенду по адресу {full_url}: {e}", exc_info=True)
            raise ConnectionError(f"Не удалось подключиться к бэкенду API: {e}") from e
        except aiohttp.ClientResponseError as e:
            error_details = await response.json() if response.content_type == 'application/json' else await response.text()
            logger.error(f"❌ Ошибка API {e.status} {e.message} от {full_url}: {error_details}", exc_info=True)
            raise ValueError(f"Ошибка API {e.status} {e.message}: {error_details}") from e
        except Exception as e:
            logger.error(f"❌ Непредвиденная ошибка при запросе к API {full_url}: {e}", exc_info=True)
            raise RuntimeError(f"Неизвестная ошибка при запросе к API: {e}") from e

    # Методы, соответствующие роутам discord_entity.py на бэкенде
    
    async def sync_discord_entities(self, guild_id: int, entities_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Отправляет пакет данных для синхронизации сущностей Discord.
        Соответствует: POST {BASE_PATH_ENTITIES}/sync
        Бэкенд ожидает {"guild_id": ..., "entities": [...]}.
        """
        payload = {"guild_id": guild_id, "entities": entities_data}
        logger.info(f"Отправляем данные для синхронизации Discord сущностей для гильдии {guild_id}.")
        return await self._request("POST", f"{BASE_PATH_ENTITIES}/sync", payload=payload)

    async def delete_discord_entities_batch(self, guild_id: int, discord_ids: List[int]) -> Dict[str, Any]:
        """
        Удаляет пачку сущностей Discord по их ID.
        Соответствует: DELETE {BASE_PATH_ENTITIES}/batch
        Бэкенд ожидает {"guild_id": ..., "discord_ids": [...]}.
        """
        payload = {"guild_id": guild_id, "discord_ids": discord_ids}
        logger.info(f"Отправляем запрос на массовое удаление Discord сущностей для гильдии {guild_id}, ID: {discord_ids}.")
        return await self._request("DELETE", f"{BASE_PATH_ENTITIES}/batch", payload=payload)

    async def create_single_discord_entity(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Создает одну сущность Discord.
        Соответствует: POST {BASE_PATH_ENTITIES}/create-one
        """
        logger.info(f"Отправляем запрос на создание одиночной Discord сущности: {entity_data.get('name', 'N/A')}.")
        return await self._request("POST", f"{BASE_PATH_ENTITIES}/create-one", payload=entity_data)

    async def get_discord_entities_by_guild(self, guild_id: int) -> Dict[str, Any]:
        """
        Получает список сущностей Discord для указанного guild_id.
        Соответствует: GET {BASE_PATH_ENTITIES}/{guild_id}
        """
        logger.info(f"Запрашиваем Discord сущности для гильдии {guild_id}.")
        return await self._request("GET", f"{BASE_PATH_ENTITIES}/{guild_id}")

    async def close_session(self):
        """Закрывает сессию aiohttp."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
            logger.info("aiohttp.ClientSession закрыта.")