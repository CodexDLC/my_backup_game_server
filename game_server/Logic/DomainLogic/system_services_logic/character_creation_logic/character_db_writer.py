# game_server/Logic/DomainLogic/system_services_logic/character_creation_logic/character_db_writer.py

import logging
from typing import Dict, Any, Callable

import inject
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select as fselect
from sqlalchemy.orm import selectinload

# Импорт моделей
from game_server.database.models.models import CharacterPool, Character, CharacterSkills
# Импорт интерфейсов репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import (
    ICharacterRepository, ICharacterSpecialRepository, ICharacterSkillRepository
)
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.active_game_data.interfaces_active_game_data import IUsedCharacterArchiveRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository

# Импорт констант и логгера
from game_server.config.logging.logging_setup import app_logger as logger
from game_server.config.constants import game_rules

class CharacterDbWriter:
    """
    Отвечает за оркестрацию записи всех данных нового персонажа в PostgreSQL.
    """
    @inject.autoparams()
    def __init__(self,
                 logger: logging.Logger,
                 char_repo_factory: Callable[[AsyncSession], ICharacterRepository],
                 special_repo_factory: Callable[[AsyncSession], ICharacterSpecialRepository],
                 skill_repo_factory: Callable[[AsyncSession], ICharacterSkillRepository],
                 archive_repo_factory: Callable[[AsyncSession], IUsedCharacterArchiveRepository],
                 pool_repo_factory: Callable[[AsyncSession], ICharacterPoolRepository],
                 account_data_repo_factory: Callable[[AsyncSession], IAccountGameDataRepository]
                 ):
        self._logger = logger
        self._char_repo_factory = char_repo_factory
        self._special_repo_factory = special_repo_factory
        self._skill_repo_factory = skill_repo_factory
        self._archive_repo_factory = archive_repo_factory
        self._pool_repo_factory = pool_repo_factory
        self._account_data_repo_factory = account_data_repo_factory
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def create_character_from_template(
        self,
        session: AsyncSession,
        template: CharacterPool,
        account_id: int
    ) -> Character:
        """
        Создает все записи для нового персонажа и архивирует шаблон.
        Обернуто в try/except для отлова и логирования любых ошибок.
        """
        self._logger.info(f"Начало создания персонажа для аккаунта ID {account_id} из шаблона ID {template.character_pool_id if template else 'NULL'}.")
        if not template:
            self._logger.error("Шаблон персонажа (template) не был передан. Прерывание операции.")
            raise ValueError("Template cannot be None.")
            
        self._logger.debug(f"Данные шаблона: Имя='{template.name}', Статы={template.base_stats}, Навыки={template.initial_skill_levels}")

        try:
            # Создаем экземпляры репозиториев с активной сессией
            char_repo = self._char_repo_factory(session)
            special_repo = self._special_repo_factory(session)
            skill_repo = self._skill_repo_factory(session)
            archive_repo = self._archive_repo_factory(session)
            pool_repo = self._pool_repo_factory(session)

            # 1. Создаем основную запись о персонаже
            char_data = {
                "account_id": account_id, "name": template.name, "surname": template.surname,
                "gender": template.gender, "creature_type_id": template.creature_type_id,
                # personality_id и background_story_id не устанавливаются для персонажей игроков
                "clan_id": None, "status": "offline"
            }
            self._logger.debug(f"Данные для создания Character: {char_data}")
            new_char = await char_repo.create_character(character_data=char_data)
            self._logger.info(f"Основная запись для персонажа ID {new_char.character_id} создана в сессии.")

            # 2. Создаем запись о S.P.E.C.I.A.L. статах
            self._logger.debug(f"Данные для создания CharacterSpecial: {template.base_stats}")
            await special_repo.create_special_stats(character_id=new_char.character_id, stats_data=template.base_stats)
            self._logger.info(f"Запись со статами для персонажа ID {new_char.character_id} создана.")

            # 3. Создаем записи о начальных навыках
            skills_to_create = [{"skill_key": key, "level": level} for key, level in template.initial_skill_levels.items()]
            if skills_to_create:
                self._logger.debug(f"Данные для создания CharacterSkills: {skills_to_create}")
                await skill_repo.bulk_create_skills(character_id=new_char.character_id, skills_data=skills_to_create)
                self._logger.info(f"Создано {len(skills_to_create)} записей о навыках для персонажа ID {new_char.character_id}.")

            # 4. Создаем запись в архиве
            simplified_data = {
                "name": template.name, "surname": template.surname,
                "gender": template.gender, "creature_type_id": template.creature_type_id,
                "base_stats": template.base_stats, "visual_appearance_data": template.visual_appearance_data,
                "initial_skill_levels": template.initial_skill_levels, "initial_role_name": template.initial_role_name,
                "quality_level": template.quality_level, "rarity_score": template.rarity_score
            }
            await archive_repo.create_archive_record(
                original_pool_id=template.character_pool_id,
                linked_entity_id=new_char.character_id,
                activation_type='PLAYER',
                lifecycle_status='ACTIVE',
                linked_account_id=account_id,
                simplified_pool_data=simplified_data
            )
            self._logger.info(f"Запись об использовании шаблона {template.character_pool_id} создана в архиве.")

            # 5. Удаляем использованный шаблон из пула
            await pool_repo.delete_template_by_id(pool_id=template.character_pool_id)
            self._logger.info(f"Шаблон ID {template.character_pool_id} удален из пула.")

            # 6. Явно загружаем все созданные связи для возврата полного объекта
            stmt = fselect(Character).options(
                selectinload(Character.personality),
                selectinload(Character.background_story),
                selectinload(Character.special_stats),
                selectinload(Character.character_skills).selectinload(CharacterSkills.skills)
            ).where(Character.character_id == new_char.character_id)
            
            result = await session.execute(stmt)
            full_new_char = result.scalar_one()
            
            self._logger.info(f"Все записи для персонажа '{full_new_char.name}' (ID: {full_new_char.character_id}) успешно созданы и готовы к сборке.")
            return full_new_char

        except SQLAlchemyError as e:
            self._logger.exception(f"Произошла ошибка базы данных при создании персонажа: {e}")
            raise
        except Exception as e:
            self._logger.exception(f"Произошла непредвиденная ошибка при создании персонажа: {e}")
            raise
