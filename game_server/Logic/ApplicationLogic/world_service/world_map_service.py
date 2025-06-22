# game_server/Logic/ApplicationLogic/world_service/world_map_service.py

import logging
from typing import Dict, Any, List, Optional

# Импорты для генератора (внутренняя зависимость)


# Импорты для внешних зависимостей
from game_server.Logic.ApplicationLogic.world_service.world_map_generation.world_map_generator import WorldMapGenerator
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_mongo.mongo_repository_manager import MongoRepositoryManager

# Импорты для высокоуровневых запросов (внутренняя зависимость)
# Если MapQueryService будет отдельным классом внутри этого модуля
# from game_server.Logic.ApplicationLogic.world_service.map_query_processor import MapQueryProcessor # Если будет такой внутренний процессор

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

class WorldMapService:
    """
    Главный сервис для управления картой мира.
    Предоставляет методы для генерации мира (для предстартового режима)
    и высокоуровневые методы для работы с данными карты (для роутов/других систем).
    Разработан с учетом потенциального выделения в отдельный Docker-контейнер
    и работы через шину команд.
    """
    def __init__(self, 
                 repository_manager: RepositoryManager,
                 redis_client: CentralRedisClient,
                 mongo_repository_manager: MongoRepositoryManager):
        
        self.repository_manager = repository_manager
        self.redis_client = redis_client
        self.mongo_repository_manager = mongo_repository_manager
        self.logger = logger
        
        # ВНУТРЕННИЕ ЗАВИСИМОСТИ СЕРВИСА:
        # 1. Генератор карты мира (для генерации/обновления данных)
        self._world_map_generator = WorldMapGenerator(
            repository_manager=self.repository_manager,
            redis_client=self.redis_client,
            mongo_repository_manager=self.mongo_repository_manager
        )
        
        # 2. Обработчик высокоуровневых запросов к карте мира
        # (Возможно, это будет внутренний класс или просто методы самого WorldMapService)
        # Если MapQueryService будет отдельным классом, инициализируем его здесь:
        # self._map_query_processor = MapQueryProcessor(mongo_repository_manager=self.mongo_repository_manager)

        self.logger.info("✅ WorldMapService инициализирован. Готов к работе с картой мира.")

    # --- МЕТОД 1: ДЛЯ ГЕНЕРАЦИИ МИРА (ПРЕДСТАРТОВЫЙ РЕЖИМ) ---
    async def initialize_world_map_for_startup(self) -> bool:
        """
        Инициализирует/обновляет карту мира в MongoDB.
        Этот метод предназначен для вызова во время предстартовой подготовки сервера.
        Возможное будущее: может быть вызван воркером по команде из шины.
        """
        self.logger.info("🚀 Запуск инициализации карты мира для старта сервера...")
        success = await self._world_map_generator.generate_and_store_world_map() # Вызов внутреннего генератора
        
        if success:
            self.logger.info("✅ Инициализация карты мира завершена успешно.")
            return True
        else:
            self.logger.critical("❌ Инициализация карты мира завершилась с ошибкой.")
            return False

    # --- МЕТОД 2: ДЛЯ ВЫСОКОУРОВНЕВОЙ РАБОТЫ С КАРТОЙ (ДЛЯ РОУТОВ/ДРУГИХ СИСТЕМ) ---
    # Эти методы будут публичными и использоваться внешними потребителями.
    # Они могут быть реализованы прямо здесь или делегированы внутреннему "процессору" (_map_query_processor).

    async def get_location_details(self, access_key: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает полную детализацию локации по её access_key из MongoDB.
        Этот метод может быть вызван через REST API (роутом) или по команде из шины.
        """
        self.logger.debug(f"Запрос публичной детализации локации для access_key: {access_key}")
        # Делегируем запрос MongoRepositoryManager.
        # Если бы был внутренний _map_query_processor, то self._map_query_processor.get_location_details(access_key)
        location_data = await self.mongo_repository_manager.world_state.get_location_by_id(access_key)
        if location_data:
            self.logger.debug(f"Получена публичная детализация для локации: {access_key}")
            return location_data
        else:
            self.logger.warning(f"Публичная локация с access_key '{access_key}' не найдена.")
            return None

    async def get_all_main_regions(self) -> List[Dict[str, Any]]:
        """
        Возвращает список всех основных регионов мира.
        """
        self.logger.debug("Запрос всех основных регионов мира через публичный API.")
        all_locations = await self.mongo_repository_manager.world_state.get_all_locations()
        main_regions = [
            loc for loc in all_locations 
            if loc.get('parent_access_key') is None and loc.get('location_type') in ['REGION', 'CITY']
        ]
        self.logger.info(f"Найдено {len(main_regions)} основных регионов.")
        return main_regions
    
    # async def handle_command_from_bus(self, command_type: str, payload: Dict[str, Any]):
    #     """
    #     Пример метода, который мог бы быть слушателем команд из шины (RabbitMQ).
    #     Если этот WorldMapService будет отдельным Docker-контейнером.
    #     """
    #     self.logger.info(f"Получена команда '{command_type}' из шины с payload: {payload}")
    #     if command_type == "GET_LOCATION_DETAILS_COMMAND":
    #         location_id = payload.get("location_id")
    #         if location_id:
    #             details = await self.get_location_details(location_id)
    #             # Отправить результат обратно в шину или другой сервис
    #             self.logger.info(f"Обработана команда GET_LOCATION_DETAILS для {location_id}. Результат: {details is not None}")
    #         else:
    #             self.logger.warning("Команда GET_LOCATION_DETAILS_COMMAND без location_id.")
    #     else:
    #         self.logger.warning(f"Неизвестная команда шины: {command_type}")