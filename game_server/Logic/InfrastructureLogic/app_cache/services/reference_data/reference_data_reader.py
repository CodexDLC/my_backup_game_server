# game_server/Logic/InfrastructureLogic/app_cache/services/reference_data/reference_data_reader.py

import logging
import random
from typing import Dict, Any, List, Optional, Tuple, Type, TypeVar, Union

import inject
import msgpack

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient


from pydantic import BaseModel

from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader
from game_server.config.constants.redis_key.reference_data_keys import (
    REDIS_KEY_GENERATOR_BACKGROUND_STORIES, REDIS_KEY_GENERATOR_ITEM_BASE, REDIS_KEY_GENERATOR_MATERIALS,
    REDIS_KEY_GENERATOR_MODIFIERS, REDIS_KEY_GENERATOR_PERSONALITIES, REDIS_KEY_GENERATOR_SKILLS,
    REDIS_KEY_GENERATOR_SUFFIXES, REDIS_KEY_WORLD_CONNECTIONS # Убедитесь, что REDIS_KEY_WORLD_CONNECTIONS импортирован
)


PydanticDtoType = TypeVar('PydanticDtoType', bound=BaseModel)

logger = logging.getLogger(__name__)

class ReferenceDataReader(IReferenceDataReader):
    
    # 👇 ВОТ РЕШЕНИЕ: ДОБАВЛЯЕМ ДЕКОРАТОР
    @inject.autoparams('central_redis_client', 'logger')
    def __init__(self, central_redis_client: CentralRedisClient, logger: logging.Logger):
        self.redis = central_redis_client
        self.logger = logger
        self.logger.info(f"✨ {self.__class__.__name__} инициализирован.")

    # --- Методы для генератора предметов (item generator) ---
    async def get_all_item_bases(self) -> Dict[str, Any]:
        return await self._get_full_hash_msgpack_data(REDIS_KEY_GENERATOR_ITEM_BASE)

    async def get_all_materials(self) -> Dict[str, Any]:
        return await self._get_full_hash_msgpack_data(REDIS_KEY_GENERATOR_MATERIALS)

    async def get_all_suffixes(self) -> Dict[str, Any]:
        return await self._get_full_hash_msgpack_data(REDIS_KEY_GENERATOR_SUFFIXES)
    
    async def get_all_modifiers(self) -> Dict[str, Any]:
        return await self._get_full_hash_msgpack_data(REDIS_KEY_GENERATOR_MODIFIERS)

    async def get_all_background_stories(self) -> Dict[str, Any]:
        return await self._get_full_hash_msgpack_data(REDIS_KEY_GENERATOR_BACKGROUND_STORIES)

    async def get_all_personalities(self) -> Dict[str, Any]:
        return await self._get_full_hash_msgpack_data(REDIS_KEY_GENERATOR_PERSONALITIES)

    async def get_all_skills(self) -> Dict[str, Any]:
        return await self._get_full_hash_msgpack_data(REDIS_KEY_GENERATOR_SKILLS)

    async def get_all_inventory_rules(self) -> Dict[str, Any]:
        # Предполагаем, что этот ключ также хранит msgpack
        return await self._get_full_hash_msgpack_data("REDIS_KEY_GENERATOR_INVENTORY_RULES") or {}

    # НОВОЕ: Добавляем метод get_cached_data для универсального чтения
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
                cached_data = await self.redis.hgetall_msgpack(redis_key)
            else:
                cached_data = await self.redis.get_msgpack(redis_key)
            
            if cached_data:
                self.logger.debug(f"Кэшированные данные для '{redis_key}' найдены.")
            else:
                self.logger.debug(f"Кэшированные данные для '{redis_key}' не найдены или пусты.")
            return cached_data
        except Exception as e:
            self.logger.error(f"Ошибка при получении кэшированных данных для ключа '{redis_key}': {e}", exc_info=True)
            return None

    async def get_world_connections_data(self) -> List[Dict[str, Any]]:
        """
        Получает данные о связях между локациями из Redis.
        Эти данные хранятся как MsgPack-сериализованный список в Redis String.
        """
        connections_list = await self.get_cached_data(REDIS_KEY_WORLD_CONNECTIONS, is_hash_data=False)
        if connections_list is None:
            self.logger.warning(f"Данные о связях мира (ключ: {REDIS_KEY_WORLD_CONNECTIONS}) не найдены в Redis или пусты.")
            return []
        return connections_list

    # --- Вспомогательные методы ---
    async def _get_full_hash_json_data(self, redis_key: str) -> Dict[str, Any]:
        data_dict = await self.redis.hgetall_json(redis_key)
        if data_dict:
            self.logger.debug(f"Успешно прочитан JSON хеш '{redis_key}' из Redis.")
            return data_dict
        else:
            self.logger.warning(f"JSON хеш '{redis_key}' не найден или пуст в Redis.")
            return {}

    async def _get_full_hash_msgpack_data(self, redis_key: str) -> Dict[str, Any]:
        """
        Вспомогательный метод для получения всех данных из Redis HASH,
        предполагая, что они сериализованы как MsgPack.
        """
        data = await self.redis.hgetall_msgpack(redis_key)
        if data is None:
            self.logger.warning(f"Данные MsgPack не найдены для ключа: {redis_key}")
            return {}
        return data

    async def get_weighted_random_id(
        self,
        redis_key: str,
        id_field: str,
        weight_field: str,
        dto_type: Type[PydanticDtoType], 
        default_id: Optional[Any] = None
    ) -> Optional[Any]:
        try:
            data_dict = await self._get_full_hash_msgpack_data(redis_key) 
            if not data_dict:
                self.logger.warning(f"Кэш для ключа '{redis_key}' пуст или не найден.")
                return default_id

            choices: List[PydanticDtoType] = [] 
            weights = []

            for item_data_dict in data_dict.values():
                try:
                    item_dto = dto_type(**item_data_dict)
                    
                    item_id = getattr(item_dto, id_field, None)
                    if item_id is None:
                        self.logger.warning(f"Элемент в кэше '{redis_key}' не содержит поле ID '{id_field}'. Пропускаем.")
                        continue

                    item_weight = float(getattr(item_dto, weight_field, 1.0))

                    if item_weight >= 0:
                        choices.append(item_dto)
                        weights.append(item_weight)
                except Exception as e:
                    self.logger.error(f"Ошибка валидации DTO или обработки элемента в кэше '{redis_key}': {item_data_dict}. Ошибка: {e}", exc_info=True)
                    continue

            if not choices:
                self.logger.warning(f"Не найдено подходящих вариантов для взвешенного выбора в кэше '{redis_key}'.")
                return default_id

            selected_dto = random.choices(choices, weights=weights, k=1)[0]
            return getattr(selected_dto, id_field)

        except Exception as e:
            self.logger.error(f"Ошибка при взвешенном выборе из кэша '{redis_key}': {e}", exc_info=True)
            return default_id

    async def get_hash_fingerprint(self, redis_key: str) -> Optional[str]:
        return await self.redis.get(redis_key)

    async def set_hash_fingerprint(self, redis_key: str, fingerprint: str, ttl: int):
        await self.redis.set(redis_key, fingerprint, ex=ttl)

    async def get_by_id_from_hash(self, redis_key: str, item_id: str) -> Optional[Any]:
        raw_value = await self.redis.hget(redis_key, item_id)
        if raw_value:
            try:
                # Предполагаем, что значение закодировано в msgpack
                return msgpack.loads(raw_value, raw=False)
            except (msgpack.exceptions.ExtraData, msgpack.exceptions.UnpackValueError, TypeError) as e:
                self.logger.error(f"Ошибка десериализации MsgPack для '{item_id}' в '{redis_key}': {e}", exc_info=True)
                return None
        return None