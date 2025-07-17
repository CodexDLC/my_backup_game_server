from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from game_server.database.models.models import Character, CharacterSkills, CharacterSpecial, SpecialStatEffect, SkillExclusion
from sqlalchemy.ext.asyncio import AsyncSession

class ICharacterRepository(ABC):
    @abstractmethod
    async def create_character(self, character_data: Dict[str, Any]) -> Character: pass
    @abstractmethod
    async def get_character_by_id(self, character_id: int) -> Optional[Character]: pass
    @abstractmethod
    async def get_character_by_name(self, name: str) -> Optional[Character]: pass
    @abstractmethod
    async def get_characters_by_account_id(self, account_id: int) -> List[Character]: pass
    @abstractmethod
    async def update_character(self, character_id: int, update_data: Dict[str, Any]) -> Optional[Character]: pass
    @abstractmethod
    async def soft_delete_character(self, character_id: int) -> bool: pass
    @abstractmethod
    async def get_online_character_by_account_id(self, account_id: int) -> Optional[Character]: pass
    @abstractmethod
    async def get_full_character_data_by_id(self, session: AsyncSession, character_id: int) -> Optional[Character]:
        pass

class ICharacterSkillRepository(ABC):
    @abstractmethod
    async def create_skill(self, character_id: int, skill_data: Dict[str, Any]) -> CharacterSkills: pass
    @abstractmethod
    async def get_skill(self, character_id: int, skill_key: int) -> Optional[CharacterSkills]: pass
    @abstractmethod
    async def update_skill(self, character_id: int, updates: Dict[str, Any]) -> Optional[CharacterSkills]: pass
    @abstractmethod
    async def delete_skill(self, character_id: int, skill_key: int) -> bool: pass
    @abstractmethod
    async def bulk_create_skills(self, character_id: int, skills_data: List[Dict[str, Any]]) -> None:
        pass


class ICharacterSpecialRepository(ABC):
    @abstractmethod
    async def create_special_stats(self, character_id: int, stats_data: Dict[str, Any]) -> CharacterSpecial: pass
    @abstractmethod
    async def get_special_stats(self, character_id: int) -> Optional[CharacterSpecial]: pass
    @abstractmethod
    async def update_special_stats(self, character_id: int, updates: Dict[str, Any]) -> Optional[CharacterSpecial]: pass
    @abstractmethod
    async def delete_special_stats(self, character_id: int) -> bool: pass
    @abstractmethod
    async def create_special_stats(self, character_id: int, stats_data: Dict[str, Any]) -> CharacterSpecial:
        pass

class ISpecialStatEffectRepository(ABC):
    @abstractmethod
    async def get_effect_by_id(self, effect_id: int) -> Optional[SpecialStatEffect]: pass
    @abstractmethod
    async def get_effect_by_keys(self, stat_key: str, affected_property: str, effect_type: str) -> Optional[SpecialStatEffect]: pass
    @abstractmethod
    async def get_effects_for_stat(self, stat_key: str) -> List[SpecialStatEffect]: pass
    @abstractmethod
    async def get_effects_for_property(self, affected_property: str) -> List[SpecialStatEffect]: pass
    @abstractmethod
    async def create_effect(self, effect_data: Dict[str, Any]) -> SpecialStatEffect: pass
    @abstractmethod
    async def update_effect(self, effect_id: int, updates: Dict[str, Any]) -> Optional[SpecialStatEffect]: pass
    @abstractmethod
    async def delete_effect(self, effect_id: int) -> bool: pass

class ISkillExclusionRepository(ABC):
    @abstractmethod
    async def get_exclusion_by_id(self, exclusion_id: int) -> Optional[SkillExclusion]: pass
    @abstractmethod
    async def get_exclusion_by_group_name(self, group_name: str) -> Optional[SkillExclusion]: pass
    @abstractmethod
    async def get_all_exclusions(self) -> List[SkillExclusion]: pass
    @abstractmethod
    async def create_exclusion(self, exclusion_data: Dict[str, Any]) -> SkillExclusion: pass
    @abstractmethod
    async def update_exclusion(self, exclusion_id: int, updates: Dict[str, Any]) -> Optional[SkillExclusion]: pass
    @abstractmethod
    async def delete_exclusion(self, exclusion_id: int) -> bool: pass