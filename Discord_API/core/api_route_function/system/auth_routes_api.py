
# Discord_API\core\api_route_function\system\auth_routes_api.py

import uuid
from typing import Dict, Any, List, Optional
import aiohttp # Используем aiohttp для асинхронных запросов

# Импортируем наш централизованный логгер бота
from Discord_API.config.logging.logging_setup_discod import logger as bot_logger
logger = bot_logger.getChild(__name__) # Получаем дочерний логгер

from Discord_API.discord_settings import API_URL # API_URL = http://fast_api:8000


class DiscordAuthAPIClient: # Переименовал класс для ясности, что это клиент API
    """
    Тонкий клиент для взаимодействия с API аутентификации на стороне бэкенда.
    Отправляет запросы и возвращает сырые ответы, обработка логики ответа происходит выше.
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
        endpoint_path: str, # Это путь относительно base_url, например "/auth/register_or_login"
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]: # Возвращает сырой JSON ответ
        """
        Вспомогательный асинхронный метод для выполнения HTTP-запросов.
        Просто отправляет запрос и выбрасывает исключение для статусов 4xx/5xx.
        Дальнейшая обработка ответа (успех/ошибка, парсинг данных) происходит в вызывающем коде.
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint_path}"
        logger.info(f"Отправляем запрос: {method} {url}")
        
        try:
            async with session.request(method, url, json=payload, headers=headers) as response:
                logger.info(f"Получен HTTP-ответ со статусом: {response.status}")
                # Просто вызываем raise_for_status() для обработки стандартных HTTP ошибок
                response.raise_for_status() 

                response_json = await response.json()
                # Мы просто возвращаем JSON, не анализируя его на success/error
                return response_json
        
        except aiohttp.ClientConnectorError as e:
            logger.error(f"❌ Ошибка подключения к бэкенду по адресу {url}: {e}", exc_info=True)
            raise ConnectionError(f"Не удалось подключиться к бэкенду API: {e}")
        except aiohttp.ClientResponseError as e:
            # При 4xx/5xx aiohttp.ClientResponseError уже содержит статус и сообщение
            error_details = await response.json() if response.content_type == 'application/json' else await response.text()
            logger.error(f"❌ Ошибка API {e.status} {e.message} от {url}: {error_details}", exc_info=True)
            # Перебрасываем эту ошибку, чтобы она была обработана вызывающим кодом
            raise ValueError(f"Ошибка API {e.status} {e.message}: {error_details}") # Преобразуем в ValueError для единообразия, но можно и просто re-raise ClientResponseError
        except Exception as e:
            logger.error(f"❌ Непредвиденная ошибка при запросе к API {url}: {e}", exc_info=True)
            raise RuntimeError(f"Неизвестная ошибка при запросе к API: {e}")

    # --- Методы, соответствующие роутам auth_routes.py ---

    async def register_or_login_account(
        self,
        identifier_type: str,
        identifier_value: str,
        username: str,
        avatar: Optional[str] = None,
        locale: Optional[str] = None,
        region: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Отправляет запрос на регистрацию или логин аккаунта.
        Соответствует: POST /auth/register_or_login
        Возвращает сырой JSON-ответ от API.
        """
        payload = {
            "identifier_type": identifier_type,
            "identifier_value": identifier_value,
            "username": username,
            "avatar": avatar,
            "locale": locale,
            "region": region,
        }
        return await self._request("POST", "/auth/register_or_login", payload=payload)


    async def get_player_data(self, auth_token: str) -> Dict[str, Any]:
        """
        Отправляет запрос на получение полных данных игрока.
        Соответствует: GET /auth/player_data
        Возвращает сырой JSON-ответ от API.
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        return await self._request("GET", "/auth/player_data", headers=headers)

    async def generate_linking_url(self, auth_token: str) -> Dict[str, Any]:
        """
        Отправляет запрос на генерацию ссылки для привязки аккаунта.
        Соответствует: GET /auth/generate_linking_url
        Возвращает сырой JSON-ответ от API.
        """
        headers = {"Authorization": f"Bearer {auth_token}"}
        return await self._request("GET", "/auth/generate_linking_url", headers=headers)
    
    async def close_session(self):
        """Закрывает сессию aiohttp."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

# --- Методы из вашего исходного кода, которые НЕ ИМЕЮТ прямых аналогов в текущем auth_routes.py ---
# Я закомментировал их, потому что роуты для них в auth_routes.py не существуют.
# Если эти роуты нужны, их нужно сначала создать на бэкенде.

# def update_account(self, update_data: dict):
#     # Роута PUT/PATCH /auth/update_account нет в auth_routes.py
#     payload = {
#         "identifier_type": self.identifier_type,
#         "identifier_value": self.identifier_value,
#         "update_data": update_data,
#     }
#     return self.send_to_api("update_account", payload)

# def delete_account(self):
#     # Роута DELETE /auth/delete_account нет в auth_routes.py
#     payload = {
#         "identifier_type": self.identifier_type,
#         "identifier_value": self.identifier_value,
#     }
#     return self.send_to_api("delete_account", payload)

# async def get_account_discord(user_id: str):
#     # Это был GET запрос с телом, что не типично.
#     # Ближайший аналог для проверки существования/логина - это register_or_login_account.
#     # Для получения данных о пользователе - get_player_data (но он требует токен).
#     # Если нужен простой GET по user_id без токена, на бэкенде нужен отдельный роут.
#     # payload = {"identifier_type": "discord_id", "identifier_value": user_id}
#     # response = requests.get(f"{API_URL}/get_account", json=payload)
#     # return response.json()
#     pass