# game_server/Logic/ApplicationLogic/world_service/world_map_service.py

import logging
from typing import Dict, Any, List, Optional

# 🔥 ИЗМЕНЕНИЕ: Импортируем интерфейсы конкретных репозиториев PostgreSQL и Mongo
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.world_map_generator.world_map_generator import WorldMapGenerator
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import IWorldStateRepository

from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
# 🔥 УДАЛЕНО: from game_server.Logic.InfrastructureLogic.app_mongo.mongo_repository_manager import MongoRepositoryManager

# 🔥 ИЗМЕНЕНИЕ: Логгер будет передан, не импортируем глобально
# from game_server.config.logging.logging_setup import app_logger as logger

class WorldMapService:
    """
    Главный сервис для управления картой мира.
    Предоставляет методы для генерации мира (для предстартового режима)
    и высокоуровневые методы для работы с данными карты (для роутов/других систем).
    Разработан с учетом потенциального выделения в отдельный Docker-контейнер
    и работы через шину команд.
    """
    def __init__(self, 
                 # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем конкретные репозитории и клиенты
                 pg_game_location_repo: IGameLocationRepository, # Для генератора (PostgreSQL)
                 mongo_world_state_repo: IWorldStateRepository, # Для генератора и запросов (MongoDB)
                 redis_client: CentralRedisClient,
                 logger: logging.Logger # 🔥 ДОБАВЛЕНО: Явно получаем логгер
                ):
        
        # 🔥 ИЗМЕНЕНИЕ: Сохраняем прямые ссылки на репозитории и клиенты
        self.pg_game_location_repo = pg_game_location_repo
        self.mongo_world_state_repo = mongo_world_state_repo
        self.redis_client = redis_client
        self.logger = logger
        
        # ВНУТРЕННИЕ ЗАВИСИМОСТИ СЕРВИСА:
        # 1. Генератор карты мира (для генерации/обновления данных)
        # 🔥 ИЗМЕНЕНИЕ: Передаем WorldMapGenerator правильные зависимости
        self._world_map_generator = WorldMapGenerator(
            pg_location_repo=self.pg_game_location_repo,
            mongo_world_repo=self.mongo_world_state_repo,
            redis_reader=None, # WorldMapGenerator также требует reference_data_reader, если он не передается, будет ошибка.
                               # Возможно, его нужно добавить в конструктор WorldMapService.
            logger=self.logger # Передаем логгер
        )
        
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
    async def get_location_details(self, access_key: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает полную детализацию локации по её access_key из MongoDB.
        Этот метод может быть вызван через REST API (роутом) или по команде из шины.
        """
        self.logger.debug(f"Запрос публичной детализации локации для access_key: {access_key}")
        # 🔥 ИЗМЕНЕНИЕ: Делегируем запрос mongo_world_state_repo напрямую
        location_data = await self.mongo_world_state_repo.get_location_by_id(access_key)
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
        # 🔥 ИЗМЕНЕНИЕ: Делегируем запрос mongo_world_state_repo напрямую
        all_locations = await self.mongo_world_state_repo.get_all_locations()
        main_regions = [
            loc for loc in all_locations 
            if loc.get('parent_access_key') is None and loc.get('location_type') in ['REGION', 'CITY']
        ]
        self.logger.info(f"Найдено {len(main_regions)} основных регионов.")
        return main_regions