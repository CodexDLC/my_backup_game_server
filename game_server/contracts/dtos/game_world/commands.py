# contracts/dtos/game_world/commands.py

import uuid
from pydantic import Field

# Импортируем BaseCommandDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseCommandDTO

class GetWorldDataCommandDTO(BaseCommandDTO):
    """
    DTO for the command to request the entire static game world skeleton.
    Перенесено из game_server/common_contracts/dtos/game_world_dtos.py
    """
    command: str = "get_world_data" # Command name that the backend will expect
    # correlation_id, trace_id, span_id, client_id - наследуются от BaseCommandDTO

