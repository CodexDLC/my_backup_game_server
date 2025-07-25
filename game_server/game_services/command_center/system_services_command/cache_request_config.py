# game_server/game_services/command_center/system_services_command/cache_request_config.py

from typing import Dict, Any

from game_server.Logic.ApplicationLogic.SystemServices.handler_cache_requests.get_location_summary_handler import GetLocationSummaryCommandHandler

from game_server.contracts.dtos.game_commands.cache_request_commands import GetLocationSummaryCommandDTO

# Импортируем DTO для команды

# Импортируем сам класс обработчика, который мы создадим на следующем шаге


# Карта, связывающая имя команды с DTO и классом-обработчиком
CACHE_REQUEST_HANDLER_MAPPING: Dict[str, Dict[str, Any]] = {
    "get_location_summary": {
        "dto": GetLocationSummaryCommandDTO,
        "handler": GetLocationSummaryCommandHandler,
    },
    # Сюда в будущем можно будет добавлять другие команды для работы с кэшем
}