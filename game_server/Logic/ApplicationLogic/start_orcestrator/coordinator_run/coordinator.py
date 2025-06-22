import asyncio
from typing import Dict, Any, Optional, Type
from arq.connections import ArqRedis

# NEW IMPORTS: ConfigProvider (оставляем, если нужен)
from game_server.config.provider import config #

# Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager # ДОБАВЛЕНО

from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.coordinator_handler.auto_exploring_handler import AutoExploringHandler
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.coordinator_handler.auto_tick_handler import AutoLevelingHandler
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.coordinator_handler.base_handler import ICommandHandler
from game_server.Logic.InfrastructureLogic.messaging.message_bus import RedisMessageBus #
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger #

# ИМПОРТ ГЛОБАЛЬНЫХ КЛИЕНТОВ (для использования в handler_dependencies)
from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import arq_pool_manager #


class Coordinator:
    """
    Активный сервис-маршрутизатор. Слушает MessageBus и вызывает
    соответствующий класс-обработчик для каждой команды.
    """
    def __init__(
        self,
        message_bus: RedisMessageBus,
        app_cache_managers: Dict[str, Any],
        repository_manager: RepositoryManager # ДОБАВЛЕНО: Теперь Coordinator также принимает RepositoryManager
    ):
        self.message_bus = message_bus
        self.app_cache_managers = app_cache_managers
        self.repository_manager = repository_manager # ДОБАВЛЕНО: Сохраняем RepositoryManager

        # Зависимости, которые могут понадобиться обработчикам
        self.handler_dependencies = {
            "arq_redis_client": arq_pool_manager.arq_redis_pool,
            "central_redis_client": self.app_cache_managers.get("central_redis_client"),
            "reference_data_reader": self.app_cache_managers.get("reference_data_reader"),
            "task_queue_cache_manager": self.app_cache_managers.get("task_queue_cache_manager"), # Добавляем явно, если нужно
            "item_cache_manager": self.app_cache_managers.get("item_cache_manager"), # Пример: если item_cache_manager нужен
            "character_cache_manager": self.app_cache_managers.get("character_cache_manager"), # Пример: если character_cache_manager нужен
            "repository_manager": self.repository_manager, # ИЗМЕНЕНО: Передаем RepositoryManager            
            "logger": logger,
        }
        self.is_running = False
        self._subscription_task: Optional[asyncio.Task] = None

        self.command_handlers: Dict[str, Type[ICommandHandler]] = {
            config.constants.coordinator.COMMAND_PROCESS_AUTO_LEVELING: AutoLevelingHandler,
            config.constants.coordinator.COMMAND_PROCESS_AUTO_EXPLORING: AutoExploringHandler
        }
        logger.info("✅ Coordinator инициализирован с картой обработчиков.")

    async def start(self):
        if self.is_running: return
        self.is_running = True
        logger.info("Coordinator starting...")
        self._subscription_task = asyncio.create_task(self._subscribe_to_commands())
        logger.info("Coordinator has started successfully.")

    async def stop(self):
        if not self.is_running: return
        self.is_running = False
        logger.info("Coordinator stopping...")
        if self._subscription_task:
            self._subscription_task.cancel()
            try: await self._subscription_task
            except asyncio.CancelledError: pass
        logger.info("Coordinator has stopped.")

    async def _subscribe_to_commands(self):
        logger.info("Coordinator command subscription service started.")
        # config.constants.coordinator.COORDINATOR_COMMAND_QUEUE - это ваша очередь для команд
        async for message in self.message_bus.subscribe(config.constants.coordinator.COORDINATOR_COMMAND_QUEUE):
            await self.handle_command(message)

    async def handle_command(self, message: Dict[str, Any]):
        """
        Находит нужный обработчик по команде, создает его экземпляр и запускает.
        """
        payload = message.get("payload", {})
        command = payload.get("command")

        if not command:
            logger.warning(f"Received message without command: {message}")
            return

        logger.info(f"Coordinator handling command: {command}")

        handler_class = self.command_handlers.get(command)

        if handler_class:
            try:
                # Передаем весь словарь dependencies как ОДИН аргумент
                handler_instance = handler_class(self.handler_dependencies)
                await handler_instance.execute(payload) # Payload, вероятно, должен быть DTO
            except Exception as e:
                logger.error(f"Error executing handler for command '{command}': {e}", exc_info=True)
        else:
            logger.warning(f"No handler found for command: {command}")