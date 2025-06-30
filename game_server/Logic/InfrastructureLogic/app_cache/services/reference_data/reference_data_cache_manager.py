# game_server/Logic/InfrastructureLogic/app_cache/services/reference_data/reference_data_cache_manager.py

import logging
from typing import Dict, Any, List, Optional, Type, Union
import uuid
import msgpack
from datetime import datetime

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_cache import IReferenceDataCacheManager
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager # Эта зависимость будет исправлена позже
# from game_server.database.models.models import Base # Удаляем, если не используется напрямую
# from pydantic import BaseModel # Удаляем, если не используется напрямую

from game_server.config.constants.redis_key.reference_data_keys import (
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

    async def _perform_caching(self, redis_key: str, data_for_redis: Union[Dict[str, Dict[str, Any]], List[Dict[str, Any]]], model_name: str) -> bool:
        """
        Вспомогательный метод для кэширования данных в Redis.
        Принимает обычные Python-словари, обрабатывает сложные типы и сериализует в MSGPACK для кэширования.
        """
        try:
            self.logger.debug(f"DEBUG_PERFORM_CACHING: Начинаем _perform_caching для {model_name}. redis_key: {redis_key}")
            self.logger.debug(f"DEBUG_PERFORM_CACHING: Тип data_for_redis: {type(data_for_redis)}. Количество элементов: {len(data_for_redis) if hasattr(data_for_redis, '__len__') else 'N/A'}")

            if isinstance(data_for_redis, dict):
                # Prepared mapping теперь будет хранить уже упакованные байты
                prepared_mapping_for_redis_bytes: Dict[str, bytes] = {}
                list_of_raw_dicts_for_hash = [] # Used for calculating hash before packing

                for key, raw_dict_data in data_for_redis.items():
                    self.logger.debug(f"DEBUG_PERFORM_CACHING_DICT_ITEM: Processing key '{key}' for {model_name}. raw_dict_data type: {type(raw_dict_data)}")
                    self.logger.debug(f"DEBUG_PERFORM_CACHING_DICT_ITEM: raw_dict_data sample: {str(raw_dict_data)[:200]}...")

                    if isinstance(raw_dict_data, dict):
                        list_of_raw_dicts_for_hash.append(raw_dict_data)
                        
                        prepared_dict = self._prepare_data_for_msgpack(raw_dict_data)
                        packed_bytes = msgpack.dumps(prepared_dict, use_bin_type=True)
                        prepared_mapping_for_redis_bytes[key] = packed_bytes
                    else:
                        self.logger.error(f"Неожиданный тип данных для кэширования в dict-формате: {type(raw_dict_data)} для ключа '{key}'. Ожидался dict.")
                        raise TypeError(f"Неподдерживаемый тип данных в 'dict' режиме для '{model_name}' (ключ: '{key}'): {type(raw_dict_data)}. Ожидался dict.")

                entity_hash = DataVersionManager._calculate_data_hash(list_of_raw_dicts_for_hash)
                current_cache_hash = await self.repository_manager.data_versions.get_current_version(model_name)
                
                if entity_hash == current_cache_hash:
                    self.logger.info(f"✅ {model_name} данные актуальны в кэше (хэш: {entity_hash[:8]}...). Пропуск.")
                    return True

                self.logger.info(f"🔄 Обнаружены изменения для {model_name}. Старый хэш: {current_cache_hash[:8] if current_cache_hash else 'N/A'}, новый: {entity_hash[:8]}....")
                
                hset_success_result = await self.redis_client.hsetall_msgpack(redis_key, prepared_mapping_for_redis_bytes)
                if not hset_success_result: # hsetall_msgpack теперь возвращает bool
                    self.logger.error(f"Не удалось записать данные {model_name} в Redis по ключу '{redis_key}'. Результат hsetall_msgpack: {hset_success_result}.")
                    raise RuntimeError(f"Не удалось записать данные {model_name} в Redis: hsetall_msgpack вернул {hset_success_result}. Проверьте соединение с Redis.")
                
                await self.repository_manager.data_versions.update_version(model_name, entity_hash)

            elif isinstance(data_for_redis, list):
                list_of_raw_dicts_for_hash = []
                prepared_list_for_msgpack: List[Dict[str, Any]] = []

                for raw_dict_data in data_for_redis:
                    self.logger.debug(f"DEBUG_PERFORM_CACHING_LIST_ITEM: Processing item {raw_dict_data} for {model_name}. raw_dict_data type: {type(raw_dict_data)}")
                    self.logger.debug(f"DEBUG_PERFORM_CACHING_LIST_ITEM: raw_dict_data sample: {str(raw_dict_data)[:200]}...")

                    if isinstance(raw_dict_data, dict):
                        list_of_raw_dicts_for_hash.append(raw_dict_data)
                        
                        prepared_dict = self._prepare_data_for_msgpack(raw_dict_data)
                        prepared_list_for_msgpack.append(prepared_dict)
                    else:
                        self.logger.error(f"Неожиданный тип данных для кэширования в list-формате: {type(raw_dict_data)}. Ожидался dict.")
                        raise TypeError(f"Неподдерживаемый тип данных в 'list' режиме для '{model_name}': {type(raw_dict_data)}. Ожидался dict.")
                
                entity_hash = DataVersionManager._calculate_data_hash(prepared_list_for_msgpack)
                current_cache_hash = await self.repository_manager.data_versions.get_current_version(model_name)

                if entity_hash == current_cache_hash:
                    self.logger.info(f"✅ {model_name} данные актуальны в кэше (хэш: {entity_hash[:8]}...). Пропуск.")
                    return True
                
                self.logger.info(f"🔄 Обнаружены изменения для {model_name}. Старый хэш: {current_cache_hash[:8] if current_cache_hash else 'N/A'}, новый: {entity_hash[:8]}....")
                
                packed_bytes = msgpack.dumps(prepared_list_for_msgpack, use_bin_type=True)
                set_success_result = await self.redis_client.set_msgpack(redis_key, packed_bytes)
                if not set_success_result: # set_msgpack теперь возвращает bool
                    self.logger.error(f"Не удалось записать данные {model_name} в Redis по ключу '{redis_key}'. Результат set_msgpack: {set_success_result}")
                    raise RuntimeError(f"Не удалось записать данные {model_name} в Redis: set_msgpack вернул {set_success_result}.")

                await self.repository_manager.data_versions.update_version(model_name, entity_hash)
            
            else:
                self.logger.error(f"Неподдерживаемый тип данных для кэширования: {type(data_for_redis)}")
                raise TypeError(f"Неподдерживаемый тип данных для кэширования '{model_name}': {type(data_for_redis)}")

            self.logger.info(f"✅ {model_name} данные кэшированы в Redis по ключу '{redis_key}'.")
            return True
        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при кэшировании {model_name} данных: {e}", exc_info=True)
            raise

    # 🔥 НОВЫЙ МЕТОД ДЛЯ ЧТЕНИЯ КЭШИРОВАННЫХ ДАННЫХ ИЗ REDIS (Использует MsgPack)
    async def get_cached_data(self, redis_key: str, is_hash_data: bool = True) -> Optional[Union[Dict[str, Any], List[Any]]]:
        """
        Получает кэшированные данные из Redis, используя соответствующие MsgPack методы.
        :param redis_key: Ключ Redis.
        :param is_hash_data: True, если данные хранятся как HASH, False, если как STRING (по умолчанию True).
        :return: Десериализованные данные или None.
        """
        self.logger.debug(f"Получение кэшированных данных для ключа '{redis_key}'. Тип: {'HASH' if is_hash_data else 'STRING'}.")
        try:
            if is_hash_data:
                # Используем hgetall_msgpack для получения всех полей хэша
                cached_data = await self.redis_client.hgetall_msgpack(redis_key)
            else:
                # Используем get_msgpack для получения строковых данных
                cached_data = await self.redis_client.get_msgpack(redis_key)
            
            if cached_data:
                self.logger.debug(f"Кэшированные данные для '{redis_key}' найдены.")
            else:
                self.logger.debug(f"Кэшированные данные для '{redis_key}' не найдены или пусты.")
            return cached_data
        except Exception as e:
            self.logger.error(f"Ошибка при получении кэшированных данных для ключа '{redis_key}': {e}", exc_info=True)
            return None


    async def _cache_from_db_with_version_check(self, repo_obj: Any, redis_key: str, pk_name: str, model_name: str) -> bool:
        """
        Загружает данные из БД, кэширует их в Redis и обновляет версию.
        Данные из БД также будут преобразованы для MsgPack.
        Логирование теперь на стандартном уровне (INFO/DEBUG), без лишних CRITICAL.
        """
        try:
            self.logger.info(f"Загрузка и кэширование {model_name} данных из БД...")
            all_orm_entities = await repo_obj.get_all()
            
            self.logger.debug(f"Для {model_name}: Загружено {len(all_orm_entities)} ORM-сущностей из БД.")
            if not all_orm_entities:
                self.logger.warning(f"Для {model_name}: all_orm_entities пуст. Нет данных для кэширования.")
                return True 

            data_for_redis_raw: Dict[str, Dict[str, Any]] = {}
            list_of_raw_dicts_for_hash = []

            for entity in all_orm_entities:
                self.logger.debug(f"Обработка сущности {model_name}. Тип объекта ORM: {type(entity)}")
                if not hasattr(entity, 'to_dict') or not callable(getattr(entity, 'to_dict')):
                    self.logger.error(f"ORM-сущность {type(entity)} не имеет callable метода 'to_dict()'")
                    raise AttributeError(f"ORM-сущность {type(entity)} не имеет callable метода 'to_dict()'")
                
                raw_dict_from_orm = entity.to_dict()
                
                self.logger.debug(f"{model_name} raw_dict_from_orm тип: {type(raw_dict_from_orm)}")
                self.logger.debug(f"{model_name} raw_dict_from_orm пример: {str(raw_dict_from_orm)[:500]}...")

                if not isinstance(raw_dict_from_orm, dict) or not raw_dict_from_orm:
                    self.logger.warning(f"{model_name}: to_dict() вернул не словарь или пустой словарь: {raw_dict_from_orm}. Пропускаем запись.")
                    continue 

                list_of_raw_dicts_for_hash.append(raw_dict_from_orm)
                
                prepared_dict = self._prepare_data_for_msgpack(raw_dict_from_orm)
                
                self.logger.debug(f"{model_name} prepared_dict тип: {type(prepared_dict)}")
                self.logger.debug(f"{model_name} prepared_dict пример: {str(prepared_dict)[:500]}...")

                pk_value = getattr(entity, pk_name)
                if not pk_value:
                    self.logger.warning(f"Для {model_name}: Значение PK ('{pk_name}') для сущности {entity} пустое или None. Пропускаем.")
                    continue 

                data_for_redis_raw[str(pk_value)] = prepared_dict
            
            self.logger.debug(f"Для {model_name}: data_for_redis_raw содержит {len(data_for_redis_raw)} элементов.")
            if not data_for_redis_raw:
                self.logger.warning(f"Для {model_name}: data_for_redis_raw пуст после обработки всех сущностей. Это приведет к hsetall_msgpack: 0.")
                return True 

            entity_hash = DataVersionManager._calculate_data_hash(list_of_raw_dicts_for_hash)
            current_cache_hash = await self.repository_manager.data_versions.get_current_version(model_name)
            
            if entity_hash == current_cache_hash:
                self.logger.info(f"✅ {model_name} данные актуальны в кэше (хэш: {entity_hash[:8]}...). Пропуск.")
                return True

            self.logger.info(f"🔄 Обнаружены изменения для {model_name}. Старый хэш: {current_cache_hash[:8] if current_cache_hash else 'N/A'}, новый: {entity_hash[:8]}....")
            
            # Мы ожидаем, что data_for_redis_raw - это уже Dict[str, Dict[str, Any]],
            # где внутренние dict'ы уже подготовлены _prepare_data_for_msgpack
            # и будут упакованы в msgpack.dumps для hsetall_msgpack.
            
            # 🔥 ИСПРАВЛЕНИЕ: Передаем hsetall_msgpack готовый dict[str, bytes]
            # Упаковка в msgpack.dumps должна происходить здесь
            final_mapping_for_hset = {
                k: msgpack.dumps(v, use_bin_type=True) for k, v in data_for_redis_raw.items()
            }

            hset_success_result = await self.redis_client.hsetall_msgpack(redis_key, final_mapping_for_hset)
            
            if not hset_success_result:
                self.logger.error(f"Не удалось записать данные {model_name} в Redis по ключу '{redis_key}'. Результат hsetall_msgpack: {hset_success_result}. Вероятно, ошибка соединения с Redis или внутренняя ошибка клиента.")
                raise RuntimeError(f"Не удалось записать данные {model_name} в Redis: hsetall_msgpack вернул {hset_success_result}. Проверьте соединение с Redis.")
            
            # Логика для hset_success_result (был True/False)
            if not hset_success_result: # Если hsetall_msgpack вернул False
                self.logger.error(f"Не удалось записать данные {model_name} в Redis по ключу '{redis_key}'. Результат hsetall_msgpack: {hset_success_result}.")
                raise RuntimeError(f"Не удалось записать данные {model_name} в Redis: hsetall_msgpack вернул {hset_success_result}. Проверьте соединение с Redis.")
            elif isinstance(hset_success_result, int) and hset_success_result == 0 and len(final_mapping_for_hset) > 0: # Это не произойдет, если hsetall_msgpack возвращает bool
                self.logger.info(f"✅ {model_name} данные обновлены в кэше Redis по ключу '{redis_key}' (все поля уже существовали).")
            elif isinstance(hset_success_result, int) and hset_success_result > 0: # Это не произойдет, если hsetall_msgpack возвращает bool
                self.logger.info(f"✅ {model_name} данные кэшированы в Redis по ключу '{redis_key}'. Добавлено новых полей: {hset_success_result}.")
            else: # Это произойдет, если hsetall_msgpack возвращает True
                self.logger.info(f"✅ {model_name} данные кэшированы в Redis по ключу '{redis_key}'.")


            await self.repository_manager.data_versions.update_version(model_name, entity_hash)
            return True # Всегда возвращаем True при успехе
        
        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при загрузке и кэшировании {model_name} данных из БД: {e}", exc_info=True)
            raise 


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
            
            data_dict_of_item_data = temp_data_dict_of_raw_dicts # Переименовано для ясности
            
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
            raise # Перевыбрасываем исключение

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
            raise # Перевыбрасываем исключение

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
            try:
                status = await task()
                cache_operations_status[name] = status
                if not status:
                    self.logger.critical(f"🚨 Кэширование {name} провалено. Процесс остановлен.")
                    raise RuntimeError(f"Кэширование {name} завершилось неудачей.")
            except Exception as e:
                self.logger.critical(f"🚨 Критическая ошибка при кэшировании данных {name} из YAML: {e}", exc_info=True)
                raise


        # 2. Кэшируем данные из БД
        data_to_cache_from_db_config = [
            (self.repository_manager.background_stories, REDIS_KEY_GENERATOR_BACKGROUND_STORIES, "name", "BackgroundStory", True), # is_hash_data = True
            (self.repository_manager.materials, REDIS_KEY_GENERATOR_MATERIALS, "material_code", "Material", True),
            (self.repository_manager.modifier_library, REDIS_KEY_GENERATOR_MODIFIERS, "modifier_code", "ModifierLibrary", True),
            (self.repository_manager.personalities, REDIS_KEY_GENERATOR_PERSONALITIES, "name", "Personality", True),
            (self.repository_manager.skills, REDIS_KEY_GENERATOR_SKILLS, "skill_key", "Skill", True),
            (self.repository_manager.suffixes, REDIS_KEY_GENERATOR_SUFFIXES, "suffix_code", "Suffix", True),
            # (self.repository_manager.game_locations, REDIS_KEY_FOR_GAME_LOCATIONS, "access_key", "GameLocation", True),
        ]

        for repo_obj, redis_key, pk_name, model_name, is_hash_data in data_to_cache_from_db_config:
            try:
                status = await self._cache_from_db_with_version_check(repo_obj, redis_key, pk_name, model_name)
                cache_operations_status[model_name] = status
                if not status:
                    self.logger.critical(f"🚨 Кэширование {model_name} провалено. Процесс остановлен.")
                    raise RuntimeError(f"Кэширование {model_name} завершилось неудачей.")
            except Exception as e:
                self.logger.critical(f"🚨 Критическая ошибка при кэшировании данных {model_name} из БД: {e}", exc_info=True)
                raise


        self.logger.info("✅ Все справочные данные успешно кэшированы.")
        return True