# game_server/Logic/InfrastructureLogic/app_cache/services/reference_data/reference_data_cache_manager.py

import logging
from typing import Dict, Any, List, Type, Union
import uuid
import msgpack
from datetime import datetime

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_cache import IReferenceDataCacheManager
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager
from game_server.database.models.models import Base
from pydantic import BaseModel # Оставляем для возможного использования в других местах, но не для прямого dumps

from game_server.config.constants.redis import (
    REDIS_KEY_GENERATOR_ITEM_BASE, REDIS_KEY_GENERATOR_MATERIALS, REDIS_KEY_GENERATOR_SUFFIXES,
    REDIS_KEY_GENERATOR_MODIFIERS, REDIS_KEY_GENERATOR_SKILLS, REDIS_KEY_GENERATOR_BACKGROUND_STORIES,
    REDIS_KEY_GENERATOR_PERSONALITIES,
    REDIS_KEY_WORLD_CONNECTIONS 
)

class ReferenceDataCacheManager(IReferenceDataCacheManager):
    def __init__(self, repository_manager: RepositoryManager, redis_client: CentralRedisClient):
        self.repository_manager = repository_manager
        self.redis_client = redis_client
        self.logger = logger
        logger.info("✅ ReferenceDataCacheManager инициализирован.")

    def _prepare_data_for_msgpack(self, data: Union[Dict[str, Any], List[Any], Any]) -> Union[Dict[str, Any], List[Any], Any]:
        """
        Рекурсивно преобразует UUID и datetime объекты в словаре/списке в строковое представление
        для совместимости с MsgPack.
        """
        if isinstance(data, dict):
            prepared_data = {}
            for k, v in data.items():
                prepared_data[k] = self._prepare_data_for_msgpack(v)
            return prepared_data
        elif isinstance(data, list):
            return [self._prepare_data_for_msgpack(item) for item in data]
        elif isinstance(data, uuid.UUID):
            return str(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        else:
            return data

    async def _perform_caching(self, redis_key: str, data_for_redis: Union[Dict[str, Dict[str, Any]], List[Dict[str, Any]]], model_name: str) -> bool: # <--- Типизация скорректирована
        """
        Вспомогательный метод для кэширования данных в Redis.
        Принимает обычные Python-словари (dict), обрабатывает сложные типы и сериализует в MSGPACK для кэширования.
        """
        try:
            # Преобразуем входящие Python-словари в MsgPack байты
            if isinstance(data_for_redis, dict):
                # data_for_redis здесь - это {item_code: raw_dict_data}
                
                prepared_mapping_for_redis_bytes: Dict[str, bytes] = {}
                list_of_raw_dicts_for_hash = [] # Used for calculating hash before packing

                for key, raw_dict_data in data_for_redis.items():
                    if isinstance(raw_dict_data, dict):
                        list_of_raw_dicts_for_hash.append(raw_dict_data) # Add raw dict for hash calculation
                        
                        prepared_dict = self._prepare_data_for_msgpack(raw_dict_data)
                        packed_bytes = msgpack.dumps(prepared_dict, use_bin_type=True)
                        prepared_mapping_for_redis_bytes[key] = packed_bytes
                    else:
                        self.logger.error(f"Неожиданный тип данных для кэширования в dict-формате: {type(raw_dict_data)} для ключа '{key}'. Ожидался dict. Пропускаем.")
                        return False

                entity_hash = DataVersionManager._calculate_data_hash(list_of_raw_dicts_for_hash)
                current_cache_hash = await self.repository_manager.data_versions.get_current_version(model_name)
                
                if entity_hash == current_cache_hash:
                    self.logger.info(f"✅ {model_name} данные актуальны в кэше (хэш: {entity_hash[:8]}...). Пропуск.")
                    return True

                self.logger.info(f"🔄 Обнаружены изменения для {model_name}. Старый хэш: {current_cache_hash[:8] if current_cache_hash else 'N/A'}, новый: {entity_hash[:8]}....")
                
                await self.redis_client.hsetall_msgpack(redis_key, prepared_mapping_for_redis_bytes)
                await self.repository_manager.data_versions.update_version(model_name, entity_hash)

            elif isinstance(data_for_redis, list):
                # data_for_redis here is List[Dict[str, Any]]
                list_of_raw_dicts_for_hash = []
                prepared_list_for_msgpack: List[Dict[str, Any]] = []

                for raw_dict_data in data_for_redis:
                    if isinstance(raw_dict_data, dict):
                        list_of_raw_dicts_for_hash.append(raw_dict_data)
                        
                        prepared_dict = self._prepare_data_for_msgpack(raw_dict_data)
                        prepared_list_for_msgpack.append(prepared_dict)
                    else:
                        self.logger.error(f"Неожиданный тип данных для кэширования в list-формате: {type(raw_dict_data)}. Ожидался dict. Пропускаем.")
                        return False
                
                entity_hash = DataVersionManager._calculate_data_hash(prepared_list_for_msgpack)
                current_cache_hash = await self.repository_manager.data_versions.get_current_version(model_name)

                if entity_hash == current_cache_hash:
                    self.logger.info(f"✅ {model_name} данные актуальны в кэше (хэш: {entity_hash[:8]}...). Пропуск.")
                    return True
                
                self.logger.info(f"🔄 Обнаружены изменения для {model_name}. Старый хэш: {current_cache_hash[:8] if current_cache_hash else 'N/A'}, новый: {entity_hash[:8]}....")
                
                packed_bytes = msgpack.dumps(prepared_list_for_msgpack, use_bin_type=True)
                await self.redis_client.set_msgpack(redis_key, packed_bytes)
                await self.repository_manager.data_versions.update_version(model_name, entity_hash)
            
            else:
                self.logger.error(f"Неподдерживаемый тип данных для кэширования: {type(data_for_redis)}")
                return False

            self.logger.info(f"✅ {model_name} данные кэшированы в Redis по ключу '{redis_key}'.")
            return True
        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при кэшировании {model_name} данных: {e}", exc_info=True)
            return False

    async def _cache_from_db_with_version_check(self, repo_obj: Any, redis_key: str, pk_name: str, model_name: str) -> bool:
        """
        Загружает данные из БД, кэширует их в Redis и обновляет версию.
        Данные из БД также будут преобразованы для MsgPack.
        """
        try:
            self.logger.info(f"Загрузка и кэширование {model_name} данных из БД...")
            all_orm_entities = await repo_obj.get_all()
            
            data_for_redis_raw: Dict[str, Dict[str, Any]] = {}
            list_of_raw_dicts_for_hash = [] # Для вычисления хеша

            for entity in all_orm_entities:
                raw_dict_from_orm = entity.to_dict() # Предполагаем, что ORM-модели имеют метод to_dict()
                list_of_raw_dicts_for_hash.append(raw_dict_from_orm) # Добавляем для хеширования
                
                prepared_dict = self._prepare_data_for_msgpack(raw_dict_from_orm)
                pk_value = getattr(entity, pk_name)
                data_for_redis_raw[str(pk_value)] = prepared_dict
            
            entity_hash = DataVersionManager._calculate_data_hash(list_of_raw_dicts_for_hash)
            current_cache_hash = await self.repository_manager.data_versions.get_current_version(model_name)
            
            if entity_hash == current_cache_hash:
                self.logger.info(f"✅ {model_name} данные актуальны в кэше (хэш: {entity_hash[:8]}...). Пропуск.")
                return True

            self.logger.info(f"🔄 Обнаружены изменения для {model_name}. Старый хэш: {current_cache_hash[:8] if current_cache_hash else 'N/A'}, новый: {entity_hash[:8]}....")
            
            # Сериализуем каждый словарь в байты для HSET
            prepared_mapping_for_redis_bytes: Dict[str, bytes] = {
                k: msgpack.dumps(v, use_bin_type=True) for k, v in data_for_redis_raw.items()
            }

            return await self.redis_client.hsetall_msgpack(redis_key, prepared_mapping_for_redis_bytes) # Call MsgPack method
        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при загрузке и кэшировании {model_name} данных из БД: {e}", exc_info=True)
            return False

    async def _cache_item_base_from_yaml(self) -> bool:
        """
        Загружает ItemBase данные из YAML-файлов.
        Ожидает список словарей из ItemBaseLoader.
        """
        try:
            self.logger.info("Загрузка и кэширование ItemBase данных (из YAML)...")
            from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.load_seeds.generic_redis.item_base_loader import ItemBaseLoader
            
            item_base_loader_instance = ItemBaseLoader()
            item_bases_data: List[Dict[str, Any]] = await item_base_loader_instance.load_all() 

            self.logger.info(f"DEBUG: ItemBaseLoader.load_all() вернул {len(item_bases_data)} сырых словарей.")

            if not item_bases_data:
                self.logger.warning("⚠️ ItemBaseLoader не вернул данных для кэширования. Пропускаем кэширование ItemBase.")
                return True

            temp_data_dict_of_raw_dicts = {}
            missing_item_code_count = 0
            empty_item_code_count = 0
            non_string_item_code_count = 0

            for idx, raw_dict_data in enumerate(item_bases_data):
                if not isinstance(raw_dict_data, dict):
                    self.logger.warning(f"⚠️ Элемент по индексу {idx} не является словарем. Элемент: {raw_dict_data}. Пропускаем.")
                    continue

                item_code_value = raw_dict_data.get('item_code')
                
                if item_code_value is None:
                    missing_item_code_count += 1
                    self.logger.warning(f"⚠️ Словарь по индексу {idx} не имеет ключа 'item_code' или его значение None. Словарь: {raw_dict_data}")
                    continue

                if not isinstance(item_code_value, str):
                    non_string_item_code_count += 1
                    self.logger.warning(f"⚠️ Словарь по индексу {idx} имеет 'item_code' не строкового типа ({type(item_code_value)}). Значение: {item_code_value}. Словарь: {raw_dict_data}")
                    continue

                if item_code_value == "":
                    empty_item_code_count += 1
                    self.logger.warning(f"⚠️ Словарь по индексу {idx} имеет пустой 'item_code'. Словарь: {raw_dict_data}")
                    continue
                
                temp_data_dict_of_raw_dicts[item_code_value] = raw_dict_data
            
            data_dict_of_item_data = temp_data_dict_of_raw_dicts # <--- Переименовано для ясности
            
            if missing_item_code_count > 0 or empty_item_code_count > 0 or non_string_item_code_count > 0:
                self.logger.warning(
                    f"⚠️ Общее количество словарей, пропущенных из-за проблем с 'item_code': "
                    f"Отсутствует ключ: {missing_item_code_count}, "
                    f"Пустая строка: {empty_item_code_count}, "
                    f"Нестроковый тип: {non_string_item_code_count}."
                )
            
            self.logger.info(f"DEBUG: Количество словарей с валидным 'item_code' для кэширования: {len(data_dict_of_item_data)}")

            if not data_dict_of_item_data:
                self.logger.critical("🚨 Все ItemBaseData словари были отфильтрованы из-за отсутствия или невалидного 'item_code'. Кэширование провалено.")
                return False

            return await self._perform_caching(REDIS_KEY_GENERATOR_ITEM_BASE, data_dict_of_item_data, "ItemBase")

        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при кэшировании ItemBase данных: {e}", exc_info=True)
            return False

    async def _cache_location_connections_from_yaml(self) -> bool:
        """
        Загружает связи между локациями из YAML-файлов и кэширует их в Redis.
        Теперь ожидает список словарей из LocationConnectionsLoader.
        """
        try:
            self.logger.info("Загрузка и кэширование Location Connections (из YAML)...")
            from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_pre_start.load_seeds.generic_redis.location_connections_loader import LocationConnectionsLoader
            
            connections_loader_instance = LocationConnectionsLoader()
            connections_data_list: List[Dict[str, Any]] = await connections_loader_instance.load_all() 
            
            return await self._perform_caching(REDIS_KEY_WORLD_CONNECTIONS, connections_data_list, "LocationConnections")
        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при кэшировании Location Connections: {e}", exc_info=True)
            return False

    # --- Главный метод ---

    async def cache_all_reference_data(self) -> bool:
        """
        Главный метод, который запускает полное кэширование всех справочных данных.
        """
        self.logger.info("🚀 Запуск полного кэширования справочных данных...")
        
        cache_operations_status: Dict[str, bool] = {}

        # 1. Кэшируем данные из YAML
        yaml_caching_tasks = {
            "ItemBase": self._cache_item_base_from_yaml,
            "LocationConnections": self._cache_location_connections_from_yaml
        }
        for name, task in yaml_caching_tasks.items():
            status = await task()
            cache_operations_status[name] = status
            if not status:
                self.logger.critical(f"🚨 Кэширование {name} провалено. Процесс остановлен.")
                return False

        # 2. Кэшируем данные из БД
        data_to_cache_from_db_config = [
            (self.repository_manager.background_stories, REDIS_KEY_GENERATOR_BACKGROUND_STORIES, "name", "BackgroundStory"),
            (self.repository_manager.materials, REDIS_KEY_GENERATOR_MATERIALS, "material_code", "Material"),
            (self.repository_manager.modifier_library, REDIS_KEY_GENERATOR_MODIFIERS, "modifier_code", "ModifierLibrary"),
            (self.repository_manager.personalities, REDIS_KEY_GENERATOR_PERSONALITIES, "name", "Personality"),
            (self.repository_manager.skills, REDIS_KEY_GENERATOR_SKILLS, "skill_key", "Skill"),
            (self.repository_manager.suffixes, REDIS_KEY_GENERATOR_SUFFIXES, "suffix_code", "Suffix"),
            # Добавьте сюда другие модели, загружаемые из БД, если таковые есть
            # (self.repository_manager.game_locations, REDIS_KEY_FOR_GAME_LOCATIONS, "access_key", "GameLocation"),
            # Убедитесь, что REDIS_KEY_FOR_GAME_LOCATIONS определен в constants/redis
        ]

        for repo_obj, redis_key, pk_name, model_name in data_to_cache_from_db_config:
            status = await self._cache_from_db_with_version_check(repo_obj, redis_key, pk_name, model_name)
            cache_operations_status[model_name] = status
            if not status:
                self.logger.critical(f"🚨 Кэширование {model_name} провалено. Процесс остановлен.")
                return False

        self.logger.info("✅ Все справочные данные успешно кэшированы.")
        return True