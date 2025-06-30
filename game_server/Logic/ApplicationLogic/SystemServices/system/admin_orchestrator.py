# =================================================================
# ФАЙЛ: game_server/Logic/ApplicationLogic/system_admin/admin_orchestrator.py
# (Главный "фасад" для всех админ-команд)
# =================================================================

# Здесь мы будем импортировать все наши функции-обработчики


from game_server.Logic.ApplicationLogic.SystemServices.system.cache_management.reloaders import perform_location_connections_reload
from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager
from game_server.config.logging.logging_setup import app_logger as logger


class AdminOrchestrator:
    """
    Единый командный центр для всех административных операций.
    Принимает команды и делегирует их выполнение конкретным функциям.
    """
    def __init__(self, reference_data_cache_manager: ReferenceDataCacheManager):
        """
        Инициализируется всеми необходимыми менеджерами и сервисами.
        """
        self.reference_data_cache_manager = reference_data_cache_manager
        logger.info("✅ AdminOrchestrator инициализирован.")

    async def reload_cache(self, cache_type: str) -> bool:
        """
        Главный метод-обертка для вызова различных перезагрузок кэша.
        
        Args:
            cache_type: Тип кэша для перезагрузки (например, 'location_connections').
        
        Returns:
            Статус выполнения операции.
        """
        if cache_type == 'location_connections':
            # Вызываем конкретную функцию, передавая ей нужную зависимость
            return await perform_location_connections_reload(self.reference_data_cache_manager)
        
        # В будущем здесь можно будет добавить другие типы кэша
        # elif cache_type == 'item_base':
        #     return await perform_item_base_reload(self.reference_data_cache_manager)
            
        else:
            logger.warning(f"ADMIN_COMMAND: Попытка перезагрузить неизвестный тип кэша: {cache_type}")
            return False