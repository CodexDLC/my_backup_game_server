# -*- coding: utf-8 -*-
from typing import List, Dict, Any # Добавлена Any
from datetime import datetime, timezone


# from sqlalchemy.ext.asyncio import AsyncSession # УДАЛЕНО
# from sqlalchemy import select, update, exists # УДАЛЕНО

# 👇 ИЗМЕНЕНИЕ: Главный импорт для всей конфигурации
from game_server.config.provider import config
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger
from game_server.database.models.models import AutoSession # Оставляем для типизации

# ДОБАВЛЕНО: Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
# ДОБАВЛЕНО: Импорт для получения app_cache_managers (для кэш-менеджеров, если нужны)
from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import get_initialized_app_cache_managers
# ДОБАВЛЕНО: Импорт интерфейса AutoSessionRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository


class SessionDataProcessor:
    """
    Проверяет наличие готовых к обработке сессий, собирает их ID и группирует по категориям.
    Теперь работает через RepositoryManager и кэш-менеджеры.
    """
    def __init__(self, repository_manager: RepositoryManager, app_cache_managers: Dict[str, Any]): # ИЗМЕНЕНО: принимаем менеджеры
        self.repository_manager = repository_manager
        self.app_cache_managers = app_cache_managers
        self.logger = logger
        
        # Получаем необходимый репозиторий AutoSession через RepositoryManager
        self.auto_session_repo: IAutoSessionRepository = self.repository_manager.auto_sessions # ДОБАВЛЕНО

        self.logger.info("✅ SessionDataProcessor инициализирован.")

    async def has_ready_sessions(self) -> bool: # ИЗМЕНЕНО: удален db_session
        """
        Легковесно проверяет, есть ли в базе данных хотя бы одна готовая к обработке сессия.
        """
        self.logger.info("SessionDataProcessor: Быстрая проверка наличия готовых сессий...")
        now_utc = datetime.now(timezone.utc)
        
        # ИЗМЕНЕНО: Используем репозиторий для проверки
        # Предполагается, что auto_session_repo имеет метод get_ready_sessions() или check_for_ready_sessions()
        # который возвращает bool
        
        # Если get_ready_sessions() возвращает список, можно так:
        ready_sessions = await self.auto_session_repo.get_ready_sessions()
        result = len(ready_sessions) > 0 # Проверяем, есть ли готовые сессии

        if result:
            self.logger.info("SessionDataProcessor: Найдены готовые сессии.")
        else:
            self.logger.info("SessionDataProcessor: Готовые сессии отсутствуют.")
        return result

    async def collect_and_categorize_sessions(self) -> Dict[str, List[int]]: # ИЗМЕНЕНО: удален db_session
        """
        Собирает ID и категории всех готовых к тику сессий, обновляет их и возвращает результат.
        """
        self.logger.info("SessionDataProcessor: Запуск полного сбора и обновления сессий...")
        
        categorized_tasks: Dict[str, List[int]] = {
            config.constants.redis.REDIS_TASK_QUEUE_EXPLORATION: [],
            config.constants.redis.REDIS_TASK_QUEUE_TRAINING: [],
            # config.constants.redis.REDIS_TASK_QUEUE_CRAFTING: [], # Если есть
        }

        character_ids_to_update: List[int] = []

        try:
            now_utc = datetime.now(timezone.utc)
            target_categories = [
                config.constants.redis.REDIS_TASK_QUEUE_EXPLORATION, 
                config.constants.redis.REDIS_TASK_QUEUE_TRAINING
                # config.constants.redis.REDIS_TASK_QUEUE_CRAFTING, # Если есть
            ]
            
            # ИЗМЕНЕНО: Используем репозиторий для сбора сессий
            # Предполагается, что get_ready_sessions() может принимать now_utc и target_categories
            # Или же, что он просто возвращает все готовые, и мы фильтруем по category
            sessions_to_process = await self.auto_session_repo.get_ready_sessions()
            # Фильтруем собранные сессии по целевым категориям
            sessions_to_process = [
                (s.character_id, s.active_category) for s in sessions_to_process
                if s.next_tick_at <= now_utc and s.active_category in target_categories
            ]


            if not sessions_to_process:
                self.logger.info("SessionDataProcessor: Нет сессий для обработки в целевых категориях.")
                return {}

            self.logger.info(f"SessionDataProcessor: Собрано {len(sessions_to_process)} сессий для обработки.")
            
            for char_id, category in sessions_to_process:
                if category in categorized_tasks:
                    categorized_tasks[category].append(char_id)
                    character_ids_to_update.append(char_id)
                else:
                    self.logger.warning(f"SessionDataProcessor: Обнаружена сессия с неизвестной категорией '{category}' для char_id '{char_id}'. Пропускаем.")

            if not character_ids_to_update:
                self.logger.info("SessionDataProcessor: Нет персонажей для обновления после категоризации.")
                return {}

            # ИЗМЕНЕНО: Используем репозиторий для обновления времени тика
            # Предполагается, что update_character_tick_time принимает character_id и interval
            # Или метод для массового обновления (batch_update_tick_time)
            
            # Для каждого character_id, обновляем tick_time
            # update_character_tick_time в репозитории должен быть изменен, чтобы работать без explicit commit
            tick_interval_minutes = config.settings.runtime.TICK_INTERVAL_MINUTES
            
            # Наиболее эффективный способ - реализовать массовое обновление в репозитории
            # Например: await self.auto_session_repo.batch_update_tick_time(character_ids_to_update, tick_interval_minutes)
            
            # Если нет batch-метода, то по одному:
            updated_count = 0
            for char_id in character_ids_to_update:
                try:
                    # update_character_tick_time в репозитории ожидает char_id и interval_minutes
                    updated_session = await self.auto_session_repo.update_character_tick_time(
                        character_id=char_id,
                        interval_minutes=tick_interval_minutes
                    )
                    if updated_session:
                        updated_count += 1
                except Exception as update_e:
                    self.logger.error(f"Ошибка обновления тика для char_id {char_id}: {update_e}", exc_info=True)

            # УДАЛЕНО: await db_session.execute(update_stmt)
            # УДАЛЕНО: await db_session.commit()
            
            self.logger.info(f"SessionDataProcessor: Обновлено время тика для {updated_count} сессий.")
            
            return {
                category: ids for category, ids in categorized_tasks.items() if ids
            }

        except Exception as e:
            # УДАЛЕНО: await db_session.rollback()
            self.logger.critical(f"SessionDataProcessor: Критическая ошибка при сборе сессий: {e}", exc_info=True)
            raise # Пробрасываем ошибку для обработки выше в Coordinator/ARQ Job