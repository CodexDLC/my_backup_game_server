# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_run/coordinator_orchestrator.py

from typing import Dict, Any, Type
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.coordinator_handler.auto_tick_handler import AutoLevelingHandler
from game_server.config.logging.logging_setup import app_logger
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus

# Импортируем базовый класс и все конкретные обработчики
from .coordinator_handler.base_handler import ICommandHandler
from .coordinator_handler.auto_exploring_handler import AutoExploringHandler

# Добавьте сюда импорты других обработчиков, если они есть

class CoordinatorOrchestrator:
    """
    Оркестратор рантайм-команд. Принимает команды от Message Bus
    и делегирует их выполнение соответствующим обработчикам (хендлерам).
    """

    def __init__(self, dependencies: Dict[str, Any]):
        """
        Инициализирует оркестратор и все его обработчики.
        
        Args:
            dependencies (Dict[str, Any]): Словарь с уже готовыми зависимостями,
                                          собранными в service_builders.py.
        """
        self.logger = dependencies.get("logger", app_logger)
        self.logger.info("🔧 CoordinatorOrchestrator: Начинаем инициализацию...")

        # <<< НАЧАЛО ИЗМЕНЕНИЙ
        # Этот блок полностью переписан.
        # Мы больше не собираем зависимости вручную. Словарь 'dependencies',
        # который мы получаем, уже содержит все, что нужно.
        # Мы просто сохраняем его, чтобы передать каждому обработчику.
        
        self.handler_dependencies = dependencies

        # Создаем карту обработчиков, передавая каждому полный набор зависимостей.
        # Каждый обработчик сам возьмет из словаря то, что ему нужно.
        self.handlers: Dict[str, ICommandHandler] = {
            "auto_exploring": AutoExploringHandler(self.handler_dependencies),
            "auto_leveling": AutoLevelingHandler(self.handler_dependencies),
            # Добавьте сюда другие обработчики по аналогии
        }
        # КОНЕЦ ИЗМЕНЕНИЙ >>>

        self.logger.info(f"✅ CoordinatorOrchestrator инициализирован. Зарегистрировано обработчиков: {len(self.handlers)}.")

    async def handle_command(self, command_type: str, payload: Dict[str, Any]) -> None:
        """
        Находит и выполняет обработчик для указанного типа команды.
        """
        handler = self.handlers.get(command_type)
        if not handler:
            self.logger.warning(f"Получена команда неизвестного типа: '{command_type}'. Пропускаем.")
            return

        try:
            self.logger.debug(f"Выполнение команды '{command_type}' с данными: {payload}")
            await handler.execute(payload)
        except Exception as e:
            self.logger.error(
                f"Ошибка при выполнении команды '{command_type}': {e}",
                exc_info=True,
                extra={"payload": payload}
            )

