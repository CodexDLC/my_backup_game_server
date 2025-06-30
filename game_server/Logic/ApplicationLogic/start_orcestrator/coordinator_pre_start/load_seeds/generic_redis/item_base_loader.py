from typing import Any, Dict, List
from game_server.common_contracts.dtos.orchestrator_dtos import ItemBaseData
from game_server.config.provider import config
from game_server.Logic.CoreServices.services.generic_redis_loader import GenericRedisLoader

class ItemBaseLoader:
    """
    СПЕЦИАЛИСТ (обновленный).
    Теперь тоже использует универсальный сервис, код стал намного чище.
    """
    def __init__(self):
        self.loader = GenericRedisLoader()
        self.data_path = config.constants.redis.ITEM_BASE_YAML_PATH

    async def load_all(self) -> List[Dict[str, Any]]:
        all_item_base_dtos = await self.loader.load_from_directory(
            directory_path=self.data_path,
            dto_type=ItemBaseData
        )
        return [dto.model_dump(mode='json', by_alias=True) for dto in all_item_base_dtos]
