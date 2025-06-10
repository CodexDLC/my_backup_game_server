from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession


from game_server.Logic.ApplicationLogic.coordinator_tick.constant_tick import ALLOWED_TICK_TASKS
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.system.manager_tick_handler.ORM_Auto_Sessions import AutoSessionsManager
from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.tick_logger import logger
# Обратите внимание на новый импорт констант


async def get_ready_characters(db: AsyncSession) -> list:
    """Получает из БД список персонажей, готовых к тику."""
    return await AutoSessionsManager.get_ready_sessions(db)


async def update_tick_info(character_id: int, db: AsyncSession):
    """Обновляет next_tick_at для персонажа в БД."""
    await AutoSessionsManager.update_character_tick_time(character_id, db)


def categorize_tasks_in_memory(sessions: list) -> dict:
    """
    Принимает список объектов сессий SQLAlchemy и группирует их 
    по типу задачи в словарь.
    """
    logger.info(f"Начало категоризации {len(sessions)} сессий в памяти...")
    batched_tasks = defaultdict(list)

    for session in sessions:
        # --- ИСПРАВЛЕНИЕ ---
        # Используем правильное имя атрибута из модели: active_category
        task_type = session.active_category

        if task_type in ALLOWED_TICK_TASKS:
            # --- УЛУЧШЕНИЕ ---
            # Преобразуем объект SQLAlchemy в простой словарь для дальнейшей работы.
            # Это делает данные независимыми от сессии БД.
            session_data = {
                "character_id": session.character_id,
                "task_type": session.active_category,
                "last_tick_at": session.last_tick_at.isoformat()
                # Добавьте сюда другие поля из session, если они нужны воркерам
            }
            batched_tasks[task_type].append(session_data)
        else:
            logger.warning(
                f"Игнорируется задача неизвестного типа '{task_type}' для персонажа ID {session.character_id}")

    logger.info(f"Категоризация завершена. Сформировано {len(batched_tasks)} батчей.")
    return dict(batched_tasks)