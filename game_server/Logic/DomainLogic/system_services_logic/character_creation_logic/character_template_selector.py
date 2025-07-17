# game_server\Logic\DomainLogic\system_services_logic\character_creation_logic\character_template_selector.py

import logging
import random
from typing import List, Tuple, Optional, Callable

import inject
from sqlalchemy.ext.asyncio import AsyncSession

# Импортируем репозиторий и модель
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.meta_data_1lvl.interfaces_meta_data_1lvl import ICharacterPoolRepository
from game_server.config.constants import game_rules
from game_server.database.models.models import CharacterPool
# Импортируем логгер и константы
from game_server.config.logging.logging_setup import app_logger as logger


class CharacterTemplateSelector:
    """
    Отвечает за логику выбора шаблона персонажа из пула CharacterPool.
    """
    @inject.autoparams()
    def __init__(self,
                 logger: logging.Logger,
                 session_factory: Callable[[], AsyncSession],
                 character_pool_repo_factory: Callable[[AsyncSession], ICharacterPoolRepository]):
        self._logger = logger
        self._session_factory = session_factory
        self._character_pool_repo_factory = character_pool_repo_factory
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    async def select_template(self, session: AsyncSession) -> CharacterPool:
        """
        Выполняет взвешенный случайный выбор шаблона персонажа.

        :param session: Активная сессия SQLAlchemy.
        :return: Полный объект выбранного шаблона CharacterPool.
        :raises ValueError: Если пул пуст или не удалось выбрать шаблон.
        """
        self._logger.info("Начинается выбор шаблона персонажа из пула...")

        character_pool_repo = self._character_pool_repo_factory(session)

        # 1. Получаем случайную выборку (id, rarity_score)
        sample_size = game_rules.CHARACTER_POOL_SAMPLE_SIZE
        self._logger.debug(f"Размер выборки из пула: {sample_size}")
        sample = await character_pool_repo.get_random_sample(sample_size)

        if not sample:
            self._logger.error("Пул доступных персонажей пуст. Невозможно выбрать шаблон.")
            raise ValueError("Character pool is empty.")

        # --- НОВОЕ ЛОГИРОВАНИЕ: Проверяем, что пришло из базы ---
        self._logger.debug(f"Получена выборка из {len(sample)} шаблонов: {sample}")

        # 2. Производим взвешенный случайный выбор на стороне приложения
        pool_ids, weights = zip(*sample)
        try:
            chosen_id = random.choices(pool_ids, weights=weights, k=1)[0]
            self._logger.info(f"Выбран шаблон с ID: {chosen_id} из выборки размером {len(pool_ids)}.")
        except IndexError:
            self._logger.error("Не удалось выполнить взвешенный выбор (random.choices).")
            raise ValueError("Weighted choice failed, the sample might be corrupted.")

        # 3. Получаем полные данные для выбранного шаблона
        chosen_template = await character_pool_repo.get_full_template_by_id(chosen_id)

        if not chosen_template:
            self._logger.error(f"Не удалось получить полные данные для шаблона ID {chosen_id}, хотя он был выбран.")
            raise ValueError(f"Could not fetch full data for chosen template ID {chosen_id}.")

        # --- НОВОЕ ЛОГИРОВАНИЕ: Показываем, какой именно шаблон выбрали ---
        self._logger.info(f"Шаблон '{chosen_template.name}' (ID: {chosen_template.character_pool_id}, Качество: {chosen_template.quality_level}) успешно выбран.")
        self._logger.debug(f"Полные данные шаблона: base_stats={chosen_template.base_stats}, initial_skills={chosen_template.initial_skill_levels}")
        
        return chosen_template
