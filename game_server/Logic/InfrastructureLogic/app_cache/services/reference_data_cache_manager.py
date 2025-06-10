# game_server/Logic/InfrastructureLogic/app_cache/redis_handler/reference_data_cache_manager.py

import json
import logging
from typing import Callable, Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import redis.exceptions 

# Импортируем наш глобальный экземпляр клиента
from game_server.Logic.ApplicationLogic.coordinator_generator.load_seeds.item_base_loader import ItemBaseLoader
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.data.ORM_background_stories_manager import BackgroundStoryManager
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.data.ORM_inventory_rule_generator import InventoryRuleGeneratorManager
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.data.ORM_personality_mager import PersonalityManager
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.data.ORM_skills_mager import SkillsManager
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.iten_templates_generator.ORM_materials import MaterialManager
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.iten_templates_generator.ORM_modifier_library import ModifierLibraryManager
from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.iten_templates_generator.ORM_suffixes import SuffixManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import central_redis_client
# Импорты констант и остального остаются без изменений
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_constants import (
    DEFAULT_TTL_STATIC_REF_DATA,
    REDIS_KEY_GENERATOR_BACKGROUND_STORIES,
    REDIS_KEY_GENERATOR_INVENTORY_RULES,
    REDIS_KEY_GENERATOR_ITEM_BASE,
    REDIS_KEY_GENERATOR_MATERIALS,
    REDIS_KEY_GENERATOR_MODIFIERS,
    REDIS_KEY_GENERATOR_PERSONALITIES,
    REDIS_KEY_GENERATOR_SKILLS,
    REDIS_KEY_GENERATOR_SUFFIXES, 
    # ... и остальные константы
)
# ... все остальные импорты ...

logger = logging.getLogger(__name__)

class ReferenceDataCacheManager:
    def __init__(self, async_session_factory: Callable[[], AsyncSession]):
        self.async_session_factory = async_session_factory
        self.item_base_loader = ItemBaseLoader()
        # 🔥 ИЗМЕНЕНИЕ: Делаем зависимость от Redis явной, как в других менеджерах.
        # Теперь класс хранит ссылку на клиент внутри себя.
        self.redis = central_redis_client
        logger.info("✅ Сервис кэширования справочных данных инициализирован.")

    async def _cache_data_as_hash(self, redis_key: str, data_list: List[Any], id_field: str, ttl_seconds: Optional[int] = 2592000): # DEFAULT_TTL_STATIC_REF_DATA):
        try:
            # 🔥 ИЗМЕНЕНИЕ: Используем self.redis вместо глобального клиента
            await self.redis.delete(redis_key)
            # Удалены логи об удалении ключа, так как это внутренняя деталь

            if not data_list:
                logger.warning(f"⚠️ Пустой список данных для ключа Redis: {redis_key}. Ключ был удален и операции HSET не будет.")
                return

            # 🔥 ИЗМЕНЕНИЕ: Используем self.redis вместо глобального клиента
            async with self.redis.pipeline() as pipe:
                cached_count = 0
                for item in data_list:
                    try:
                        if isinstance(item, dict):
                            item_dict = item
                        else:
                            # Предполагается, что item имеет атрибут __table__.columns
                            item_dict = {c.name: getattr(item, c.name) for c in item.__table__.columns}

                        item_id = item_dict.get(id_field)
                        if item_id is None:
                            logger.error(f"Объект без поля ID '{id_field}' не может быть кэширован для ключа: {redis_key}. Объект: {str(item_dict)[:200]}...")
                            continue

                        json_value = json.dumps(item_dict, default=str)
                        pipe.hset(redis_key, str(item_id), json_value)
                        cached_count += 1
                    except Exception as e:
                        logger.critical(f"Критическая ошибка при подготовке элемента для кэша Redis ({redis_key}, ID: {item_id}): {e}", exc_info=True)

                # Удалены логи о выполнении пайплайна и фактическом количестве
                await pipe.execute()

            if ttl_seconds is not None:
                # 🔥 ИЗМЕНЕНИЕ: Используем self.redis вместо глобального клиента
                await self.redis.expire(redis_key, ttl_seconds)
                # Удален лог об установке TTL

            # Оставляем только одну итоговую, информативную строку
            logger.info(f"Успешно кэшировано {cached_count} элементов в Redis под ключом {redis_key} (TTL: {ttl_seconds}s).")

        except Exception as e: # Общий блок для RedisError и других ошибок
            logger.critical(f"Критическая ошибка при кэшировании данных в Redis для ключа {redis_key}: {e}", exc_info=True)


    # Все остальные методы (`cache_item_data_from_db`, `cache_all_reference_data` и т.д.)
    # остаются БЕЗ ИЗМЕНЕНИЙ, так как они вызывают `_cache_data_as_hash`, 
    # который мы уже исправили.

    async def cache_item_data_from_db(self):
        logger.info("Кэширование данных предметов из БД...")
        async with self.async_session_factory() as session:
            materials_data = await session.run_sync(lambda sync_session: MaterialManager(sync_session).get_all_materials())
            await self._cache_data_as_hash(REDIS_KEY_GENERATOR_MATERIALS, materials_data, 'material_code')
            
            suffixes_data = await session.run_sync(lambda sync_session: SuffixManager(sync_session).get_all_suffixes())
            await self._cache_data_as_hash(REDIS_KEY_GENERATOR_SUFFIXES, suffixes_data, 'suffix_code')
            
            modifiers_data = await session.run_sync(lambda sync_session: ModifierLibraryManager(sync_session).get_all_modifiers())
            await self._cache_data_as_hash(REDIS_KEY_GENERATOR_MODIFIERS, modifiers_data, 'modifier_code')
        logger.info("Данные предметов из БД кэшированы.")
    
    async def cache_skills(self):
        logger.info("Кэширование навыков...")
        async with self.async_session_factory() as session:
            data = await SkillsManager(session).get_all_skills()
            await self._cache_data_as_hash(REDIS_KEY_GENERATOR_SKILLS, data, 'skill_key')
        logger.info("Навыки кэшированы.")

    async def cache_background_stories(self):
        logger.info("Кэширование предысторий...")
        async with self.async_session_factory() as session:
            data = await BackgroundStoryManager(session).get_all_background_stories()
            await self._cache_data_as_hash(REDIS_KEY_GENERATOR_BACKGROUND_STORIES, data, 'story_id')
        logger.info("Предыстории кэшированы.")

    async def cache_personalities(self):
        logger.info("Кэширование личностей...")
        async with self.async_session_factory() as session:
            data = await PersonalityManager(session).get_all_personalities()
            await self._cache_data_as_hash(REDIS_KEY_GENERATOR_PERSONALITIES, data, 'personality_id')
        logger.info("Личности кэшированы.")

    async def cache_inventory_rules(self):
        logger.info("Кэширование шаблонов правил генерации...")
        async with self.async_session_factory() as session:
            data = await InventoryRuleGeneratorManager(session).get_all()
            await self._cache_data_as_hash(REDIS_KEY_GENERATOR_INVENTORY_RULES, data, 'rule_key')
        logger.info("Шаблоны правил генерации кэшированы.")

    async def cache_all_reference_data(self) -> bool:
        logger.info("Начало кэширования всех справочных данных в Redis.")
        try:
            item_bases_from_yaml = await self.item_base_loader.load_and_cache()
            if item_bases_from_yaml:
                await self._cache_data_as_hash(
                    redis_key=REDIS_KEY_GENERATOR_ITEM_BASE,
                    data_list=list(item_bases_from_yaml.values()),
                    id_field='sub_category_code',
                    ttl_seconds=DEFAULT_TTL_STATIC_REF_DATA
                )
                logger.info(f"Успешно закэшировано {len(item_bases_from_yaml)} записей item_base из YAML в Redis.")
            else:
                logger.warning("Данные item_base не загружены из YAML, кэширование item_base пропущено.")

            await self.cache_skills()
            await self.cache_background_stories()
            await self.cache_personalities()
            await self.cache_inventory_rules()
            await self.cache_item_data_from_db() 
            
            logger.info("Завершено кэширование всех справочных данных в Redis.")
            return True
        except Exception as e:
            logger.critical(f"Критическая ошибка при полном кэшировании справочных данных: {e}", exc_info=True)
            return False

from game_server.Logic.InfrastructureLogic.DataAccessLogic.db_instance import AsyncSessionLocal
reference_data_cache_manager = ReferenceDataCacheManager(async_session_factory=AsyncSessionLocal)