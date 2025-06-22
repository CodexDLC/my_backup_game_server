# game_server/Logic/ApplicationLogic/world_map_generation/world_map_generator.py

import logging
from typing import Dict, Any, List, Optional

# Импорты репозиториев/клиентов
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
# Импортируем MongoRepositoryManager, который будет агрегировать репозитории MongoDB
from game_server.Logic.InfrastructureLogic.app_mongo.mongo_repository_manager import MongoRepositoryManager

# Импорт DTOs, если они будут использоваться для связей
# from game_server.common_contracts.start_orcestrator.dtos import LocationConnectionData

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

class WorldMapGenerator:
    """
    Генератор данных для MongoDB, формирующий красивые представления
    локаций и их связей на основе данных из PostgreSQL и Redis.
    Использует MongoRepositoryManager для взаимодействия с MongoDB.
    """
    def __init__(self, 
                 repository_manager: RepositoryManager, # Для PostgreSQL
                 redis_client: CentralRedisClient,       # Для Redis
                 mongo_repository_manager: MongoRepositoryManager # Для MongoDB
                ):
        self.repository_manager = repository_manager
        self.redis_client = redis_client
        self.mongo_repository_manager = mongo_repository_manager
        self.logger = logger
        self.logger.info("✅ WorldMapGenerator инициализирован.")

    async def generate_and_store_world_map(self) -> bool:
        """
        Главный метод для генерации и сохранения карты мира в MongoDB.
        """
        try:
            self.logger.info("🚀 Запуск генерации и сохранения карты мира в MongoDB...")

            # 1. Получаем все локации из PostgreSQL
            game_locations_repo = self.repository_manager.game_locations
            all_locations_orm = await game_locations_repo.get_all()
            
            locations_data: Dict[str, Dict[str, Any]] = {
                loc.access_key: loc.to_dict() for loc in all_locations_orm
            }
            self.logger.info(f"Получено {len(locations_data)} локаций из PostgreSQL.")

            # 2. Получаем все связи локаций из Redis
            # Используем константу REDIS_KEY_WORLD_CONNECTIONS, которая должна быть доступна
            # либо через self.redis_client, либо импортирована напрямую.
            # Предполагаем, что она находится в game_server.config.constants.redis
            from game_server.config.constants.redis import REDIS_KEY_WORLD_CONNECTIONS
            
            connections_list: Optional[List[Dict[str, Any]]] = await self.redis_client.get_msgpack(
                REDIS_KEY_WORLD_CONNECTIONS 
            ) 

            if connections_list is None:
                connections_list = []
                self.logger.warning("⚠️ Не найдено данных о связях локаций в Redis. Создание карты без связей.")
            else:
                self.logger.info(f"Получено {len(connections_list)} связей локаций из Redis.")
            
            # 3. Формируем документы для MongoDB
            mongo_documents = []
            for access_key, loc_data in locations_data.items():
                doc = {
                    "_id": access_key, # Используем access_key как _id MongoDB
                    **loc_data # Разворачиваем все данные локации
                }
                
                doc['connections'] = []
                for conn in connections_list:
                    # Убедитесь, что 'from_location' и 'to_location' присутствуют в conn
                    if conn.get('from_location') == access_key:
                        doc['connections'].append({
                            "to_location": conn.get('to_location'),
                            "description": conn.get('description'),
                        })
                mongo_documents.append(doc)

            # 4. Сохраняем документы в MongoDB через MongoRepositoryManager
            # Предполагаем, что у MongoRepositoryManager есть свойство 'world_state'
            # и у него есть метод 'upsert_locations_with_connections' или аналогичный
            # для работы с коллекцией 'locations'.
            
            # Предварительно очищаем коллекцию (опционально, если хотите перезаписывать)
            world_state_mongo_repo = self.mongo_repository_manager.world_state # <-- ДОСТУП К РЕПОЗИТОРИЮ
            await world_state_mongo_repo.delete_all_locations() # <-- Предполагаемый метод очистки

            if mongo_documents:
                # Предполагаем, что world_state_mongo_repo имеет метод для массового upsert'а
                await world_state_mongo_repo.upsert_locations_with_connections(mongo_documents) # <-- Предполагаемый метод upsert
                self.logger.info(f"✅ Успешно сгенерировано и сохранено {len(mongo_documents)} документов локаций в MongoDB.")
            else:
                self.logger.warning("Не было документов для сохранения в MongoDB.")
            
            return True

        except Exception as e:
            self.logger.critical(f"🚨 Критическая ошибка при генерации или сохранении карты мира в MongoDB: {e}", exc_info=True)
            return False