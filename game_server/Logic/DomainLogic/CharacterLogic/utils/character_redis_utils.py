import json
from game_server.services.logging.logging_setup import logger

# Настраиваем логгер

DEFAULT_TTL = 86400  # Данные хранятся 24 часа (86400 секунд)

async def update_character_data_in_redis(redis_client, character_id: int, new_data: dict):
    """
    Обновляет данные персонажа в Redis, добавляя новые части информации.
    
    :param redis_client: Асинхронный клиент Redis.
    :param character_id: ID персонажа.
    :param new_data: Часть данных для обновления (например, из диалога).
    """
    if not new_data:  
        logger.warning(f"⚠ Пустые данные для обновления персонажа {character_id}, пропускаем.")
        return

    redis_key = f"character:{character_id}"

    # Получаем текущие данные
    character_data = await redis_client.get(redis_key)
    character_data = json.loads(character_data) if character_data else {}

    # Объединяем старые и новые данные
    character_data.update(new_data)

    # Записываем обратно в Redis с TTL
    await redis_client.set(redis_key, json.dumps(character_data), ex=DEFAULT_TTL)

    logger.info(f"✅ Данные персонажа {character_id} обновлены в Redis: {new_data}")


async def get_character_data_from_redis(redis_client, character_id: int) -> dict:
    """
    Получает данные персонажа из Redis перед записью в БД.
    
    :param redis_client: Асинхронный клиент Redis.
    :param character_id: ID персонажа.
    :return: Словарь с данными персонажа.
    """
    redis_key = f"character:{character_id}"
    character_data = await redis_client.get(redis_key)

    if not character_data:
        logger.warning(f"⚠ Данные персонажа {character_id} отсутствуют в Redis!")
        return {}

    parsed_data = json.loads(character_data)  
    logger.info(f"📥 Данные персонажа {character_id} загружены из Redis.")

    return parsed_data  
