# game_server/Logic/ApplicationLogic/SystemServices/handler/admin/reload_cache_handler.py
# Version: 0.001

import logging # ▼▼▼ НОВЫЙ ИМПОРТ: logging ▼▼▼
from typing import Dict, Any
import inject # ▼▼▼ НОВЫЙ ИМПОРТ: inject ▼▼▼

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler


# Зависимости, которые нужны этому обработчику
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager
from game_server.Logic.ApplicationLogic.SystemServices.system.cache_management.reloaders import perform_location_connections_reload
from game_server.contracts.dtos.admin.commands import ReloadCacheCommandDTO
from game_server.contracts.dtos.admin.results import AdminOperationResultDTO


class AdminReloadCacheHandler(ISystemServiceHandler):
    """
    Обработчик для выполнения команды на перезагрузку определенного типа кэша.
    """
    # ▼▼▼ ИСПОЛЬЗУЕМ @inject.autoparams() И ЯВНО ОБЪЯВЛЯЕМ ЗАВИСИМОСТИ ▼▼▼
    @inject.autoparams()
    def __init__(self, logger: logging.Logger, reference_data_cache_manager: ReferenceDataCacheManager):
        self._logger = logger
        self.reference_data_cache_manager: ReferenceDataCacheManager = reference_data_cache_manager
        self._logger.info("AdminReloadCacheHandler инициализирован.")

    # ▼▼▼ РЕАЛИЗАЦИЯ АБСТРАКТНОГО СВОЙСТВА logger ИЗ ISystemServiceHandler ▼▼▼
    @property
    def logger(self) -> logging.Logger:
        return self._logger

    async def process(self, command_dto: ReloadCacheCommandDTO) -> AdminOperationResultDTO:
        """
        Выполняет логику перезагрузки кэша.
        """
        cache_type = command_dto.cache_type
        self.logger.info(f"Получена команда на перезагрузку кэша типа: '{cache_type}'.")

        try:
            success = False
            if cache_type == 'location_connections':
                # Вызываем конкретную функцию-загрузчик, передавая ей нужную зависимость
                success = await perform_location_connections_reload(self.reference_data_cache_manager)
            
            # В будущем здесь можно будет добавить другие типы кэша
            # elif cache_type == 'item_base':
            #     success = await perform_item_base_reload(...)
                
            else:
                self.logger.warning(f"Попытка перезагрузить неизвестный тип кэша: {cache_type}")
                return AdminOperationResultDTO(
                    correlation_id=command_dto.correlation_id,
                    success=False,
                    message=f"Неизвестный тип кэша: {cache_type}"
                )

            if success:
                message = f"Кэш '{cache_type}' успешно перезагружен."
                self.logger.info(message)
            else:
                message = f"Произошла ошибка при перезагрузке кэша '{cache_type}'."
                self.logger.error(message)

            return AdminOperationResultDTO(
                correlation_id=command_dto.correlation_id,
                success=success,
                message=message
            )

        except Exception as e:
            self.logger.exception(f"Непредвиденная ошибка при перезагрузке кэша '{cache_type}': {e}")
            return AdminOperationResultDTO(
                correlation_id=command_dto.correlation_id,
                success=False,
                message=f"Критическая ошибка при обработке команды: {e}"
            )
