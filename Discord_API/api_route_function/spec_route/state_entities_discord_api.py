import json
import aiohttp
from typing import List, Dict, Union
from Discord_API.config.logging.logging_setup import logger
from Discord_API.discord_settings import API_URL # Для более точной типизации возвращаемых значений

# Подгружаем актуальный URL API и логгер
# from Discord_API.settings import API_URL
# from Discord_API.config.logging.logging_setup import logger

BASE_PATH = "/discord"            # Базовый путь для Discord API
# from logging_setup import logger # Предполагаем, что logger уже настроен


async def get_all_entities_discord(guild_id: int) -> Dict:
    """Запрос на получение всех записей для гильдии и логирование данных."""
    if guild_id is None:
        logger.error("❌ Некорректный `guild_id`, отмена запроса на получение всех сущностей.")
        return {"error": "Некорректный guild_id"}

    url = f"{API_URL}{BASE_PATH}/entities/{guild_id}"
    logger.info(f"🛠 Отправляем GET запрос к API: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_json = await response.json()
                if response.status >= 400:
                    logger.error(f"❌ Ошибка получения всех сущностей от API: {response.status} - {response_json.get('detail', response_json)}")
                else:
                    logger.info(f"✅ Полученные данные от API: {response_json}")
                return response_json
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ Ошибка подключения к API ({url}): {e}")
        return {"error": f"Ошибка подключения к API: {e}"}
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при запросе всех сущностей: {e}", exc_info=True)
        return {"error": f"Непредвиденная ошибка: {e}"}


async def get_entity_by_primary_key_discord(guild_id: int, world_id: str, access_code: int) -> Dict:
    """Запрос на получение одной записи по полному первичному ключу."""
    if not all([guild_id, world_id, access_code]):
        logger.error("❌ Недостаточно данных для получения сущности по ПК.")
        return {"error": "Недостаточно данных."}

    url = f"{API_URL}{BASE_PATH}/entity_by_pk/{guild_id}/{world_id}/{access_code}"
    logger.info(f"🛠 Отправляем GET запрос к API: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response_json = await response.json()
                if response.status >= 400:
                    logger.error(f"❌ Ошибка получения сущности по ПК от API: {response.status} - {response_json.get('detail', response_json)}")
                else:
                    logger.info(f"✅ Получена сущность по ПК: {response_json}")
                return response_json
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ Ошибка подключения к API ({url}): {e}")
        return {"error": f"Ошибка подключения к API: {e}"}
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при запросе сущности по ПК: {e}", exc_info=True)
        return {"error": f"Непредвиденная ошибка: {e}"}


async def update_entity_discord(guild_id: int, world_id: str, access_code: int, entity_data: dict) -> Dict:
    """Запрос на обновление записи по полному первичному ключу."""
    if not all([guild_id, world_id, access_code, entity_data]):
        logger.error("❌ Недостаточно данных для обновления сущности: guild_id, world_id, access_code и entity_data обязательны.")
        return {"error": "Недостаточно данных для обновления."}

    url = f"{API_URL}{BASE_PATH}/update_by_pk/{guild_id}/{world_id}/{access_code}"
    logger.info(f"🛠 Отправляем PUT запрос к API: {url} с данными: {entity_data}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.put(url, json=entity_data) as response:
                response_json = await response.json()
                if response.status >= 400:
                    logger.error(f"❌ Ошибка обновления сущности в API: {response.status} - {response_json.get('detail', response_json)}")
                else:
                    logger.info(f"✅ Успешно обновлена сущность: {response_json}")
                return response_json
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ Ошибка подключения к API ({url}): {e}")
        return {"error": f"Ошибка подключения к API: {e}"}
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при обновлении сущности: {e}", exc_info=True)
        return {"error": f"Непредвиденная ошибка: {e}"}


async def delete_entity_discord(guild_id: int, world_id: str, access_code: int) -> Dict:
    """Запрос на удаление записи по полному первичному ключу."""
    if not all([guild_id, world_id, access_code]):
        logger.error("❌ Недостаточно данных для удаления сущности: guild_id, world_id, access_code обязательны.")
        return {"error": "Недостаточно данных для удаления."}

    url = f"{API_URL}{BASE_PATH}/delete_by_pk/{guild_id}/{world_id}/{access_code}"
    logger.info(f"🛠 Отправляем DELETE запрос к API: {url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(url) as response:
                response_json = await response.json()
                if response.status >= 400:
                    logger.error(f"❌ Ошибка удаления сущности в API: {response.status} - {response_json.get('detail', response_json)}")
                else:
                    logger.info(f"✅ Успешно удалена сущность: {response_json}")
                return response_json
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ Ошибка подключения к API ({url}): {e}")
        return {"error": f"Ошибка подключения к API: {e}"}
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при удалении сущности: {e}", exc_info=True)
        return {"error": f"Непредвиденная ошибка: {e}"}


async def create_roles_discord(roles_batch: List[Dict]) -> Dict:
    """Запрос на массовое добавление/обновление записей ролей в БД (UPSERT)."""
    if not roles_batch:
        logger.warning("Нет данных для массового добавления/обновления ролей.")
        return {"message": "Нет данных для обработки."}

    url = f"{API_URL}{BASE_PATH}/create_roles/" # Используем роут для create_roles
    logger.info(f"🛠 Отправляем POST запрос к API: {url} с {len(roles_batch)} записями.")
    # print(f"🚀 Перед отправкой в API (create_roles_discord): {json.dumps(roles_batch, indent=2, ensure_ascii=False)}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=roles_batch,
                headers={"Content-Type": "application/json"}
            ) as response:
                # print(f"🔍 Status (create_roles_discord): {response.status}")
                # print(f"🔍 Headers (create_roles_discord): {response.headers}")
                response_text = await response.text()
                # print(f"🔍 Response (create_roles_discord): {response_text}")

                try:
                    if "application/json" in response.headers.get("Content-Type", ""):
                        response_json = json.loads(response_text) # Используем json.loads для обработки текста
                        if response.status >= 400:
                            logger.error(f"❌ Ошибка массового добавления/обновления ролей в API: {response.status} - {response_json.get('detail', response_json)}")
                        else:
                            logger.info(f"✅ Успешно выполнено массовое добавление/обновление ролей: {response_json}")
                        return response_json
                    else:
                        logger.warning(f"⚠️ API вернул `text/plain` для create_roles_discord, возможно, ошибка формата: {response_text}")
                        return {"error": response_text}
                except json.JSONDecodeError as e:
                    logger.error(f"❌ Ошибка обработки JSON-ответа для create_roles_discord: {e}. Ответ: {response_text}", exc_info=True)
                    return {"error": response_text}
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ Ошибка подключения к API ({url}): {e}")
        return {"error": f"Ошибка подключения к API: {e}"}
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при массовом добавлении/обновлении ролей: {e}", exc_info=True)
        return {"error": f"Непредвиденная ошибка: {e}"}