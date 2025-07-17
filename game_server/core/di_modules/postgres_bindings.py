# game_server/core/di_modules/postgres_bindings.py


from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession

# Импорты интерфейсов и реализаций PostgreSQL репозиториев
# accounts
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountInfoRepository, IAccountGameDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.account_info_repository_impl import AccountInfoRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.account_game_data_repository import AccountGameDataRepositoryImpl
# character
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository, ICharacterSkillRepository, ICharacterSpecialRepository, ISpecialStatEffectRepository, ISkillExclusionRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.character_repository_impl import CharacterRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.character_skill_repository_impl import CharacterSkillRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.character_special_repository_impl import CharacterSpecialRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.special_stat_effect_repository_impl import SpecialStatEffectRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.skill_exclusion_repository_impl import SkillExclusionRepositoryImpl
# discord
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.interfaces_discord import IDiscordEntityRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.discord.discord_entity_repository_impl import DiscordEntityRepositoryImpl
# game_shards
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.game_shard_repository_impl import GameShardRepositoryImpl
# meta_data_0lvl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import IAbilityRepository, IBackgroundStoryRepository, ICreatureTypeRepository, IMaterialRepository, IModifierLibraryRepository, IPersonalityRepository, ISkillRepository, ICreatureTypeInitialSkillRepository, IStaticItemTemplateRepository, ISuffixRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.ability_repository_impl import AbilityRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.background_story_repository_impl import BackgroundStoryRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.creature_type_repository_impl import CreatureTypeRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.material_repository_impl import MaterialRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.modifier_library_repository_impl import ModifierLibraryRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.personality_repository_impl import PersonalityRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.skill_repository_impl import SkillRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.creature_type_initial_skill_repository_impl import CreatureTypeInitialSkillRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.static_item_template_repository_impl import StaticItemTemplateRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.suffix_repository_impl import SuffixRepositoryImpl
# meta_data_1lvl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository, IEquipmentTemplateRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.character_pool_repository_impl import CharacterPoolRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.equipment_template_repository_impl import EquipmentTemplateRepositoryImpl
# npc.monster
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.npc.monster.interfaces_monster import IEliteMonsterRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.npc.monster.elite_monster_repository_impl import EliteMonsterRepositoryImpl
# system
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.data_version_repository_impl import DataVersionRepositoryImpl
# world_state.core_world
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository, IStateEntityRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.game_location_repository_impl import GameLocationRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.state_entity_repository_impl import StateEntityRepositoryImpl
# world_state.auto_session
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository, IXpTickDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.auto_session_repository_impl import AutoSessionRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.xp_tick_data_repository_impl import XpTickDataRepositoryImpl
# active_game_data
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.active_game_data.interfaces_active_game_data import IUsedCharacterArchiveRepository, IItemInstanceRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.active_game_data.used_character_archive_repository_impl import UsedCharacterArchiveRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.active_game_data.item_instance_repository_impl import ItemInstanceRepositoryImpl


def configure_postgres_repositories(binder):
    """
    Конфигурирует связывания для всех репозиториев PostgreSQL.
    Все они теперь биндятся как ФАБРИКИ (Callable[[AsyncSession], IRepositoryInterface]),
    которые принимают активную сессию.
    """
    # Регистрация репозиториев PostgreSQL (интерфейс к реализации)
    # Все они теперь биндятся как ФАБРИКИ СЕССИЙ (Callable[[AsyncSession], IRepositoryInterface])
    binder.bind(Callable[[AsyncSession], IAbilityRepository], lambda session: AbilityRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IBackgroundStoryRepository], lambda session: BackgroundStoryRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ICreatureTypeRepository], lambda session: CreatureTypeRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IMaterialRepository], lambda session: MaterialRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IModifierLibraryRepository], lambda session: ModifierLibraryRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IPersonalityRepository], lambda session: PersonalityRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ISkillRepository], lambda session: SkillRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ICreatureTypeInitialSkillRepository], lambda session: CreatureTypeInitialSkillRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IStaticItemTemplateRepository], lambda session: StaticItemTemplateRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ISuffixRepository], lambda session: SuffixRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ICharacterPoolRepository], lambda session: CharacterPoolRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IEquipmentTemplateRepository], lambda session: EquipmentTemplateRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IEliteMonsterRepository], lambda session: EliteMonsterRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IDataVersionRepository], lambda session: DataVersionRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IGameLocationRepository], lambda session: GameLocationRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IStateEntityRepository], lambda session: StateEntityRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IAutoSessionRepository], lambda session: AutoSessionRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IXpTickDataRepository], lambda session: XpTickDataRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IAccountInfoRepository], lambda session: AccountInfoRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IAccountGameDataRepository], lambda session: AccountGameDataRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ICharacterRepository], lambda session: CharacterRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ICharacterSkillRepository], lambda session: CharacterSkillRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ICharacterSpecialRepository], lambda session: CharacterSpecialRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ISpecialStatEffectRepository], lambda session: SpecialStatEffectRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], ISkillExclusionRepository], lambda session: SkillExclusionRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IDiscordEntityRepository], lambda session: DiscordEntityRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IGameShardRepository], lambda session: GameShardRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IUsedCharacterArchiveRepository], lambda session: UsedCharacterArchiveRepositoryImpl(session))
    binder.bind(Callable[[AsyncSession], IItemInstanceRepository], lambda session: ItemInstanceRepositoryImpl(session))