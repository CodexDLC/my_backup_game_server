
from typing import Any, Dict, List
import aiohttp
from Discord_API.config.logging.logging_setup import logger
from Discord_API.discord_settings import API_URL



BASE_PATH = "/system/mapping"





async def get_all_entities() -> Dict[str, List[Any]]:
    """Запрос на получение всех записей `state_entities` из API.
    Ожидает API-ответ в формате: {"status": "success", "data": [...]}.
    """
    
    logger.info("🛠 Запрос `state_entities` для получения ролей...") # Или print()
    url = f"{API_URL}{BASE_PATH}/state-entities"
    logger.info(f"🛠 Отправляем запрос: {url}") # Или print()

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                logger.info(f"🛠 Получен HTTP-ответ со статусом: {response.status}") # Или print()
                response.raise_for_status() # Вызовет исключение для ошибок 4xx/5xx

                data = await response.json()
                logger.info(f"✅ API-ответ получен: {data}") # 🔥 Это ваш лог, который мы хотели увидеть

                # 🚀 Ожидаем, что data является словарем и содержит ключ 'data'
                if isinstance(data, dict) and "data" in data:
                    logger.debug(f"💡 Обнаружены данные в 'data' ключе: {len(data['data'])} записей.") # Или print()
                    return {"roles": data["data"]}
                else:
                    # ❌ Если API-ответ не соответствует ожидаемому формату {"status": ..., "data": ...}
                    logger.warning( # Или print()
                        f"⚠️ Ошибка! API-ответ имеет неожиданный формат. "
                        f"Ожидали dict с ключом 'data', получили {type(data)}: {data}"
                    )
                    return {"roles": []}

    except aiohttp.ClientError as e:
        logger.error(f"❌ Ошибка HTTP-запроса к {url}: {e}", exc_info=True) # Или print()
        return {"roles": []}
    except Exception as e:
        logger.error(f"❌ Непредвиденная ошибка при получении сущностей: {e}", exc_info=True) # Или print()
        return {"roles": []}




async def get_entity_by_access_code(access_code: int):
    """Запрос на получение записи `state_entities_discord` по `access_code`."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}{BASE_PATH}/state-entities/{access_code}") as response:
            return await response.json()


async def get_state_by_access_code(access_code: int):
    """Получить данные состояния по `access_code`."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/state-entities/{access_code}") as response:
            return await response.json()

async def update_state_status(access_code: int, is_active: bool):
    """Обновить статус состояния (`is_active`)."""
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{API_URL}/state-entities/{access_code}/status", json={"is_active": is_active}) as response:
            return await response.json()

# 🔄 Функции для `entity_state_map`
async def get_states(entity_access_key: str):
    """Получить состояния, привязанные к `entity_access_key`."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/entity-state-map/{entity_access_key}") as response:
            return await response.json()

async def create_state_mapping(entity_access_key: str, state_data: dict):
    """Привязать `access_code` к `entity_access_key`."""
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/entity-state-map/{entity_access_key}", json=state_data) as response:
            return await response.json()

async def update_state_mapping(entity_access_key: str, state_data: dict):
    """Обновить привязку состояния (`access_code` ↔ `entity_access_key`)."""
    async with aiohttp.ClientSession() as session:
        async with session.put(f"{API_URL}/entity-state-map/{entity_access_key}", json=state_data) as response:
            return await response.json()