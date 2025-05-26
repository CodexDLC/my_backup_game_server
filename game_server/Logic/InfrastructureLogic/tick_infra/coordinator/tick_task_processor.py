import asyncio
from game_server.Logic.InfrastructureLogic.tick_infra.tick_utils.tick_logger import logger
from game_server.app_cache.redis_client import RedisClient
from game_server.Logic.InfrastructureLogic.tick_infra.coordinator.handler.task_processor_handler import process_tasks



class TaskProcessor:
    """Оптимизированный обработчик задач с интеграцией в Coordinator"""
    
    def __init__(self, coordinator=None, redis=None):
        """
        :param coordinator: Ссылка на родительский Coordinator
        :param redis: Опционально - существующее подключение к Redis
        """
        self.coordinator = coordinator
        self.redis = redis or RedisClient()
        self._using_external_redis = redis is not None

    async def run(self):
        """Основной цикл обработки с улучшенной интеграцией"""
        try:
            logger.info("🚀 [START] TaskProcessor проверяет очередь...")
            
            if await self._should_process():
                await self._full_processing_cycle()
            else:
                logger.info("💤 Нет задач, завершаем работу")
                
        except Exception as e:
            logger.error(f"❌ Ошибка в TaskProcessor: {str(e)}")
            await self._notify_failure()
        finally:
            await self._cleanup_resources()

    async def _should_process(self) -> bool:
        """Проверка необходимости обработки"""
        batch_status_all = await self.redis.hgetall("batch_status")
        return any(status == "initiation" for status in batch_status_all.values())

    async def _full_processing_cycle(self):
        """Полный цикл обработки задач"""
        logger.info("✅ Задачи найдены! Начинаем обработку...")
        
        await self._set_coordinator_status("new_tasks", True)
        await process_tasks(self.redis)
        await self._transition_to_next_stage()
        
        logger.info("🏁 Обработка задач завершена")

    async def _transition_to_next_stage(self):
        """Переход к следующему этапу обработки"""
        await self._set_coordinator_status("new_tasks", False)
        
        if self.coordinator:
            await self.coordinator.handle_command("check_report")
        else:
            await self.redis.publish("coordinator_channel", "check_report")

    async def _set_coordinator_status(self, status_name: str, value: bool):
        """Унифицированная установка статуса"""
        await self.redis.set(f"coordinator:{status_name}", "true" if value else "false")

    async def _notify_failure(self):
        """Уведомление о сбое"""
        if self.coordinator:
            await self.coordinator.handle_command("process_failed")
        else:
            await self.redis.publish("coordinator_channel", "process_failed")

    async def _cleanup_resources(self):
        """Очистка ресурсов"""
        if not self._using_external_redis:
            await self.redis.close()