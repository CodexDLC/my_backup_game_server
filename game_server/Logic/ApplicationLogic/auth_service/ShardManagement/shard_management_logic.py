# game_server\Logic\ApplicationLogic\auth_service\ShardManagement\shard_management_logic.py

import logging
from typing import Dict, Any, Optional

from game_server.Logic.ApplicationLogic.SystemServices.handler.shard.admin_save_shard_handler import AdminSaveShardHandler
from game_server.Logic.ApplicationLogic.auth_service.ShardManagement.Handlers.assign_shard_handler import AssignShardHandler
from game_server.Logic.ApplicationLogic.auth_service.ShardManagement.Handlers.i_shard_management_handler import IShardManagementHandler

# Импортируем DTO для команд


# Импортируем все обработчики


# from .Handlers.admin_load_shard_handler import AdminLoadShardHandler # Раскомментировать, когда будет создан

class ShardOrchestrator:
    """
    Класс-оркестратор для логики управления шардами.
    Диспетчеризует задачи на соответствующие обработчики.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        handler_dependencies = {**dependencies}

        self.handlers: Dict[str, IShardManagementHandler] = {
            # Логика для игроков
            "assign_account_to_shard": AssignShardHandler(handler_dependencies),
            
            # Логика для админских команд
            "admin_save_shard": AdminSaveShardHandler(handler_dependencies),
            # "admin_load_shard": AdminLoadShardHandler(handler_dependencies), # Раскомментировать
        }
        
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован с {len(self.handlers)} обработчиками.")

    # --- Метод для ВНУТРЕННИХ вызовов (например, из AuthOrchestrator) ---
    async def get_or_assign_shard_for_account(
        self, 
        account_id: int, 
        preferred_shard_id: str | None = None
    ) -> Optional[str]:
        """
        Высокоуровневый метод для получения или назначения шарда игроку.
        Делегирует выполнение соответствующему обработчику.
        """
        handler = self.handlers["assign_account_to_shard"]
        return await handler.process(
            account_id=account_id, 
            preferred_shard_id=preferred_shard_id
        )

    # --- НОВЫЙ Метод для ВНЕШНИХ команд из шины ---
    async def process_command(self, command_dto: Any) -> Any:
        """
        Обрабатывает входящую команду из шины, выбирая нужный обработчик
        по типу команды.
        """
        command_type = getattr(command_dto, 'command_type', None)
        if not command_type or command_type not in self.handlers:
            self.logger.error(f"Получена неизвестная или некорректная команда: {command_type}")
            # В реальном проекте здесь нужно вернуть DTO с ошибкой,
            # содержащий correlation_id для обратной связи
            return None

        self.logger.info(f"Получена команда '{command_type}', делегирование обработчику...")
        handler = self.handlers[command_type]
        result_dto = await handler.process(command_dto)
        
        # Здесь будет логика отправки result_dto обратно в шину команд
        # self.message_bus.publish(..., message=result_dto)
        self.logger.info(f"Команда '{command_type}' обработана.")
        
        return result_dto