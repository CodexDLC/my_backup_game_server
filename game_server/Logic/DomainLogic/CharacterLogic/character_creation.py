import logging
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any # Добавляем для типизации

# Утилиты и хелперы
from game_server.Logic.DomainLogic.CharacterLogic.character_utils.character_creation_helpers import precalculate_skill_xp_data, select_template_from_pool
from game_server.Logic.CoreServices.services.identifiers_servise import IdentifiersServise


# Репозитории

# Кэш
from game_server.Logic.InfrastructureLogic.app_cache.services.character.character_cache_manager import CharacterCacheManager

# Модели
from game_server.database.models.models import Character

logger = logging.getLogger(__name__)


# Основной класс для создания персонажа
class CharacterCreationOrchestrator:
    def __init__(self, session: AsyncSession, cache_manager: CharacterCacheManager):
        self.session = session
        self.character_cache_manager = cache_manager
        self.account_finder = IdentifiersServise(session)
        self.pool_repo = CharacterPoolRepository(session)
        self.character_repo = CharacterMetaRepository(session)
        self.stats_manager = CharacterSpecialManager(session)
        self.skills_manager = CharacterSkillsManager(session)
        self.xp_tick_repo = XpTickDataRepository(session)
        self.skills_repo = SkillsRepository(session)

    async def execute(self, character_creation_data: Dict[str, Any]) -> Character: # <--- Принимает словарь
        # Извлекаем discord_id из словаря
        discord_id = character_creation_data.get("discord_id")

        if not discord_id:
            logger.warning("Отсутствует 'discord_id' в данных для создания персонажа.")
            raise ValueError("Отсутствует обязательное поле 'discord_id'.")

        try:
            # Управляем транзакцией внутри оркестратора
            async with self.session.begin():
                account_id = await self.account_finder.get_account_id('discord_id', discord_id)
                if not account_id: 
                    logger.warning(f"Аккаунт для Discord ID {discord_id} не найден.")
                    raise ValueError(f"Account for Discord ID {discord_id} not found.")
                
                pool_character = await select_template_from_pool(self.pool_repo)
                if not pool_character: 
                    logger.warning("Нет доступных персонажей в пуле для создания.")
                    raise ValueError("No available characters in the pool.")
                
                char_data = {
                    "account_id": account_id, "name": pool_character.name,
                    "surname": pool_character.surname, "creature_type_id": pool_character.creature_type_id,
                    "personality_id": pool_character.personality_id, "background_story_id": pool_character.background_story_id,
                    "status": 'offline'
                }
                new_character = await self.character_repo.create_character(char_data)
                
                await self.stats_manager.create_special_stats(new_character.character_id, pool_character.base_stats)
                
                for skill_key, level in pool_character.initial_skill_levels.items():
                    await self.skills_manager.create_skill(new_character.character_id, {"skill_key": skill_key, "level": level})

                all_skills = await self.skills_repo.get_all_skills()
                xp_data = precalculate_skill_xp_data(new_character.character_id, pool_character.base_stats, all_skills)
                await self.xp_tick_repo.bulk_create_xp_data(xp_data)

                # UsedCharacterArchiveManager.create_entry принимает session как аргумент
                await UsedCharacterArchiveRepositoryImpl.create_entry(
                    session=self.session, # <--- session передается явно
                    original_pool_id=pool_character.character_pool_id,
                    linked_entity_id=new_character.character_id, activation_type='PLAYER',
                    linked_account_id=account_id, simplified_pool_data={"name": pool_character.name}
                )
                await self.pool_repo.delete_character(pool_character)
            
            logger.info(f"Персонаж {new_character.character_id} успешно создан для аккаунта {account_id}.")
            return new_character # Возвращаем ORM-объект, который роут затем преобразует в Pydantic

        except ValueError: # Ловим ожидаемые ошибки и перебрасываем их
            raise
        except Exception as e:
            logger.error(f"Непредвиденная ошибка при выполнении CharacterCreationOrchestrator: {e}", exc_info=True)
            raise # Пробрасываем для обработки в роуте