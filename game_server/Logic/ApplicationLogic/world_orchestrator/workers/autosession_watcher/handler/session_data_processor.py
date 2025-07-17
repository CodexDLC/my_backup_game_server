# -*- coding: utf-8 -*-
import logging # Для типизации logger
from typing import List, Dict, Any
from datetime import datetime, timezone

# 👇 ИЗМЕНЕНИЕ: Главный импорт для всей конфигурации
from game_server.config.provider import config
# 🔥 ИЗМЕНЕНИЕ: НЕ импортируем глобальный logger здесь, он будет передан
# from game_server.config.logging.logging_setup import app_logger as logger
from game_server.database.models.models import AutoSession # Оставляем для типизации


# 🔥 ИЗМЕНЕНИЕ: Импортируем ИНТЕРФЕЙСЫ КОНКРЕТНЫХ РЕПОЗИТОРИЕВ
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository, IXpTickDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository # Добавлено, если нужен
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository # Добавлено, если нужен

# ДОБАВЛЕНО: Импорт для получения app_cache_managers (для кэш-менеджеров, если нужны)
# 🔥 ИЗМЕНЕНИЕ: Убираем прямой вызов геттера, он будет передан
# from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import get_initialized_app_cache_managers

# 🔥 ДОБАВЛЕНО: Импорт RabbitMQMessageBus, если он нужен напрямую в Processor
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus


class SessionDataProcessor:
    """
    Проверяет наличие готовых к обработке сессий, собирает их ID и группирует по категориям.
    Теперь работает через напрямую переданные репозитории и кэш-менеджеры.
    """
    def __init__(
        self, 
        # 🔥 ИЗМЕНЕНИЕ: Теперь принимаем конкретные репозитории
        auto_session_repo: IAutoSessionRepository,
        xp_tick_data_repo: IXpTickDataRepository, # Если нужен для XP
        character_repo: ICharacterRepository, # Если нужен для персонажей
        account_game_data_repo: IAccountGameDataRepository, # Если нужен для данных аккаунта
        
        app_cache_managers: Dict[str, Any], # ИЗМЕНЕНО: теперь это общий словарь
        message_bus: RabbitMQMessageBus, # Если нужен напрямую здесь
        logger: logging.Logger # 🔥 ДОБАВЛЕНО: Логгер теперь зависимость
    ):
        # 🔥 ИЗМЕНЕНИЕ: Сохраняем переданные репозитории
        self.auto_session_repo = auto_session_repo
        self.xp_tick_data_repo = xp_tick_data_repo
        self.character_repo = character_repo
        self.account_game_data_repo = account_game_data_repo

        self.app_cache_managers = app_cache_managers
        self.message_bus = message_bus
        self.logger = logger # 🔥 ИЗМЕНЕНИЕ: Логгер сохраняем переданный
        
        self.logger.info("✅ SessionDataProcessor инициализирован.")

    async def has_ready_sessions(self) -> bool:
        self.logger.info("SessionDataProcessor: Быстрая проверка наличия готовых сессий...")
        now_utc = datetime.now(timezone.utc)
        
        # 🔥 ИЗМЕНЕНИЕ: Используем auto_session_repo напрямую
        ready_sessions = await self.auto_session_repo.get_ready_sessions()
        result = len(ready_sessions) > 0

        if result:
            self.logger.info("SessionDataProcessor: Найдены готовые сессии.")
        else:
            self.logger.info("SessionDataProcessor: Готовые сессии отсутствуют.")
        return result

    async def collect_and_categorize_sessions(self) -> Dict[str, List[int]]:
        self.logger.info("SessionDataProcessor: Запуск полного сбора и обновления сессий...")
        
        categorized_tasks: Dict[str, List[int]] = {
            config.constants.redis.REDIS_TASK_QUEUE_EXPLORATION: [],
            config.constants.redis.REDIS_TASK_QUEUE_TRAINING: [],
        }

        character_ids_to_update: List[int] = []

        try:
            now_utc = datetime.now(timezone.utc)
            target_categories = [
                config.constants.redis.REDIS_TASK_QUEUE_EXPLORATION, 
                config.constants.redis.REDIS_TASK_QUEUE_TRAINING
            ]
            
            # 🔥 ИЗМЕНЕНИЕ: Используем auto_session_repo напрямую
            sessions_to_process = await self.auto_session_repo.get_ready_sessions()
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

            tick_interval_minutes = config.settings.runtime.TICK_INTERVAL_MINUTES
            
            updated_count = 0
            for char_id in character_ids_to_update:
                try:
                    # 🔥 ИЗМЕНЕНИЕ: Используем auto_session_repo напрямую
                    updated_session = await self.auto_session_repo.update_character_tick_time(
                        character_id=char_id,
                        interval_minutes=tick_interval_minutes
                    )
                    if updated_session:
                        updated_count += 1
                except Exception as update_e:
                    self.logger.error(f"Ошибка обновления тика для char_id {char_id}: {update_e}", exc_info=True)

            self.logger.info(f"SessionDataProcessor: Обновлено время тика для {updated_count} сессий.")
            
            return {
                category: ids for category, ids in categorized_tasks.items() if ids
            }

        except Exception as e:
            self.logger.critical(f"SessionDataProcessor: Критическая ошибка при сборе сессий: {e}", exc_info=True)
            raise