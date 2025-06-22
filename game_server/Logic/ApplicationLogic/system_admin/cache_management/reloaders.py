# =================================================================
# ФАЙЛ: game_server/Logic/ApplicationLogic/system_admin/cache_management/reloaders.py
# (Содержит конкретную логику перезагрузки)
# =================================================================

from game_server.Logic.InfrastructureLogic.app_cache.services.reference_data.reference_data_cache_manager import ReferenceDataCacheManager
from game_server.Logic.InfrastructureLogic.logging.logging_setup import app_logger as logger

async def perform_location_connections_reload(cache_manager: ReferenceDataCacheManager) -> bool:
    """
    Конкретная функция, выполняющая перезагрузку кэша связей между локациями.

    Args:
        cache_manager: Экземпляр менеджера кэша, который умеет выполнять операцию.

    Returns:
        True, если перезагрузка прошла успешно, иначе False.
    """
    logger.info("ADMIN_COMMAND: Запуск перезагрузки кэша location_connections...")
    try:
        # Вызываем публичный метод менеджера, который мы спроектировали ранее
        success = await cache_manager.reload_location_connections()
        if success:
            logger.info("ADMIN_COMMAND: Перезагрузка кэша location_connections успешно завершена.")
        else:
            logger.error("ADMIN_COMMAND: Ошибка во время перезагрузки кэша location_connections.")
        return success
    except Exception as e:
        logger.critical(f"ADMIN_COMMAND: Критическая ошибка при перезагрузке кэша связей: {e}", exc_info=True)
        return False
