import asyncio
import os
import time
from game_server.Logic.DataAccessLogic.db_in import AsyncDatabase
from game_server.Logic.DomainLogic.Services.random_pool_logic import RandomPoolManager
from game_server.Logic.InfrastructureLogic.tick_infra.collector.tick_collector import Collector
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.task_utils import finish_active_tasks
from game_server.app_cache.redis_client import RedisClient
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.tick_report_processor import ReportProcessor
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.tick_Clean_Processor import CleanProcessor
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.tick_task_processor import TaskProcessor
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.tick_failed_processor import TickFailedProcessor
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.tick_coordinator_listener import CoordinatorListener
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.tick_AutoSession_Watcher import AutoSessionWatcher
from game_server.settings import DATABASE_URL_SYNC, REDIS_URL

class Coordinator:
    def __init__(self):
        self.db = AsyncDatabase(DATABASE_URL_SYNC)
        self.listener = CoordinatorListener()  
        self.watcher = AutoSessionWatcher()
        self.current_status = "sleeping"        
        self.is_busy = False
        self.active_tasks = set()
        self.lock = asyncio.Lock()
        self.redis = RedisClient()  # ✅ Инкапсулированный клиент
        self._collector_lock = asyncio.Lock()
        self.watcher_task = None

        
    async def init_redis(self):
        """Инициализация и проверка подключения Redis через клиент."""
        if not await self.redis.ping():  # ✅ Используем публичный метод
            logger.error("Ошибка подключения к Redis: сервер не отвечает")
            raise ConnectionError("Redis connection failed")    

    async def start(self):
     
        logger.info("🟢 Инициализация статусов координатора...")
        init_statuses = {
            "shutdown": False,
            "new_tasks": False,
            "check_report": False,
            "process_failed": False,
            "finish_report": False
        }
        for status, value in init_statuses.items():
            await self.set_status_coordinator(status, value)
            logger.info(f"✅ Статус `{status}` установлен в `{value}`")

        logger.info("🔄 Запуск AutoSessionWatcher...")
        await self.start_watcher()

        logger.info("🔄 Подключение слушателя...")
        await self.listener.connect()
        logger.info("✅ Слушатель подключен")

        logger.info("🎧 Ожидание команд...")
        await self.listener.listen(self.handle_command)
        logger.info("✅ Слушатель команд успешно запущен")

    async def start_watcher(self):
        """Запускает watcher и следит за ним"""
        if self.watcher_task and not self.watcher_task.done():
            logger.warning("⚠️ Watcher уже запущен, перезапуск не требуется")
            return

        self.watcher_task = await self.watcher.start()        

    async def restart_watcher(self):
        """Принудительно перезапускает Watcher"""
        logger.warning("♻️ Перезапуск AutoSessionWatcher...")
        if self.watcher_task:
            self.watcher_task.cancel()  # ❌ Останавливаем старый процесс
        await self.start_watcher()  # 🔄 Запускаем новый

    async def handle_command(self, command):
        async with self.lock:
            
            if command == "run_collector":  # Новый тип команды
                if self.is_busy:
                    return
                self.is_busy = True
                try:
                    tick_id = str(int(time.time()))
                    async with Collector(DATABASE_URL_SYNC).lifecycle() as col:
                        await col.run_collector(tick_id)
                finally:
                    self.is_busy = False
                return            
            
            logger.info(f"Получена команда: {command}")
            if command == "shutdown":
                await self.set_status_coordinator("shutdown", True)
                await self.shutdown()
                return

            if self.is_busy:
                logger.warning(f"Команда '{command}' проигнорирована: координатор занят")
                return

            self.is_busy = True
            try:
                processor = None
                status_key = ""

                if command == "new_tasks":
                    status_key = "new_tasks"
                    processor = TaskProcessor()
                elif command == "check_report":
                    status_key = "check_report"
                    processor = ReportProcessor(coordinator=self)
                elif command == "process_failed":
                    status_key = "process_failed"
                    processor = TickFailedProcessor()
                elif command == "clean":
                    status_key = "finish_report"
                    processor = CleanProcessor()
                else:
                    logger.warning(f"Неизвестная команда: {command}")
                    return

                await self.set_status_coordinator(status_key, True)

                task = asyncio.create_task(
                    processor.run() if hasattr(processor, 'run') else
                    processor.process_report() if hasattr(processor, 'process_report') else
                    processor.process_failed() if hasattr(processor, 'process_failed') else
                    processor.cleanup()
                )

                def task_done_callback(t):
                    self.active_tasks.discard(t)
                    logger.debug(f"Задача {t.get_name()} завершена")

                task.add_done_callback(task_done_callback)
                self.active_tasks.add(task)
                task.set_name(f"{command}_task_{id(task)}")

            except Exception as e:
                logger.error(f"Ошибка при обработке команды {command}: {e}", exc_info=True)
                await self.set_status_coordinator(status_key, False)
                raise
            finally:
                self.is_busy = False

                
    async def _collector_runner(self, tick_id: int) -> None:
        """Обёртка для запуска Collector с lifecycle."""
        async with Collector().lifecycle() as col:
            await col.run_collector(tick_id)

    async def set_status_coordinator(self, status_name: str, value: bool):
        val_str = "true" if value else "false"
        key = f"coordinator:{status_name}"
        await self.redis.set(key, val_str)
        logger.debug(f"Установлен статус {key} = {val_str}")

    async def shutdown(self):
        logger.info("Начат процесс остановки координатора...")
        await self.set_status_coordinator("sleeping", True)

        if self.active_tasks:
            logger.info(f"Завершение {len(self.active_tasks)} активных задач...")
            await finish_active_tasks(self.redis)

        await self.listener.shutdown()
        await self.set_status_coordinator("stopped", True)
        logger.info("✅ Координатор полностью остановлен")


async def main():
    coord = Coordinator()
    await coord.init_redis()

    await coord.start()


if __name__ == "__main__":
    asyncio.run(main())




