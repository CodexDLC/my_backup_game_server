# game_server/Logic/ApplicationLogic/shared_logic/ShardManagement/shard_management_logic.py

import inject
import logging
from typing import Dict, Any, Optional, Callable
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

# Импорты для обработчиков
from game_server.Logic.ApplicationLogic.SystemServices.handler.shard.admin_save_shard_handler import AdminSaveShardHandler
from game_server.Logic.ApplicationLogic.shared_logic.ShardManagement.Handlers.assign_shard_handler import AssignShardHandler
from game_server.Logic.ApplicationLogic.shared_logic.ShardManagement.Handlers.i_shard_management_handler import IShardManagementHandler
from game_server.Logic.ApplicationLogic.shared_logic.ShardManagement.Handlers.cleanup_inactive_players_handler import CleanupInactivePlayersHandler

# Импорты для зависимостей, которые нужны handler_dependencies
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.accounts.interfaces_accounts import IAccountGameDataRepository
from game_server.Logic.InfrastructureLogic.app_post.repository_groups.game_shards.interfaces_game_shards import IGameShardRepository
from game_server.Logic.InfrastructureLogic.app_cache.services.shard_count.shard_count_cache_manager import ShardCountCacheManager
from game_server.Logic.InfrastructureLogic.messaging.i_message_bus import IMessageBus
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO


class ShardOrchestrator:
    """
    Класс-оркестратор для логики управления шардами.
    Теперь зависимости внедряются напрямую через @inject.autoparams.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        session_factory: Callable[[], AsyncSession], # <--- НОВОЕ: Фабрика сессий
        # Фабрики репозиториев
        account_game_data_repo_factory: Callable[[AsyncSession], IAccountGameDataRepository], # <--- ИЗМЕНЕНО
        game_shards_repo_factory: Callable[[AsyncSession], IGameShardRepository], # <--- ИЗМЕНЕНО
        shard_count_cache_manager: ShardCountCacheManager,
        message_bus: IMessageBus,
        # Хендлеры, которые теперь должны быть привязаны с их новыми зависимостями
        assign_shard_handler: AssignShardHandler, # <--- ПРОВЕРИТЬ БИНДИНГ
        cleanup_inactive_players_handler: CleanupInactivePlayersHandler, # <--- ПРОВЕРИТЬ БИНДИНГ
    ):
        self.logger = logger
        self._session_factory = session_factory
        self._account_game_data_repo_factory = account_game_data_repo_factory
        self._game_shards_repo_factory = game_shards_repo_factory
        self.shard_count_cache_manager = shard_count_cache_manager
        self.message_bus = message_bus
        self.cleanup_inactive_players_handler = cleanup_inactive_players_handler

        self.handlers: Dict[str, IShardManagementHandler] = {
            "assign_account_to_shard": assign_shard_handler,
            "cleanup_inactive_players": cleanup_inactive_players_handler,
        }
        
        self.logger.info(f"✅ {self.__class__.__name__} инициализирован с {len(self.handlers)} обработчиками.")

    async def get_or_assign_shard_for_account(
        self, 
        session: AsyncSession, # <--- ДОБАВЛЕНО: Теперь метод принимает активную сессию
        account_id: int,
    ) -> Optional[int]:
        """
        Высокоуровневый метод для получения или назначения шарда игроку.
        Делегирует выполнение соответствующему обработчику, передавая ему активную сессию.
        Транзакционная граница управляется вызывающим кодом.

        :param session: Активная сессия SQLAlchemy, переданная извне.
        :param account_id: ID аккаунта, для которого нужно получить или назначить шард.
        :return: ID назначенного шарда или None в случае ошибки.
        """
        self.logger.info(f"Запрос на получение или назначение шарда для account_id: {account_id} в рамках внешней транзакции.")
        handler = self.handlers["assign_account_to_shard"]
        
        correlation_id = uuid.uuid4()
        trace_id = uuid.uuid4()
        span_id = uuid.uuid4()

        # Теперь передаем сессию обработчику
        result_dto: BaseResultDTO[Dict[str, Any]] = await handler.process(
            session=session, # <--- ПЕРЕДАЕМ СЕССИЮ
            account_id=account_id, 
            correlation_id=correlation_id,
            trace_id=trace_id,
            span_id=span_id
        )
        
        if result_dto and result_dto.success and result_dto.data and 'shard_id' in result_dto.data:
            self.logger.info(f"Шард {result_dto.data['shard_id']} успешно получен/назначен для account_id {account_id}.")
            return result_dto.data['shard_id']
        
        self.logger.error(f"Не удалось получить или назначить шард для account_id {account_id}. Result: {result_dto.message if result_dto else 'No result'}")
        return None

    # --- Метод для ВНЕШНИХ команд из шины ---
    async def process_command(self, command_dto: Any) -> Any:
        """
        Обрабатывает входящую команду из шины, выбирая нужный обработчик
        по типу команды.
        """
        # Этот метод не изменится, так как он только диспетчеризует команды
        # и не работает напрямую с репозиториями или сессиями.
        command_type = getattr(command_dto, 'command_type', None)
        if not command_type or command_type not in self.handlers:
            self.logger.error(f"Получена неизвестная или некорректная команда: {command_type}")
            return None

        self.logger.info(f"Получена команда '{command_type}', делегирование обработчику...")
        handler = self.handlers[command_type]
        
        # Здесь мы не можем передать сессию, так как command_dto не содержит ее.
        # Если handlers, вызываемые этим методом, должны работать с БД,
        # они должны будут открывать собственные сессии.
        # Это нормально для отдельных "команд", которые сами являются единицами работы.
        result_dto = await handler.process(command_dto)
        
        self.logger.info(f"Команда '{command_type}' обработана.")
        
        return result_dto