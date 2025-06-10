from sqlalchemy.ext.asyncio import AsyncSession

import logging


from game_server.Logic.DomainLogic.CharacterLogic.utils.character_database_utils import fetch_starting_skills


from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.database.models.models import CharacterSkills, Character




logger = logging.getLogger(__name__)

async def insert_character_metadata(character_id: int, metadata: dict, db_session: AsyncSession):
    """
    Записывает основные параметры персонажа (`characters`).
    :param character_id: ID персонажа.
    :param metadata: Словарь с параметрами (name, race_id, bloodline_id).
    :param db_session: Асинхронная сессия базы данных.
    """
    if not metadata:
        logger.warning(f"⚠ Пустые метаданные для персонажа {character_id}, пропускаем запись.")
        return

    new_character = Character(
        character_id=character_id,
        account_id=metadata.get("account_id"),
        name=metadata.get("name", "Безымянный"),
        surname=metadata.get("surname"),
        bloodline_id=metadata.get("bloodline_id"),
        race_id=metadata.get("race_id"),
        is_deleted=False
    )

    db_session.add(new_character)
    try:
        await db_session.commit()
        logger.info(f"✅ Метаданные персонажа {character_id} записаны!")
    except Exception as e:
        logger.error(f"❌ Ошибка записи метаданных персонажа {character_id}: {e}")
        raise


async def insert_character_base_skills(character_id: int, db_session: AsyncSession):
    """
    Записывает стартовые навыки персонажа (`character_skills`) и ставит их в состояние 'PAUSE'.
    :param character_id: ID персонажа.
    :param db_session: Асинхронная сессия базы данных.
    """
    skills = await fetch_starting_skills()

    if not skills:
        logger.warning(f"⚠ Нет стартовых навыков для персонажа {character_id}, пропускаем запись.")
        return

    character_skills = [
        CharacterSkills(
            character_id=character_id,
            skill_key=skill["skill_key"],
            level=0,
            xp=0,
            progress_state="PAUSE"
        )
        for skill in skills
    ]

    db_session.add_all(character_skills)
    try:
        await db_session.commit()
        logger.info(f"✅ Стартовые навыки записаны для персонажа {character_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка записи навыков персонажа {character_id}: {e}")
        raise



async def finalize_character_creation(character_id: int, db_session: AsyncSession, redis_client: CentralRedisClient):
    """
    Финализирует создание персонажа, забирая данные из Redis и записывая их в БД.
    :param character_id: ID персонажа.
    :param db_session: Асинхронная сессия базы данных.
    :param redis_client: Асинхронный Redis-клиент.
    """
    character_data = await redis_client.get_json(f"character:{character_id}")
    
    if not character_data:
        logger.error(f"❌ Данные персонажа {character_id} отсутствуют в Redis! Финализация отменена.")
        return

    try:
        await insert_character_metadata(character_id, character_data.get("metadata", {}), db_session)
        await insert_character_base_skills(character_id, db_session)
        logger.info(f"🎉 Персонаж {character_id} успешно финализирован и записан в БД!")
    except Exception as e:
        logger.error(f"❌ Ошибка финализации персонажа {character_id}: {e}")
        raise
