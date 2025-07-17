# game_server/core/di_modules/world_orchestrator_bindings.py

import inject
import logging
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from pymongo.database import Database # Для типа 'mongo_database_obj'

# Импорты World Orchestrator
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_cache.services.item.item_cache_manager import ItemCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import IWorldStateRepository, ILocationStateRepository
from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import ArqQueueService
# from game_server.config.provider import config # Больше не нужен здесь, если константы импортируются напрямую в классах

# Импорты обработчиков PreStartCoordinator
from game_server.Logic.ApplicationLogic.world_orchestrator.pre_start.handlers.data_loaders_handler import DataLoadersHandler
from game_server.Logic.ApplicationLogic.world_orchestrator.pre_start.handlers.template_planners_handler import TemplatePlannersHandler
from game_server.Logic.ApplicationLogic.world_orchestrator.pre_start.handlers.world_generation_handler import WorldGenerationHandler

# Импорты обработчиков RuntimeCoordinator
from game_server.Logic.ApplicationLogic.world_orchestrator.runtime.handlers.auto_exploring_handler import AutoExploringHandler
from game_server.Logic.ApplicationLogic.world_orchestrator.runtime.handlers.auto_leveling_handler import AutoLevelingHandler
from game_server.Logic.ApplicationLogic.world_orchestrator.runtime.runtime_coordinator import RuntimeCoordinator

# Импорты зависимостей, которые нужны World Orchestrator
# PostgreSQL Repositories - ТЕПЕРЬ ИНЖЕКТИРУЕМ ФАБРИКИ РЕПОЗИТОРИЕВ
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository, ICharacterSkillRepository, ICharacterSpecialRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    IAbilityRepository, IBackgroundStoryRepository, ICreatureTypeRepository, IMaterialRepository,
    IModifierLibraryRepository, IPersonalityRepository, ISkillRepository, ICreatureTypeInitialSkillRepository, IStaticItemTemplateRepository,
    ISuffixRepository
)
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository, IEquipmentTemplateRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository, IStateEntityRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository, IXpTickDataRepository


# Импорт PreStartCoordinator
from game_server.Logic.ApplicationLogic.world_orchestrator.pre_start.coordinator_pre_start import PreStartCoordinator
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
# from game_server.config.settings.character.generator_settings import CHARACTER_TEMPLATE_QUALITY_CONFIG, TARGET_POOL_QUALITY_DISTRIBUTION # Теперь импортируются в классах
# from game_server.config.settings.process.prestart import CHARACTER_GENERATION_MAX_BATCH_SIZE, CHARACTER_POOL_TARGET_SIZE # Теперь импортируются в классах
# from game_server.config.settings.redis_setting import BATCH_TASK_TTL_SECONDS # Теперь импортируются в классах

# Импорты классов, в которые инжектируем репозитории
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.character_generator.handler_utils.creature_type_data_orchestrator import CreatureTypeDataOrchestrator
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.character_generator.template_generator_character.character_template_planner import CharacterTemplatePlanner
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.item_generator.item_template_planner import ItemTemplatePlanner
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.load_kesh_database.load_seeds.reference_data_loader import ReferenceDataLoader
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.load_kesh_database.load_seeds.seeds_manager import SeedsManager
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.world_map_generator.world_map_generator import WorldMapGenerator
from game_server.Logic.CoreServices.services.world_map_service import WorldMapService

from game_server.Logic.ApplicationLogic.world_orchestrator.workers.character_generator.character_batch_processor import CharacterBatchProcessor

# 🔥 ДОБАВЛЕНО: Импорты реализаций MongoDB репозиториев (с правильными именами)
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.world_state_repository_mongo_impl import MongoWorldStateRepositoryImpl, MongoLocationStateRepositoryImpl
from game_server.config.constants.item import DEFAULT_RARITY_LEVEL, MATERIAL_COMPATIBILITY_RULES
from game_server.config.settings.process.prestart import ITEM_GENERATION_BATCH_SIZE
from game_server.config.settings.redis_setting import BATCH_TASK_TTL_SECONDS


def configure_world_orchestrators(binder):
    """
    Конфигурирует связывания для оркестраторов мира.
    Теперь все привязки используют bind_to_constructor, если статические константы импортируются напрямую в классах.
    """
    # ArqQueueService
    binder.bind_to_constructor(ArqQueueService, ArqQueueService)
    
    # CreatureTypeDataOrchestrator
    binder.bind_to_constructor(CreatureTypeDataOrchestrator, CreatureTypeDataOrchestrator)

    # ReferenceDataLoader
    binder.bind_to_constructor(ReferenceDataLoader, ReferenceDataLoader)

    # SeedsManager
    binder.bind_to_constructor(SeedsManager, SeedsManager)

    # CharacterTemplatePlanner (теперь bind_to_constructor, если константы импортируются напрямую)
    binder.bind_to_constructor(CharacterTemplatePlanner, CharacterTemplatePlanner)

    # ItemTemplatePlanner (теперь bind_to_constructor, если константы импортируются напрямую)
    binder.bind_to_constructor(ItemTemplatePlanner, ItemTemplatePlanner)  
    
    # CharacterBatchProcessor
    binder.bind_to_constructor(CharacterBatchProcessor, CharacterBatchProcessor)

    # WorldMapGenerator
    binder.bind_to_constructor(WorldMapGenerator, WorldMapGenerator)

    # WorldMapService
    binder.bind_to_constructor(WorldMapService, WorldMapService)

    # --- Runtime Orchestrator Components ---

    # RuntimeCoordinator
    binder.bind_to_constructor(RuntimeCoordinator, RuntimeCoordinator)

    # AutoExploringHandler
    binder.bind_to_constructor(AutoExploringHandler, AutoExploringHandler)

    # AutoLevelingHandler
    binder.bind_to_constructor(AutoLevelingHandler, AutoLevelingHandler)

    # --- Прочие компоненты ---

    # DataLoadersHandler
    binder.bind_to_constructor(DataLoadersHandler, DataLoadersHandler)

    # TemplatePlannersHandler
    binder.bind_to_constructor(TemplatePlannersHandler, TemplatePlannersHandler)

    # WorldGenerationHandler
    binder.bind_to_constructor(WorldGenerationHandler, WorldGenerationHandler)

    binder.bind('batch_task_ttl', BATCH_TASK_TTL_SECONDS)
    binder.bind('item_generation_batch_size', ITEM_GENERATION_BATCH_SIZE)
    binder.bind('default_rarity_level', DEFAULT_RARITY_LEVEL)
    binder.bind('material_compatibility_rules', MATERIAL_COMPATIBILITY_RULES)