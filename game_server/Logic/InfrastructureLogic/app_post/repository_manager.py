# game_server/Logic/InfrastructureLogic/DataAccessLogic/repository_manager.py

from typing import Type
from sqlalchemy.ext.asyncio import AsyncSession

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.static_item_template_repository_impl import StaticItemTemplateRepositoryImpl
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.equipment_template_repository_impl import EquipmentTemplateRepositoryImpl

# Импортируем все доменные интерфейсы
from .repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
from .repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository, IAccountInfoRepository
from .repository_groups.active_game_data.interfaces_active_game_data import IItemInstanceRepository, IUsedCharacterArchiveRepository
from .repository_groups.character.interfaces_character import (
    ICharacterRepository, ICharacterSkillRepository, ICharacterSpecialRepository,
    ISpecialStatEffectRepository, ISkillExclusionRepository
)
from .repository_groups.discord.interfaces_discord import IDiscordEntityRepository
from .repository_groups.world_state.core_world.interfaces_core_world import IStateEntityRepository, IGameLocationRepository
from .repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository, IXpTickDataRepository
from .repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    IAbilityRepository, IBackgroundStoryRepository, ICreatureTypeRepository, IMaterialRepository,
    IModifierLibraryRepository, IPersonalityRepository, ISkillRepository, ICreatureTypeInitialSkillRepository, IStaticItemTemplateRepository,
    ISuffixRepository
)
from .repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import (
    ICharacterPoolRepository, IEquipmentTemplateRepository, 
)
from .repository_groups.npc.monster.interfaces_monster import IEliteMonsterRepository
from .repository_groups.system.interfaces_system import IDataVersionRepository

# Импортируем конкретные реализации репозиториев
# (Это будут ваши _impl.py файлы, которые вы ранее обработали)
from .repository_groups.game_shards.game_shard_repository_impl import GameShardRepositoryImpl
from .repository_groups.accounts.account_game_data_repository import AccountGameDataRepositoryImpl # Исправьте, если имя файла отличается
from .repository_groups.accounts.account_info_repository_impl import AccountInfoRepositoryImpl
from .repository_groups.active_game_data.item_instance_repository_impl import ItemInstanceRepositoryImpl
from .repository_groups.active_game_data.used_character_archive_repository_impl import UsedCharacterArchiveRepositoryImpl
from .repository_groups.character.character_repository_impl import CharacterRepositoryImpl
from .repository_groups.character.character_skill_repository_impl import CharacterSkillRepositoryImpl
from .repository_groups.character.character_special_repository_impl import CharacterSpecialRepositoryImpl
from .repository_groups.character.special_stat_effect_repository_impl import SpecialStatEffectRepositoryImpl
from .repository_groups.character.skill_exclusion_repository_impl import SkillExclusionRepositoryImpl
from .repository_groups.discord.discord_entity_repository_impl import DiscordEntityRepositoryImpl

from .repository_groups.world_state.core_world.state_entity_repository_impl import StateEntityRepositoryImpl
from .repository_groups.world_state.core_world.game_location_repository_impl import GameLocationRepositoryImpl
from .repository_groups.world_state.auto_session.auto_session_repository_impl import AutoSessionRepositoryImpl
from .repository_groups.world_state.auto_session.xp_tick_data_repository_impl import XpTickDataRepositoryImpl
from .repository_groups.meta_data_0lvl.ability_repository_impl import AbilityRepositoryImpl
from .repository_groups.meta_data_0lvl.background_story_repository_impl import BackgroundStoryRepositoryImpl
from .repository_groups.meta_data_0lvl.creature_type_repository_impl import CreatureTypeRepositoryImpl
from .repository_groups.meta_data_0lvl.material_repository_impl import MaterialRepositoryImpl
from .repository_groups.meta_data_0lvl.modifier_library_repository_impl import ModifierLibraryRepositoryImpl
from .repository_groups.meta_data_0lvl.personality_repository_impl import PersonalityRepositoryImpl
from .repository_groups.meta_data_0lvl.skill_repository_impl import SkillRepositoryImpl
from .repository_groups.meta_data_0lvl.creature_type_initial_skill_repository_impl import CreatureTypeInitialSkillRepositoryImpl
from .repository_groups.meta_data_0lvl.suffix_repository_impl import SuffixRepositoryImpl
from .repository_groups.meta_data_1lvl.character_pool_repository_impl import CharacterPoolRepositoryImpl
from .repository_groups.npc.monster.elite_monster_repository_impl import EliteMonsterRepositoryImpl
from .repository_groups.system.data_version_repository_impl import DataVersionRepositoryImpl


class RepositoryManager:
    def __init__(self, db_session_factory: Type[AsyncSession]):
        self._db_session_factory = db_session_factory

        # Инициализация всех репозиториев
        self._game_shards_repo: IGameShardRepository = GameShardRepositoryImpl(db_session_factory)
        self._account_game_data_repo: IAccountGameDataRepository = AccountGameDataRepositoryImpl(db_session_factory)
        self._account_info_repo: IAccountInfoRepository = AccountInfoRepositoryImpl(db_session_factory)
        self._item_instance_repo: IItemInstanceRepository = ItemInstanceRepositoryImpl(db_session_factory)
        self._used_character_archive_repo: IUsedCharacterArchiveRepository = UsedCharacterArchiveRepositoryImpl(db_session_factory)
        self._character_repo: ICharacterRepository = CharacterRepositoryImpl(db_session_factory)
        self._character_skill_repo: ICharacterSkillRepository = CharacterSkillRepositoryImpl(db_session_factory)
        self._character_special_repo: ICharacterSpecialRepository = CharacterSpecialRepositoryImpl(db_session_factory)
        self._special_stat_effect_repo: ISpecialStatEffectRepository = SpecialStatEffectRepositoryImpl(db_session_factory)
        self._skill_exclusion_repo: ISkillExclusionRepository = SkillExclusionRepositoryImpl(db_session_factory)
        self._discord_entity_repo: IDiscordEntityRepository = DiscordEntityRepositoryImpl(db_session_factory)

        self._state_entity_repo: IStateEntityRepository = StateEntityRepositoryImpl(db_session_factory)
        self._game_location_repo: IGameLocationRepository = GameLocationRepositoryImpl(db_session_factory)
        self._auto_session_repo: IAutoSessionRepository = AutoSessionRepositoryImpl(db_session_factory)
        self._xp_tick_data_repo: IXpTickDataRepository = XpTickDataRepositoryImpl(db_session_factory)
        self._ability_repo: IAbilityRepository = AbilityRepositoryImpl(db_session_factory)
        self._background_story_repo: IBackgroundStoryRepository = BackgroundStoryRepositoryImpl(db_session_factory)
        self._creature_type_repo: ICreatureTypeRepository = CreatureTypeRepositoryImpl(db_session_factory)
        self._material_repo: IMaterialRepository = MaterialRepositoryImpl(db_session_factory)
        self._modifier_library_repo: IModifierLibraryRepository = ModifierLibraryRepositoryImpl(db_session_factory)
        self._personality_repo: IPersonalityRepository = PersonalityRepositoryImpl(db_session_factory)
        self._skill_repo: ISkillRepository = SkillRepositoryImpl(db_session_factory)
        self._creature_type_initial_skill_repo: ICreatureTypeInitialSkillRepository = CreatureTypeInitialSkillRepositoryImpl(db_session_factory)
        self._suffix_repo: ISuffixRepository = SuffixRepositoryImpl(db_session_factory)
        self._character_pool_repo: ICharacterPoolRepository = CharacterPoolRepositoryImpl(db_session_factory)
        self._equipment_template_repo: IEquipmentTemplateRepository = EquipmentTemplateRepositoryImpl(db_session_factory) # <-- ДОБАВИТЬ ЭТУ
        self._static_item_template_repo: IStaticItemTemplateRepository = StaticItemTemplateRepositoryImpl(db_session_factory) # <-- И ЭТУ
        self._elite_monster_repo: IEliteMonsterRepository = EliteMonsterRepositoryImpl(db_session_factory)
        self._data_version_repo: IDataVersionRepository = DataVersionRepositoryImpl(db_session_factory)

    # Свойства для доступа к каждому репозиторию
    @property
    def game_shards(self) -> IGameShardRepository:
        return self._game_shards_repo

    @property
    def account_game_data(self) -> IAccountGameDataRepository:
        return self._account_game_data_repo

    @property
    def account_info(self) -> IAccountInfoRepository:
        return self._account_info_repo

    @property
    def item_instances(self) -> IItemInstanceRepository:
        return self._item_instance_repo

    @property
    def used_character_archive(self) -> IUsedCharacterArchiveRepository:
        return self._used_character_archive_repo

    @property
    def characters(self) -> ICharacterRepository:
        return self._character_repo

    @property
    def character_skills(self) -> ICharacterSkillRepository:
        return self._character_skill_repo

    @property
    def character_special(self) -> ICharacterSpecialRepository:
        return self._character_special_repo

    @property
    def special_stat_effects(self) -> ISpecialStatEffectRepository:
        return self._special_stat_effect_repo

    @property
    def skill_exclusions(self) -> ISkillExclusionRepository:
        return self._skill_exclusion_repo

    @property
    def discord_entities(self) -> IDiscordEntityRepository:
        return self._discord_entity_repo

    @property
    def state_entities(self) -> IStateEntityRepository:
        return self._state_entity_repo

    @property
    def game_locations(self) -> IGameLocationRepository:
        return self._game_location_repo

    @property
    def auto_sessions(self) -> IAutoSessionRepository:
        return self._auto_session_repo

    @property
    def xp_tick_data(self) -> IXpTickDataRepository:
        return self._xp_tick_data_repo

    @property
    def abilities(self) -> IAbilityRepository:
        return self._ability_repo

    @property
    def background_stories(self) -> IBackgroundStoryRepository:
        return self._background_story_repo

    @property
    def creature_types(self) -> ICreatureTypeRepository:
        return self._creature_type_repo

    @property
    def materials(self) -> IMaterialRepository:
        return self._material_repo

    @property
    def modifier_library(self) -> IModifierLibraryRepository:
        return self._modifier_library_repo

    @property
    def personalities(self) -> IPersonalityRepository:
        return self._personality_repo

    @property
    def skills(self) -> ISkillRepository:
        return self._skill_repo

    @property
    def creature_type_initial_skills(self) -> ICreatureTypeInitialSkillRepository:
        return self._creature_type_initial_skill_repo

    @property
    def suffixes(self) -> ISuffixRepository:
        return self._suffix_repo

    @property
    def character_pools(self) -> ICharacterPoolRepository:
        return self._character_pool_repo

    @property
    def equipment_templates(self) -> IEquipmentTemplateRepository:
        return self._equipment_template_repo

    @property
    def static_item_templates(self) -> IStaticItemTemplateRepository:
        return self._static_item_template_repo

    @property
    def elite_monsters(self) -> IEliteMonsterRepository:
        return self._elite_monster_repo

    @property
    def data_versions(self) -> IDataVersionRepository:
        return self._data_version_repo