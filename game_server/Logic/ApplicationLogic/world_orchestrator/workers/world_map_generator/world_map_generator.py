# game_server/Logic/ApplicationLogic/world_orchestrator/workers/world_map_generator/world_map_generator.py

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime

# --- Импорты репозиториев и DTO ---
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import ILocationStateRepository, IWorldStateRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_reader import ReferenceDataReader


# Импортируем GameLocationData для доступа к новым полям из YAML

# Импортируем ORM-модель GameLocation для преобразования

from game_server.contracts.db_models.mongo.world_map.data_models import ActiveLocationDocument, LocationExit, StaticLocationData, WorldRegionDocument
from game_server.contracts.dtos.orchestrator.data_models import GameLocationData
from game_server.database.models.models import GameLocation 

from pydantic import BaseModel # Для isinstance проверки

# Импортируем утилиты для построения карты
from game_server.Logic.ApplicationLogic.shared_logic.world_map_service.world_map_builder_utils import WorldMapBuilderUtils

class WorldMapGenerator:
    """
    Отвечает за генерацию статической карты мира.
    1. Читает данные из PostgreSQL.
    2. Обогащает их данными о связях из Redis.
    3. Собирает в иерархическую структуру регионов.
    4. Сохраняет результат в MongoDB.
    5. Инициализирует пустые динамические документы локаций.
    """
    def __init__(self,
                 pg_location_repo: IGameLocationRepository,
                 mongo_world_repo: IWorldStateRepository,
                 location_state_repo: ILocationStateRepository,
                 redis_reader: ReferenceDataReader,
                 logger: logging.Logger):
        self.pg_location_repo = pg_location_repo
        self.mongo_world_repo = mongo_world_repo
        self.location_state_repo = location_state_repo
        self.redis_reader = redis_reader
        self.logger = logger

    async def generate_and_store_world_map(self) -> bool:
        """Основной метод, запускающий весь процесс."""
        self.logger.info("🚀 Начало генерации статической карты мира...")
        self.logger.debug("--- Debug: generate_and_store_world_map started ---")
        
        try:
            # 1. EXTRACT: Получаем все локации из PostgreSQL (ORM-объекты)
            self.logger.debug("Debug: Шаг 1: Получение всех локаций из PostgreSQL.")
            all_orm_locations: List[GameLocation] = await self.pg_location_repo.get_all() 
            
            if not all_orm_locations:
                self.logger.warning("Не найдено ни одной локации в PostgreSQL. Генерация прервана.")
                self.logger.debug("Debug: Шаг 1 завершен с предупреждением: all_orm_locations is empty.")
                return True # Завершаем успешно, так как ошибки нет

            # Преобразуем ORM-объекты в Pydantic DTO
            all_pg_locations_dtos: List[GameLocationData] = []
            for loc in all_orm_locations:
                try:
                    all_pg_locations_dtos.append(GameLocationData.model_validate(loc.to_dict()))
                except Exception as e:
                    self.logger.error(f"Ошибка при преобразовании ORM-объекта GameLocation '{loc.access_key}' в DTO: {e}", exc_info=True)
                    continue 

            if not all_pg_locations_dtos:
                self.logger.warning("Все локации из PostgreSQL не удалось преобразовать в DTO. Генерация прервана.")
                return True

            self.logger.info(f"Получено {len(all_pg_locations_dtos)} локаций из PostgreSQL. Начинаем сборку регионов...")
            self.logger.debug(f"Debug: Первые 5 локаций из PG: {[loc.access_key for loc in all_pg_locations_dtos[:5]]}") 

            # 2. TRANSFORM: Собираем регионы
            self.logger.debug("Debug: Шаг 2: Начинаем сборку регионов (_build_regions).")
            world_regions = await self._build_regions(all_pg_locations_dtos) # Передаем DTO
            
            if not world_regions:
                self.logger.warning("Не удалось собрать ни одного региона. Проверьте структуру parent_id или наличие корневых локаций.")
                self.logger.debug("Debug: Шаг 2 завершен с предупреждением: world_regions is empty.")
                return True

            # 3. LOAD: Сохраняем регионы в MongoDB (статическая карта)
            self.logger.info(f"Собрано {len(world_regions)} регионов. Сохранение статической карты в MongoDB...")
            self.logger.debug(f"Debug: Шаг 3: Начинаем сохранение статической карты в MongoDB (bulk_save_regions).")
            
            self.logger.debug(f"Debug: Количество регионов для сохранения: {len(world_regions)}")
            
            regions_to_save: List[Dict[str, Any]] = []
            for i, region in enumerate(world_regions):
                try:
                    # 🔥 ГЛАВНОЕ ИЗМЕНЕНИЕ: Явно формируем словарь с '_id'
                    region_dict = region.model_dump(by_alias=False) # Получаем словарь с внутренним 'id'
                    region_dict['_id'] = region_dict['id'] # Копируем значение 'id' в '_id'
                    del region_dict['id'] # Удаляем 'id', если оно не нужно в Mongo
                    regions_to_save.append(region_dict) 
                except Exception as dump_e:
                    self.logger.error(f"Ошибка при model_dump для региона {i} (ID: {getattr(region, 'id', 'N/A')}): {dump_e}", exc_info=True) # Используем 'id'
                    continue
            
            if not regions_to_save:
                self.logger.warning("Все регионы оказались невалидными или не удалось их сериализовать. Сохранение статической карты в MongoDB отменено.")
                self.logger.debug("Debug: Шаг 3 завершен с предупреждением: regions_to_save is empty after dump.")
                return True

            result = await self.mongo_world_repo.bulk_save_regions(regions_to_save)
            
            self.logger.debug(f"Debug: Результат bulk_save_regions: upserted_count={getattr(result, 'upserted_count', 'N/A')}, modified_count={getattr(result, 'modified_count', 'N/A')}, matched_count={getattr(result, 'matched_count', 'N/A')}")

            self.logger.info(
                f"✅ Успешно сохранено/обновлено в MongoDB: "
                f"{getattr(result, 'upserted_count', 0) + getattr(result, 'modified_count', 0)} регионов статической карты."
            )
            
            # Инициализация и сохранение динамических локаций
            self.logger.info("🚀 Начало инициализации динамических документов локаций...")
            self.logger.debug("Debug: Шаг 4: Инициализация и сохранение динамических локаций.")

            await self._initialize_and_store_dynamic_locations(all_pg_locations_dtos) # Передаем DTO
            
            self.logger.debug("--- Debug: generate_and_store_world_map finished successfully ---")
            return True

        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка во время генерации карты мира: {e}", exc_info=True)
            self.logger.debug("--- Debug: generate_and_store_world_map finished with critical error ---")
            return False

    # all_pg_locations теперь List[GameLocationData]
    async def _build_regions(self, all_pg_locations: List[GameLocationData]) -> List[WorldRegionDocument]:
        """Собирает плоский список локаций в иерархию регионов."""
        self.logger.debug("Debug: _build_regions started.")
        
        # --- Шаг 2.1: Подготовка данных ---
        self.logger.debug("Debug: Шаг 2.1: Подготовка данных WorldMapBuilderUtils.")
        # Передаем GameLocationData DTO
        locations_by_access_key: Dict[str, GameLocationData] = WorldMapBuilderUtils.get_location_by_access_key(all_pg_locations)
        children_by_parent_key = WorldMapBuilderUtils.build_parent_child_map(all_pg_locations)
        root_locations = WorldMapBuilderUtils.get_root_locations(all_pg_locations)
        
        self.logger.debug(f"Debug: Количество локаций по access_key: {len(locations_by_access_key)}")
        self.logger.debug(f"Debug: Количество родительских связей: {len(children_by_parent_key)}")
        self.logger.debug(f"Debug: Количество корневых локаций: {len(root_locations)}")

        # --- Шаг 2.2: Получение всех связей из Redis заранее ---
        self.logger.debug("Debug: Шаг 2.2: Получение всех связей из Redis (get_world_connections_data).")
        all_connections_data = await self.redis_reader.get_world_connections_data()
        
        if not all_connections_data:
            self.logger.info("Нет данных о связях локаций в Redis. Регионы будут без выходов.")
            self.logger.debug("Debug: all_connections_data is empty.")

        connections_by_from_key = defaultdict(list)
        for conn in all_connections_data:
            try:
                if isinstance(conn, Dict) and 'from' in conn and 'description' in conn and 'to' in conn:
                    connections_by_from_key[conn['from']].append(LocationExit(label=conn['description'], target_location_id=conn['to']))
                else:
                    self.logger.warning(f"⚠️ Некорректный формат данных связи в Redis: {conn}. Ожидался словарь с 'from', 'description', 'to'. Пропускаем.")
            except Exception as conn_e:
                self.logger.error(f"Ошибка при обработке данных связи {conn}: {conn_e}", exc_info=True)
                continue
        self.logger.debug(f"Debug: Количество связей по from_key: {len(connections_by_from_key)}")


        # --- Шаг 2.3: Сборка каждого региона ---
        self.logger.debug("Debug: Шаг 2.3: Сборка финальных регионов.")
        final_regions = []
        # root_loc теперь GameLocationData DTO
        for i, root_loc in enumerate(root_locations): 
            self.logger.debug(f"Debug: Обработка корневой локации {i+1}/{len(root_locations)}: {root_loc.access_key}") 
            region_locations: Dict[str, StaticLocationData] = {}
            
            await self._collect_location_tree(
                current_loc_access_key=root_loc.access_key, 
                locations_by_access_key=locations_by_access_key,
                children_by_parent_key=children_by_parent_key,
                all_connections_by_from_key=connections_by_from_key,
                output_dict=region_locations
            )
            
            if not region_locations:
                self.logger.warning(f"Регион, начинающийся с '{root_loc.access_key}', не содержит локаций после сборки дерева. Пропускаем этот регион.") 
                continue

            try:
                region_doc = WorldRegionDocument(
                    id=root_loc.access_key, # � ИЗМЕНЕНИЕ: Используем 'id' вместо '_id' для инициализации DTO
                    name=root_loc.name,
                    locations=region_locations
                )
                final_regions.append(region_doc)
                self.logger.debug(f"Debug: Регион '{root_loc.access_key}' успешно сформирован.") 
            except Exception as region_e:
                self.logger.error(f"Ошибка при создании WorldRegionDocument для корневой локации '{root_loc.access_key}': {region_e}", exc_info=True) 
                continue
                
        self.logger.debug(f"Debug: _build_regions finished. Сформировано {len(final_regions)} WorldRegionDocument.")
        return final_regions

    # locations_by_access_key теперь Dict[str, GameLocationData]
    async def _collect_location_tree(self, current_loc_access_key: str, locations_by_access_key: Dict[str, GameLocationData], 
                                      children_by_parent_key: Dict, all_connections_by_from_key: Dict,
                                      output_dict: Dict):
        """Рекурсивная функция для сборки дерева одного региона."""
        self.logger.debug(f"Debug: _collect_location_tree: Обработка {current_loc_access_key}")
        
        if current_loc_access_key in output_dict:
            self.logger.debug(f"Debug: _collect_location_tree: Локация {current_loc_access_key} уже обработана, пропуск.")
            return

        # pg_loc теперь GameLocationData DTO
        pg_loc: GameLocationData = locations_by_access_key.get(current_loc_access_key)
        if not pg_loc:
            self.logger.warning(f"Локация с access_key '{current_loc_access_key}' не найдена в исходных данных PostgreSQL. Пропускаем.")
            return

        # --- Шаг 2.4: Обогащение данными из Redis (связи/выходы) ---
        self.logger.debug(f"Debug: Шаг 2.4: Получение связей для {current_loc_access_key}.")
        exits_for_current_loc = all_connections_by_from_key.get(current_loc_access_key, [])
        self.logger.debug(f"Debug: Найдено {len(exits_for_current_loc)} выходов для {current_loc_access_key}.")

        # --- Шаг 2.5: Формирование DTO локации для MongoDB (StaticLocationData) ---
        self.logger.debug(f"Debug: Шаг 2.5: Формирование StaticLocationData для {current_loc_access_key}.")
        # child_locs теперь List[GameLocationData]
        child_locs: List[GameLocationData] = children_by_parent_key.get(current_loc_access_key, [])
        # Используем access_key для child_access_keys
        child_access_keys = [child.access_key for child in child_locs] 

        try:
            static_data = StaticLocationData(
                location_id=pg_loc.access_key, 
                parent_id=pg_loc.parent_id,
                type=pg_loc.specific_category, 
                name=pg_loc.name,
                description=pg_loc.description,
                exits=exits_for_current_loc,
                unified_display_type=pg_loc.unified_display_type,
                specific_category=pg_loc.specific_category,
                presentation=pg_loc.presentation.model_dump() if isinstance(pg_loc.presentation, BaseModel) else pg_loc.presentation, 
                entry_point_location_id=pg_loc.entry_point_location_id,
                flavor_text_options=pg_loc.flavor_text_options,
                tags=pg_loc.tags,
            )
            self.logger.debug(f"Debug: StaticLocationData для {current_loc_access_key} успешно сформирована.")
        except Exception as dto_e:
            self.logger.error(f"Ошибка валидации DTO при формировании StaticLocationData для '{current_loc_access_key}': {dto_e}", exc_info=True)
            return

        output_dict[current_loc_access_key] = static_data
        
        # child_loc теперь GameLocationData DTO
        for child_loc in child_locs: 
            await self._collect_location_tree(
                child_loc.access_key, 
                locations_by_access_key,
                children_by_parent_key,
                all_connections_by_from_key,
                output_dict
            )
        self.logger.debug(f"Debug: _collect_location_tree: Завершено для {current_loc_access_key}.")

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
