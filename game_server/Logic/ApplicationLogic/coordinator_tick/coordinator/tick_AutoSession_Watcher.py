# Logic/ApplicationLogic/tick_infra/coordinator/tick_AutoSession_Watcher.py

import asyncio


from sqlalchemy.ext.asyncio import AsyncSession
from Logic.InfrastructureLogic.DataAccessLogic.db_instance import get_db_session
from Logic.InfrastructureLogic.app_cache.central_redis_client import redis_client
from Logic.InfrastructureLogic.DataAccessLogic.manager.system.manager_tick_handler.ORM_Auto_Sessions import AutoSessionsManager
from game_server.Logic.ApplicationLogic.coordinator_tick.constant_tick import COMMAND_RUN_COLLECTOR, COORDINATOR_CHANNEL
from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.task_utils import logger



async def run_watcher_check():
    """
    Выполняет один цикл проверки готовых к тику сессий.
    Если находит готовые сессии, отправляет команду Координатору.
    """
    db_session: AsyncSession = get_db_session()
    try:
        logger.info("Watcher-Worker: Запущен цикл проверки сессий.")

        # Проверяем, не идет ли уже обработка другого тика
        if await redis_client.get('tick_processed'):
            logger.info("Watcher-Worker: Тик уже в процессе. Проверка отложена.")
            return

        # Ищем в БД сессии, готовые к обработке
        ready_sessions = await AutoSessionsManager.get_ready_sessions(db_session)
        
        if ready_sessions:
            session_ids = [s.character_id for s in ready_sessions]
            logger.info(f"Watcher-Worker: Найдено {len(session_ids)} готовых сессий. Отправка команды '{COMMAND_RUN_COLLECTOR}'.")
            
            # Отправляем команду координатору
            await redis_client.publish(COORDINATOR_CHANNEL, COMMAND_RUN_COLLECTOR)
        else:
            logger.info("Watcher-Worker: Готовые сессии не найдены.")
            
    except Exception as e:
        logger.error(f"Watcher-Worker: Произошла ошибка при проверке сессий: {e}", exc_info=True)
    finally:
        await db_session.close()
        logger.info("Watcher-Worker: Цикл проверки завершен. Соединение с БД закрыто.")

# Этот блок выполнится, только если запустить файл напрямую: python tick_AutoSession_Watcher.py
if __name__ == "__main__":
    print("Запуск Watcher как одноразового воркера...")
    asyncio.run(run_watcher_check())
    print("Воркер Watcher завершил работу.")