# -*- coding: utf-8 -*-
import logging
from pathlib import Path
from typing import List, Any, Dict, Optional, Set, Tuple # Добавлена Tuple для _get_all_pks_from_db

from game_server.Logic.CoreServices.utils.seed_utils import get_pk_column_name
from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository
from game_server.config.constants.seeds import FILE_LOAD_ORDER, SEEDS_DIR

from game_server.database.models.models import Base
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger # Импортируем app_logger

from .seed_loader import SeedLoader

from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    IAbilityRepository, IBackgroundStoryRepository, ICreatureTypeRepository, IMaterialRepository,
    IModifierLibraryRepository, IPersonalityRepository, ISkillRepository, ICreatureTypeInitialSkillRepository, IStaticItemTemplateRepository,
    ISuffixRepository
)
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository

from pydantic import BaseModel # Добавлено для типизации BaseModel


class SeedsManager:
    def __init__(self, repository_manager: RepositoryManager):
        logger.debug("✅ Инициализация SeedsManager...")
        self.repository_manager = repository_manager
        
        self.loader = SeedLoader(self.repository_manager)
        self.logger = logger  # <--- ИСПРАВЛЕНО

        self.data_version_repo: IDataVersionRepository = self.repository_manager.data_versions

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
        self.game_location_repo: IGameLocationRepository = self.repository_manager.game_locations 

        self.inserted_total = 0
        self.updated_total = 0
        self.deleted_total = 0

    @classmethod
    def convert_filename_to_model(cls, filename: str) -> str:
        name = filename.replace('.yml', '')
        if '_' in name and name.split('_')[0].isdigit():
            name = '_'.join(name.split('_')[1:])
        return ''.join(word.capitalize() for word in name.split('_'))

    def _collect_seed_files(self) -> list[Path]:
        self.logger.info(f"📌 Ищем seed-файлы внутри {SEEDS_DIR}...") # Используем self.logger
        all_yml_files = list(SEEDS_DIR.rglob('*.yml'))
        ordered_files = []
        ordered_file_names = set(FILE_LOAD_ORDER)
        file_paths_by_name = {f.name: f for f in all_yml_files}

        critical_files_missing = False
        for name in FILE_LOAD_ORDER:
            if name in file_paths_by_name:
                ordered_files.append(file_paths_by_name[name])
            else:
                self.logger.critical(f"🚨 Критическая ошибка: Файл '{name}' из FILE_LOAD_ORDER не найден. Без него продолжение невозможно.") # Используем self.logger
                critical_files_missing = True

        if critical_files_missing:
            raise RuntimeError("Критические seed-файлы отсутствуют. Процесс загрузки прерван.")

        remaining_files = sorted([f for f in all_yml_files if f.name not in ordered_file_names], key=lambda x: x.name)
        final_file_list = ordered_files + remaining_files

        if not final_file_list:
            self.logger.critical("🚨 Критическая ошибка: Нет .yml файлов в SEEDS_DIR. Загрузка сидов невозможна.") # Используем self.logger
            raise RuntimeError("Отсутствуют YML-файлы сидов.")
            
        self.logger.info(f"✅ Найдено {len(final_file_list)} seed-файлов для загрузки.") # Используем self.logger
        return final_file_list

    async def import_seeds(self, models_module):
        self.logger.info("🚀 Запуск процесса импорта Seed-данных...") # Используем self.logger
        
        try:
            seed_files = self._collect_seed_files()
            if not seed_files:
                raise RuntimeError("Нет seed-files для обработки.")

            grouped_data: Dict[str, Dict[str, Any]] = {}

            for file_path in seed_files:
                model_name = self.convert_filename_to_model(file_path.name)
                model = getattr(models_module, model_name, None)

                if not model:
                    raise RuntimeError(f"Модель '{model_name}' для файла '{file_path}' не найдена. Импорт прерван.")
                
                table_name = model.__tablename__
                if table_name not in grouped_data:
                    grouped_data[table_name] = {'model': model, 'files': [], 'all_items': []}
                grouped_data[table_name]['files'].append(file_path)

            self.logger.info(f"📊 Обнаружено {len(grouped_data)} различных моделей для загрузки: {', '.join(grouped_data.keys())}.") # Используем self.logger

            for table_name, data_info in grouped_data.items():
                model = data_info['model']
                all_items_for_model: List[BaseModel] = []

                self.logger.info(f"⚙️ Обработка данных для таблицы '{table_name}'.") # Используем self.logger

                for file_path in data_info['files']:
                    items_from_file = await self.loader.load_and_prepare_data_from_yaml(file_path, model)
                    if items_from_file is None:
                        raise RuntimeError(f"Критическая ошибка при загрузке данных из файла {file_path.name}. Импорт прерван.")
                    all_items_for_model.extend(items_from_file)
                
                self.logger.debug(f"DEBUG: После чтения YAML для {table_name}, собрано {len(all_items_for_model)} элементов.") # Используем self.logger
                if not all_items_for_model:
                    self.logger.critical(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Для таблицы {table_name} собрано 0 элементов из YAML-файлов. " # Используем self.logger
                                    f"Проверьте YAML-файлы на наличие данных в ключе 'data'.")
                    
                    items_for_hash_calculation = [item.model_dump(by_alias=True) for item in all_items_for_model]
                    new_hash_empty = DataVersionManager._calculate_data_hash(items_for_hash_calculation)
                    
                    current_hash_empty = await self.data_version_repo.get_current_version(table_name)
                    if new_hash_empty != current_hash_empty:
                         self.logger.warning(f"⚠️ Версия для '{table_name}' изменится на хэш пустых данных ({new_hash_empty[:8]}...)." # Используем self.logger
                                        f" Обновляю версию, чтобы избежать повторной обработки.")
                         await self.data_version_repo.update_version(table_name, new_hash_empty)
                    else:
                         self.logger.info(f"✅ Данные для '{table_name}' пусты и хэш уже актуален ({new_hash_empty[:8]}...). Пропуск.") # Используем self.logger
                    continue

                items_for_hash_calculation = [item.model_dump(by_alias=True) for item in all_items_for_model]
                new_hash = DataVersionManager._calculate_data_hash(items_for_hash_calculation)
                
                current_hash = await self.data_version_repo.get_current_version(table_name)

                if new_hash == current_hash:
                    self.logger.info(f"✅ Данные для '{table_name}' актуальны (хэш: {new_hash[:8]}...). Пропуск.") # Используем self.logger
                    continue
                
                self.logger.info(f"🔄 Обнаружены изменения для '{table_name}'. Старый хэш: {current_hash[:8] if current_hash else 'N/A'}, новый: {new_hash[:8]}....") # Используем self.logger
                
                pk_column_name = get_pk_column_name(model)

                existing_pks_in_db = await self._get_all_pks_from_db(model, pk_column_name)
                
                new_pks_from_yaml = set()
                for item in all_items_for_model:
                    if pk_column_name == "creature_type_id" and model.__name__ == "CreatureTypeInitialSkill":
                        if hasattr(item, 'creature_type_id') and hasattr(item, 'skill_key'):
                             new_pks_from_yaml.add((item.creature_type_id, item.skill_key))
                    elif hasattr(item, pk_column_name):
                        pk_value = getattr(item, pk_column_name)
                        if pk_value is not None:
                            new_pks_from_yaml.add(pk_value)
                    else:
                        self.logger.error(f"DTO для модели {model.__name__} не содержит ожидаемый PK атрибут '{pk_column_name}'. Элемент: {item.model_dump()}") # Используем self.logger
                        raise RuntimeError(f"DTO для модели {model.__name__} не имеет PK атрибута '{pk_column_name}'.")

                pks_to_delete = existing_pks_in_db - new_pks_from_yaml

                if pks_to_delete:
                    deleted_count = await self._perform_deletions(model, pk_column_name, list(pks_to_delete))
                    self.deleted_total += deleted_count
                    self.logger.info(f"🗑️ Удалено {deleted_count} записей из '{table_name}'.") # Используем self.logger

                self.logger.debug(f"DEBUG: Вызов self.loader.upsert_data для {table_name} с {len(all_items_for_model)} элементами.") # Используем self.logger
                
                inserted, updated = await self.loader.upsert_data(model, all_items_for_model)

                self.inserted_total += inserted
                self.updated_total += updated
                
                if all_items_for_model:
                    await self.data_version_repo.update_version(table_name, new_hash)
                    self.logger.info(f"✅ Успешно обновлена версия для таблицы '{table_name}'.") # Используем self.logger
                else:
                    self.logger.warning(f"⚠️ Внимание: Хэш для '{table_name}' изменился, но в YAML-файлах нет данных. " # Используем self.logger
                                   f"Версия для пустых данных ({new_hash[:8]}...) будет установлена, если не актуальна.")
        except RuntimeError as e:
            self.logger.critical(f"🚨 Критическая ошибка в процессе импорта сидов: {e}") # Используем self.logger
            raise
        except Exception as e:
            self.logger.critical(f"🚨 Непредвиденная критическая ошибка при импорте сидов: {e}", exc_info=True) # Используем self.logger
            raise

    async def _get_all_pks_from_db(self, model: Base, pk_column_name: str) -> Set[Any]:
        self.logger.debug(f"Получение всех PK из БД для модели {model.__name__}...") # Используем self.logger
        try:
            repo_property_name = self._get_repo_property_name(model)
            if not repo_property_name:
                raise RuntimeError(f"Не удалось найти свойство репозитория для модели {model.__name__} в RepositoryManager.")
            
            repository = getattr(self.repository_manager, repo_property_name)
            
            pks_set: Set[Any] = set()

            entities = []
            if hasattr(repository, 'get_all'):
                entities = await repository.get_all()
            elif model.__name__ == "Ability": entities = await self.ability_repo.get_all_abilities()
            elif model.__name__ == "BackgroundStory": entities = await self.background_story_repo.get_all_background_stories()
            elif model.__name__ == "CreatureType": entities = await self.creature_type_repo.get_all_creature_types()
            elif model.__name__ == "Material": entities = await self.material_repo.get_all()
            elif model.__name__ == "ModifierLibrary": entities = await self.modifier_library_repo.get_all()
            elif model.__name__ == "Personality": entities = await self.personality_repo.get_all_personalities()
            elif model.__name__ == "Skills": entities = await self.skill_repo.get_all_skills()
            elif model.__name__ == "CreatureTypeInitialSkill": 
                entities = await self.creature_type_initial_skill_repo.get_all()
                pks_set = {(e.creature_type_id, e.skill_key) for e in entities}
                self.logger.debug(f"Получено {len(pks_set)} PK (составной) из БД для модели {model.__name__}.") # Используем self.logger
                return pks_set
            elif model.__name__ == "StaticItemTemplate": entities = await self.static_item_template_repo.get_all_templates()
            elif model.__name__ == "Suffix": entities = await self.suffix_repo.get_all()
            elif model.__name__ == "StateEntity": entities = await self.repository_manager.state_entities.get_all()
            else:
                raise RuntimeError(f"Модель {model.__name__} не поддерживается для получения PK в SeedsManager.")

            pks_set = {getattr(e, pk_column_name) for e in entities}


            self.logger.debug(f"Получено {len(pks_set)} PK из БД для модели {model.__name__}.") # Используем self.logger
            return pks_set
        except Exception as e:
            self.logger.error(f"❌ Ошибка при получении первичных ключей из '{model.__tablename__}': {e}", exc_info=True) # Используем self.logger
            raise

    def _get_repo_property_name(self, model: Base) -> Optional[str]:
        """
        Добавляем сюда нашу новую модель, чтобы менеджер знал,
        какое свойство в RepositoryManager ей соответствует.
        """
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
            "GameLocation": "game_locations", 
        }
        return mapping.get(model.__name__)

    async def _perform_deletions(self, model: Base, pk_column_name: str, pks_to_delete: List[Any]) -> int:
        if not pks_to_delete:
            return 0
        
        try:
            repo_property_name = self._get_repo_property_name(model)
            if not repo_property_name:
                raise RuntimeError(f"Не удалось найти свойство репозитория для модели {model.__name__} для удаления.")
            
            repository = getattr(self.repository_manager, repo_property_name)
            
            deleted_count = 0
            
            if model.__name__ == "StaticItemTemplate":
                deleted_count = await repository.delete_by_item_code_batch(pks_to_delete)
            elif model.__name__ == "CreatureTypeInitialSkill":
                self.logger.warning(f"Удаление для {model.__name__} (составной PK) не реализовано пакетно. Удаляем по одному.") # Используем self.logger
                for pk_tuple in pks_to_delete:
                    try:
                        await repository.delete_initial_skill(creature_type_id=pk_tuple[0], skill_key=pk_tuple[1])
                        deleted_count += 1
                    except Exception as single_delete_e:
                        self.logger.error(f"Ошибка при удалении отдельного PK {pk_tuple} для {model.__name__}: {single_delete_e}", exc_info=True) # Используем self.logger
            else:
                if hasattr(repository, 'delete_batch_by_pks'):
                    deleted_count = await repository.delete_batch_by_pks(pks_to_delete)
                elif hasattr(repository, 'delete_by_pks'):
                    deleted_count = await repository.delete_by_pks(pks_to_delete)
                else:
                    self.logger.warning(f"Удаление для {model.__name__} не реализовано пакетно. Удаляем по одному.") # Используем self.logger
                    for pk in pks_to_delete:
                        try:
                            if model.__name__ == "Ability": await repository.delete_ability(pk)
                            elif model.__name__ == "BackgroundStory": await repository.delete_background_story(pk)
                            elif model.__name__ == "CreatureType": await repository.delete_creature_type(pk)
                            elif model.__name__ == "Material": await repository.delete_material(pk)
                            elif model.__name__ == "ModifierLibrary": await repository.delete_modifier(pk)
                            elif model.__name__ == "Personality": await repository.delete_personality(pk)
                            elif model.__name__ == "Skills": await repository.delete_skill(pk)
                            elif model.__name__ == "Suffix": await repository.delete_suffix(pk)
                            elif model.__name__ == "StateEntity": await repository.delete_by_access_code(pk)
                            deleted_count += 1
                        except Exception as single_delete_e:
                            self.logger.error(f"Ошибка при удалении отдельного PK {pk} для {model.__name__}: {single_delete_e}", exc_info=True) # Используем self.logger

            self.logger.info(f"🗑️ Успешно удалено {deleted_count} записей из '{model.__tablename__}'.") # Используем self.logger
            return deleted_count
        except Exception as e:
            self.logger.error(f"❌ Ошибка при удалении записей из '{model.__tablename__}': {e}", exc_info=True) # Используем self.logger
            raise