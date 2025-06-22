# game_server/Logic/InfrastructureLogic/app_cache/services/reference_data/reference_data_reader.py

import json
import random
from typing import Dict, Any, Optional, List, Type, TypeVar, Union # Добавлен Union
from abc import ABC, abstractmethod

# Импортируем сам класс CentralRedisClient для аннотаций и передачи
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient

from game_server.config.constants.redis import (
    REDIS_KEY_GENERATOR_BACKGROUND_STORIES,
    REDIS_KEY_GENERATOR_ITEM_BASE, REDIS_KEY_GENERATOR_MATERIALS,
    REDIS_KEY_GENERATOR_MODIFIERS, REDIS_KEY_GENERATOR_PERSONALITIES,
    REDIS_KEY_GENERATOR_SKILLS, REDIS_KEY_GENERATOR_SUFFIXES
)

# Обновленный импорт логгера
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# Импортируем новый интерфейс
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_reader import IReferenceDataReader

# ДОБАВЛЕНО: Импорт BaseModel для типизации Pydantic DTOs
from pydantic import BaseModel

# ИЗМЕНЕНО: Корректное определение TypeVar для Pydantic DTO
# Определяем TypeVar один раз в начале файла
PydanticDtoType = TypeVar('PydanticDtoType', bound=BaseModel) # <--- ИСПРАВЛЕНО


# Изменяем класс ReferenceDataReader, чтобы он наследовал от IReferenceDataReader
class ReferenceDataReader(IReferenceDataReader):
    def __init__(self, redis_client: CentralRedisClient):
        self.redis = redis_client
        self.logger = logger
        self.logger.info("✅ ReferenceDataReader инициализирован.")

    async def _get_full_hash_as_dict(self, redis_key: str) -> Optional[Dict[str, Any]]:
        """
        Извлекает весь хеш из Redis по заданному ключу.
        Предполагает, что значения хеша - это JSON-строки, которые нужно распарсить.
        """
        data_dict = await self.redis.hgetall_json(redis_key)

        if data_dict:
            self.logger.debug(f"Успешно прочитан хеш '{redis_key}' из Redis.")
            return data_dict
        else:
            self.logger.warning(f"Хеш '{redis_key}' не найден или пуст в Redis.")
            return None

    # ИЗМЕНЕНО: Адаптация для работы с DTO (как обсуждалось для character_cache_handlers.py)
    # Возвращает DTO, а не int, так как ID могут быть строками (UUID)
    async def get_weighted_random_id(
        self,
        redis_key: str,
        id_field: str,
        weight_field: str,
        dto_type: Type[PydanticDtoType], # <--- ИСПРАВЛЕНО: Используем уже определенный TypeVar
        default_id: Optional[Any] = None # default_id может быть str или int
    ) -> Optional[Any]: # Возвращает Any, т.к. ID может быть int/str
        """
        Получает данные из Redis HASH, делает случайный выбор ID с учетом веса.
        Возвращает ID из выбранного DTO объекта.
        """
        try:
            data_dict = await self._get_full_hash_as_dict(redis_key)
            if not data_dict:
                self.logger.warning(f"Кэш для ключа '{redis_key}' пуст или не найден.")
                return default_id

            choices: List[PydanticDtoType] = [] # <--- ИСПРАВЛЕНО
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

    # --- Остальные методы чтения ---
    async def get_all_item_bases(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_ITEM_BASE)

    async def get_all_materials(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_MATERIALS)

    async def get_all_suffixes(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_SUFFIXES)

    async def get_all_modifiers(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_MODIFIERS)

    async def get_all_skills(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_SKILLS)

    async def get_all_background_stories(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_BACKGROUND_STORIES)

    async def get_all_personalities(self) -> Dict[str, Any]:
        return await self._get_full_hash_as_dict(REDIS_KEY_GENERATOR_PERSONALITIES)

    # ДОБАВЛЕНО: Реализация абстрактного метода get_all_inventory_rules
    async def get_all_inventory_rules(self) -> Dict[str, Any]:
        """
        Получает все правила генерации инвентаря из Redis.
        Если эти данные не кэшируются, вернет пустой словарь.
        """
        # Здесь должен быть ключ Redis для правил инвентаря, если он есть.
        # Если такого ключа нет, то get_all_inventory_rules должен возвращать пустой словарь.
        # logger.warning("Метод get_all_inventory_rules вызван, но его данные не кэшируются в Redis по умолчанию.")
        # Предполагается, что REDIS_KEY_GENERATOR_INVENTORY_RULES где-то определен
        # Если его нет, то get_all_inventory_rules должен возвращать пустой словарь.
        return await self._get_full_hash_as_dict("REDIS_KEY_GENERATOR_INVENTORY_RULES") or {}