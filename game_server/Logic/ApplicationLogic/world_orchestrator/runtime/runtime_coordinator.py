# game_server/Logic/ApplicationLogic/world_orchestrator/runtime/runtime_coordinator.py
import logging
from typing import Dict, Any, Callable # Добавлен Callable для фабрик
import inject
from sqlalchemy.ext.asyncio import AsyncSession # Добавлен AsyncSession для типизации фабрик

# Импорты обработчиков из той же директории
from .handlers.base_command_handler import ICommandHandler
from .handlers.auto_exploring_handler import AutoExploringHandler
from .handlers.auto_leveling_handler import AutoLevelingHandler

# Импорты зависимостей, которые нужны RuntimeCoordinator (он сам их будет получать)
# 🔥 ИЗМЕНЕНО: Импортируем ИНТЕРФЕЙСЫ репозиториев
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.world_state.auto_session.interfaces_auto_session import IAutoSessionRepository, IXpTickDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.character.interfaces_character import ICharacterRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.item.item_cache_manager import ItemCacheManager
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.Logic.InfrastructureLogic.app_cache.central_redis_client import CentralRedisClient
from game_server.Logic.InfrastructureLogic.app_cache.services.task_queue.redis_batch_store import RedisBatchStore
from game_server.Logic.InfrastructureLogic.arq_worker.arq_manager import ArqQueueService


class RuntimeCoordinator:
    """Оркестратор рантайм-команд. Принимает команды и делегирует их обработчикам."""
    # 🔥 ИЗМЕНЕНО: Удалено явное перечисление параметров. inject.autoparams() сам использует аннотации типов.
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        # � ИЗМЕНЕНО: Теперь принимаем ФАБРИКИ репозиториев PostgreSQL
        auto_session_repo_factory: Callable[[AsyncSession], IAutoSessionRepository],
        xp_tick_data_repo_factory: Callable[[AsyncSession], IXpTickDataRepository],
        character_repo_factory: Callable[[AsyncSession], ICharacterRepository],
        item_cache_manager: ItemCacheManager,
        message_bus: IMessageBus,
        central_redis_client: CentralRedisClient,
        redis_batch_store: RedisBatchStore,
        arq_service: ArqQueueService,
    ):
        self.logger = logger
        # 🔥 СОХРАНЯЕМ ФАБРИКИ
        self._auto_session_repo_factory = auto_session_repo_factory
        self._xp_tick_data_repo_factory = xp_tick_data_repo_factory
        self._character_repo_factory = character_repo_factory
        self.item_cache_manager = item_cache_manager
        self.message_bus = message_bus
        self.central_redis_client = central_redis_client
        self.redis_batch_store = redis_batch_store
        self.arq_service = arq_service

        self.logger.info("🔧 RuntimeCoordinator: Начинаем инициализацию...")

        # 🔥 ИЗМЕНЕНО: Создаем экземпляры обработчиков через inject.instance()
        # DI-контейнер сам разрешит их зависимости.
        # ВАЖНО: Эти обработчики (AutoExploringHandler, AutoLevelingHandler)
        # теперь должны быть транзакционными границами и принимать session_factory
        # и фабрики репозиториев в своих конструкторах.
        self.handlers: Dict[str, ICommandHandler] = {
            "auto_exploring": inject.instance(AutoExploringHandler),
            "auto_leveling": inject.instance(AutoLevelingHandler),
        }
        self.logger.info(f"✅ RuntimeCoordinator инициализирован. Зарегистрировано обработчиков: {len(self.handlers)}.")

    async def handle_command(self, command_type: str, payload: Dict[str, Any]) -> None:
        """Находит и выполняет обработчик для указанного типа команды."""
        handler = self.handlers.get(command_type)
        if not handler:
            self.logger.warning(f"Получена команда неизвестного типа: '{command_type}'. Пропускаем.")
            return
        try:
            # 🔥 ВАЖНО: Если обработчики являются транзакционными границами,
            # они сами будут открывать сессию и использовать фабрики репозиториев.
            await handler.execute(payload)
        except Exception as e:
            self.logger.error(f"Ошибка при выполнении команды '{command_type}': {e}", exc_info=True)
