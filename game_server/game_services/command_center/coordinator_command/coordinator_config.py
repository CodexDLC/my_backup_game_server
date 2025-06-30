# game_server/game_services/command_center/coordinator/coordinator_config.py

# Импортируем классы-обработчики, которые будем использовать
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.coordinator_handler.auto_exploring_handler import AutoExploringHandler
from game_server.Logic.ApplicationLogic.start_orcestrator.coordinator_run.coordinator_handler.auto_tick_handler import AutoLevelingHandler


# Импортируем имя очереди из нашей центральной топологии RabbitMQ
# (Предполагается, что вы добавите очередь для координатора в rabbitmq_topology.py)


from game_server.common_contracts.dtos.coordinator_dtos import ProcessAutoExploringDTO, ProcessAutoLevelingDTO
from game_server.config.settings.rabbitmq.rabbitmq_names import Queues


# --- Часть 1: Обязательные параметры для BaseMicroserviceListener ---

# Имя очереди, которую будет слушать Координатор
SERVICE_QUEUE = Queues.COORDINATOR_COMMANDS # Например, 'q.coordinator.commands'

# Политики обработки
MAX_CONCURRENT_TASKS = 50
COMMAND_PROCESSING_TIMEOUT = 60.0 # У Координатора могут быть более долгие задачи, поэтому таймаут больше


# --- Часть 2: Специфичные параметры для логики Координатора ---

# Теперь константы для имен команд живут здесь, а не в глобальном конфиге
COMMAND_PROCESS_AUTO_LEVELING = "PROCESS_AUTO_LEVELING"
COMMAND_PROCESS_AUTO_EXPLORING = "PROCESS_AUTO_EXPLORING"

# ИЗМЕНЕНИЕ: Теперь маппинг хранит и обработчик, и DTO
COMMAND_HANDLER_MAPPING = {
    COMMAND_PROCESS_AUTO_LEVELING: {
        "handler": AutoLevelingHandler,
        "dto": ProcessAutoLevelingDTO
    },
    COMMAND_PROCESS_AUTO_EXPLORING: {
        "handler": AutoExploringHandler,
        "dto": ProcessAutoExploringDTO
    },
}