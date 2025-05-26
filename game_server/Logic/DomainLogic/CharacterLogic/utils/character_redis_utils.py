import json
from game_server.settings import REDIS_URL
import aioredis
from game_server.services.logging.logging_setup import logger

# Подключаем Redis через переменную окружения
redis = aioredis.from_url(REDIS_URL)

# Настраиваем логгер
logger = logger.getLogger(__name__)

DEFAULT_TTL = 86400  # Данные хранятся 24 часа (86400 секунд)

async def update_character_data_in_redis(character_id: int, new_data: dict):
    """
    Постепенно обновляет данные персонажа в Redis, добавляя новые части информации.
    
    :param character_id: ID персонажа.
    :param new_data: Часть данных для обновления (например, из диалога).
    """
    if not new_data:  # Проверяем, есть ли новые данные
        logger.warning(f"⚠ Пустые данные для обновления персонажа {character_id}, пропускаем.")
        return

    redis_key = f"character:{character_id}"

    # Получаем текущие данные, если они есть
    character_data = await redis.get(redis_key)
    if character_data:
        character_data = json.loads(character_data)
    else:
        character_data = {}  # Если данных нет, создаём пустой объект

    # Объединяем старые и новые данные
    character_data.update(new_data)

    # Записываем обратно в Redis с TTL (время жизни данных)
    await redis.set(redis_key, json.dumps(character_data), ex=DEFAULT_TTL)

    logger.info(f"✅ Данные персонажа {character_id} обновлены в Redis: {new_data}")


async def get_character_data_from_redis(character_id: int) -> dict:
    """
    Получает данные персонажа из Redis перед записью в БД.
    
    :param character_id: ID персонажа.
    :return: Словарь с данными персонажа (метаданные + характеристики).
    """
    redis_key = f"character:{character_id}"
    character_data = await redis.get(redis_key)

    if not character_data:
        logger.warning(f"⚠ Данные персонажа {character_id} отсутствуют в Redis!")
        return {}

    parsed_data = json.loads(character_data)  
    logger.info(f"📥 Данные персонажа {character_id} загружены из Redis.")  # Логируем получение данных

    return parsed_data  # Преобразуем строку JSON в словарь
