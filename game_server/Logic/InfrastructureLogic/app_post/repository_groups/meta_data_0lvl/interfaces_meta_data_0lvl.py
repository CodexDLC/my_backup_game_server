from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple, Union # Добавлен Union для Any в ID
from game_server.database.models.models import (
    Ability, BackgroundStory, CreatureType, Material, ModifierLibrary, Personality,
    Skills, CreatureTypeInitialSkill, StaticItemTemplate, Suffix # StaticItemTemplate перенесен в meta_data_1lvl
)

# Унифицированные типы для PK: Union[int, str]
UnifiedIdType = Union[int, str]


class IAbilityRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Ability: pass
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Ability]: pass # Если PK int
    @abstractmethod
    async def get_by_key(self, key: str) -> Optional[Ability]: pass # Если есть уникальный строковый ключ
    @abstractmethod
    async def get_all(self) -> List[Ability]: pass
    @abstractmethod
    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[Ability]: pass # Если PK int
    @abstractmethod
    async def delete(self, id: int) -> bool: pass # Если PK int
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> Ability: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass # Для массовой вставки/обновления
    # Специфические методы, если нужны
    @abstractmethod
    async def get_ability_with_skill_requirement(self, ability_key: str) -> Optional[Ability]: pass


class IBackgroundStoryRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> BackgroundStory: pass
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[BackgroundStory]: pass # PK int
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[BackgroundStory]: pass # Уникальный строковый ключ
    @abstractmethod
    async def get_all(self) -> List[BackgroundStory]: pass
    @abstractmethod
    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[BackgroundStory]: pass # PK int
    @abstractmethod
    async def delete(self, id: int) -> bool: pass # PK int
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> BackgroundStory: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass


class ICreatureTypeRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> CreatureType: pass
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[CreatureType]: pass # PK int
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[CreatureType]: pass # Уникальный строковый ключ (если есть)
    @abstractmethod
    async def get_all(self) -> List[CreatureType]: pass
    @abstractmethod
    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[CreatureType]: pass # PK int
    @abstractmethod
    async def delete(self, id: int) -> bool: pass # PK int
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> CreatureType: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass
    # Специфические методы
    @abstractmethod
    async def get_filtered_by_category_and_playable(self, category: str, is_playable: bool) -> List[CreatureType]: pass
    @abstractmethod
    async def get_creature_type_with_initial_skills(self, creature_type_id: int) -> Optional[CreatureType]: pass


class IMaterialRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Material: pass
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Material]: pass # PK str (material_code)
    @abstractmethod
    async def get_all(self) -> List[Material]: pass
    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Material]: pass # PK str
    @abstractmethod
    async def delete(self, id: str) -> bool: pass # PK str
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> Material: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass


class IModifierLibraryRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> ModifierLibrary: pass
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[ModifierLibrary]: pass # PK str (modifier_code)
    @abstractmethod
    async def get_all(self) -> List[ModifierLibrary]: pass
    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[ModifierLibrary]: pass # PK str
    @abstractmethod
    async def delete(self, id: str) -> bool: pass # PK str
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> ModifierLibrary: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass


class IPersonalityRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Personality: pass
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[Personality]: pass # PK int
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Personality]: pass # Уникальный строковый ключ
    @abstractmethod
    async def get_all(self) -> List[Personality]: pass
    @abstractmethod
    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[Personality]: pass # PK int
    @abstractmethod
    async def delete(self, id: int) -> bool: pass # PK int
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> Personality: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass


class ISkillRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Skills: pass
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Skills]: pass # PK str (skill_key)
    @abstractmethod
    async def get_all(self) -> List[Skills]: pass
    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Skills]: pass # PK str
    @abstractmethod
    async def delete(self, id: str) -> bool: pass # PK str
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> Skills: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass
    # Специфические методы

    @abstractmethod
    async def get_skill_by_id(self, skill_id: int) -> Optional[Skills]: pass # Остается для специфичности
    @abstractmethod
    async def get_all_skills(self) -> List[Skills]: pass # Остается для специфичности


class ICreatureTypeInitialSkillRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> CreatureTypeInitialSkill: pass
    @abstractmethod
    async def get_by_id(self, id: Tuple[int, str]) -> Optional[CreatureTypeInitialSkill]: pass # PK Tuple (creature_type_id, skill_key)
    @abstractmethod
    async def get_all(self) -> List[CreatureTypeInitialSkill]: pass
    @abstractmethod
    async def update(self, id: Tuple[int, str], updates: Dict[str, Any]) -> Optional[CreatureTypeInitialSkill]: pass # PK Tuple
    @abstractmethod
    async def delete(self, id: Tuple[int, str]) -> bool: pass # PK Tuple
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> CreatureTypeInitialSkill: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass
    # Специфические методы
    @abstractmethod
    async def get_initial_skill(self, creature_type_id: int, skill_key: str) -> Optional[CreatureTypeInitialSkill]: pass
    @abstractmethod
    async def get_initial_skills_for_creature_type(self, creature_type_id: int) -> List[CreatureTypeInitialSkill]: pass
    @abstractmethod
    async def delete_initial_skill(self, creature_type_id: int, skill_key: str) -> bool: pass


class ISuffixRepository(ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> Suffix: pass
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[Suffix]: pass # PK str (suffix_code)
    @abstractmethod
    async def get_all(self) -> List[Suffix]: pass
    @abstractmethod
    async def update(self, id: str, updates: Dict[str, Any]) -> Optional[Suffix]: pass # PK str
    @abstractmethod
    async def delete(self, id: str) -> bool: pass # PK str
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> Suffix: pass
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass
    # Специфические методы
    @abstractmethod
    async def get_suffixes_by_group(self, group: str) -> List[Suffix]: pass

class IStaticItemTemplateRepository(ABC):
    # ИЗМЕНЕНО: Унифицированные методы для IStaticItemTemplateRepository
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> StaticItemTemplate: pass # Унифицирован
    @abstractmethod
    async def get_by_id(self, id: int) -> Optional[StaticItemTemplate]: pass # Унифицирован
    @abstractmethod
    async def get_by_item_code(self, item_code: str) -> Optional[StaticItemTemplate]: pass # Сохраняем специфический метод
    @abstractmethod
    async def get_all(self) -> List[StaticItemTemplate]: pass # Унифицирован
    @abstractmethod
    async def update(self, id: int, updates: Dict[str, Any]) -> Optional[StaticItemTemplate]: pass # Унифицирован
    @abstractmethod
    async def delete(self, id: int) -> bool: pass # Унифицирован
    @abstractmethod
    async def delete_by_item_code_batch(self, item_codes: List[str]) -> int: pass # Сохраняем специфический метод
    @abstractmethod
    async def upsert(self, data: Dict[str, Any]) -> StaticItemTemplate: pass # Унифицирован
    @abstractmethod
    async def upsert_many(self, data_list: List[Dict[str, Any]]) -> int: pass # Добавлен

# CreatureTypeInitialSkillRepository уже в meta_data_0lvl