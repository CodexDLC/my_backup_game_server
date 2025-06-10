# Logic/ApplicationLogic/tick_infra/collector/tick_collector.py



# Импортируем наш обновленный обработчик
from game_server.Logic.ApplicationLogic.coordinator_tick.collector.tick_collector_processor import collector_handler
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_in import AsyncDatabase

from game_server.Logic.ApplicationLogic.coordinator_tick.tick_utils.tick_logger import logger


class Collector:
    """
    Упрощенный класс-обертка для запуска процесса сбора задач.
    Больше не управляет состоянием или жизненным циклом соединений.
    Его единственная задача — вызвать обработчик и вернуть результат.
    """

    async def run_collector(self) -> dict:
        """
        Основной метод, который выполняет полный цикл сбора задач.
        1. Устанавливает соединение с БД на время выполнения.
        2. Вызывает обработчик-оркестратор `collector_handler`.
        3. Возвращает результат (словарь с батчами) напрямую Координатору.
        """
        logger.info("Collector: Запуск run_collector...")

        try:
            # Используем контекстный менеджер для сессии БД,
            # чтобы соединение гарантированно открылось и закрылось.
            async with AsyncDatabase() as db:
                # collector_handler выполняет всю работу и возвращает результат
                task_batches = await collector_handler(db)
                
                if task_batches:
                    logger.info(f"Collector: Успешно получено {len(task_batches)} батчей от обработчика.")
                else:
                    logger.info("Collector: Обработчик не вернул задач для обработки.")
                    
                return task_batches
                
        except Exception as e:
            logger.error(f"Collector: Критическая ошибка на уровне run_collector: {e}", exc_info=True)
            # В случае полного провала возвращаем пустой словарь,
            # чтобы не сломать вызывающую логику в Координаторе.
            return {}