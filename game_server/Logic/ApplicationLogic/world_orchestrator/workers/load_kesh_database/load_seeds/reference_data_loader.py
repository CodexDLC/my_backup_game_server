# game_server/Logic/ApplicationLogic/world_orchestrator/pre_start/data_loaders/reference_data_loader.py

import logging
import inject
from typing import Dict, Any, List, Optional, Union, Callable
from sqlalchemy.ext.asyncio import AsyncSession
import inspect # 🔥 ДОБАВЛЕНО: Импорт inspect для проверки сигнатуры

from game_server.Logic.ApplicationLogic.world_orchestrator.workers.load_kesh_database.load_seeds.generic_redis.item_base_loader import ItemBaseLoader
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.load_kesh_database.load_seeds.generic_redis.location_connections_loader import LocationConnectionsLoader

from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager
from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    IAbilityRepository, IBackgroundStoryRepository, ICreatureTypeRepository, IMaterialRepository,
    IModifierLibraryRepository, IPersonalityRepository, ISkillRepository, ICreatureTypeInitialSkillRepository,
    IStaticItemTemplateRepository, ISuffixRepository
)

from game_server.config.constants.redis_key.reference_data_keys import (
    REDIS_KEY_GENERATOR_ITEM_BASE, REDIS_KEY_GENERATOR_MATERIALS, REDIS_KEY_GENERATOR_SUFFIXES,
    REDIS_KEY_GENERATOR_MODIFIERS, REDIS_KEY_GENERATOR_SKILLS, REDIS_KEY_GENERATOR_BACKGROUND_STORIES,
    REDIS_KEY_GENERATOR_PERSONALITIES, REDIS_KEY_WORLD_CONNECTIONS
)


class ReferenceDataLoader:
    @inject.autoparams()
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        background_story_repo_factory: Callable[[AsyncSession], IBackgroundStoryRepository],
        material_repo_factory: Callable[[AsyncSession], IMaterialRepository],
        modifier_library_repo_factory: Callable[[AsyncSession], IModifierLibraryRepository],
        personality_repo_factory: Callable[[AsyncSession], IPersonalityRepository],
        skill_repo_factory: Callable[[AsyncSession], ISkillRepository],
        suffix_repo_factory: Callable[[AsyncSession], ISuffixRepository],
        data_version_manager: DataVersionManager,
        cache_manager: ReferenceDataCacheManager,
        logger: logging.Logger,
    ):
        self._session_factory = session_factory
        self._background_story_repo_factory = background_story_repo_factory
        self._material_repo_factory = material_repo_factory
        self._modifier_library_repo_factory = modifier_library_repo_factory
        self._personality_repo_factory = personality_repo_factory
        self._skill_repo_factory = skill_repo_factory
        self._suffix_repo_factory = suffix_repo_factory
        self.data_version_manager = data_version_manager
        self.cache_manager = cache_manager
        self.logger = logger
        self.logger.info(f"✅ ReferenceDataLoader инициализирован.")

        self._model_name_to_repo_factory: Dict[str, Callable[[AsyncSession], Any]] = {
            "BackgroundStory": self._background_story_repo_factory,
            "Material": self._material_repo_factory,
            "ModifierLibrary": self._modifier_library_repo_factory,
            "Personality": self._personality_repo_factory,
            "Skill": self._skill_repo_factory,
            "Suffix": self._suffix_repo_factory,
        }


    async def load_and_cache_all_data(self) -> bool:
        self.logger.info("🚀 Запуск загрузки и кэширования всех справочных данных...")
        
        async with self._session_factory() as session:
            try:
                yaml_loaders = {
                    "ItemBase": (ItemBaseLoader(), REDIS_KEY_GENERATOR_ITEM_BASE, self._process_item_base_data),
                    "LocationConnections": (LocationConnectionsLoader(), REDIS_KEY_WORLD_CONNECTIONS, self._process_location_connections_data)
                }
                for name, (loader, redis_key, processor) in yaml_loaders.items():
                    try:
                        raw_data = await loader.load_all()
                        processed_data = await processor(raw_data, name)
                        if processed_data is not None:
                            await self._conditional_cache(session, redis_key, processed_data, name, is_hash=True if name == "ItemBase" else False)
                        else:
                            self.logger.warning(f"⚠️ Лоадер {name} не вернул данных для кэширования.")
                    except Exception as e:
                        self.logger.critical(f"🚨 Критическая ошибка при загрузке/кэшировании данных {name} из YAML: {e}", exc_info=True)
                        raise

                data_to_cache_from_db_config = [
                    (self._background_story_repo_factory, "BackgroundStory", REDIS_KEY_GENERATOR_BACKGROUND_STORIES, "name", True),
                    (self._material_repo_factory, "Material", REDIS_KEY_GENERATOR_MATERIALS, "material_code", True),
                    (self._modifier_library_repo_factory, "ModifierLibrary", REDIS_KEY_GENERATOR_MODIFIERS, "modifier_code", True),
                    (self._personality_repo_factory, "Personality", REDIS_KEY_GENERATOR_PERSONALITIES, "name", True),
                    (self._skill_repo_factory, "Skill", REDIS_KEY_GENERATOR_SKILLS, "skill_key", True),
                    (self._suffix_repo_factory, "Suffix", REDIS_KEY_GENERATOR_SUFFIXES, "suffix_code", True),
                ]

                for repo_factory, model_name_for_hash, redis_key, pk_name, is_hash_data in data_to_cache_from_db_config:
                    await self._load_and_cache_from_db(session, repo_factory, model_name_for_hash, redis_key, pk_name, is_hash_data)

                await session.commit()
                self.logger.info("✅ Все справочные данные успешно загружены и кэшированы.")
                return True

            except Exception as e:
                self.logger.critical(f"🚨 Критическая ошибка в load_and_cache_all_data: {e}", exc_info=True)
                await session.rollback()
                raise

    async def _process_item_base_data(self, raw_data: List[Dict[str, Any]], model_name: str) -> Optional[Dict[str, Any]]:
        temp_data_dict = {}
        for idx, item_data in enumerate(raw_data):
            item_code = item_data.get('item_code')
            if item_code and isinstance(item_code, str):
                temp_data_dict[item_code] = item_data
            else:
                self.logger.warning(f"⚠️ Элемент ItemBase по индексу {idx} имеет невалидный 'item_code': {item_code}. Пропускаем.")
        if not temp_data_dict:
            self.logger.warning(f"⚠️ После обработки ItemBase не осталось валидных данных.")
            return None
        return temp_data_dict

    async def _process_location_connections_data(self, raw_data: List[Dict[str, Any]], model_name: str) -> Optional[List[Dict[str, Any]]]:
        if not raw_data:
            self.logger.warning(f"⚠️ Лоадер LocationConnections не вернул данных.")
            return None
        return raw_data
    
    async def _load_and_cache_from_db(self, session: AsyncSession, repo_factory: Callable[[AsyncSession], Any], model_name_for_hash: str, redis_key: str, pk_name: str, is_hash_data: bool) -> bool:
        try:
            self.logger.info(f"Загрузка и кэширование {model_name_for_hash} данных из БД...")
            
            repo_obj = repo_factory(session)

            all_orm_entities = await repo_obj.get_all()
            
            if not all_orm_entities:
                self.logger.warning(f"Для {model_name_for_hash}: all_orm_entities пуст. Нет данных для кэширования.")
                return True 

            data_for_caching: Union[Dict[str, Dict[str, Any]], List[Dict[str, Any]]] = {} if is_hash_data else []
            list_of_raw_dicts_for_hash = []

            for entity in all_orm_entities:
                if not hasattr(entity, 'to_dict') or not callable(getattr(entity, 'to_dict')):
                    self.logger.error(f"ORM-сущность {type(entity)} не имеет callable метода 'to_dict()'")
                    raise AttributeError(f"ORM-сущность {type(entity)} не имеет callable метода 'to_dict()'")
                
                raw_dict_from_orm = entity.to_dict()
                list_of_raw_dicts_for_hash.append(raw_dict_from_orm)
                
                if is_hash_data:
                    pk_value = getattr(entity, pk_name)
                    if not pk_value:
                        self.logger.warning(f"Для {model_name_for_hash}: Значение PK ('{pk_name}') для сущности {entity} пустое или None. Пропускаем.")
                        continue 
                    data_for_caching[str(pk_value)] = raw_dict_from_orm
                else:
                    data_for_caching.append(raw_dict_from_orm)

            entity_hash = self.data_version_manager._calculate_data_hash(list_of_raw_dicts_for_hash)
            
            # 🔥 ДОБАВЛЕНЫ ДИАГНОСТИЧЕСКИЕ ЛОГИ
            self.logger.debug(f"DEBUG: _load_and_cache_from_db - Тип self.data_version_manager: {type(self.data_version_manager)}")
            self.logger.debug(f"DEBUG: _load_and_cache_from_db - Сигнатура get_redis_version: {inspect.signature(self.data_version_manager.get_redis_version)}")
            self.logger.debug(f"DEBUG: _load_and_cache_from_db - Передаваемый model_name_for_hash: '{model_name_for_hash}'")

            current_cache_hash = await self.data_version_manager.get_redis_version(model_name_for_hash)
            
            if entity_hash == current_cache_hash:
                self.logger.info(f"✅ {model_name_for_hash} данные актуальны в кэше (хэш: {entity_hash[:8]}...). Пропуск.")
                return True

            self.logger.info(f"🔄 Обнаружены изменения для {model_name_for_hash}. Старый хэш: {current_cache_hash[:8] if current_cache_hash else 'N/A'}, новый: {entity_hash[:8]}....")
            
            success = await self.cache_manager.cache_data_with_prep(redis_key, data_for_caching, model_name_for_hash, is_hash=is_hash_data)
            
            if success:
                # 🔥 ДОБАВЛЕНЫ ДИАГНОСТИЧЕСКИЕ ЛОГИ
                self.logger.debug(f"DEBUG: _load_and_cache_from_db - Тип self.data_version_manager: {type(self.data_version_manager)}")
                self.logger.debug(f"DEBUG: _load_and_cache_from_db - Сигнатура update_redis_version: {inspect.signature(self.data_version_manager.update_redis_version)}")
                self.logger.debug(f"DEBUG: _load_and_cache_from_db - Передаваемый redis_key: '{redis_key}', entity_hash: '{entity_hash}'")
                await self.data_version_manager.update_redis_version(redis_key, entity_hash)
            return success
        
        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при загрузке и кэшировании {model_name_for_hash} данных из БД: {e}", exc_info=True)
            raise 

    async def _conditional_cache(self, session: AsyncSession, redis_key: str, data: Union[Dict[str, Dict[str, Any]], List[Dict[str, Any]]], model_name: str, is_hash: bool) -> bool:
        """
        Кэширует данные в Redis только если они изменились.
        """
        entity_hash = self.data_version_manager._calculate_data_hash(list(data.values()) if isinstance(data, dict) else data)
        
        # 🔥 ДОБАВЛЕНЫ ДИАГНОСТИЧЕСКИЕ ЛОГИ
        self.logger.debug(f"DEBUG: _conditional_cache - Тип self.data_version_manager: {type(self.data_version_manager)}")
        self.logger.debug(f"DEBUG: _conditional_cache - Сигнатура get_redis_version: {inspect.signature(self.data_version_manager.get_redis_version)}")
        self.logger.debug(f"DEBUG: _conditional_cache - Передаваемый model_name: '{model_name}'")

        current_cache_hash = await self.data_version_manager.get_redis_version(model_name)

        if entity_hash == current_cache_hash:
            self.logger.info(f"✅ {model_name} данные актуальны в кэше (хэш: {entity_hash[:8]}...). Пропуск.")
            return True

        self.logger.info(f"🔄 Обнаружены изменения для {model_name}. Старый хэш: {current_cache_hash[:8] if current_cache_hash else 'N/A'}, новый: {entity_hash[:8]}....")

        return await self.cache_manager.cache_data_with_prep(redis_key, data, model_name, is_hash=is_hash)
