# game_server/Logic/ApplicationLogic/auth_service/Handlers/login_character_by_id_handler.py

import logging
import inject
from typing import Callable, Optional, Dict, Any # Добавлены Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

# --- Локальная логика и зависимости ---

# Импорты фабрик репозиториев
from game_server.Logic.DomainLogic.system_services_logic.character_creation_logic.character_data_assembler import CharacterDataAssembler
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ICreatureTypeRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.character_cache.interfaces_character_cache_mongo import IMongoCharacterCacheRepository
from game_server.contracts.db_models.mongo.character.data_models import CharacterCacheDTO
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO, BaseResultDTO

from .i_auth_handler import IAuthHandler


class LoginCharacterByIdHandler(IAuthHandler):
    """
    Обработчик для команды character_login_by_id.
    Выполняет второй этап: формирование и запись "теплого кэша" в MongoDB.
    """
    @inject.autoparams()
    def __init__(self,
                 logger: logging.Logger, # <--- Добавлен логгер, если он не был первым
                 session_factory: Callable[[], AsyncSession], # <--- Фабрика сессий
                 char_repo_factory: Callable[[AsyncSession], ICharacterRepository], # <--- Фабрика ICharacterRepository
                 creature_repo_factory: Callable[[AsyncSession], ICreatureTypeRepository], # <--- Фабрика ICreatureTypeRepository
                 mongo_repo: IMongoCharacterCacheRepository, # <--- Mongo репозиторий, т.к. он не использует AsyncSession
                 assembler: CharacterDataAssembler,
                 ):
        self._logger = logger
        self._session_factory = session_factory
        self._char_repo_factory = char_repo_factory
        self._creature_repo_factory = creature_repo_factory
        self._mongo_repo = mongo_repo
        self._assembler = assembler
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def process(self, command: BaseCommandDTO) -> BaseResultDTO:
        """
        Обрабатывает команду, загружая данные и формируя кэш.

        :param command: Входной DTO команды.
        :return: DTO с результатом операции.
        """
        # Получаем correlation_id и другие системные поля из команды
        correlation_id = getattr(command, "correlation_id", None)
        trace_id = getattr(command, "trace_id", None)
        span_id = getattr(command, "span_id", None)
        client_id = getattr(command, "client_id", None)

        character_id = getattr(command.payload, "character_id", None) # Используем getattr для безопасности
        if not character_id:
            return BaseResultDTO(
                success=False,
                message="character_id is required in payload.",
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                client_id=client_id
            )

        try:
            # Сессия для чтения из PostgreSQL
            async with self._session_factory() as session:
                # Создаем экземпляры репозиториев с активной сессией
                character_repo = self._char_repo_factory(session)
                creature_repo = self._creature_repo_factory(session)

                # Загружаем данные персонажа и тип существа
                character_data = await character_repo.get_full_character_data_by_id(character_id) # Метод репозитория использует self.db_session
                if not character_data:
                    raise ValueError(f"Character with ID {character_id} not found in PostgreSQL.")

                creature_type = await creature_repo.get_by_id(character_data.creature_type_id) # Метод репозитория использует self.db_session
                creature_type_name = creature_type.name if creature_type else "Unknown"
            
                await session.commit() # Коммит транзакции на чтение, если требуется

            # Сборка и запись в MongoDB не требуют сессии PostgreSQL
            mongo_document = await self._assembler.assemble_warm_cache_document(character_data, creature_type_name)
            await self._mongo_repo.upsert_character(mongo_document)
            
            self._logger.info(f"Теплый кэш для персонажа ID {character_id} успешно сформирован и записан в MongoDB.")

            return BaseResultDTO(
                success=True,
                message="Character cache created successfully.",
                data=CharacterCacheDTO(character_document=mongo_document),
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                client_id=client_id
            )

        except Exception as e:
            self._logger.error(f"Ошибка при логине и кэшировании персонажа {character_id}: {e}", exc_info=True)
            # Откат сессии, если она была открыта и произошла ошибка.
            # Если исключение возникает после закрытия сессии, это не повлияет.
            if 'session' in locals() and session.in_transaction():
                await session.rollback()

            return BaseResultDTO(
                success=False,
                message=str(e),
                error={"code": "CACHE_CREATION_FAILED", "message": str(e)},
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                client_id=client_id
            )