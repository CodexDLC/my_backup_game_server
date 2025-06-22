# -*- coding: utf-8 -*-
from typing import Dict, List, Any # Добавлена Any для app_cache_managers
# from sqlalchemy.ext.asyncio import AsyncSession # УДАЛЕНО

# 👇 ИЗМЕНЕНИЕ: Главный импорт для всей конфигурации
from game_server.config.provider import config

# Остальные импорты
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.auto_tick_module.handler.session_data_processor import SessionDataProcessor
from game_server.Logic.InfrastructureLogic.messaging.message_bus import RedisMessageBus
from game_server.Logic.InfrastructureLogic.messaging.message_format import create_message
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

# ДОБАВЛЕНО: Импорт RepositoryManager
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager
# ДОБАВЛЕНО: Импорт для получения app_cache_managers, если SessionDataProcessor их использует
from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import get_initialized_app_cache_managers


async def collect_and_dispatch_sessions(
    repository_manager: RepositoryManager, # ИЗМЕНЕНО: теперь принимает RepositoryManager
    message_bus: RedisMessageBus,
    app_cache_managers: Dict[str, Any] # ДОБАВЛЕНО: принимаем app_cache_managers
):
    """
    Оркестрирует процесс проверки и сбора готовых сессий.
    """
    logger.info("ARQ Job 'collect_and_dispatch_sessions': Запуск...")
    
    # ИЗМЕНЕНО: Инициализация SessionDataProcessor с RepositoryManager и app_cache_managers
    processor = SessionDataProcessor(
        repository_manager=repository_manager,
        app_cache_managers=app_cache_managers
    )

    try:
        # ИЗМЕНЕНО: Вызовы методов processor теперь без db_session
        if await processor.has_ready_sessions():
            
            categorized_tasks = await processor.collect_and_categorize_sessions()

            if categorized_tasks:
                logger.info(f"ARQ Job: Обнаружены категоризированные задачи: {list(categorized_tasks.keys())}")
                
                # --- Отправка задач на авто-исследование ---
                exploration_ids = categorized_tasks.get(config.constants.redis.REDIS_TASK_QUEUE_EXPLORATION)
                if exploration_ids:
                    logger.info(f"ARQ Job: Отправка {len(exploration_ids)} задач на авто-исследование.")
                    command_payload = {
                        "command": config.constants.coordinator.COMMAND_PROCESS_AUTO_EXPLORING,
                        "character_ids": exploration_ids
                    }
                    message = create_message(command_payload)
                    await message_bus.publish(config.constants.coordinator.COORDINATOR_COMMAND_QUEUE, message)
                else:
                    logger.debug("ARQ Job: Нет задач на авто-исследование для отправки.")


                # --- Отправка задач на авто-тренировку/прокачку ---
                training_ids = categorized_tasks.get(config.constants.redis.REDIS_TASK_QUEUE_TRAINING)
                if training_ids:
                    logger.info(f"ARQ Job: Отправка {len(training_ids)} задач на авто-тренировку/прокачку.")
                    command_payload = {
                        "command": config.constants.coordinator.COMMAND_PROCESS_AUTO_LEVELING,
                        "character_ids": training_ids
                    }
                    message = create_message(command_payload)
                    await message_bus.publish(config.constants.coordinator.COORDINATOR_COMMAND_QUEUE, message)
                else:
                    logger.debug("ARQ Job: Нет задач на авто-тренировку/прокачку для отправки.")

            else:
                logger.info("ARQ Job: Готовых к обработке категоризированных сессий не найдено.")
        else:
            logger.info("ARQ Job: Готовых к обработке сессий не найдено.")
            
    except Exception as e:
        logger.critical(f"ARQ Job 'collect_and_dispatch_sessions': Критическая ошибка: {e}", exc_info=True)
    
    finally:
        logger.info("ARQ Job 'collect_and_dispatch_sessions': Цикл завершен.")