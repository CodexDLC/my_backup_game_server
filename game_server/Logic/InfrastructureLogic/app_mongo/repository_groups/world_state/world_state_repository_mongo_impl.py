# game_server/Logic/InfrastructureLogic/app_mongo/repository_groups/world_state/world_state_repository_mongo_impl.py

import inject
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from typing import Optional, Dict, Any, List
from pymongo import ReplaceOne, UpdateOne 
from pymongo.results import BulkWriteResult

from game_server.Logic.InfrastructureLogic.app_mongo.base_repository import BaseMongoRepository


from .interfaces_world_state_mongo import IWorldStateRepository, ILocationStateRepository

logger = logging.getLogger(__name__) # Используем логгер для этого модуля

# --- Репозиторий для статических регионов мира ---

class MongoWorldStateRepositoryImpl(BaseMongoRepository, IWorldStateRepository):
    
    @inject.autoparams()
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, collection_name="static_world_regions")

    async def get_region_by_id(self, region_id: str) -> Optional[Dict[str, Any]]:
        """Получает один документ-регион по его ID."""
        return await self.get_by_id(region_id)

    async def get_all_regions(self) -> List[Dict[str, Any]]:
        """Получает все документы-регионы из коллекции."""
        return await self.get_all()

    async def save_region(self, region_data: Dict[str, Any]) -> bool:
        """
        Сохраняет или полностью перезаписывает один регион.
        Ожидается, что в region_data есть ключ '_id'.
        """
        region_id = region_data.get("_id")
        if not region_id:
            raise ValueError("Region data must contain an '_id' field.")
            
        result = await self.collection.replace_one(
            filter={"_id": region_id},
            replacement=region_data,
            upsert=True
        )
        return result.modified_count > 0 or result.upserted_id is not None

    async def bulk_save_regions(self, regions_data: List[Dict[str, Any]]) -> BulkWriteResult:
        """
        Выполняет пакетное сохранение/обновление нескольких регионов.
        Это предпочтительный метод для генератора.
        """
        if not regions_data:
            return BulkWriteResult({'ok': 1.0, 'writeErrors': [], 'writeConcernErrors': [], 'nInserted': 0, 'nUpserted': 0, 'nMatched': 0, 'nModified': 0, 'nRemoved': 0, 'upserted': []}, acknowledged=True)

        operations = [
            ReplaceOne(
                filter={"_id": region.get("_id")}, 
                replacement=region, 
                upsert=True
            )
            for region in regions_data if region.get("_id")
        ]
        
        if not operations:
            raise ValueError("All items in regions_data must contain an '_id' field.")

        # --- НАЧАЛО ДЕБАГ-ЛОГОВ (УДАЛИТЬ ПОСЛЕ РЕШЕНИЯ ПРОБЛЕМЫ) ---
        # Временные логи для диагностики проблемы 'object BulkWriteResult can't be used in await expression'
        logger.critical(f"DEBUG Mongo BEFORE: Попытка выполнить bulk_write. Количество операций: {len(operations)}")
        logger.critical(f"DEBUG Mongo: Тип self.collection: {type(self.collection)}")
        logger.critical(f"DEBUG Mongo: Является ли self.collection Motor-коллекцией (AsyncIOMotorCollection): {isinstance(self.collection, AsyncIOMotorCollection)}")
        logger.critical(f"DEBUG Mongo: У self.collection есть bulk_write: {'bulk_write' in dir(self.collection)}")
        if 'bulk_write' in dir(self.collection):
            logger.critical(f"DEBUG Mongo: Тип self.collection.bulk_write: {type(self.collection.bulk_write)}")
            logger.critical(f"DEBUG Mongo: Является ли self.collection.bulk_write awaitable: {hasattr(self.collection.bulk_write, '__await__')}")
        # --- КОНЕЦ ДЕБАГ-ЛОГОВ ---

        return await self.collection.bulk_write(operations)


# --- Репозиторий для "живых" локаций (ДОБАВЛЕН bulk_save_active_locations) ---

class MongoLocationStateRepositoryImpl(BaseMongoRepository, ILocationStateRepository):

    @inject.autoparams()
    def __init__(self, db: AsyncIOMotorDatabase):
        super().__init__(db, collection_name="active_locations")

    async def get_location_by_id(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Получает одну активную локацию по ID."""
        return await self.get_by_id(location_id)

    async def get_all_locations(self) -> List[Dict[str, Any]]:
        """Получает все активные локации."""
        return await self.get_all()

    async def add_player_to_location(self, location_id: str, player_data: Dict[str, Any]) -> bool:
        """Добавляет игрока в массив 'players'."""
        result = await self.collection.update_one(
            {"_id": location_id},
            {"$push": {"players": player_data}}
        )
        return result.modified_count > 0

    async def remove_player_from_location(self, location_id: str, player_id: str) -> bool:
        """Удаляет игрока из массива 'players' по его ID."""
        result = await self.collection.update_one(
            {"_id": location_id},
            {"$pull": {"players": {"player_id": player_id}}}
        )
        return result.modified_count > 0

    async def bulk_save_active_locations(self, documents: List[Dict[str, Any]]) -> BulkWriteResult:
        """
        Массово сохраняет (или обновляет, если _id совпадает) документы активных локаций.
        Использует upsert для существующих документов.
        """
        if not documents:
            return BulkWriteResult({'ok': 1.0, 'writeErrors': [], 'writeConcernErrors': [], 'nInserted': 0, 'nUpserted': 0, 'nMatched': 0, 'nModified': 0, 'nRemoved': 0, 'upserted': []}, acknowledged=True)

        operations = []
        for doc in documents:
            if "_id" not in doc:
                raise ValueError("Each document in bulk_save_active_locations must contain an '_id' field.")
            operations.append(
                UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True)
            )
        
        return await self.collection.bulk_write(operations)