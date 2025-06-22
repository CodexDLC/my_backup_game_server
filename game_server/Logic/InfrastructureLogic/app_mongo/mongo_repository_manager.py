# game_server/Logic/InfrastructureLogic/app_mongo/mongo_repository_manager.py
import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase # <--- Импорт для типизации AsyncIOMotorDatabase

# Импортируем реализацию вашего центрального клиента Motor, чтобы получить DB-объект


# Импортируем реализации репозиториев
from game_server.Logic.InfrastructureLogic.app_mongo.mongo_client import get_mongo_database
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.interfaces_world_state_mongo import IWorldStateMongoRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.world_state.world_state_repository_mongo_impl import WorldStateMongoRepositoryImpl

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

class MongoRepositoryManager:
    def __init__(self): # <--- Конструктор теперь не принимает клиента напрямую, а использует get_mongo_database()
        self.logger = logger
        # Получаем асинхронный объект базы данных из глобального инициализированного клиента
        self._mongo_database: AsyncIOMotorDatabase = get_mongo_database() # <--- Используем ваш get_mongo_database()
        self.logger.info("✅ MongoRepositoryManager инициализирован.")

        # Инициализация доменно-ориентированных репозиториев
        self._world_state_repo: IWorldStateMongoRepository = WorldStateMongoRepositoryImpl(
            mongo_database=self._mongo_database # <--- Передаем объект базы данных
        )
        # Добавьте здесь инициализацию других репозиториев по мере их создания
        # self._bot_commands_repo: IBotCommandsMongoRepository = BotCommandsMongoRepositoryImpl(mongo_database=self._mongo_database)
            
    @property
    def world_state(self) -> IWorldStateMongoRepository:
        return self._world_state_repo
    
    # Добавьте другие свойства для доступа к репозиториям
    # @property
    # def bot_commands(self) -> IBotCommandsMongoRepository:
    #     return self._bot_commands_repo