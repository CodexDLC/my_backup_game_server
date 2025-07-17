# game_server/Logic/InfrastructureLogic/app_cache/interfaces/interfaces_reference_data_cache.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union

# CentralRedisClient здесь не импортируется, так как это деталь реализации, а не часть контракта.

class IReferenceDataCacheManager(ABC):
    """
    Интерфейс для менеджера кэша справочных данных.
    Отвечает только за запись (кэширование) данных в Redis.
    """
    @abstractmethod
    async def cache_data_with_prep(self, redis_key: str, data_to_cache: Union[Dict[str, Any], List[Dict[str, Any]]], model_name: str, is_hash: bool) -> bool:
        """
        Кэширует подготовленные данные в Redis, включая подготовку для MsgPack.
        
        Args:
            redis_key (str): Ключ Redis, под которым будут храниться данные.
            data_to_cache (Union[Dict[str, Any], List[Dict[str, Any]]]): Данные для кэширования (уже в формате, готовом для подготовки к MsgPack).
            model_name (str): Имя модели/типа данных для логирования.
            is_hash (bool): True, если данные должны быть сохранены как Redis HASH; False, если как Redis STRING (список).
        
        Returns:
            bool: True в случае успешного кэширования, иначе False.
        """
        pass

    # Все остальные абстрактные методы, которые ранее были здесь (такие как _perform_caching,
    # _cache_from_db_with_version_check, _cache_item_base_from_yaml, cache_all_reference_data),
    # удалены, так как они относятся к логике ЗАГРУЗКИ данных, а не кэширования.
    # Эта логика будет перенесена в ReferenceDataLoader.
