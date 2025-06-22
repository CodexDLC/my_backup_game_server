# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/data_processing/creature_type_data_orchestrator.py

import logging
from typing import Any, Dict, List, Optional

# Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
# Импорты репозиториев, которые CreatureTypeDataOrchestrator будет использовать
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    ICreatureTypeRepository,
    ICreatureTypeInitialSkillRepository
)
# Добавляем импорт ORM моделей, которые будут использоваться напрямую для типизации
from game_server.database.models.models import CreatureType, CreatureTypeInitialSkill

# ДОБАВЛЕНО: Импорт DTO для CreatureType и PlayableRace
from game_server.common_contracts.start_orcestrator.dtos import CreatureTypeData, PlayableRaceData # Предполагаем, что PlayableRaceData будет создана


logger = logging.getLogger(__name__)

class CreatureTypeDataOrchestrator:
    def __init__(self, repository_manager: RepositoryManager):
        self.repository_manager = repository_manager
        self.logger = logger
        # Получаем необходимые репозитории через RepositoryManager
        self.creature_type_repo: ICreatureTypeRepository = self.repository_manager.creature_types
        self.creature_type_initial_skill_repo: ICreatureTypeInitialSkillRepository = self.repository_manager.creature_type_initial_skills

        # Внутренние хранилища данных
        self.raw_creature_types_data: List[CreatureTypeData] = []
        self.processed_creature_types_for_generators: List[CreatureTypeData] = []
        self.playable_races_list: List[PlayableRaceData] = []

        logger.info("✅ CreatureTypeDataOrchestrator инициализирован.")

    async def load_raw_data(self) -> None:
        """
        Загружает исходные данные по типам существ из БД и преобразует их в CreatureTypeData DTO.
        """
        self.logger.debug("CreatureTypeDataOrchestrator: Загрузка исходных данных по типам существ из БД...")
        try:
            all_creature_types_orm: List[CreatureType] = await self.creature_type_repo.get_all()
            
            self.raw_creature_types_data = []
            for ct in all_creature_types_orm:
                try:
                    # Преобразуем ORM-объект в словарь, затем в DTO
                    # Используем dict() для преобразования ORM-объекта в словарь, если это возможно,
                    # или вручную перечисляем атрибуты, соответствующие DTO.
                    # Предполагаем, что CreatureTypeData имеет атрибуты, напрямую соответствующие колонкам ORM-модели
                    # Включая 'creature_type_id' вместо 'id'
                    ct_dict = {
                        "creature_type_id": ct.creature_type_id,
                        "name": ct.name,
                        "description": ct.description,
                        "category": ct.category,
                        "subcategory": ct.subcategory,
                        "visual_tags": ct.visual_tags,
                        "rarity_weight": ct.rarity_weight,
                        "is_playable": ct.is_playable,
                        # Добавьте другие поля вашей модели CreatureType, если они есть в CreatureTypeData DTO
                    }
                    self.raw_creature_types_data.append(CreatureTypeData(**ct_dict))
                except Exception as e:
                    # Используем creature_type_id для логирования, так как 'id' может не существовать
                    self.logger.error(f"Ошибка при преобразовании ORM CreatureType в DTO: {e}. Пропускаем: {getattr(ct, 'creature_type_id', 'N/A')}", exc_info=True)
                    continue

            self.logger.info(f"CreatureTypeDataOrchestrator: Загружено {len(self.raw_creature_types_data)} исходных типов существ (в виде DTO).")
        except Exception as e:
            self.logger.error(f"CreatureTypeDataOrchestrator: Ошибка при загрузке исходных данных по типам существ: {e}", exc_info=True)
            raise

    async def process_data_for_generators(self) -> None:
        """
        Обрабатывает загруженные данные (CreatureTypeData DTO), подготавливая их для использования генераторами.
        Это включает фильтрацию играбельных рас (category='RACE', is_playable=True)
        и загрузку их начальных навыков, создавая PlayableRaceData DTO.
        """
        self.logger.debug("CreatureTypeDataOrchestrator: Обработка данных для генераторов...")
        self.processed_creature_types_for_generators = []
        self.playable_races_list = []
        
        if not self.raw_creature_types_data:
            self.logger.warning("CreatureTypeDataOrchestrator: Нет исходных данных для обработки.")
            return

        for creature_type_dto in self.raw_creature_types_data:
            self.processed_creature_types_for_generators.append(creature_type_dto)

            RACE_CATEGORY_VALUE = "RACE"
            
            if creature_type_dto.is_playable and creature_type_dto.category == RACE_CATEGORY_VALUE:
                # ИЗМЕНЕНО: ИСПОЛЬЗУЕМ creature_type_id ВМЕСТО id
                initial_skills_orm: List[CreatureTypeInitialSkill] = await self.creature_type_initial_skill_repo.get_initial_skills_for_creature_type(creature_type_dto.creature_type_id)
                
                initial_skills_data = [
                    {k: v for k, v in skill.__dict__.items() if not k.startswith('_sa_')}
                    for skill in initial_skills_orm
                ]
                
                try:
                    playable_race_dto = PlayableRaceData(
                        creature_type_id=creature_type_dto.creature_type_id, # ИЗМЕНЕНО: creature_type_id
                        name=creature_type_dto.name,
                        category=creature_type_dto.category,
                        subcategory=creature_type_dto.subcategory,
                        is_playable=creature_type_dto.is_playable,
                        rarity_weight=creature_type_dto.rarity_weight,
                        description=creature_type_dto.description,
                        visual_tags=creature_type_dto.visual_tags,
                        initial_skills=initial_skills_data
                    )
                    self.playable_races_list.append(playable_race_dto)
                except Exception as e:
                    self.logger.error(f"Ошибка при создании PlayableRaceData DTO для {creature_type_dto.creature_type_id}: {e}", exc_info=True) # ИЗМЕНЕНО: creature_type_id
                    continue
        
        self.logger.info(f"CreatureTypeDataOrchestrator: Обработано {len(self.processed_creature_types_for_generators)} типов существ. Найдено {len(self.playable_races_list)} игровых рас (в виде DTO).")

    def get_playable_race_list(self) -> List[PlayableRaceData]:
        """
        Возвращает список игровых рас (PlayableRaceData DTO), подготовленных для планировщиков персонажей.
        """
        if not self.playable_races_list:
            self.logger.warning("CreatureTypeDataOrchestrator: Список игровых рас пуст. Возможно, load_raw_data() или process_data_for_generators() не были вызваны или не нашли играбельных рас.")
        return self.playable_races_list