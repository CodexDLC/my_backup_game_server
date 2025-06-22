# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/character/character_config.py

# Импорты реализаций репозиториев
from .character_repository_impl import CharacterRepositoryImpl
from .character_skill_repository_impl import CharacterSkillRepositoryImpl
from .character_special_repository_impl import CharacterSpecialRepositoryImpl
from .special_stat_effect_repository_impl import SpecialStatEffectRepositoryImpl


# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import (
    ICharacterRepository,
    ICharacterSkillRepository,
    ICharacterSpecialRepository,
    ISpecialStatEffectRepository
)


# Конфигурация для группы репозиториев 'character'
character_repo_config = [
    {
        "name": "character_repository",
        "implementation": CharacterRepositoryImpl,
        "interface": ICharacterRepository
    },
    {
        "name": "character_skill_repository",
        "implementation": CharacterSkillRepositoryImpl,
        "interface": ICharacterSkillRepository
    },
    {
        "name": "character_special_repository",
        "implementation": CharacterSpecialRepositoryImpl,
        "interface": ICharacterSpecialRepository
    },
    {
        "name": "special_stat_effect_repository",
        "implementation": SpecialStatEffectRepositoryImpl,
        "interface": ISpecialStatEffectRepository
    },
    # Если в будущем будут другие репозитории в этой группе, добавьте их сюда.
]