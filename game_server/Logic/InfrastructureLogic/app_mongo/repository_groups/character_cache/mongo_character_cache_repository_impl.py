# game_server/Logic/InfrastructureLogic/app_mongo/repository_groups/character_cache/mongo_character_cache_repository_impl.py

import logging
from typing import Dict, Any, Optional
import inject
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.results import UpdateResult, DeleteResult
from pymongo.errors import PyMongoError

from .interfaces_character_cache_mongo import IMongoCharacterCacheRepository

# Используем ваш логгер
from game_server.config.logging.logging_setup import app_logger as logger

class MongoCharacterCacheRepositoryImpl(IMongoCharacterCacheRepository):
    """
    Реализация репозитория для "тёплого кэша" персонажей в MongoDB.
    """
    _collection_name = "characters_warm_cache"
    
    @inject.autoparams()
    def __init__(self, db_instance: AsyncIOMotorDatabase):
        self.db = db_instance
        self.collection = self.db[self._collection_name]
        logger.info(f"✅ {self.__class__.__name__} инициализирован с коллекцией '{self._collection_name}'.")


    async def get_character_by_id(self, character_id: int) -> Optional[Dict[str, Any]]:
        try:
            document = await self.collection.find_one({"_id": character_id})
            if document:
                logger.debug(f"Документ для персонажа ID {character_id} найден в MongoDB.")
            else:
                logger.debug(f"Документ для персонажа ID {character_id} не найден в MongoDB.")
            return document
        except PyMongoError as e:
            logger.error(f"Ошибка MongoDB при получении персонажа ID {character_id}: {e}", exc_info=True)
            raise

    async def upsert_character(self, character_document: Dict[str, Any]) -> None:
        character_id = character_document.get("_id")
        if not character_id:
            logger.error("Попытка upsert документа персонажа без '_id'.")
            raise ValueError("Документ персонажа должен содержать поле '_id'.")

        try:
            result: UpdateResult = await self.collection.update_one(
                {"_id": character_id},
                {"$set": character_document},
                upsert=True
            )
            if result.upserted_id:
                logger.info(f"Новый документ для персонажа ID {character_id} создан в MongoDB.")
            else:
                logger.info(f"Документ для персонажа ID {character_id} обновлен в MongoDB.")

        except PyMongoError as e:
            logger.error(f"Ошибка MongoDB при upsert персонажа ID {character_id}: {e}", exc_info=True)
            raise


    async def delete_character(self, character_id: int) -> bool:
        try:
            result: DeleteResult = await self.collection.delete_one({"_id": character_id})
            if result.deleted_count > 0:
                logger.info(f"Документ персонажа ID {character_id} удален из MongoDB.")
                return True
            else:
                logger.warning(f"Документ персонажа ID {character_id} не найден для удаления в MongoDB.")
                return False
        except PyMongoError as e:
            logger.error(f"Ошибка MongoDB при удалении персонажа ID {character_id}: {e}", exc_info=True)
            raise