# game_server/Logic/ApplicationLogic/world_orchestrator/workers/character_generator/handler_utils/creature_type_data_orchestrator.py

import logging
import inject
from typing import Any, Dict, List, Callable
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем интерфейсы репозиториев и DTO
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_0lvl.interfaces_meta_data_0lvl import (
    ICreatureTypeRepository,
    ICreatureTypeInitialSkillRepository
)
from game_server.Logic.InfrastructureLogic.db_instance import AsyncSessionLocal

from game_server.Logic.InfrastructureLogic.app_post.utils.transactional_decorator import transactional
from game_server.contracts.dtos.orchestrator.data_models import CreatureTypeData, PlayableRaceData

class CreatureTypeDataOrchestrator:
    # 👇 ШАГ 3: УБИРАЕМ session_factory ИЗ ВНЕДРЕНИЯ ЗАВИСИМОСТЕЙ
    @inject.autoparams(
        'logger',
        'creature_type_repo_factory',
        'creature_type_initial_skill_repo_factory'
    )
    def __init__(
        self,
        logger: logging.Logger,
        creature_type_repo_factory: Callable[[AsyncSession], ICreatureTypeRepository],
        creature_type_initial_skill_repo_factory: Callable[[AsyncSession], ICreatureTypeInitialSkillRepository]
    ):
        self.logger = logger
        # self._session_factory больше не нужен
        self._creature_type_repo_factory = creature_type_repo_factory
        self._creature_type_initial_skill_repo_factory = creature_type_initial_skill_repo_factory

        self.playable_races_list: List[PlayableRaceData] = []
        self.logger.info("✅ CreatureTypeDataOrchestrator инициализирован.")

    @transactional(AsyncSessionLocal)
    async def prepare_data(self, session: AsyncSession):
        """
        Основной метод: загружает и обрабатывает все необходимые данные в одной транзакции.
        """
        self.logger.debug("CreatureTypeDataOrchestrator: Загрузка и обработка данных...")

        # Создаем репозитории с активной сессией
        creature_type_repo = self._creature_type_repo_factory(session)
        initial_skill_repo = self._creature_type_initial_skill_repo_factory(session)

        # --- Бывшая логика load_raw_data ---
        all_creature_types_orm = await creature_type_repo.get_all()
        raw_creature_types_data: List[CreatureTypeData] = []
        for ct in all_creature_types_orm:
            try:
                raw_creature_types_data.append(CreatureTypeData.from_orm(ct))
            except Exception as e:
                self.logger.error(f"Ошибка при преобразовании ORM CreatureType в DTO: {e}. Пропускаем: {getattr(ct, 'creature_type_id', 'N/A')}")

        # --- Бывшая логика process_data_for_generators ---
        self.playable_races_list = []
        for creature_type_dto in raw_creature_types_data:
            if creature_type_dto.is_playable and creature_type_dto.category == "RACE":
                initial_skills_orm = await initial_skill_repo.get_initial_skills_for_creature_type(creature_type_dto.creature_type_id)
                initial_skills_data = [
                    {k: v for k, v in skill.__dict__.items() if not k.startswith('_sa_')}
                    for skill in initial_skills_orm
                ]
                try:
                    self.playable_races_list.append(
                        PlayableRaceData(**creature_type_dto.dict(), initial_skills=initial_skills_data)
                    )
                except Exception as e:
                    self.logger.error(f"Ошибка при создании PlayableRaceData DTO для {creature_type_dto.creature_type_id}: {e}")

        self.logger.info(f"CreatureTypeDataOrchestrator: Найдено {len(self.playable_races_list)} игровых рас.")

    def get_playable_race_list(self) -> List[PlayableRaceData]:
        """Возвращает подготовленный список игровых рас."""
        return self.playable_races_list