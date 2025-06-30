# game_server/Logic/ApplicationLogic/SystemServices/handler/admin/reload_cache_handler.py

from typing import Dict, Any

from game_server.Logic.ApplicationLogic.SystemServices.handler.i_system_handler import ISystemServiceHandler
from game_server.common_contracts.dtos.Admin_dtos import AdminOperationResultDTO, ReloadCacheCommandDTO

# Импортируем интерфейс (можно будет создать более общий ICommandHandler в будущем)


# DTO для команды и результата


# Зависимости, которые нужны этому обработчику
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager
from game_server.Logic.ApplicationLogic.SystemServices.system.cache_management.reloaders import perform_location_connections_reload


class AdminReloadCacheHandler(ISystemServiceHandler):
    """
    Обработчик для выполнения команды на перезагрузку определенного типа кэша.
    """
    def __init__(self, dependencies: Dict[str, Any]):
        super().__init__(dependencies)
        try:
            # Извлекаем нужную нам зависимость - менеджер кэша справочных данных
            self.reference_data_cache_manager: ReferenceDataCacheManager = dependencies['app_cache_managers']['reference_data_cache_manager']
        except KeyError as e:
            self.logger.critical(f"Критическая ошибка: В {self.__class__.__name__} не передана зависимость {e}.")
            raise

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