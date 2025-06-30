# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/coordinator_pre_start.py
import asyncio
from typing import List, Type, Dict, Any

from game_server.config.settings.process.prestart import MAX_TASK_RETRY_ATTEMPTS
from game_server.config.logging.logging_setup import app_logger as logger

from .handlers.base_step_handler import IPreStartStepHandler
from .handlers.seeds_handler import SeedsHandler
from .handlers.cache_handler import CacheReferenceDataHandler
from .handlers.data_loaders_handler import InitializeDataLoadersHandler
from .handlers.level1_generators_handler import RunLevel1GeneratorsHandler

from arq import ArqRedis
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

# 🔥 ИЗМЕНЕНИЕ: Импортируем правильные классы
from .template_generator_item.item_template_planner import ItemTemplatePlanner
from .template_generator_character.character_template_planner import CharacterTemplatePlanner
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader


class GeneratorPreStart:
    def __init__(
        self,
        repository_manager: RepositoryManager,
        app_cache_managers: Dict[str, Any],
        arq_redis_pool: ArqRedis
    ):
        self.is_prestart_completed = False
        self.logger = logger
        self.repository_manager = repository_manager
        self.app_cache_managers = app_cache_managers
        self.arq_redis_pool = arq_redis_pool

        # --- 🔥 ИЗМЕНЕНИЕ: Получаем правильные зависимости из app_cache_managers ---
        redis_batch_store: RedisBatchStore = self.app_cache_managers.get("redis_batch_store")
        central_redis_client: Any = self.app_cache_managers.get("central_redis_client")
        reference_data_reader: IReferenceDataReader = self.app_cache_managers.get("reference_data_reader")

        # Проверяем, что все зависимости получены
        if not all([redis_batch_store, central_redis_client, reference_data_reader]):
            raise RuntimeError("Не удалось получить один или несколько обязательных кэш-менеджеров (redis_batch_store, central_redis_client, reference_data_reader).")

        # --- 🔥 ИЗМЕНЕНИЕ: Инициализируем планировщики с правильными зависимостями ---
        item_planner = ItemTemplatePlanner(
            repository_manager=self.repository_manager,
            central_redis_client=central_redis_client,
            reference_data_reader=reference_data_reader,
            redis_batch_store=redis_batch_store # Передаем redis_batch_store
        )
        character_planner = CharacterTemplatePlanner(
            repository_manager=self.repository_manager,
            redis_batch_store=redis_batch_store # Передаем redis_batch_store
        )

        # --- 🔥 ИЗМЕНЕНИЕ: Собираем обновленный словарь зависимостей для обработчиков ---
        self.handler_dependencies: Dict[str, Any] = {
            "arq_redis_client": self.arq_redis_pool,
            "repository_manager": self.repository_manager,
            "logger": self.logger,
            "item_template_planner": item_planner,
            "character_template_planner": character_planner,
            "reference_data_cache_manager": self.app_cache_managers.get("reference_data_cache_manager"),
            "redis_client": central_redis_client,
            "reference_data_reader": reference_data_reader,
            "redis_batch_store": redis_batch_store, # Добавляем redis_batch_store
        }

        self.startup_pipeline: List[Type[IPreStartStepHandler]] = [
            SeedsHandler,
            CacheReferenceDataHandler,
            InitializeDataLoadersHandler,
            RunLevel1GeneratorsHandler
        ]
        self.logger.debug("✨ Координатор Генераторов (v2) инициализирован с конвейером задач.")

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
