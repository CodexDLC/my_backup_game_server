# game_server\Logic\ApplicationLogic\SystemServices\handler\account\create_new_character_handler.py

import logging
import inject
from typing import Callable, Optional, Dict, Any, List, Union # Добавлен Union для возвращаемого типа
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.DomainLogic.system_services_logic.character_creation_logic.character_data_assembler import CharacterDataAssembler
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal
from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.Logic.DomainLogic.system_services_logic.character_creation_logic.character_db_writer import CharacterDbWriter
from game_server.Logic.DomainLogic.system_services_logic.character_creation_logic.character_template_selector import CharacterTemplateSelector

# Импорты для MongoDB репозитория и репозитория типов существ
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import ICreatureTypeRepository
from game_server.Logic.InfrastructureLogic.app_mongo.repository_groups.character_cache.interfaces_character_cache_mongo import IMongoCharacterCacheRepository 
# НОВОЕ: Импорты для проверки существующих персонажей
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository
from game_server.contracts.api_models.character.responses import CharacterListResponseData, GetCharacterListForAccountResultDTO
from game_server.contracts.dtos.character.data_models import CharacterDTO
from game_server.database.models.models import Character # Для типизации raw_characters

from game_server.contracts.dtos.character.commands import CreateNewCharacterCommandDTO
from game_server.contracts.dtos.character.data_models import CharacterCreatedDTO
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
from game_server.contracts.shared_models.base_responses import ErrorDetail


class CreateNewCharacterHandler(ISystemServiceHandler):
    @inject.autoparams()
    def __init__(self,
                 template_selector: CharacterTemplateSelector,
                 db_writer: CharacterDbWriter,
                 data_assembler: CharacterDataAssembler,
                 creature_type_repo_factory: Callable[[AsyncSession], ICreatureTypeRepository],
                 mongo_character_repo: IMongoCharacterCacheRepository,
                 logger: logging.Logger,
                 character_repo_factory: Callable[[AsyncSession], ICharacterRepository], # НОВОЕ: Инжекция фабрики репозитория персонажей
                 ):
        self._template_selector = template_selector
        self._db_writer = db_writer
        self._data_assembler = data_assembler
        self._creature_type_repo_factory = creature_type_repo_factory
        self._mongo_character_repo = mongo_character_repo
        self._logger = logger
        self._character_repo_factory = character_repo_factory # НОВОЕ: Сохраняем фабрику репозитория персонажей
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    @transactional(AsyncSessionLocal)
    # ИЗМЕНЕНО: Возвращаемый тип теперь может быть GetCharacterListForAccountResultDTO
    async def process(self, session: AsyncSession, command_dto: CreateNewCharacterCommandDTO) -> Union[BaseResultDTO, GetCharacterListForAccountResultDTO]:
        correlation_id = command_dto.correlation_id
        trace_id = getattr(command_dto, "trace_id", None)
        span_id = getattr(command_dto, "span_id", None)
        client_id = getattr(command_dto, "client_id", None)

        payload = command_dto.payload
          # Pydantic уже проверил, что payload и account_id существуют,
          # поэтому мы можем обращаться к ним напрямую.
        account_id = payload.account_id
          
          # Если понадобятся другие данные из payload:
          # discord_user_id = payload.discord_user_id
          # guild_id = payload.guild_id

        try:
            # НОВОЕ: Шаг 0: Проверяем, есть ли уже персонажи у аккаунта
            character_repo = self._character_repo_factory(session)
            existing_raw_characters: List[Character] = await character_repo.get_characters_by_account_id(
                account_id=account_id
            )

            if existing_raw_characters:
                self._logger.warning(f"Аккаунт {account_id} уже имеет {len(existing_raw_characters)} персонажей. Возвращаем список вместо создания нового.")
                characters_dto: List[CharacterDTO] = []
                for char in existing_raw_characters:
                    characters_dto.append(CharacterDTO(
                        character_id=char.character_id,
                        name=char.name,
                        surname=char.surname,
                        creature_type_id=char.creature_type_id,
                        status=char.status,
                        clan_id=char.clan_id
                    ))
                
                # Возвращаем DTO со списком персонажей
                return GetCharacterListForAccountResultDTO(
                    correlation_id=correlation_id,
                    trace_id=trace_id,
                    span_id=span_id,
                    success=True,
                    message="Персонажи уже существуют. Возвращен список.",
                    data=CharacterListResponseData(characters=characters_dto),
                    client_id=client_id
                )

            # Если персонажей нет, продолжаем с существующей логикой создания
            self._logger.info(f"Начинается выбор шаблона для аккаунта {account_id}.")
            template = await self._template_selector.select_template(session)
            self._logger.info(f"Для аккаунта {account_id} выбран шаблон ID {template.character_pool_id}.")

            # 1. Создание персонажа в PostgreSQL
            new_character = await self._db_writer.create_character_from_template(
                session=session,
                template=template,
                account_id=account_id
            )
            self._logger.info(f"Персонаж ID {new_character.character_id} успешно создан в PostgreSQL.")

            # 2. Получение имени типа существа для MongoDB документа
            creature_type_repo = self._creature_type_repo_factory(session)
            creature_type = await creature_type_repo.get_by_id(template.creature_type_id)
            if not creature_type:
                raise ValueError(f"Тип существа с ID {template.creature_type_id} не найден.")
            creature_type_name = creature_type.name
            self._logger.info(f"Получено имя типа существа '{creature_type_name}' для персонажа.")

            # 3. Сборка документа для MongoDB
            assembled_mongo_document = await self._data_assembler.assemble_warm_cache_document(
                character=new_character,
                creature_type_name=creature_type_name
            )
            self._logger.info(f"Документ для MongoDB собран для персонажа ID {new_character.character_id}.")

            # 4. Сохранение документа в MongoDB
            await self._mongo_character_repo.upsert_character(assembled_mongo_document)
            self._logger.info(f"Документ персонажа ID {new_character.character_id} успешно сохранен в MongoDB.")

            self._logger.info(f"Операция создания персонажа ID {new_character.character_id} успешно завершена (коммит будет извне).")

            return BaseResultDTO(
                success=True,
                message="Character created successfully.",
                data=CharacterCreatedDTO(
                    character_id=new_character.character_id,
                    account_id=new_character.account_id
                ),
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                client_id=client_id
            )

        except Exception as e:
            self._logger.error(f"Критическая ошибка при создании персонажа для аккаунта {account_id}: {e}", exc_info=True)
            self._logger.warning(f"Операция для аккаунта {account_id} завершилась ошибкой (откат будет извне).")
            return BaseResultDTO(
                success=False,
                message=f"Ошибка сервера при создании персонажа: {str(e)}",
                error=ErrorDetail(
                    code="CHARACTER_CREATION_FAILED",
                    message=f"Внутренняя ошибка: {str(e)}"
                ).model_dump(),
                correlation_id=correlation_id,
                trace_id=trace_id,
                span_id=span_id,
                client_id=client_id
            )
