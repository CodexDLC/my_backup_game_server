


from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger

from game_server.Logic.DataAccessLogic.db_in import AsyncDatabase
from game_server.Logic.InfrastructureLogic.tick_infra.collector.handler.tick_collector_handler import (
    categorize_tasks, 
    cleanup_tick_processing_queue, 
    fetch_and_process_tasks, 
    get_ready_characters, 
    send_to_redis, 
    update_tick_info
    )


async def collector_handler(redis_client, tick_id, db: AsyncDatabase):
    """Следит за задачами, управляет подключением к БД и пробуждает координатор."""
    
    logger.info("🔄 [auto_tick] Начало обработки тика")  # ✅ Финальный `INFO` в начале

    try:
        # 🔍 Получение списка готовых персонажей
        logger.debug("🔍 Запрос списка готовых персонажей...")
        active_sessions = await get_ready_characters(db)

        if not active_sessions:
            logger.info("✅ Нет готовых персонажей, обработка завершена.")  # ✅ Финальный `INFO`
            return

        logger.debug(f"👥 Найдено {len(active_sessions)} готовых персонажей.")

        # 📤 Запись персонажей в Redis
        await send_to_redis(active_sessions, redis_client, tick_id)

        # ⏳ Обновление `next_tick_at` в БД
        logger.debug("⏳ Обновление параметров тиков персонажей...")
        for char in active_sessions:
            await update_tick_info(char['character_id'], db)

        # 🗑️ Очистка списка персонажей после обработки
        active_sessions.clear()
        logger.debug("🗑️ `active_sessions` очищены после обновления данных.")

        # 🔄 Обработка задач `tick_processing_queue`
        parsed_tasks = await fetch_and_process_tasks(redis_client)

        if not parsed_tasks:
            logger.info("✅ Нет задач для обработки, выход.")  # ✅ Финальный `INFO`
            return

        logger.debug(f"📦 Обработано {len(parsed_tasks)} задач, готовим их к распределению.")

        # 🔎 Категоризация задач
        task_groups = await categorize_tasks(parsed_tasks, redis_client)

        if not task_groups:
            logger.info("✅ Нет сформированных пакетов задач, выход.")  # ✅ Финальный `INFO`
            return

        logger.debug(f"🗃️ Сформировано {len(task_groups)} `batch_id`, записано в Redis.")

        # 🗑️ Очистка `tick_processing_queue`, если все задачи перенесены
        await cleanup_tick_processing_queue(redis_client)

        logger.info("🏁 `collector_handler` успешно завершил обработку.")  # ✅ Финальный `INFO`

    except Exception as e:
        logger.error(f"❌ Ошибка в `collector_handler`: {e}", exc_info=True)



