# -*- coding: utf-8 -*-
import uuid
from pathlib import Path
import logging
from typing import Callable, List, Any, Dict, Optional, Set, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
import inject
from sqlalchemy import select # Добавлен импорт select для _get_all_pks_from_db

from game_server.Logic.CoreServices.utils.seed_utils import get_pk_column_name
from game_server.Logic.CoreServices.services.data_version_manager import DataVersionManager
# 🔥 ИЗМЕНЕНИЕ: Импортируем все необходимые интерфейсы репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    IAbilityRepository, IBackgroundStoryRepository, ICreatureTypeRepository, IMaterialRepository,
    IModifierLibraryRepository, IPersonalityRepository, ISkillRepository, ICreatureTypeInitialSkillRepository, IStaticItemTemplateRepository,
    ISuffixRepository
)
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import IEquipmentTemplateRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.core_world.interfaces_core_world import IGameLocationRepository, IStateEntityRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.system.interfaces_system import IDataVersionRepository


from game_server.config.constants.seeds import FILE_LOAD_ORDER, SEEDS_DIR

from game_server.database.models.models import Base, Ability, BackgroundStory, CreatureType, GameLocation, Material, \
    ModifierLibrary, Personality, Skills, CreatureTypeInitialSkill, StaticItemTemplate, Suffix, \
    EquipmentTemplate, StateEntity

from .seed_loader import SeedLoader # Предполагаем, что SeedLoader инжектируется или создается здесь

from pydantic import BaseModel


class SeedsManager:
    """
    Менеджер для загрузки и управления "сидами" (начальными данными) в базу данных.
    Является транзакционной границей.
    """
    @inject.autoparams()
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession], # Фабрика сессий
        ability_repo_factory: Callable[[AsyncSession], IAbilityRepository],
        background_story_repo_factory: Callable[[AsyncSession], IBackgroundStoryRepository],
        creature_type_repo_factory: Callable[[AsyncSession], ICreatureTypeRepository],
        material_repo_factory: Callable[[AsyncSession], IMaterialRepository],
        modifier_library_repo_factory: Callable[[AsyncSession], IModifierLibraryRepository],
        personality_repo_factory: Callable[[AsyncSession], IPersonalityRepository],
        skill_repo_factory: Callable[[AsyncSession], ISkillRepository],
        creature_type_initial_skill_repo_factory: Callable[[AsyncSession], ICreatureTypeInitialSkillRepository],
        static_item_template_repo_factory: Callable[[AsyncSession], IStaticItemTemplateRepository],
        suffix_repo_factory: Callable[[AsyncSession], ISuffixRepository],
        equipment_template_repo_factory: Callable[[AsyncSession], IEquipmentTemplateRepository],
        game_location_repo_factory: Callable[[AsyncSession], IGameLocationRepository],
        state_entity_repo_factory: Callable[[AsyncSession], IStateEntityRepository],
        data_version_repo_factory: Callable[[AsyncSession], IDataVersionRepository],
        logger: logging.Logger,
        loader: SeedLoader # Предполагаем, что SeedLoader инжектируется
    ):
        self._session_factory = session_factory
        self._ability_repo_factory = ability_repo_factory
        self._background_story_repo_factory = background_story_repo_factory
        self._creature_type_repo_factory = creature_type_repo_factory
        self._material_repo_factory = material_repo_factory
        self._modifier_library_repo_factory = modifier_library_repo_factory
        self._personality_repo_factory = personality_repo_factory
        self._skill_repo_factory = skill_repo_factory
        self._creature_type_initial_skill_repo_factory = creature_type_initial_skill_repo_factory
        self._static_item_template_repo_factory = static_item_template_repo_factory
        self._suffix_repo_factory = suffix_repo_factory
        self._equipment_template_repo_factory = equipment_template_repo_factory
        self._game_location_repo_factory = game_location_repo_factory
        self._state_entity_repo_factory = state_entity_repo_factory
        self._data_version_repo_factory = data_version_repo_factory
        self.logger = logger
        self.loader = loader # Сохраняем инжектированный loader
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован.")
        
        # Словарь для быстрого доступа к фабрикам репозиториев по классу модели
        self._model_to_repo_factory: Dict[type[Base], Callable[[AsyncSession], Any]] = {
            Ability: self._ability_repo_factory,
            BackgroundStory: self._background_story_repo_factory,
            CreatureType: self._creature_type_repo_factory,
            Material: self._material_repo_factory,
            ModifierLibrary: self._modifier_library_repo_factory,
            Personality: self._personality_repo_factory,
            Skills: self._skill_repo_factory,
            CreatureTypeInitialSkill: self._creature_type_initial_skill_repo_factory,
            StaticItemTemplate: self._static_item_template_repo_factory,
            Suffix: self._suffix_repo_factory,
            EquipmentTemplate: self._equipment_template_repo_factory,
            GameLocation: self._game_location_repo_factory,
            StateEntity: self._state_entity_repo_factory,
            # DataVersion не включаем сюда, так как он используется отдельно
        }

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
        self.logger.info(f"📌 Ищем seed-файлы внутри {SEEDS_DIR}...")
        all_yml_files = list(SEEDS_DIR.rglob('*.yml'))
        ordered_files = []
        ordered_file_names = set(FILE_LOAD_ORDER)
        file_paths_by_name = {f.name: f for f in all_yml_files}

        critical_files_missing = False
        for name in FILE_LOAD_ORDER:
            if name in file_paths_by_name:
                ordered_files.append(file_paths_by_name[name])
            else:
                self.logger.critical(f"🚨 Критическая ошибка: Файл '{name}' из FILE_LOAD_ORDER не найден. Без него продолжение невозможно.")
                critical_files_missing = True

        if critical_files_missing:
            raise RuntimeError("Критические seed-файлы отсутствуют. Процесс загрузки прерван.")

        remaining_files = sorted([f for f in all_yml_files if f.name not in ordered_file_names], key=lambda x: x.name)
        final_file_list = ordered_files + remaining_files

        if not final_file_list:
            self.logger.critical("🚨 Критическая ошибка: Нет .yml файлов в SEEDS_DIR. Загрузка сидов невозможна.")
            raise RuntimeError("Отсутствуют YML-файлы сидов.")
            
        self.logger.info(f"✅ Найдено {len(final_file_list)} seed-файлов для загрузки.")
        return final_file_list

    # 🔥 ИЗМЕНЕНИЕ: Добавлен return True в конце успешного выполнения
    async def import_seeds(self, session: AsyncSession, models_module: Any) -> bool:
        self.logger.info("🚀 Запуск процесса импорта Seed-данных...")
        
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

            self.logger.info(f"📊 Обнаружено {len(grouped_data)} различных моделей для загрузки: {', '.join(grouped_data.keys())}.")

            for table_name, data_info in grouped_data.items():
                model = data_info['model']
                all_items_for_model: List[BaseModel] = []

                self.logger.info(f"⚙️ Обработка данных для таблицы '{table_name}'.")

                for file_path in data_info['files']:
                    items_from_file = await self.loader.load_and_prepare_data_from_yaml(file_path, model)
                    if items_from_file is None:
                        raise RuntimeError(f"Критическая ошибка при загрузке данных из файла {file_path.name}. Импорт прерван.")
                    all_items_for_model.extend(items_from_file)
                
                self.logger.debug(f"DEBUG: После чтения YAML для {table_name}, собрано {len(all_items_for_model)} элементов.")
                
                data_version_repo = self._data_version_repo_factory(session) # Создаем репозиторий здесь

                if not all_items_for_model:
                    self.logger.critical(f"🚨 КРИТИЧЕСКАЯ ОШИБКА: Для таблицы {table_name} собрано 0 элементов из YAML-файлов. "
                                        f"Проверьте YAML-файлы на наличие данных в ключе 'data'.")
                    
                    items_for_hash_calculation = [item.model_dump(by_alias=True) for item in all_items_for_model]
                    new_hash_empty = DataVersionManager._calculate_data_hash(items_for_hash_calculation)
                    
                    current_hash_empty = await data_version_repo.get_current_version(table_name)
                    if new_hash_empty != current_hash_empty:
                        self.logger.warning(f"⚠️ Версия для '{table_name}' изменится на хэш пустых данных ({new_hash_empty[:8]}...)."
                                            f" Обновляю версию, чтобы избежать повторной обработки.")
                        await data_version_repo.update_version(table_name, new_hash_empty)
                    # await session.commit() # Коммит изменений версии - это будет сделано в DataLoadersHandler
                    continue

                items_for_hash_calculation = [item.model_dump(by_alias=True) for item in all_items_for_model]
                new_hash = DataVersionManager._calculate_data_hash(items_for_hash_calculation)
                
                current_hash = await data_version_repo.get_current_version(table_name)

                if new_hash == current_hash:
                    self.logger.info(f"✅ Данные для '{table_name}' актуальны (хэш: {new_hash[:8]}...). Пропуск.")
                    # await session.commit() # Коммит, если были изменения версии - это будет сделано в DataLoadersHandler
                    continue
                
                self.logger.info(f"🔄 Обнаружены изменения для '{table_name}'. Старый хэш: {current_hash[:8] if current_hash else 'N/A'}, новый: {new_hash[:8]}....")
                
                pk_column_name = get_pk_column_name(model)

                existing_pks_in_db = await self._get_all_pks_from_db(session, model, pk_column_name)
                
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
                        self.logger.error(f"DTO для модели {model.__name__} не содержит ожидаемый PK атрибут '{pk_column_name}'. Элемент: {item.model_dump()}")
                        raise RuntimeError(f"DTO для модели {model.__name__} не имеет PK атрибута '{pk_column_name}'.")

                pks_to_delete = existing_pks_in_db - new_pks_from_yaml

                if pks_to_delete:
                    deleted_count = await self._perform_deletions(session, model, pk_column_name, list(pks_to_delete))
                    self.deleted_total += deleted_count
                    self.logger.info(f"🗑️ Удалено {deleted_count} записей из '{table_name}'.")

                self.logger.debug(f"DEBUG: Вызов self.loader.upsert_data для {table_name} с {len(all_items_for_model)} элементами.")
                
                repo_factory = self._model_to_repo_factory.get(model)
                if not repo_factory:
                    raise RuntimeError(f"Фабрика репозитория для модели {model.__name__} не найдена.")
                repository = repo_factory(session)

                inserted, updated = await self.loader.upsert_data(session, repository, model, all_items_for_model)

                self.inserted_total += inserted
                self.updated_total += updated
                
                if all_items_for_model:
                    await data_version_repo.update_version(table_name, new_hash)
                    self.logger.info(f"✅ Успешно обновлена версия для таблицы '{table_name}'.")
                # else: # Этот else блок обрабатывает случай, когда all_items_for_model пуст, но хэш изменился.
                #     self.logger.warning(f"⚠️ Внимание: Хэш для '{table_name}' изменился, но в YAML-файлах нет данных. "
                #                         f"Версия для пустых данных ({new_hash[:8]}...) будет установлена, если не актуальна.")
                
                # await session.commit() # Коммит всех изменений в этой транзакции - это будет сделано в DataLoadersHandler
            
            self.logger.info("✅ Процесс импорта Seed-данных завершен успешно.") # 🔥 ДОБАВЛЕН ЛОГ
            return True # 🔥 ДОБАВЛЕН: Явный возврат True при успешном завершении

        except RuntimeError as e:
            self.logger.critical(f"🚨 Критическая ошибка в процессе импорта сидов: {e}")
            raise
        except Exception as e:
            self.logger.critical(f"🚨 Непредвиденная критическая ошибка при импорте сидов: {e}", exc_info=True)
            raise

    async def _get_all_pks_from_db(self, session: AsyncSession, model: Any, pk_column_name: str) -> Set[Any]:
        self.logger.debug(f"Получение всех PK из БД для модели {model.__name__}...")
        try:
            repo_factory = self._model_to_repo_factory.get(model)
            if not repo_factory:
                raise RuntimeError(f"Не удалось найти фабрику репозитория для модели {model.__name__}.")
            
            repository = repo_factory(session)

            if not repository:
                raise RuntimeError(f"Не удалось найти свойство репозитория для модели {model.__name__}.")
            
            pks_set: Set[Any] = set()

            entities = []
            if hasattr(repository, 'get_all'):
                entities = await repository.get_all()
            elif model.__name__ == "CreatureTypeInitialSkill": 
                entities = await repository.get_all()
                pks_set = {(e.creature_type_id, e.skill_key) for e in entities}
                self.logger.debug(f"Получено {len(pks_set)} PK (составной) из БД для модели {model.__name__}.")
                return pks_set
            else:
                self.logger.warning(f"Модель {model.__name__} не имеет универсального метода 'get_all()' в репозитории. "
                                    f"Попытка получить PK напрямую через сессию.")
                # Fallback to direct session query if get_all is not available
                from sqlalchemy import select # Локальный импорт для fallback
                stmt = select(getattr(model, pk_column_name))
                result = await session.execute(stmt)
                pks_set = set(result.scalars().all())
                self.logger.debug(f"Получено {len(pks_set)} PK из БД для модели {model.__name__} напрямую через сессию.")
                return pks_set

            pks_set = {getattr(e, pk_column_name) for e in entities}

            self.logger.debug(f"Получено {len(pks_set)} PK из БД для модели {model.__name__}.")
            return pks_set
        except Exception as e:
            self.logger.error(f"❌ Ошибка при получении первичных ключей из '{model.__tablename__}': {e}", exc_info=True)
            raise

    def _get_repo_by_model(self, model: Any) -> Optional[Callable[[AsyncSession], Any]]:
        """
        Возвращает соответствующую ФАБРИКУ репозитория для данной модели.
        """
        repo_factory = self._model_to_repo_factory.get(model)
        if not repo_factory:
            self.logger.error(f"Фабрика репозитория для модели {model.__name__} не найдена в _model_to_repo_factory.")
        return repo_factory

    async def _perform_deletions(self, session: AsyncSession, model: Any, pk_column_name: str, pks_to_delete: List[Any]) -> int:
        if not pks_to_delete:
            return 0
        
        try:
            repo_factory = self._model_to_repo_factory.get(model)
            if not repo_factory:
                self.logger.critical(f"🚨 Critical error: Repository factory not found for model {model.__name__} for data cleaning.")
                raise RuntimeError(f"Data cleaning impossible: repository factory for model {model.__name__} not found.")
            
            repository = repo_factory(session)

            deleted_count = 0
            
            if hasattr(repository, 'delete_all_records'):
                deleted_count = await repository.delete_all_records()
            elif hasattr(repository, 'delete_all'):
                deleted_count = await repository.delete_all()
            else:
                self.logger.warning(f"Удаление для {model.__name__} не реализовано пакетно. Удаляем по одному.")
                for pk in pks_to_delete:
                    try:
                        if hasattr(repository, 'delete_by_pk'):
                            await repository.delete_by_pk(pk)
                        else:
                            self.logger.error(f"Неизвестный метод удаления для модели {model.__name__} с PK {pk}.")
                            continue
                        deleted_count += 1
                    except Exception as single_delete_e:
                        self.logger.error(f"Ошибка при удалении отдельного PK {pk} для {model.__name__}: {single_delete_e}", exc_info=True)
                
            self.logger.info(f"🗑️ Успешно удалено {deleted_count} записей из '{model.__tablename__}'.")
            return deleted_count
        except Exception as e:
            self.logger.error(f"❌ Ошибка при удалении записей из '{model.__tablename__}': {e}", exc_info=True)
            raise
