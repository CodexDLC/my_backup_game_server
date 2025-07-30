# game_server/Logic/ApplicationLogic/world_orchestrator/workers/world_map_generator/world_map_generator.py

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import ILocationStateRepository, IWorldStateRepository
# --- УДАЛЕНО ---: Больше не нужен Redis Reader для выходов
# from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader

from game_server.contracts.db_models.mongo.world_map.data_models import ActiveLocationDocument, LocationExit, StaticLocationData, WorldRegionDocument
from game_server.contracts.dtos.orchestrator.data_models import GameLocationData
from game_server.database.models.models import GameLocation 
from pydantic import BaseModel
from game_server.Logic.ApplicationLogic.shared_logic.world_map_service.world_map_builder_utils import WorldMapBuilderUtils

class WorldMapGenerator:
    """
    Отвечает за генерацию статической карты мира.
    1. Читает данные из PostgreSQL.
    2. Собирает в иерархическую структуру регионов (выходы берутся из тех же данных).
    3. Сохраняет результат в MongoDB.
    4. Инициализирует пустые динамические документы локаций.
    """
    def __init__(self,
                 pg_location_repo: IGameLocationRepository,
                 mongo_world_repo: IWorldStateRepository,
                 location_state_repo: ILocationStateRepository,
                 # --- УДАЛЕНО ---: redis_reader больше не передается
                 logger: logging.Logger):
        self.pg_location_repo = pg_location_repo
        self.mongo_world_repo = mongo_world_repo
        self.location_state_repo = location_state_repo
        # --- УДАЛЕНО ---: self.redis_reader = redis_reader
        self.logger = logger

    async def generate_and_store_world_map(self) -> bool:
        """Основной метод, запускающий весь процесс."""
        self.logger.info("🚀 Начало генерации статической карты мира...")
        try:
            # 1. EXTRACT: Получаем все локации из PostgreSQL
            all_orm_locations: List[GameLocation] = await self.pg_location_repo.get_all() 
            
            if not all_orm_locations:
                self.logger.warning("Не найдено ни одной локации в PostgreSQL. Генерация прервана.")
                return True

            all_pg_locations_dtos: List[GameLocationData] = [
                GameLocationData.model_validate(loc.to_dict()) for loc in all_orm_locations
            ]

            if not all_pg_locations_dtos:
                self.logger.warning("Не удалось преобразовать ORM-объекты в DTO. Генерация прервана.")
                return True

            self.logger.info(f"Получено {len(all_pg_locations_dtos)} локаций из PostgreSQL. Начинаем сборку регионов...")

            # 2. TRANSFORM: Собираем регионы
            world_regions = await self._build_regions(all_pg_locations_dtos)
            
            if not world_regions:
                self.logger.warning("Не удалось собрать ни одного региона.")
                return True

            # 3. LOAD: Сохраняем регионы в MongoDB
            self.logger.info(f"Собрано {len(world_regions)} регионов. Сохранение статической карты в MongoDB...")
            
            regions_to_save: List[Dict[str, Any]] = []
            for region in world_regions:
                region_dict = region.model_dump()
                region_dict['_id'] = region_dict.pop('id')
                regions_to_save.append(region_dict)
            
            if regions_to_save:
                result = await self.mongo_world_repo.bulk_save_regions(regions_to_save)
                self.logger.info(
                    f"✅ Успешно сохранено/обновлено: {getattr(result, 'upserted_count', 0) + getattr(result, 'modified_count', 0)} регионов."
                )
            
            # 4. Инициализация динамических локаций (без изменений)
            self.logger.info("🚀 Начало инициализации динамических документов локаций...")
            await self._initialize_and_store_dynamic_locations(all_pg_locations_dtos)
            
            return True

        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка во время генерации карты мира: {e}", exc_info=True)
            return False

    async def _build_regions(self, all_pg_locations: List[GameLocationData]) -> List[WorldRegionDocument]:
        """Собирает плоский список локаций в иерархию регионов."""
        locations_by_access_key = WorldMapBuilderUtils.get_location_by_access_key(all_pg_locations)
        children_by_parent_key = WorldMapBuilderUtils.build_parent_child_map(all_pg_locations)
        root_locations = WorldMapBuilderUtils.get_root_locations(all_pg_locations)
        
        # --- УДАЛЕНО ---: Весь блок получения связей из Redis удален отсюда.

        final_regions = []
        for root_loc in root_locations: 
            region_locations: Dict[str, StaticLocationData] = {}
            
            await self._collect_location_tree(
                current_loc_access_key=root_loc.access_key, 
                locations_by_access_key=locations_by_access_key,
                children_by_parent_key=children_by_parent_key,
                output_dict=region_locations
            )
            
            if region_locations:
                region_doc = WorldRegionDocument(
                    id=root_loc.access_key,
                    name=root_loc.name,
                    locations=region_locations
                )
                final_regions.append(region_doc)
                
        return final_regions

    async def _collect_location_tree(self, current_loc_access_key: str, 
                                     locations_by_access_key: Dict[str, GameLocationData], 
                                     children_by_parent_key: Dict,
                                     output_dict: Dict):
        """Рекурсивная функция для сборки дерева одного региона."""
        if current_loc_access_key in output_dict:
            return

        pg_loc = locations_by_access_key.get(current_loc_access_key)
        if not pg_loc:
            return

        # --- ИСПРАВЛЕНИЕ 1: Работаем с exits как с объектами, а не словарями ---
        exits_for_current_loc = []
        if pg_loc.exits:
            for exit_obj in pg_loc.exits:
                try:
                    # Используем прямой доступ к атрибутам .label и .target_location_id
                    exits_for_current_loc.append(LocationExit(
                        label=exit_obj.label,
                        target_location_id=exit_obj.target_location_id
                    ))
                except Exception as e:
                    self.logger.warning(f"Не удалось обработать выход {exit_obj} для локации {pg_loc.access_key}: {e}")

        child_locs = children_by_parent_key.get(current_loc_access_key, [])
        
        try:
            # --- ИСПРАВЛЕНИЕ 2: Явно преобразуем presentation в словарь ---
            presentation_dict = None
            if isinstance(pg_loc.presentation, BaseModel):
                presentation_dict = pg_loc.presentation.model_dump()
            elif isinstance(pg_loc.presentation, dict):
                presentation_dict = pg_loc.presentation

            static_data = StaticLocationData(
                location_id=pg_loc.access_key, 
                parent_id=pg_loc.parent_id,
                name=pg_loc.name,
                description=pg_loc.description,
                type=pg_loc.specific_category,
                exits=exits_for_current_loc,
                unified_display_type=pg_loc.unified_display_type,
                specific_category=pg_loc.specific_category,
                presentation=presentation_dict, # <-- Передаем готовый словарь
                entry_point_location_id=pg_loc.entry_point_location_id,
                flavor_text_options=pg_loc.flavor_text_options,
                tags=pg_loc.tags,
            )
            output_dict[current_loc_access_key] = static_data
        except Exception as dto_e:
            self.logger.error(f"Ошибка DTO для '{current_loc_access_key}': {dto_e}", exc_info=True)
            return
        
        for child_loc in child_locs: 
            await self._collect_location_tree(
                child_loc.access_key, 
                locations_by_access_key,
                children_by_parent_key,
                output_dict
            )

    # all_pg_locations теперь List[GameLocationData]
    async def _initialize_and_store_dynamic_locations(self, all_pg_locations: List[GameLocationData]) -> bool:
        """
        Создает и сохраняет пустые динамические документы для каждой локации.
        """
        self.logger.debug("Debug: _initialize_and_store_dynamic_locations started.")
        dynamic_locations_to_save: List[Dict[str, Any]] = []

        # 🔥 ДОБАВЛЕНО: Получаем World_instance_id из конфига или заглушки (ВАЖНО: замените на реальный ID)
        # Если у вас есть один глобальный ID для текущего инстанса мира, используйте его.
        # Временная заглушка:
        world_instance_id = "main_world_instance_001" 
        self.logger.debug(f"Debug: Используется world_instance_id: {world_instance_id}")

        # pg_loc теперь GameLocationData DTO
        for pg_loc in all_pg_locations: 
            try:
                # Создаем пустой динамический документ для каждой локации
                active_loc_doc = ActiveLocationDocument(
                    _id=pg_loc.access_key, 
                    world_instance_id=world_instance_id,
                    last_update=datetime.utcnow(),
                    players=[],
                    npcs=[],
                    items_on_ground=[],
                    resource_nodes=[],
                    location_effects=[]
                )
                dynamic_locations_to_save.append(active_loc_doc.model_dump(by_alias=True))
                self.logger.debug(f"Debug: Сформирован ActiveLocationDocument для локации: {pg_loc.access_key}") 
            except Exception as e:
                self.logger.error(f"Ошибка при создании ActiveLocationDocument для локации '{pg_loc.access_key}': {e}", exc_info=True) 
                continue # Пропускаем эту локацию, если не удалось создать DTO
        
        if not dynamic_locations_to_save:
            self.logger.warning("Не сформировано ни одного динамического документа локации. Пропускаем сохранение.")
            self.logger.debug("Debug: dynamic_locations_to_save is empty.")
            return True

        self.logger.info(f"Сформировано {len(dynamic_locations_to_save)} динамических документов локаций. Сохранение в MongoDB...")
        
        try:
            # Используется bulk_save_active_locations
            result = await self.location_state_repo.bulk_save_active_locations(dynamic_locations_to_save)
                        
            self.logger.debug(f"Debug: Результат bulk_save_active_locations: upserted_count={getattr(result, 'upserted_count', 'N/A')}, modified_count={getattr(result, 'modified_count', 'N/A')}, matched_count={getattr(result, 'matched_count', 'N/A')}")
            
            self.logger.info(
                f"✅ Успешно сохранено/обновлено в MongoDB: "
                f"{getattr(result, 'upserted_count', 0) + getattr(result, 'modified_count', 0)} динамических локаций."
            )
            self.logger.debug("Debug: _initialize_and_store_dynamic_locations finished successfully.")
            return True
        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при сохранении динамических локаций в MongoDB: {e}", exc_info=True)
            self.logger.debug("Debug: _initialize_and_store_dynamic_locations finished with error.")
            return False
