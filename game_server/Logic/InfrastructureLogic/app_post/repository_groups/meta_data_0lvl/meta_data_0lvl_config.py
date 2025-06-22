# game_server/Logic/InfrastructureLogic/DataAccessLogic/app_post/repository_groups/meta_data_0lvl/meta_data_0lvl_config.py

# Импорты реализаций репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IStaticItemTemplateRepository
from .ability_repository_impl import AbilityRepositoryImpl
from .background_story_repository_impl import BackgroundStoryRepositoryImpl
from .creature_type_repository_impl import CreatureTypeRepositoryImpl
from .material_repository_impl import MaterialRepositoryImpl
from .modifier_library_repository_impl import ModifierLibraryRepositoryImpl
from .personality_repository_impl import PersonalityRepositoryImpl
from .skill_repository_impl import SkillRepositoryImpl
from .creature_type_initial_skill_repository_impl import CreatureTypeInitialSkillRepositoryImpl
from .static_item_template_repository_impl import StaticItemTemplateRepositoryImpl # <--- ДОБАВЛЕНО
from .suffix_repository_impl import SuffixRepositoryImpl # <--- ДОБАВЛЕНО


# Импорты интерфейсов
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    IAbilityRepository,
    IBackgroundStoryRepository,
    ICreatureTypeRepository,
    IMaterialRepository,
    IModifierLibraryRepository,
    IPersonalityRepository,
    ISkillRepository,
    ICreatureTypeInitialSkillRepository,    
    ISuffixRepository # <--- ДОБАВЛЕНО
)


# Конфигурация для группы репозиториев 'meta_data_0lvl'
meta_data_0lvl_repo_config = [
    {
        "name": "ability_repository",
        "implementation": AbilityRepositoryImpl,
        "interface": IAbilityRepository
    },
    {
        "name": "background_story_repository",
        "implementation": BackgroundStoryRepositoryImpl,
        "interface": IBackgroundStoryRepository
    },
    {
        "name": "creature_type_repository",
        "implementation": CreatureTypeRepositoryImpl,
        "interface": ICreatureTypeRepository
    },
    {
        "name": "material_repository",
        "implementation": MaterialRepositoryImpl,
        "interface": IMaterialRepository
    },
    {
        "name": "modifier_library_repository",
        "implementation": ModifierLibraryRepositoryImpl,
        "interface": IModifierLibraryRepository
    },
    {
        "name": "personality_repository",
        "implementation": PersonalityRepositoryImpl,
        "interface": IPersonalityRepository
    },
    {
        "name": "skill_repository",
        "implementation": SkillRepositoryImpl,
        "interface": ISkillRepository
    },
    {
        "name": "creature_type_initial_skill_repository",
        "implementation": CreatureTypeInitialSkillRepositoryImpl,
        "interface": ICreatureTypeInitialSkillRepository
    },
    {
        "name": "static_item_template_repository", # <--- ДОБАВЛЕНО
        "implementation": StaticItemTemplateRepositoryImpl,
        "interface": IStaticItemTemplateRepository
    },
    {
        "name": "suffix_repository", # <--- ДОБАВЛЕНО
        "implementation": SuffixRepositoryImpl,
        "interface": ISuffixRepository
    },
    # Если в будущем будут другие репозитории в этой группе, добавьте их сюда.
]