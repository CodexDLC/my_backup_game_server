# game_server/Logic/InfrastructureLogic/arq_worker/arq_jobs.py

import asyncio
import logging # Re-import logger if it's directly used and not passed
from typing import Dict, List, Any

# 👇 ИЗМЕНЕНИЕ: Главный импорт для всей конфигурации
from game_server.config.provider import config

# Импорты для компонентов ARQ Job
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.auto_tick_module.handler.session_data_processor import SessionDataProcessor

# 🔥 ИЗМЕНЕНИЕ: Используем RabbitMQMessageBus вместо RedisMessageBus
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus
from game_server.Logic.InfrastructureLogic.messaging.message_format import create_message

# Добавлен импорт для logger, так как он используется напрямую
from game_server.config.logging.logging_setup import app_logger as logger

# ДОБАВЛЕНО: Импорт RepositoryManager (для типизации и передачи в SessionDataProcessor)
from game_server.Logic.InfrastructureLogic.app_post.repository_manager import RepositoryManager

# ДОБАВЛЕНО: Импорт для app_cache_managers (для типизации и передачи в SessionDataProcessor)
from typing import Dict, Any # Already imported, but good to ensure

# Импортируем необходимые константы из вашей конфигурации
from game_server.config.constants.coordinator import (    
    COMMAND_PROCESS_AUTO_EXPLORING,
    COMMAND_PROCESS_AUTO_LEVELING
)
from game_server.config.constants.redis_key import ( # Предполагается, что эти константы здесь
    REDIS_TASK_QUEUE_EXPLORATION,
    REDIS_TASK_QUEUE_TRAINING
)
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges


async def collect_and_dispatch_sessions(
    repository_manager: RepositoryManager,
    message_bus: RabbitMQMessageBus, # 🔥 ИЗМЕНЕНИЕ: Типизация на RabbitMQMessageBus
    app_cache_managers: Dict[str, Any]
):
    """
    Оркестрирует процесс проверки и сбора готовых сессий.
    Эта ARQ-задача будет запускаться по расписанию (например, каждые 30 секунд).
    """
    logger.info("ARQ Job 'collect_and_dispatch_sessions': Запуск...")
    
    # Инициализация SessionDataProcessor с RepositoryManager и app_cache_managers
    processor = SessionDataProcessor(
        repository_manager=repository_manager,
        app_cache_managers=app_cache_managers,
        # Если SessionDataProcessor нуждается в message_bus, передайте его здесь
        # message_bus=message_bus
    )

    try:
        if await processor.has_ready_sessions():
            categorized_tasks = await processor.collect_and_categorize_sessions()

            if categorized_tasks:
                logger.info(f"ARQ Job: Обнаружены категоризированные задачи: {list(categorized_tasks.keys())}")
                
                # --- Отправка задач на авто-исследование ---
                exploration_ids = categorized_tasks.get(REDIS_TASK_QUEUE_EXPLORATION)
                if exploration_ids:
                    logger.info(f"ARQ Job: Отправка {len(exploration_ids)} задач на авто-исследование.")
                    command_payload = {
                        "command": COMMAND_PROCESS_AUTO_EXPLORING, # Используем константу команды
                        "character_ids": exploration_ids
                    }
                    message = create_message(command_payload)
                    # 🔥 ИЗМЕНЕНИЕ: Публикация в RabbitMQ с указанием exchange и routing_key
                    # Routing key должен соответствовать привязке очереди координатора
                    await message_bus.publish(
                        Exchanges.COMMANDS, # Имя обменника: "commands.exchange"
                        f"system.command.coordinator.{COMMAND_PROCESS_AUTO_EXPLORING.lower()}", # Детальный routing_key
                        message
                    )
                else:
                    logger.debug("ARQ Job: Нет задач на авто-исследование для отправки.")


                # --- Отправка задач на авто-тренировку/прокачку ---
                training_ids = categorized_tasks.get(REDIS_TASK_QUEUE_TRAINING)
                if training_ids:
                    logger.info(f"ARQ Job: Отправка {len(training_ids)} задач на авто-тренировку/прокачку.")
                    command_payload = {
                        "command": COMMAND_PROCESS_AUTO_LEVELING, # Используем константу команды
                        "character_ids": training_ids
                    }
                    message = create_message(command_payload)
                    # 🔥 ИЗМЕНЕНИЕ: Публикация в RabbitMQ с указанием exchange и routing_key
                    await message_bus.publish(
                        Exchanges.COMMANDS, # Имя обменника: "commands.exchange"
                        f"system.command.coordinator.{COMMAND_PROCESS_AUTO_LEVELING.lower()}", # Детальный routing_key
                        message
                    )
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
