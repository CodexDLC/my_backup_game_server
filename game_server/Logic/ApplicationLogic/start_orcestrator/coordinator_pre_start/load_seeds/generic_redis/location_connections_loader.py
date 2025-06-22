# game_server/Logic/ApplicationLogic/start_orcestrator/coordinator_pre_start/load_seeds/generic_redis/location_connections_loader.py

from typing import Any, Dict, List
from game_server.config.provider import config
from game_server.Logic.CoreServices.services.generic_redis_loader import GenericRedisLoader

# Импортируем DTO, которое мы только что определили (или обновили)
from game_server.common_contracts.start_orcestrator.dtos import LocationConnectionData

# Используем ваш уникальный логгер
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

class LocationConnectionsLoader:
    """
    СПЕЦИАЛИСТ по загрузке данных о связях между локациями.
    Использует универсальный GenericRedisLoader.
    """
    def __init__(self):
        self.loader = GenericRedisLoader()
        # Предполагаем, что путь к YAML-файлам для связей определен в config
        self.data_path = config.constants.redis.LOCATION_CONNECTIONS_YAML_PATH 
        # Убедитесь, что LOCATION_CONNECTIONS_YAML_PATH определен в config/constants/redis.py
        logger.info(f"LocationConnectionsLoader инициализирован. Путь к данным: {self.data_path}")

    async def load_all(self) -> List[Dict[str, Any]]:
        """
        Загружает все связи из YAML-файлов, валидирует их с помощью DTO,
        и возвращает как список словарей, готовых для Redis.
        """
        logger.info("Запуск загрузки Location Connections через GenericRedisLoader...")
        
        all_connections_dtos = await self.loader.load_from_directory(
            directory_path=self.data_path,
            dto_type=LocationConnectionData # Передаем класс DTO
        )
        
        if not all_connections_dtos:
            logger.warning("⚠️ LocationConnectionsLoader не вернул DTO. Возможно, нет данных в YAML.")
            return []

        # Конвертируем Pydantic DTO в словари, как ItemBaseLoader
        # 'mode="json"' здесь не нужен, так как model_dump по умолчанию хорошо преобразует в dict
        # и _prepare_data_for_msgpack будет заниматься финальной сериализацией.
        return [dto.model_dump(by_alias=True) for dto in all_connections_dtos]