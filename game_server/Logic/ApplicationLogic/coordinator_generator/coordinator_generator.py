# Logic/ApplicationLogic/coordinator_generator/coordinator_generator.py

import asyncio
import logging
from typing import Callable, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

# --- Импорты ---
from game_server.Logic.ApplicationLogic.coordinator_generator.generator_settings import *
from game_server.Logic.ApplicationLogic.coordinator_generator.template_generator_character.character_template_planner import CharacterTemplatePlanner
from game_server.Logic.ApplicationLogic.coordinator_generator.data_processing.creature_type_data_orchestrator import CreatureTypeDataOrchestrator
from game_server.Logic.ApplicationLogic.coordinator_generator.template_generator_item.item_template_planner import ItemTemplatePlanner
from game_server.Logic.ApplicationLogic.coordinator_generator.constant.constant_generator import *
from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import AsyncSessionLocal
from game_server.Logic.ApplicationLogic.coordinator_generator.load_seeds.seeds_manager import SeedsManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE, ITEM_GENERATION_WORKER_QUEUE_NAME, REDIS_TASK_INITIAL_TTL_SECONDS

from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data_cache_manager import ReferenceDataCacheManager
from game_server.Logic.InfrastructureLogic.celery.task.tasks_item_generation import process_item_generation_batch_task
from game_server.database.models import models
from game_server.services.logging.logging_setup import logger
from game_server.Logic.InfrastructureLogic.celery.task.tasks_character_generation import process_character_generation_batch_task
from game_server.Logic.InfrastructureLogic.messaging.rabbit_utils import TaskDispatcher




class GeneratorCoordinator:
    """
    Координатор Генераторов, работающий через архитектуру app_cache.
    """

    def __init__(self):
        """Конструктор больше не принимает и не зависит от Redis."""
        
        self.async_session_factory: Callable[[], AsyncSession] = AsyncSessionLocal
        self.creature_type_orchestrator: Optional[CreatureTypeDataOrchestrator] = None

        self.reference_data_cache_manager = ReferenceDataCacheManager(
            async_session_factory=self.async_session_factory
        )
        self.item_template_planner = ItemTemplatePlanner(
            async_session_factory=self.async_session_factory
        )
        self.character_template_planner = CharacterTemplatePlanner(
            async_session_factory=self.async_session_factory
        )
        self.task_dispatcher = TaskDispatcher()

        self.is_prestart_completed = False
        self.runtime_mode_active = False
        logger.info("✨ Координатор Генераторов инициализирован.")

    # Все остальные методы (_run_seeds_script, _cache_reference_data, и т.д.)
    # остаются БЕЗ ИЗМЕНЕНИЙ. Они просто вызывают методы тех объектов,
    # которые мы так чисто инициализировали выше.
    async def _run_seeds_script(self) -> bool:
        logger.info("⚙️ Шаг 1: Запуск скрипта загрузки метаданных (Seeds)...")
        try:
            async with self.async_session_factory() as session:
                seeds_manager = SeedsManager(session)
                await seeds_manager.import_seeds(models)
            logger.info("✅ Шаг 1: Загрузка метаданных завершена успешно.")
            return True
        except Exception as e:
            logger.critical(f"🚨 Шаг 1: Ошибка при загрузке метаданных: {e}", exc_info=True)
            return False

    async def _cache_reference_data(self) -> bool:
        logger.info("⚙️ Шаг 2: Загрузка справочных данных из БД в Redis-кэш...")
        try:
            await self.reference_data_cache_manager.cache_all_reference_data()
            logger.info("✅ Шаг 2: Справочные данные успешно закэшированы в Redis.")
            return True
        except Exception as e:
            logger.critical(f"🚨 Шаг 2: Ошибка при кэшировании справочных данных: {e}", exc_info=True)
            return False
            
    async def initialize_data_loaders(self) -> bool:
        logger.info("⚙️ Инициализация загрузчиков данных для генераторов...")
        try:
            async with self.async_session_factory() as session:
                self.creature_type_orchestrator = CreatureTypeDataOrchestrator(session)
                await self.creature_type_orchestrator.load_raw_data()
                await self.creature_type_orchestrator.process_data_for_generators()
            logger.info("✅ Загрузчики данных генераторов успешно инициализированы и данные обработаны.")
            return True
        except Exception as e:
            logger.critical(f"🚨 Ошибка при инициализации загрузчиков данных генераторов: {e}", exc_info=True)
            return False

    async def _run_level_1_generators(self) -> bool:
        logger.info("⚙️ Шаг 3: Запуск планировщиков шаблонов 1 уровня...")
        try:
            logger.info("➡️ Запуск планировщика для шаблонов ПРЕДМЕТОВ...")
            item_tasks = await self.item_template_planner.check_and_prepare_generation_tasks()
            if item_tasks:
                await self.task_dispatcher.process_and_dispatch_tasks(
                    task_list=item_tasks,
                    batch_size=TEMPLATE_GENERATION_BATCH_SIZE,
                    redis_task_key_template=ITEM_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                    redis_ttl_seconds=REDIS_TASK_INITIAL_TTL_SECONDS, # <--- 🔥 ДОБАВЛЕНО 🔥
                    celery_queue_name=ITEM_GENERATION_WORKER_QUEUE_NAME,
                    celery_task_callable=process_item_generation_batch_task,
                    task_type_name="предметов"
                )
            else:
                logger.info("Планировщик предметов не нашел задач для генерации.")

            logger.info("➡️ Запуск планировщика для шаблонов ПЕРСОНАЖЕЙ...")
            if not self.creature_type_orchestrator:
                logger.error("🚨 Оркестратор данных для персонажей не инициализирован.")
                return False
            
            playable_races_list = self.creature_type_orchestrator.get_playable_race_list()
            if not playable_races_list:
                logger.warning("⚠️ Список игровых рас пуст. Планирование персонажей пропускается.")
            else:
                character_tasks = await self.character_template_planner.pre_process(
                    playable_races_data=playable_races_list,
                    desired_gender_ratio=DEFAULT_CHARACTER_GENDER_RATIO
                )
                if character_tasks:
                    await self.task_dispatcher.process_and_dispatch_tasks(
                        task_list=character_tasks,
                        batch_size=CHARACTER_GENERATION_MAX_BATCH_SIZE,
                        redis_task_key_template=CHARACTER_GENERATION_REDIS_TASK_KEY_TEMPLATE,
                        redis_ttl_seconds=REDIS_TASK_INITIAL_TTL_SECONDS, # <--- 🔥 ДОБАВЛЕНО 🔥
                        celery_queue_name=CHARACTER_GENERATION_WORKER_QUEUE_NAME,
                        celery_task_callable=process_character_generation_batch_task,
                        task_type_name="персонажей"
                    )
                else:
                    logger.info("Планировщик персонажей не нашел задач для генерации.")
            
            logger.info("✅ Шаг 3: Планировщики шаблонов 1 уровня завершили свою работу.")
            return True
        except Exception as e:
            logger.critical(f"🚨 Шаг 3: Ошибка при запуске планировщиков 1 уровня: {e}", exc_info=True)
            return False

    async def pre_start_mode(self):
        """
        Первый режим работы Координатора Генераторов: Предстартовая подготовка шаблонов.
        Включает механизм повторных попыток для критических шагов.
        """
        logger.info("🚀 Координатор Генераторов входит в ПРЕДСТАРТОВЫЙ РЕЖИМ (Pre-Start Mode)...")

        # 1. Запуск скрипта нулевого уровня (загрузка/обновление БД из YAML) с повторными попытками
        attempt = 0
        while attempt < MAX_TASK_RETRY_ATTEMPTS:
            logger.info(f"🔁 Попытка {attempt + 1}/{MAX_TASK_RETRY_ATTEMPTS} запуска скрипта Seeds...")
            if await self._run_seeds_script():
                break
            else:
                attempt += 1
                if attempt < MAX_TASK_RETRY_ATTEMPTS:
                    logger.warning(f"❌ Ошибка в Шаге 1. Повторная попытка через 5 секунд...")
                    await asyncio.sleep(5)
                else:
                    logger.critical(f"🚨 Предстартовый режим завершился с ошибкой: не удалось обновить базовые метаданные в БД после {MAX_TASK_RETRY_ATTEMPTS} попыток.")
                    return False

        # 2. Загрузка данных из БД в Redis-кэш с повторными попытками
        attempt = 0
        while attempt < MAX_TASK_RETRY_ATTEMPTS:
            logger.info(f"🔁 Попытка {attempt + 1}/{MAX_TASK_RETRY_ATTEMPTS} кэширования справочных данных...")
            if await self._cache_reference_data():
                break
            else:
                attempt += 1
                if attempt < MAX_TASK_RETRY_ATTEMPTS:
                    logger.warning(f"❌ Ошибка в Шаге 2. Повторная попытка через 5 секунд...")
                    await asyncio.sleep(5)
                else:
                    logger.critical(f"🚨 Предстартовый режим завершился с ошибкой: не удалось закэшировать справочные данные после {MAX_TASK_RETRY_ATTEMPTS} попыток.")
                    return False
        
        # 3. Инициализация загрузчиков данных для планировщиков с повторными попытками
        attempt = 0
        while attempt < MAX_TASK_RETRY_ATTEMPTS:
            logger.info(f"🔁 Попытка {attempt + 1}/{MAX_TASK_RETRY_ATTEMPTS} инициализации загрузчиков данных...")
            if await self.initialize_data_loaders():
                break
            else:
                attempt += 1
                if attempt < MAX_TASK_RETRY_ATTEMPTS:
                    logger.warning(f"❌ Ошибка в инициализации загрузчиков данных. Повторная попытка через 5 секунд...")
                    await asyncio.sleep(5)
                else:
                    logger.critical(f"🚨 Предстартовый режим завершился с ошибкой: не удалось инициализировать загрузчики данных после {MAX_TASK_RETRY_ATTEMPTS} попыток.")
                    return False

        # 4. Асинхронный запуск планировщиков шаблонов 1 уровня с повторными попытками
        attempt = 0
        while attempt < MAX_TASK_RETRY_ATTEMPTS:
            logger.info(f"🔁 Попытка {attempt + 1}/{MAX_TASK_RETRY_ATTEMPTS} запуска планировщиков шаблонов 1 уровня...")
            if await self._run_level_1_generators():
                break
            else:
                attempt += 1
                if attempt < MAX_TASK_RETRY_ATTEMPTS:
                    logger.warning(f"❌ Ошибка в Шаге 3. Повторная попытка через 5 секунд...")
                    await asyncio.sleep(5)
                else:
                    logger.critical(f"🚨 Предстартовый режим завершился с ошибкой: не удалось запустить планировщики шаблонов 1 уровня после {MAX_TASK_RETRY_ATTEMPTS} попыток.")
                    return False

        self.is_prestart_completed = True
        logger.info("✅ Предстартовый режим завершён. Координатор Генераторов готов к переходу в РАБОЧИЙ РЕЖИМ.")
        logger.info("⌛ Ожидание команды на старт основного рабочего процесса...")
        return True


    async def start_runtime_mode(self):
        if not self.is_prestart_completed:
            logger.warning("⚠️ Невозможно перейти в рабочий режим: предстартовая подготовка не завершена.")
            return

        logger.info("🟢 Координатор Генераторов переходит в РАБОЧИЙ РЕЖИМ (Runtime Mode).")
        self.runtime_mode_active = True
        
        while self.runtime_mode_active:
            # Здесь будет логика чтения из Redis очереди команд или pub/sub
            await asyncio.sleep(5)
        logger.info("🔴 Координатор Генераторов вышел из РАБОЧЕГО РЕЖИМА.")

    async def _process_runtime_command(self, command: str):
        logger.info(f"Получена команда в рабочем режиме: {command}")
        # Здесь будет логика вызова соответствующих планировщиков "на лету"


async def main_generator_coordinator():
    logger.info("🚀 Запуск Главного Координатора Генераторов...")
    # redis_client = CentralRedisClient() # Эту строку можно убрать, так как global central_redis_client уже есть и используется
    coordinator = GeneratorCoordinator() # <--- ИЗМЕНЕНО: Аргумент redis_client удален

    success_prestart = await coordinator.pre_start_mode()
    if success_prestart:
        await coordinator.start_runtime_mode()
    else:
        logger.error("❌ Главный Координатор Генераторов завершился из-за ошибок в предстартовом режиме.")


if __name__ == "__main__":
    asyncio.run(main_generator_coordinator())