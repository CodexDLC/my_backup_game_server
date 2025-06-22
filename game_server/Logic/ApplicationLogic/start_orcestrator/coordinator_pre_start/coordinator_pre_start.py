import asyncio
from typing import List, Type, Dict, Any
# from sqlalchemy.ext.asyncio import AsyncSession # УДАЛЕНО

from game_server.config.settings.process.prestart import MAX_TASK_RETRY_ATTEMPTS
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

from .handlers.base_step_handler import IPreStartStepHandler
from .handlers.seeds_handler import SeedsHandler
from .handlers.cache_handler import CacheReferenceDataHandler
from .handlers.data_loaders_handler import InitializeDataLoadersHandler
from .handlers.level1_generators_handler import RunLevel1GeneratorsHandler

# Импортируем менеджер пула ARQ (arq_pool_manager)
# УДАЛЕНО: from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import arq_pool_manager # Не нужен, если arq_redis_pool передается

# Импорты для типизации
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.task_queue_cache_manager import TaskQueueCacheManager
from arq import ArqRedis # Для типизации arq_redis_pool

# Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager # ДОБАВЛЕНО

# Классы, которые мы будем инициализировать внутри
from .template_generator_item.item_template_planner import ItemTemplatePlanner
from .template_generator_character.character_template_planner import CharacterTemplatePlanner


class GeneratorPreStart:
    def __init__(
        self,
        repository_manager: RepositoryManager,
        app_cache_managers: Dict[str, Any],
        arq_redis_pool: ArqRedis # <--- ДОБАВЛЕНО: Теперь принимаем arq_redis_pool
    ):
        self.is_prestart_completed = False
        self.logger = logger
        self.repository_manager = repository_manager
        self.app_cache_managers = app_cache_managers
        self.arq_redis_pool = arq_redis_pool # <--- ДОБАВЛЕНО: Сохраняем


        self.logger.critical(f"DEBUG: В GeneratorPreStart.__init__, reference_data_cache_manager: {self.app_cache_managers.get('reference_data_cache_manager')}")
        self.logger.critical(f"DEBUG: В GeneratorPreStart.__init__, central_redis_client_instance: {self.app_cache_managers.get('central_redis_client')}")

        # Получаем необходимые менеджеры из app_cache_managers
        task_queue_cache_manager: TaskQueueCacheManager = self.app_cache_managers.get("task_queue_cache_manager")
        central_redis_client: Any = self.app_cache_managers.get("central_redis_client")
        reference_data_reader: Any = self.app_cache_managers.get("reference_data_reader")
        # arq_redis_pool: ArqRedis = arq_pool_manager.arq_redis_pool # <--- УДАЛЕНО: Теперь получаем из аргументов


        item_planner = ItemTemplatePlanner(
            repository_manager=self.repository_manager,
            central_redis_client=central_redis_client,
            reference_data_reader=reference_data_reader,
            task_queue_cache_manager=task_queue_cache_manager,
            arq_redis_pool=self.arq_redis_pool # <--- ИЗМЕНЕНО: Используем self.arq_redis_pool
        )
        character_planner = CharacterTemplatePlanner(
            repository_manager=self.repository_manager,
            task_queue_cache_manager=task_queue_cache_manager,
            arq_redis_pool=self.arq_redis_pool # <--- ИЗМЕНЕНО: Используем self.arq_redis_pool
        )

        self.handler_dependencies: Dict[str, Any] = {
            "arq_redis_client": self.arq_redis_pool, # <--- ИЗМЕНЕНО: Используем self.arq_redis_pool
            "repository_manager": self.repository_manager,
            "logger": self.logger,
            "item_template_planner": item_planner,
            "character_template_planner": character_planner,
            "reference_data_cache_manager": self.app_cache_managers.get("reference_data_cache_manager"),
            "redis_client": central_redis_client,
            "reference_data_reader": reference_data_reader,
            "task_queue_cache_manager": task_queue_cache_manager,
        }

        self.startup_pipeline: List[Type[IPreStartStepHandler]] = [
            SeedsHandler,
            CacheReferenceDataHandler,
            InitializeDataLoadersHandler,
            RunLevel1GeneratorsHandler
        ]
        self.logger.debug("✨ Координатор Генераторов инициализирован с конвейером задач.")

    async def execute_step_with_retries(self, handler_class: Type[IPreStartStepHandler]) -> bool:
        """ Утилита для выполнения одного шага с логикой повторных попыток. """
        attempt = 0
        handler_instance = handler_class(self.handler_dependencies)

        while attempt < MAX_TASK_RETRY_ATTEMPTS:
            self.logger.debug(f"🔁 Попытка {attempt + 1}/{MAX_TASK_RETRY_ATTEMPTS} запуска шага '{handler_class.__name__}'...")
            if await handler_instance.execute():
                return True

            attempt += 1
            if attempt < MAX_TASK_RETRY_ATTEMPTS:
                self.logger.warning(f"❌ Ошибка в шаге '{handler_class.__name__}'. Повтор через 5 секунд...")
                await asyncio.sleep(5)

        self.logger.critical(f"🚨 Предстартовый режим завершился с ошибкой: не удалось выполнить шаг '{handler_class.__name__}' после {MAX_TASK_RETRY_ATTEMPTS} попыток.")
        return False

    async def pre_start_mode(self) -> bool:
        """
        Главный метод, который последовательно запускает все шаги из конвейера.
        """
        self.logger.debug("🚀 Координатор Генераторов входит в ПРЕДСТАРТОВЫЙ РЕЖИМ...")

        for step_handler_class in self.startup_pipeline:
            if not await self.execute_step_with_retries(step_handler_class):
                return False

        self.is_prestart_completed = True
        self.logger.debug("✅ Предстартовый режим завершён.")
        return True