# game_server/Logic/InfrastructureLogic/app_cache/services/reference_data/reference_data_cache_manager.py

import logging
from typing import Dict, Any, List, Optional, Union
import uuid
import msgpack
from datetime import datetime
import inject # 🔥 КРИТИЧЕСКИ ВАЖНО: Убедитесь, что inject импортирован!

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_cache import IReferenceDataCacheManager
# 🔥 УДАЛЕНО: from game_server.config.logging.logging_setup import app_logger as logger (логгер будет инжектирован)

# DataVersionManager здесь не нужен, так как логика хэширования перенесена в ReferenceDataLoader

class ReferenceDataCacheManager(IReferenceDataCacheManager):
    """
    Менеджер для кэширования справочных данных в Redis.
    Оперирует Hash-объектами для каждого типа справочных данных.
    """
    # 🔥 КРИТИЧЕСКИ ВАЖНО: ДОБАВИТЬ ЭТОТ ДЕКОРАТОР!
    @inject.autoparams()
    def __init__(self, redis_client: CentralRedisClient, logger: logging.Logger):
        self.redis_client = redis_client # Используем ваше имя переменной
        self.logger = logger
        self.logger.info("✅ ReferenceDataCacheManager инициализирован.")

    def _prepare_data_for_msgpack(self, data: Union[Dict[str, Any], List[Any], Any]) -> Union[Dict[str, Any], List[Any], Any]:
        """
        Рекурсивно преобразует UUID и datetime объекты в словаре/списке в строковое представление
        для совместимости с MsgPack. Это вспомогательный метод для упаковки.
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

    async def cache_data_with_prep(self, redis_key: str, data_to_cache: Union[Dict[str, Any], List[Dict[str, Any]]], model_name: str, is_hash: bool) -> bool:
        """
        Кэширует подготовленные данные в Redis. Включает подготовку для MsgPack.
        Это новый основной метод кэширования.
        """
        try:
            self.logger.debug(f"Начинаем кэширование данных для {model_name}. redis_key: {redis_key}, is_hash: {is_hash}")

            if is_hash: # Данные для HASH
                prepared_mapping_for_redis_bytes: Dict[str, bytes] = {}
                for key, raw_dict_data in data_to_cache.items():
                    if isinstance(raw_dict_data, dict):
                        prepared_dict = self._prepare_data_for_msgpack(raw_dict_data)
                        packed_bytes = msgpack.dumps(prepared_dict, use_bin_type=True)
                        prepared_mapping_for_redis_bytes[key] = packed_bytes
                    else:
                        self.logger.error(f"Неожиданный тип данных для HASH кэширования: {type(raw_dict_data)} для ключа '{key}'. Ожидался dict.")
                        raise TypeError(f"Неподдерживаемый тип данных для HASH '{model_name}' (ключ: '{key}'): {type(raw_dict_data)}. Ожидался dict.")
                
                # 🔥 ИЗМЕНЕНО: Используем self.redis_client
                hset_success_result = await self.redis_client.hsetall_msgpack(redis_key, prepared_mapping_for_redis_bytes)
                if not hset_success_result:
                    self.logger.error(f"Не удалось записать данные {model_name} в Redis по ключу '{redis_key}'.")
                    return False

            else: # Данные для STRING (List)
                prepared_list_for_msgpack: List[Dict[str, Any]] = []
                for raw_dict_data in data_to_cache:
                    if isinstance(raw_dict_data, dict):
                        prepared_dict = self._prepare_data_for_msgpack(raw_dict_data)
                        prepared_list_for_msgpack.append(prepared_dict)
                    else:
                        self.logger.error(f"Неожиданный тип данных для LIST кэширования: {type(raw_dict_data)}. Ожидался dict.")
                        raise TypeError(f"Неподдерживаемый тип данных для LIST '{model_name}': {type(raw_dict_data)}. Ожидался dict.")
                
                packed_bytes = msgpack.dumps(prepared_list_for_msgpack, use_bin_type=True)
                # 🔥 ИЗМЕНЕНО: Используем self.redis_client
                set_success_result = await self.redis_client.set_msgpack(redis_key, packed_bytes)
                if not set_success_result:
                    self.logger.error(f"Не удалось записать данные {model_name} в Redis по ключу '{redis_key}'.")
                    return False
            
            self.logger.info(f"✅ {model_name} данные кэшированы в Redis по ключу '{redis_key}'.")
            return True
        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при кэшировании {model_name} данных: {e}", exc_info=True)
            raise

    # Метод get_cached_data, который был здесь, должен быть в ReferenceDataReader,
    # так как он отвечает за чтение. ReferenceDataReader уже существует.

    # async def get_cached_data(self, redis_key: str, is_hash_data: bool = True) -> Optional[Union[Dict[str, Any], List[Any]]]:
    #     """
    #     Этот метод должен быть перемещен в ReferenceDataReader.
    #     """
    #     return await self.redis_client.hgetall_msgpack(redis_key) if is_hash_data else await self.redis_client.get_msgpack(redis_key)
