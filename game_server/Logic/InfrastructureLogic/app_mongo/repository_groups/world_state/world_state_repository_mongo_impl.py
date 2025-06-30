# game_server/Logic/InfrastructureLogic/app_mongo/repository_groups/world_state/world_state_repository_mongo_impl.py
import logging
from typing import Dict, Any, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase # <--- Импорт для типизации AsyncIOMotorDatabase
from pymongo import UpdateMany # Для массового обновления/вставки

from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import IWorldStateMongoRepository
# Используем ваш уникальный логгер
from game_server.config.logging.logging_setup import app_logger as logger

class WorldStateMongoRepositoryImpl(IWorldStateMongoRepository):
    def __init__(self, mongo_database: AsyncIOMotorDatabase): # <--- Принимает AsyncIOMotorDatabase
        self.db = mongo_database
        self.locations_collection = self.db['locations'] # <--- Ваша коллекция 'locations'
        self.logger = logger
        self.logger.info("WorldStateMongoRepositoryImpl инициализирован.")

    async def upsert_locations_with_connections(self, documents: List[Dict[str, Any]]) -> None:
        """
        Массово вставляет или обновляет документы локаций в коллекцию 'locations'.
        Использует AsyncIOMotorClient для асинхронных операций.
        """
        if not documents:
            self.logger.info("Нет документов для вставки/обновления в коллекцию 'locations'.")
            return

        # Для массового upsert используем bulk_write с UpdateMany
        requests = []
        for doc in documents:
            # Важно: '_id' должен присутствовать в каждом документе
            if '_id' not in doc:
                self.logger.error(f"Документ не содержит '_id'. Пропуск: {doc}")
                continue
            requests.append(UpdateMany({'_id': doc['_id']}, {'$set': doc}, upsert=True))
        
        if requests:
            result = await self.locations_collection.bulk_write(requests, ordered=False) # ordered=False для параллельного выполнения
            self.logger.info(f"Вставлено: {result.upserted_count}, Обновлено: {result.matched_count} документов в коллекцию 'locations'.")
        else:
            self.logger.warning("После фильтрации не осталось документов для массовой записи.")

    async def delete_all_locations(self) -> None:
        """
        Очищает все документы из коллекции 'locations'.
        """
        result = await self.locations_collection.delete_many({})
        self.logger.info(f"Коллекция 'locations' очищена. Удалено документов: {result.deleted_count}.")

    # Добавьте другие необходимые методы для работы с коллекцией 'locations'
    async def get_location_by_id(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Получает документ локации по её _id."""
        return await self.locations_collection.find_one({'_id': location_id})

    async def get_all_locations(self) -> List[Dict[str, Any]]:
        """Получает все документы локаций."""
        return await self.locations_collection.find().to_list(None) # to_list(None) для получения всех результатов