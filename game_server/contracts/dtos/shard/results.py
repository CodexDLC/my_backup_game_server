# contracts/dtos/shard/results.py

from typing import Optional

from pydantic import Field
# Импортируем BaseResultDTO из новой общей папки
from game_server.contracts.shared_models.base_commands_results import BaseResultDTO
# Импортируем ShardDataDTO из data_models в этом же домене
from .data_models import ShardDataDTO

class ShardOperationResultDTO(BaseResultDTO[ShardDataDTO]):
    """
    DTO для результата операции с шардом (сохранение, обновление).
    Перенесено из game_server/common_contracts/dtos/shard_dtos.py
    """
    shard_data: Optional[ShardDataDTO] = Field(None, description="Данные о шарде после операции.")

