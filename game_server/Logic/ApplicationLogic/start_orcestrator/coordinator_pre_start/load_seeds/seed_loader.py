# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/load_seeds/seed_loader.py

# -*- coding: utf-8 -*-
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Type, List, TypeVar

from game_server.common_contracts.dtos.state_entity_dtos import StateEntityDTO




from .....CoreServices.utils.yaml_readers import YamlReader

from game_server.Logic.CoreServices.utils.seed_utils import get_pk_column_name
from game_server.config.settings.process.prestart import SEEDING_DELETION_BATCH_SIZE

from game_server.database.models.models import Base, Ability, BackgroundStory, CreatureType, GameLocation, Material, \
    ModifierLibrary, Personality, Skills, CreatureTypeInitialSkill, StaticItemTemplate, Suffix, \
    EquipmentTemplate, StateEntity
from game_server.config.logging.logging_setup import app_logger as logger

from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    IAbilityRepository, IBackgroundStoryRepository, ICreatureTypeRepository, IMaterialRepository,
    IModifierLibraryRepository, IPersonalityRepository, ISkillRepository, ICreatureTypeInitialSkillRepository, IStaticItemTemplateRepository,
    ISuffixRepository
)
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository


from pydantic import BaseModel, ValidationError

from game_server.common_contracts.dtos.orchestrator_dtos import (
    AbilityData, BackgroundStoryData, CreatureTypeData, GameLocationData, MaterialData,
    ModifierLibraryData, PersonalityData, SkillData, CreatureTypeInitialSkillData,
    StaticItemTemplateData, SuffixData
)

PydanticDtoType = TypeVar('PydanticDtoType', bound=BaseModel)


class SeedLoader:
    # ДОБАВЛЯЕМ СООТВЕТСТВИЕ В КАРТУ
    MODEL_TO_DTO_MAP: Dict[Type[Base], Type[BaseModel]] = {
        Ability: AbilityData,
        BackgroundStory: BackgroundStoryData,
        CreatureType: CreatureTypeData,
        Material: MaterialData,
        ModifierLibrary: ModifierLibraryData,
        Personality: PersonalityData,
        Skills: SkillData,
        CreatureTypeInitialSkill: CreatureTypeInitialSkillData,
        StaticItemTemplate: StaticItemTemplateData,
        Suffix: SuffixData,
        StateEntity: StateEntityDTO,
        GameLocation: GameLocationData, # <--- ВОТ ЭТА СТРОКА РЕШАЕТ ПРОБЛЕМУ
    }

    def __init__(self, repository_manager: RepositoryManager):
        # ... (остальной код класса остается без изменений)
        self.repository_manager = repository_manager
        self.logger = logger
        self.yaml_reader = YamlReader()
        self.logger.info("✅ SeedLoader инициализирован")

        self.ability_repo: IAbilityRepository = self.repository_manager.abilities
        self.background_story_repo: IBackgroundStoryRepository = self.repository_manager.background_stories
        self.creature_type_repo: ICreatureTypeRepository = self.repository_manager.creature_types
        self.material_repo: IMaterialRepository = self.repository_manager.materials
        self.modifier_library_repo: IModifierLibraryRepository = self.repository_manager.modifier_library
        self.personality_repo: IPersonalityRepository = self.repository_manager.personalities
        self.skill_repo: ISkillRepository = self.repository_manager.skills
        self.creature_type_initial_skill_repo: ICreatureTypeInitialSkillRepository = self.repository_manager.creature_type_initial_skills
        self.static_item_template_repo: IStaticItemTemplateRepository = self.repository_manager.static_item_templates
        self.suffix_repo: ISuffixRepository = self.repository_manager.suffixes
        self.equipment_template_repo: IEquipmentTemplateRepository = self.repository_manager.equipment_templates
        self.state_entity_repo = self.repository_manager.state_entities

    async def load_and_prepare_data_from_yaml(self, file_path: Path, model: Type[Base]) -> Optional[List[PydanticDtoType]]:
        dto_type = self.MODEL_TO_DTO_MAP.get(model)
        if not dto_type:
            self.logger.critical(f"🚨 Critical error: Pydantic DTO not found for ORM model '{model.__name__}'. "
                            f"Check mapping in SeedLoader.MODEL_TO_DTO_MAP.")
            return None

        try:
            pk_for_yaml_reader = get_pk_column_name(model)
        except RuntimeError as e:
            self.logger.error(f"❌ {e}. Skipping file {file_path.name}.")
            return None

        try:
            items_to_process_dicts = await self.yaml_reader.get_items_from_yaml(file_path, pk_for_yaml_reader)
        except RuntimeError as e:
            self.logger.critical(f"🚨 Critical YAML format error in file {file_path.name}: {e}. Skipping file.")
            return None

        if items_to_process_dicts is None:
            return None
        if not items_to_process_dicts:
            self.logger.warning(f"⚠️ File {file_path.name} processed, but contains no data for loading.")
            return []

        validated_items: List[PydanticDtoType] = []
        for item_data_dict in items_to_process_dicts:
            try:
                validated_item = dto_type(**item_data_dict)
                validated_items.append(validated_item)
            except ValidationError as e:
                self.logger.critical(f"🚨🚨� Pydantic ValidationError for '{model.__name__}' from file '{file_path.name}' "
                                     f"Element: {item_data_dict}. Error: {e.errors()}", exc_info=True)
                raise RuntimeError(f"Critical Pydantic validation error for file {file_path.name}. "
                                   f"Error: {e.errors()}")
            except Exception as e:
                self.logger.critical(f"🚨🚨🚨 Unexpected error during Pydantic validation for '{model.__name__}' from file '{file_path.name}' "
                                     f"Element: {item_data_dict}. Error: {e}", exc_info=True)
                raise RuntimeError(f"Unexpected validation error for file {file_path.name}.")

        self.logger.debug(f"Successfully validated {len(validated_items)} elements for model {model.__name__} from file {file_path.name}.")
        return validated_items

    async def upsert_data(self, model: Type[Base], items_to_process: List[BaseModel]) -> Tuple[int, int]:
        if not items_to_process:
            self.logger.info(f"ℹ️ No data to UPSERT for model {model.__name__}.")
            return 0, 0

        items_for_repo: List[Dict[str, Any]] = [item.model_dump(by_alias=True) for item in items_to_process]

        # ИЗМЕНЕНО: теперь возвращаем общий count, а не inserted/updated отдельно
        total_affected_count = 0
        inserted_count = 0 # Для более детального логирования, если upsert_many не возвращает tuple
        updated_count = 0 # Для более детального логирования, если upsert_many не возвращает tuple


        repo_property_name = self._get_repo_property_name(model)
        if not repo_property_name:
            self.logger.critical(f"🚨 Critical error: Repository property not found for model {model.__name__} in RepositoryManager for UPSERT.")
            raise RuntimeError(f"UPSERT impossible: repository for model {model.__name__} not found.")
        
        repository = getattr(self.repository_manager, repo_property_name)

        try:
            if hasattr(repository, 'upsert_many'):
                # ИСПРАВЛЕНО: ожидаем одно int значение от upsert_many
                total_affected_count = await repository.upsert_many(items_for_repo)
                # Для логирования, если upsert_many возвращает только общее количество
                inserted_count = total_affected_count # Предполагаем, что большинство - это вставки
                updated_count = 0 # Или сложно определить без детального возврата из upsert_many
            else:
                self.logger.warning(f"Batch UPSERT for {model.__name__} not implemented. Performing single UPSERT.")
                for item_data in items_for_repo:
                    try:
                        if model.__name__ == "Ability": await self.ability_repo.upsert(item_data)
                        elif model.__name__ == "BackgroundStory": await self.background_story_repo.upsert(item_data)
                        elif model.__name__ == "CreatureType": await self.creature_type_repo.upsert(item_data)
                        elif model.__name__ == "Material": await self.material_repo.upsert(item_data) # ИСПРАВЛЕНО: изменено на .upsert
                        elif model.__name__ == "ModifierLibrary": await self.modifier_library_repo.upsert(item_data)
                        elif model.__name__ == "Personality": await self.personality_repo.upsert(item_data)
                        elif model.__name__ == "Skills": await self.skill_repo.upsert(item_data)
                        elif model.__name__ == "CreatureTypeInitialSkill": await self.creature_type_initial_skill_repo.upsert(item_data)
                        elif model.__name__ == "StaticItemTemplate": await self.static_item_template_repo.upsert(item_data)
                        elif model.__name__ == "Suffix": await self.suffix_repo.upsert(item_data)
                        elif model.__name__ == "StateEntity": await self.state_entity_repo.upsert(item_data)
                        else: raise NotImplementedError(f"Single UPSERT for model {model.__name__} not implemented.")
                        
                        # Если upsert для одиночного элемента возвращает ORM-объект,
                        # то сложно определить, была ли это вставка или обновление.
                        # Предполагаем, что это "вставка" для счетчика, если не можем точно определить.
                        inserted_count += 1
                        total_affected_count += 1
                    except Exception as single_upsert_e:
                        self.logger.error(f"Error during single UPSERT for {model.__name__}: {single_upsert_e}", exc_info=True)
                        raise

            self.logger.info(f"✅ UPSERT completed for {model.__name__}. Affected rows: {total_affected_count}. (Inserted: {inserted_count}, Updated: {updated_count}).")
            return inserted_count, updated_count # Возвращаем inserted_count, updated_count как запрошено в signature

        except Exception as e:
            self.logger.critical(f"🚨 CRITICAL UPSERT error for {model.__name__}: {e}", exc_info=True)
            raise

    def _get_repo_property_name(self, model: Type[Base]) -> Optional[str]:
        mapping = {
            "Ability": "abilities",
            "BackgroundStory": "background_stories",
            "CreatureType": "creature_types",
            "Material": "materials",
            "ModifierLibrary": "modifier_library",
            "Personality": "personalities",
            "Skills": "skills",
            "CreatureTypeInitialSkill": "creature_type_initial_skills",
            "StaticItemTemplate": "static_item_templates",
            "Suffix": "suffixes",
            "DataVersion": "data_versions",
            "EquipmentTemplate": "equipment_templates",
            "StateEntity": "state_entities",
            "GameLocation": "game_locations", # <--- ДОБАВЬТЕ ЭТУ СТРОКУ
        }
        return mapping.get(model.__name__)

    async def _clear_model_data(self, model: Type[Base]) -> int:
        try:
            repo_property_name = self._get_repo_property_name(model)
            if not repo_property_name:
                self.logger.critical(f"🚨 Critical error: Repository property not found for model {model.__name__} for data cleaning.")
                raise RuntimeError(f"Data cleaning impossible: repository for model {model.__name__} not found.")
            
            repository = getattr(self.repository_manager, repo_property_name)
            
            deleted_count = 0
            
            if hasattr(repository, 'delete_all_records'):
                deleted_count = await repository.delete_all_records()
            elif hasattr(repository, 'delete_all'):
                deleted_count = await repository.delete_all()
            else:
                self.logger.warning(f"Table cleaning for {model.__name__} not directly implemented in repository. Deleting all items one by one (inefficient).")
                all_pks = await self.repository_manager.get_all_pks_for_model(model, get_pk_column_name(model))
                deleted_count = await self.repository_manager.perform_deletions_for_model(model, get_pk_column_name(model), list(all_pks))
                
            self.logger.info(f"🗑️ Deleted all records ({deleted_count}) from table {model.__tablename__}.")
            return deleted_count
        except Exception as e:
            self.logger.error(f"❌ Error cleaning table {model.__tablename__}: {e}", exc_info=True)
            raise
