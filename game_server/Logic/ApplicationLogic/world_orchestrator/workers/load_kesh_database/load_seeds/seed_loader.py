# game_server/Logic/ApplicationLogic/world_orchestrator/workers/load_kesh_database/load_seeds/seed_loader.py

# -*- coding: utf-8 -*-
import uuid
from pathlib import Path
import logging # Для типизации logger
from typing import Dict, Any, Optional, Tuple, Type, List, TypeVar
import inject # Добавлено для @inject.autoparams()
import yaml # Для работы с YAML

from game_server.Logic.CoreServices.utils.yaml_readers import YamlReader # Убедитесь, что YamlReader импортирован


# 🔥 ВАЖНО: Импорты репозиториев здесь больше не нужны,
# так как SeedLoader не будет получать их напрямую в конструкторе и выбирать в _get_repo_by_model.
# Он будет получать готовый репозиторий в методах от SeedsManager.
# from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
#     IAbilityRepository, IBackgroundStoryRepository, ICreatureTypeRepository, IMaterialRepository,
#     IModifierLibraryRepository, IPersonalityRepository, ISkillRepository, ICreatureTypeInitialSkillRepository,
#     IStaticItemTemplateRepository, ISuffixRepository
# )
# from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository
# from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IStateEntityRepository, IGameLocationRepository
# from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository


from game_server.Logic.CoreServices.utils.seed_utils import get_pk_column_name
from game_server.config.settings.process.prestart import SEEDING_DELETION_BATCH_SIZE

from game_server.contracts.dtos.orchestrator.data_models import AbilityData, BackgroundStoryData, CreatureTypeData, CreatureTypeInitialSkillData, GameLocationData, MaterialData, ModifierLibraryData, PersonalityData, SkillData, StaticItemTemplateData, SuffixData
from game_server.contracts.dtos.state_entity.data_models import StateEntityDTO
from game_server.database.models.models import Base, Ability, BackgroundStory, CreatureType, GameLocation, Material, \
    ModifierLibrary, Personality, Skills, CreatureTypeInitialSkill, StaticItemTemplate, Suffix, \
    EquipmentTemplate, StateEntity


from pydantic import BaseModel, ValidationError


PydanticDtoType = TypeVar('PydanticDtoType', bound=BaseModel)


class SeedLoader:
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
        GameLocation: GameLocationData,
    }

    # 🔥 ИЗМЕНЕНИЕ: Конструктор теперь принимает только те зависимости, которые нужны SeedLoader для его основной работы
    # (чтение YAML, валидация DTO), а не все репозитории.
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        yaml_reader: YamlReader # Предполагаем, что YamlReader инжектируется и имеет @inject.autoparams()
    ):
        self.logger = logger
        self.yaml_reader = yaml_reader # Сохраняем инжектированный YamlReader
        self.logger.info("✅ SeedLoader инициализирован")

        # 🔥 УДАЛЕНО: Все сохранения репозиториев напрямую.
        # Они будут передаваться в методы, которые работают с БД.

    @staticmethod
    def load_json_seed(file_path: Path) -> Dict[str, Any]:
        """Загружает данные из JSON/YAML файла."""
        with open(file_path, 'r', encoding='utf-8') as f:
            # Используем yaml.safe_load для YAML файлов
            data = yaml.safe_load(f)
        return data

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
            # 🔥 ИЗМЕНЕНИЕ: Используем self.yaml_reader
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
                self.logger.critical(f"🚨🚨 Pydantic ValidationError for '{model.__name__}' from file '{file_path.name}' "
                                     f"Element: {item_data_dict}. Error: {e.errors()}", exc_info=True)
                raise RuntimeError(f"Critical Pydantic validation error for file {file_path.name}. "
                                   f"Error: {e.errors()}")
            except Exception as e:
                self.logger.critical(f"🚨🚨🚨 Unexpected error during Pydantic validation for '{model.__name__}' from file '{file_path.name}' "
                                     f"Element: {item_data_dict}. Error: {e}", exc_info=True)
                raise RuntimeError(f"Unexpected validation error for file {file_path.name}.")

        self.logger.debug(f"Successfully validated {len(validated_items)} elements for model {model.__name__} from file {file_path.name}.")
        return validated_items

    # 🔥 ИЗМЕНЕНИЕ: upsert_data теперь принимает конкретный репозиторий и сессию
    async def upsert_data(self, session: Any, repository: Any, model: Type[Base], items_to_process: List[BaseModel]) -> Tuple[int, int]:
        """
        Вставляет или обновляет данные в базу данных, используя переданный репозиторий.
        """
        inserted_count = 0
        updated_count = 0

        if not items_to_process:
            self.logger.info(f"ℹ️ No data to UPSERT for model {model.__name__}.")
            return 0, 0

        transformed_data_list: List[Dict[str, Any]] = []

        orm_columns = [c.name for c in model.__table__.columns]

        for item_dto in items_to_process:
            item_dict_from_dto = item_dto.model_dump(by_alias=False)

            transformed_item = {}
            for col_name in orm_columns:
                if col_name in item_dict_from_dto:
                    value = item_dict_from_dto[col_name]
                    if isinstance(value, BaseModel):
                        transformed_item[col_name] = value.model_dump()
                    elif isinstance(value, uuid.UUID):
                        transformed_item[col_name] = str(value)
                    else:
                        transformed_item[col_name] = value

            transformed_data_list.append(transformed_item)

        total_affected_count = 0
        inserted_count = 0
        updated_count = 0

        try:
            if hasattr(repository, 'upsert_many'):
                total_affected_count = await repository.upsert_many(transformed_data_list)
                inserted_count = total_affected_count
                updated_count = 0
            else:
                self.logger.warning(f"Batch UPSERT for {model.__name__} not implemented in repository. Performing single UPSERT.")
                pk_column_name = get_pk_column_name(model) # Получаем PK здесь, если нужен для single upsert

                for item_data in transformed_data_list:
                    pk_value = item_data.get(pk_column_name) # Получаем PK из данных
                    if pk_value is None:
                        self.logger.warning(f"Пропущен элемент без PK для модели {model.__name__} в single UPSERT: {item_data}")
                        continue

                    # Проверяем, существует ли запись, если репозиторий поддерживает get_by_pk
                    existing_record = None
                    if hasattr(repository, 'get_by_pk'):
                        existing_record = await repository.get_by_pk(pk_value)

                    if existing_record:
                        if hasattr(repository, 'update_by_pk'):
                            await repository.update_by_pk(pk_value, item_data)
                            updated_count += 1
                        else:
                            self.logger.error(f"Репозиторий {model.__name__} не поддерживает update_by_pk для single UPSERT.")
                            raise NotImplementedError(f"Update by PK for model {model.__name__} not implemented.")
                    else:
                        if hasattr(repository, 'create'):
                            await repository.create(item_data)
                            inserted_count += 1
                        else:
                            self.logger.error(f"Репозиторий {model.__name__} не поддерживает create для single UPSERT.")
                            raise NotImplementedError(f"Create for model {model.__name__} not implemented.")

                    total_affected_count += 1

            self.logger.info(f"✅ UPSERT completed for {model.__name__}. Affected rows: {total_affected_count}. (Inserted: {inserted_count}, Updated: {updated_count}).")
            return inserted_count, updated_count

        except Exception as e:
            self.logger.critical(f"🚨 CRITICAL UPSERT error for {model.__name__}: {e}", exc_info=True)
            raise

    # 🔥 ИЗМЕНЕНИЕ: _clear_model_data теперь должен быть в SeedsManager (если он там был)
    # async def _clear_model_data(self, model: Type[Base]) -> int: ... (УДАЛЕН)
