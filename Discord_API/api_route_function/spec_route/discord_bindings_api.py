# Discord_API\api_route_function\spec_route\discord_bindings_api.py

import json
import aiohttp
from typing import List, Dict, Any, Optional

from Discord_API.discord_settings import API_URL # Ваш базовый URL API
from Discord_API.config.logging.logging_setup import logger # Ваш настроенный логгер

# Базовый путь для привязок Discord API
# 🔥 Обновлено на /discord/bindings (без слеша в конце, чтобы легко добавлять подпути)
BASE_PATH = "/discord/bindings"

class DiscordAPIClientError(Exception):
    """Кастомное исключение для ошибок при взаимодействии с Discord API."""
    pass

async def upsert_discord_bindings_api(bindings_data: List[Dict]) -> Dict[str, Any]:
    """
    Выполняет UPSERT (вставку/обновление) привязок Discord через API.
    Соответствует роуту POST /discord/bindings/upsert.

    Args:
        bindings_data (List[Dict]): Список словарей с данными привязок.

    Returns:
        Dict[str, Any]: Ответ от API (например, {"status": "success", ...}).

    Raises:
        DiscordAPIClientError: Если произошла ошибка при HTTP-запросе или в ответе API.
    """
    # 🔥 Обновленный URL для роута UPSERT
    url = f"{API_URL}{BASE_PATH}/upsert" 
    
    json_data = json.dumps(bindings_data, ensure_ascii=False)
    logger.debug(f"🚀 Отправка UPSERT запроса в API: {url} с данными: {json_data[:200]}...") # Ограничим вывод для больших данных

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=json_data, headers={"Content-Type": "application/json"}) as response:
                logger.info(f"🔍 Получен ответ от API. Статус: {response.status} для {url}")
                response_json = {}
                try:
                    response_json = await response.json()
                    logger.debug(f"🔍 Ответ API: {response_json}")
                except aiohttp.ContentTypeError:
                    response_text = await response.text()
                    logger.error(f"❌ Ошибка: Ответ API не является JSON. Статус: {response.status}, Текст: {response_text}")
                    raise DiscordAPIClientError(f"API вернул не-JSON ответ. Статус: {response.status}, Текст: {response_text}")

                if 200 <= response.status < 300: # Успешные статусы (2xx)
                    return response_json
                else:
                    # Обрабатываем ошибки, которые API может вернуть (например, HTTPException)
                    error_detail = response_json.get("detail", "Неизвестная ошибка API")
                    logger.error(f"❌ API вернул ошибку. Статус: {response.status}, Детали: {error_detail}")
                    raise DiscordAPIClientError(f"API вернул ошибку: {response.status} - {error_detail}")

    except aiohttp.ClientError as e:
        logger.error(f"❌ Ошибка сетевого запроса к API {url}: {e}", exc_info=True)
        raise DiscordAPIClientError(f"Ошибка подключения к API: {e}") from e
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при UPSERT привязок: {e}", exc_info=True)
        raise DiscordAPIClientError(f"Непредвиденная ошибка: {e}") from e


async def get_discord_binding_api(guild_id: int, access_key: str) -> Optional[Dict[str, Any]]:
    """
    Получает одну привязку Discord через API.
    Соответствует роуту GET /discord/bindings/{guild_id}/{access_key}.
    """
    url = f"{API_URL}{BASE_PATH}/{guild_id}/{access_key}"
    logger.debug(f"🚀 Отправка GET запроса в API: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                logger.info(f"🔍 Получен ответ от API. Статус: {response.status} для {url}")
                if response.status == 404:
                    logger.info(f"Привязка не найдена для guild_id={guild_id}, access_key='{access_key}'.")
                    return None # Возвращаем None, если привязка не найдена
                
                response_json = await response.json() # Ожидаем JSON или ContentTypeError
                if 200 <= response.status < 300:
                    return response_json.get("data") # Наш API роут возвращает {"status": "found", "data": binding}
                else:
                    error_detail = response_json.get("detail", "Неизвестная ошибка API")
                    raise DiscordAPIClientError(f"API вернул ошибку: {response.status} - {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Ошибка сетевого запроса к API {url}: {e}", exc_info=True)
        raise DiscordAPIClientError(f"Ошибка подключения к API: {e}") from e
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при получении привязки: {e}", exc_info=True)
        raise DiscordAPIClientError(f"Непредвиденная ошибка: {e}") from e

async def get_all_discord_bindings_api(guild_id: int) -> List[Dict[str, Any]]: # 🔥 ДОБАВЛЕН guild_id
    """
    Получает ВСЕ существующие привязки Discord для указанной гильдии через API.
    Соответствует роуту GET /discord/bindings/guild/{guild_id}/all.
    """
    url = f"{API_URL}{BASE_PATH}/guild/{guild_id}/all" # 🔥 ИСПРАВЛЕННЫЙ URL
    logger.debug(f"🚀 Отправка GET запроса в API для получения всех привязок: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                logger.info(f"🔍 Получен ответ от API. Статус: {response.status} для {url}")
                
                response_json = await response.json()
                if 200 <= response.status < 300:
                    return response_json.get("data", []) 
                else:
                    error_detail = response_json.get("detail", "Неизвестная ошибка API")
                    raise DiscordAPIClientError(f"API вернул ошибку: {response.status} - {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Ошибка сетевого запроса к API {url}: {e}", exc_info=True)
        raise DiscordAPIClientError(f"Ошибка подключения к API: {e}") from e
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при получении всех привязок: {e}", exc_info=True)
        raise DiscordAPIClientError(f"Непредвиденная ошибка: {e}") from e


async def delete_discord_binding_api(guild_id: int, access_key: str) -> bool:
    """
    Удаляет привязку Discord через API.
    Соответствует роуту DELETE /discord/bindings/{guild_id}/{access_key}.
    Возвращает True, если удалено, False если не найдено.
    """
    url = f"{API_URL}{BASE_PATH}/{guild_id}/{access_key}"
    logger.debug(f"🚀 Отправка DELETE запроса в API: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                logger.info(f"🔍 Получен ответ от API. Статус: {response.status} для {url}")
                if response.status == 200:
                    return True # Успешное удаление
                elif response.status == 404:
                    return False # Не найдено для удаления
                else:
                    response_json = {}
                    try:
                        response_json = await response.json()
                    except aiohttp.ContentTypeError:
                        pass # Может быть не-JSON ответ
                    error_detail = response_json.get("detail", "Неизвестная ошибка API")
                    raise DiscordAPIClientError(f"API вернул ошибку при удалении: {response.status} - {error_detail}")
    except aiohttp.ClientError as e:
        logger.error(f"❌ Ошибка сетевого запроса к API {url}: {e}", exc_info=True)
        raise DiscordAPIClientError(f"Ошибка подключения к API: {e}") from e
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при удалении привязки: {e}", exc_info=True)
        raise DiscordAPIClientError(f"Непредвиденная ошибка: {e}") from e

# Старые функции update_binding и get_binding (по guild_id без access_key)
# удалены, так как они не соответствуют новой логике API роутов и менеджмента.