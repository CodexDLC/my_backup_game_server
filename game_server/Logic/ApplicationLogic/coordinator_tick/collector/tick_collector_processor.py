# Logic/ApplicationLogic/tick_infra/collector/tick_collector_processor.py

from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.tick_logger import logger
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_in import AsyncDatabase

# --- ИМПОРТЫ ДЛЯ НОВОЙ ЛОГИКИ ---
# get_ready_characters находится в tick_collector_handler.py
# categorize_tasks_in_memory находится в tick_collector_handler.py
from game_server.Logic.ApplicationLogic.coordinator_tick.collector.handler.tick_collector_handler import (
    get_ready_characters, 
    categorize_tasks_in_memory, # Импортируем нашу новую функцию категоризации
    update_tick_info # update_tick_info все еще используется здесь
)

# Удаляем импорты устаревших функций, которые больше не используются:
# cleanup_tick_processing_queue, fetch_and_process_tasks, send_to_redis


async def collector_handler(db: AsyncDatabase) -> dict: # Удаляем tick_id, он не нужен здесь
    """
    Оркестратор сбора задач. Получает готовых персонажей из БД,
    категоризирует их и возвращает в виде словаря для TaskProcessor.
    Больше не взаимодействует с Redis напрямую.
    """
    logger.info("🔄 [auto_tick] Начало обработки тика")

    try:
        # 1. Получение готовых персонажей
        logger.debug("🔍 Запрос списка готовых персонажей...")
        active_sessions = await get_ready_characters(db)
        if not active_sessions:
            logger.info("✅ Нет готовых персонажей, обработка завершена.")
            return {} # Возвращаем пустой словарь, как и ранее
        logger.debug(f"👥 Найдено {len(active_sessions)} готовых персонажей.")

        # 2. Обновление `next_tick_at` для каждого персонажа в БД
        logger.debug("⏳ Обновление параметров тиков персонажей в БД...")
        # Убедимся, что active_sessions содержит словари с 'character_id'
        # Если active_sessions - это объекты SQLAlchemy, то char.character_id
        for session_obj in active_sessions:
            # Предполагаем, что session_obj - это объект SQLAlchemy с атрибутом character_id
            await update_tick_info(session_obj.character_id, db) 
        
        # 3. Категоризация задач в памяти
        # Используем categorize_tasks_in_memory, которая преобразует объекты сессий в словари
        logger.debug("📦 Категоризация и форматирование задач в памяти...")
        categorized_raw_tasks = categorize_tasks_in_memory(active_sessions) # Передаем объекты сессий
        
        logger.info(f"🏁 `collector_handler` успешно завершил обработку. Сформировано {len(categorized_raw_tasks)} категорий задач.")
        return categorized_raw_tasks # Возвращаем сгруппированные сырые задачи

    except Exception as e:
        logger.error(f"❌ Ошибка в `collector_handler`: {e}", exc_info=True)
        return {} # Возвращаем пустой словарь в случае ошибки