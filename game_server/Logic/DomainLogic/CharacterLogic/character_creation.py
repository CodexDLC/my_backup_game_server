from sqlalchemy import text
from game_server.Logic.DomainLogic.CharacterLogic.utils.character_database_utils import fetch_starting_skills
from game_server.Logic.DomainLogic.CharacterLogic.utils.character_database_utils import insert_character_stats
from game_server.Logic.DomainLogic.CharacterLogic.utils.character_redis_utils import get_character_data_from_redis

from game_server.services.logging.logging_setup import logger
  

async def insert_character_metadata(character_id: int, metadata: dict, db_session):
    """
    Записывает основные параметры (characters): имя, раса, происхождение.
    :param character_id: ID персонажа.
    :param metadata: Словарь с параметрами (name, race_id, bloodline_id).
    :param db_session: Переданная сессия базы данных.
    """
    if not metadata:
        logger.warning(f"⚠ Пустые метаданные для персонажа {character_id}, пропускаем запись.")
        return

    query = text("""
        INSERT INTO characters (character_id, account_id, name, surname, bloodline_id, race_id, created_at, updated_at, is_deleted)
        VALUES (:character_id, :account_id, :name, :surname, :bloodline_id, :race_id, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, false)
    """)

    try:
        await db_session.execute(query, metadata)
        await db_session.commit()
        logger.info(f"✅ Метаданные персонажа {character_id} записаны!")
    except Exception as e:
        logger.error(f"❌ Ошибка записи метаданных персонажа {character_id}: {e}")
        raise


async def insert_character_base_skills(character_id: int, db_session):
    """
    Записывает стартовые навыки персонажа и сразу ставит их в состояние 'PAUSE'.
    
    :param character_id: ID персонажа.
    :param db_session: Переданная сессия базы данных.
    """
    skills = await fetch_starting_skills()

    if not skills:
        logger.warning(f"⚠ Нет стартовых навыков для персонажа {character_id}, пропускаем запись.")
        return

    character_skills = [
        {
            "character_id": character_id,
            "skill_key": skill["skill_key"],
            "level": 0,
            "xp": 0,
            "progress_state": "PAUSE"
        }
        for skill in skills
    ]

    query = text("""
        INSERT INTO character_skills (character_id, skill_key, level, xp, progress_state)
        VALUES (:character_id, :skill_key, :level, :xp, :progress_state)
    """)

    try:
        await db_session.execute(query, character_skills)
        await db_session.commit()
        logger.info(f"✅ Стартовые навыки записаны и установлены в 'PAUSE' для персонажа {character_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка записи навыков персонажа {character_id}: {e}")
        raise



async def finalize_character_creation(character_id: int, db_session, redis_client):
    """
    Финализирует создание персонажа, забирая данные из Redis и записывая их в БД.
    :param character_id: ID персонажа.
    :param db_session: Переданная сессия базы данных.
    :param redis_client: Переданный клиент Redis.
    """
    character_data = await get_character_data_from_redis(character_id, redis_client)
    if not character_data:
        logger.error(f"❌ Данные персонажа {character_id} отсутствуют в Redis! Финализация отменена.")
        return

    try:
        await insert_character_metadata(character_id, character_data.get("metadata", {}), db_session)
        await insert_character_stats(character_id, character_data.get("stats", {}), db_session)
        await insert_character_base_skills(character_id, db_session)
        logger.info(f"🎉 Персонаж {character_id} успешно финализирован и записан в БД!")
    except Exception as e:
        logger.error(f"❌ Ошибка финализации персонажа {character_id}: {e}")
        raise