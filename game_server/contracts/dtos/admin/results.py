# contracts/dtos/admin/results.py

from typing import Optional
# Импортируем BaseResultDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO

class AdminOperationResultDTO(BaseResultDTO[None]):
    """
    DTO для результата административной операции.
    Перенесено из game_server/common_contracts/dtos/Admin_dtos.py
    """
    pass

