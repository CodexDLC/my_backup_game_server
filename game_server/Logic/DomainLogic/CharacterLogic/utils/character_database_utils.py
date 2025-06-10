




import random
import time
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session
from game_server.services.logging.logging_setup import logger
from sqlalchemy import text




def generate_character_id(account_id: int) -> str:
    """
    Генерирует уникальный character_id на основе account_id, timestamp и случайного числа.
    
    :param account_id: ID аккаунта.
    :return: Структурированный character_id, например "123456-654321-23".
    """
    timestamp = int(time.time()) % 1000000  # Последние 6 цифр времени
    random_suffix = random.randint(10, 99)  # Случайный двухзначный код
    return f"{account_id}-{timestamp}-{random_suffix}"

async def fetch_starting_skills() -> list:
    """
    Получает список стартовых навыков из таблицы skills_library, включая skill_key.
    
    :return: Список навыков в виде словаря {skill_id, skill_key, name}.
    """
    query = text("SELECT skill_id, skill_key, name FROM skills_library")
    async with get_db_session() as session:
        try:
            result = await session.execute(query)
            rows = result.fetchall()
            skills = [dict(row) for row in rows]
            return skills
        except Exception as e:
            logger.error(f"Ошибка получения стартовых навыков: {e}")
            raise

