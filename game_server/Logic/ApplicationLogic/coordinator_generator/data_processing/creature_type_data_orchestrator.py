# game_server/Logic/InfrastructureLogic/Generators/coordinator_generator/data_processing/creature_type_data_orchestrator.py

# УДАЛИТЬ: import logging (если он был)
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
# from redis.asyncio import Redis 

from game_server.Logic.InfrastructureLogic.DataAccessLogic.manager.generators.data.ORM_creature_type_manager import CreatureTypeManager

from .playable_character_list_processor import process_playable_character_races
from .monster_list_processor import process_monster_types_placeholder 
    

# ИЗМЕНЕНО: ИСПОЛЬЗУЕМ ВАШ ЦЕНТРАЛИЗОВАННЫЙ ЛОГГЕР
from game_server.services.logging.logging_setup import logger

class CreatureTypeDataOrchestrator:
    """
    Класс-оркестратор для загрузки, кэширования и координации обработки данных
    о типах существ для генераторов.
    """
    def __init__(self, session: AsyncSession):
        self.creature_type_manager = CreatureTypeManager(session)

        self._all_creature_types_raw: List[Dict[str, Any]] = []
        self._creature_types_by_id_raw: Dict[int, Dict[str, Any]] = {}
        self._creature_types_by_category_raw: Dict[str, List[Dict[str, Any]]] = {}

        self._processed_playable_races: List[Dict[str, Any]] = [] 
        self._processed_monsters: List[Dict[str, Any]] = []
        self._processed_items: List[Dict[str, Any]] = []


    async def load_raw_data(self):
        """
        Асинхронно загружает все сырые данные о типах существ из БД
        и кэширует их.
        """
        all_types_orm = await self.creature_type_manager.get_all_creature_types()
        
        self._all_creature_types_raw.clear()
        self._creature_types_by_id_raw.clear()
        self._creature_types_by_category_raw.clear()

        for ct_orm in all_types_orm:
            ct_data = ct_orm.to_dict()
            self._all_creature_types_raw.append(ct_data)
            self._creature_types_by_id_raw[ct_data["creature_type_id"]] = ct_data

            category = ct_data.get("category")
            if category:
                if category not in self._creature_types_by_category_raw:
                    self._creature_types_by_category_raw[category] = []
                self._creature_types_by_category_raw[category].append(ct_data)
        
        # Использование централизованного логгера
        logger.debug("CreatureTypeDataOrchestrator: Сырые данные типов существ загружены и кэшированы.")


    async def process_data_for_generators(self):
        """
        Запускает обработку сырых данных для создания списков,
        необходимых конкретным генераторам.
        Этот метод может вызываться после load_raw_data или при необходимости.
        """
        if not self._all_creature_types_raw:
            await self.load_raw_data()

        self._processed_playable_races = await process_playable_character_races(
            self._all_creature_types_raw,
            self._creature_types_by_category_raw,
            self.creature_type_manager
        )
        
        self._processed_monsters = await process_monster_types_placeholder(
            self._all_creature_types_raw,
            self._creature_types_by_category_raw,
            self.creature_type_manager
        )
        # Использование централизованного логгера
        logger.debug("CreatureTypeDataOrchestrator: Данные обработаны для генераторов.")


    # ... (остальные методы get_playable_race_list и другие геттеры) ...

    # --- Методы для предоставления уже обработанных данных генераторам ---

    # ИЗМЕНЕНИЕ ЗДЕСЬ: имя геттера для рас
    def get_playable_race_list(self) -> List[Dict[str, Any]]:
        """Возвращает список подготовленных данных для игровых рас."""
        return self._processed_playable_races

    def get_monster_list(self) -> List[Dict[str, Any]]:
        """Возвращает список подготовленных данных для монстров."""
        return self._processed_monsters

    def get_item_list(self) -> List[Dict[str, Any]]:
        """Возвращает список подготовленных данных для предметов."""
        return self._processed_items

    def get_raw_creature_type_by_id(self, creature_type_id: int) -> Optional[Dict[str, Any]]:
        """Возвращает сырые данные типа существа по ID из кэша оркестратора."""
        return self._creature_types_by_id_raw.get(creature_type_id)

    def get_raw_creature_types_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Возвращает сырые данные типов существ по категории из кэша оркестратора."""
        return self._creature_types_by_category_raw.get(category, [])