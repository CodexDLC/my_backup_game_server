# game_server\Logic\ApplicationLogic\world_orchestrator\workers\autosession_watcher\tick_AutoSession_Watcher.py
import asyncio
import logging
from typing import Dict, List, Any
import inject # <-- ДОБАВЛЕНО: Для inject.autoparams

# Импорты для компонентов ARQ Job
from game_server.Logic.ApplicationLogic.world_orchestrator.workers.autosession_watcher.handler.session_data_processor import SessionDataProcessor
from game_server.config.provider import config

# 🔥 ИЗМЕНЕНИЕ: Используем RabbitMQMessageBus вместо RedisMessageBus
from game_server.Logic.InfrastructureLogic.messaging.rabbitmq_message_bus import RabbitMQMessageBus
from game_server.Logic.InfrastructureLogic.messaging.message_format import create_message

# 🔥 ИЗМЕНЕНИЕ: logger будет инжектирован, не импортируется напрямую глобально здесь
# from game_server.config.logging.logging_setup import app_logger as logger

# 🔥 ИЗМЕНЕНИЕ: Импортируем ИНТЕРФЕЙСЫ конкретных репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository, IXpTickDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository

# 🔥 ДОБАВЛЕНО: Импорт менеджеров кэша, если они нужны в SessionDataProcessor напрямую
from game_server.Logic.InfrastructureLogic.app_cache.services.item.item_cache_manager import ItemCacheManager # Пример

from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore # Уже есть, но убедимся


# Импортируем необходимые константы из вашей конфигурации
from game_server.config.constants.coordinator import (
    COMMAND_PROCESS_AUTO_EXPLORING,
    COMMAND_PROCESS_AUTO_LEVELING
)
from game_server.config.constants.redis_key import (
    REDIS_TASK_QUEUE_EXPLORATION,
    REDIS_TASK_QUEUE_TRAINING
)
from game_server.config.settings.rabbitmq.rabbitmq_names import Exchanges

# 🔥 ИЗМЕНЕНИЕ: Добавляем @inject.autoparams
@inject.autoparams(
    'auto_session_repo',
    'xp_tick_data_repo',
    'character_repo',
    'account_game_data_repo',
    'message_bus',
    'logger', # Логгер будет инжектирован
    # 🔥 ДОБАВИТЬ: Если SessionDataProcessor нуждается в конкретных менеджерах кэша,
    # перечислите их здесь (например, redis_batch_store уже был в ctx)
    'redis_batch_store', # Этот уже был в ctx, теперь инжектируем
    # 'item_cache_manager', # Пример, если нужен
    # 'reference_data_cache_manager', # Пример, если нужен
    # 'shard_count_cache_manager' # Пример, если нужен
)
async def collect_and_dispatch_sessions(
    auto_session_repo: IAutoSessionRepository,
    xp_tick_data_repo: IXpTickDataRepository,
    character_repo: ICharacterRepository,
    account_game_data_repo: IAccountGameDataRepository,
    message_bus: RabbitMQMessageBus,
    logger: logging.Logger, # 🔥 ИЗМЕНЕНИЕ: Логгер теперь инжектируется
    redis_batch_store: RedisBatchStore, # 🔥 ИЗМЕНЕНИЕ: Пример менеджера кэша, если нужен в процессоре
    # 🔥 УДАЛЕНО: app_cache_managers больше не передается как общий словарь
    # app_cache_managers: Dict[str, Any]
):
    """
    Оркестрирует процесс проверки и сбора готовых сессий.
    Эта ARQ-задача будет запускаться по расписанию (например, каждые 30 секунд).
    """
    logger.info("ARQ Job 'collect_and_dispatch_sessions': Запуск...")
    
    # Инициализация SessionDataProcessor с НОВЫМИ зависимостями
    processor = SessionDataProcessor(
        auto_session_repo=auto_session_repo,
        xp_tick_data_repo=xp_tick_data_repo,
        character_repo=character_repo,
        account_game_data_repo=account_game_data_repo,
        
        # 🔥 ИЗМЕНЕНИЕ: Передаем конкретные менеджеры кэша, если SessionDataProcessor их требует
        # Если SessionDataProcessor ожидает именно словарь, то возможно, этот подход не сработает напрямую.
        # В таком случае, SessionDataProcessor должен быть изменен для приема конкретных менеджеров
        # или использовать inject.autoparams() сам.
        # Пока предполагаем, что он ожидает конкретные зависимости:
        redis_batch_store=redis_batch_store,
        # ... другие менеджеры кэша, если они нужны в SessionDataProcessor и инжектированы здесь ...
        message_bus=message_bus,
        logger=logger
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
                        "command": COMMAND_PROCESS_AUTO_EXPLORING,
                        "character_ids": exploration_ids
                    }
                    message = create_message(command_payload)
                    await message_bus.publish(
                        Exchanges.COMMANDS,
                        f"system.command.coordinator.{COMMAND_PROCESS_AUTO_EXPLORING.lower()}",
                        message
                    )
                else:
                    logger.debug("ARQ Job: Нет задач на авто-исследование для отправки.")

                # --- Отправка задач на авто-тренировку/прокачку ---
                training_ids = categorized_tasks.get(REDIS_TASK_QUEUE_TRAINING)
                if training_ids:
                    logger.info(f"ARQ Job: Отправка {len(training_ids)} задач на авто-тренировку/прокачку.")
                    command_payload = {
                        "command": COMMAND_PROCESS_AUTO_LEVELING,
                        "character_ids": training_ids
                    }
                    message = create_message(command_payload)
                    await message_bus.publish(
                        Exchanges.COMMANDS,
                        f"system.command.coordinator.{COMMAND_PROCESS_AUTO_LEVELING.lower()}",
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
