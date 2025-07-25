# game_server/Logic/ApplicationLogic/SystemServices/handler_cache_requests/get_location_summary_handler.py

import logging
import inject
import json # Импортируем json для десериализации
from typing import Dict, Any

from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_dinamic_location_manager import IDynamicLocationManager

from ..handler.i_system_handler import ISystemServiceHandler
from .....contracts.shared_models.base_commands_results import BaseResultDTO
from .....contracts.shared_models.base_responses import ErrorDetail
from .....contracts.dtos.game_commands.cache_request_commands import (
    GetLocationSummaryCommandDTO,
    GetLocationSummaryResultDTO
)



class GetLocationSummaryCommandHandler(ISystemServiceHandler):
    """
    Обработчик команды для получения полных данных о локации из центрального кэша Redis.
    """
    @inject.autoparams()
    def __init__(
        self,
        logger: logging.Logger,
        dynamic_location_manager: IDynamicLocationManager
    ):
        self._logger = logger
        self._location_manager = dynamic_location_manager
        self._logger.info(f"✅ {self.__class__.__name__} инициализирован.")

    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def process(self, command_dto: GetLocationSummaryCommandDTO) -> BaseResultDTO:
        """
        Основной метод. Получает ID локации, читает данные из кэша и возвращает их.
        """
        payload = command_dto.payload
        location_id = payload.location_id
        self.logger.info(f"Получен запрос на данные по локации {location_id} из кэша.")

        try:
            # Вызываем менеджер кэша для получения данных
            cached_data = await self._location_manager.get_location_summary(location_id)

            if cached_data is None:
                return GetLocationSummaryResultDTO(
                    correlation_id=command_dto.correlation_id,
                    success=False,
                    message=f"Данные для локации {location_id} не найдены в кэше.",
                    error=ErrorDetail(code="CACHE_MISS", message="Location data not found in cache."),
                    client_id=command_dto.client_id
                )
            
            # Десериализуем JSON-строки обратно в списки/объекты
            deserialized_data = {
                key: json.loads(value) if isinstance(value, str) and value.startswith('[') else value
                for key, value in cached_data.items()
            }
            
            return GetLocationSummaryResultDTO(
                correlation_id=command_dto.correlation_id,
                success=True,
                message="Данные по локации успешно получены из кэша.",
                data=deserialized_data,
                client_id=command_dto.client_id
            )

        except Exception as e:
            self.logger.critical(f"Критическая ошибка при получении данных о локации {location_id} из кэша: {e}", exc_info=True)
            return GetLocationSummaryResultDTO(
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Внутренняя ошибка сервера: {e}",
                error=ErrorDetail(code="SERVER_ERROR", message=str(e)),
                client_id=command_dto.client_id
            )