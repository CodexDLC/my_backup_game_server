import logging
from .base_step_handler import IPreStartStepHandler
# 🔥 УДАЛЯЕМ этот импорт, так как он приводит к получению None
# from game_server.Logic.InfrastructureLogic.app_cache.app_cache_initializer import reference_data_cache_manager # УДАЛЕНО

# ДОБАВЛЕНО: Импорт интерфейса ReferenceDataCacheManager для типизации
from game_server.Logic.InfrastructureLogic.app_cache.interfaces.interfaces_reference_data_cache import IReferenceDataCacheManager


logger = logging.getLogger(__name__)

class CacheReferenceDataHandler(IPreStartStepHandler):
    def __init__(self, dependencies: dict):
        super().__init__(dependencies) # Вызов конструктора базового класса IPreStartStepHandler
        # self.logger = dependencies.get("logger", logger) # Эта строка не нужна, так как logger уже устанавливается в базовом классе
        # 🔥 ПОЛУЧАЕМ reference_data_cache_manager ИЗ ЗАВИСИМОСТЕЙ
        self.reference_data_cache_manager: IReferenceDataCacheManager = self.dependencies.get("reference_data_cache_manager") # ИЗМЕНЕНО: добавлена типизация

        # ОПЦИОНАЛЬНО: Добавить проверку, если хотите быть уверенными
        if self.reference_data_cache_manager is None:
            self.logger.critical("🚨 CRITICAL: CacheReferenceDataHandler не получил reference_data_cache_manager через зависимости.")
            raise ValueError("reference_data_cache_manager не передан в CacheReferenceDataHandler.")


    async def execute(self) -> bool:
        self.logger.info("⚡ Шаг 2: Кэширование справочных данных...")
        try:
            # 🔥 ИСПОЛЬЗУЕМ СОХРАНЕННЫЙ ЭКЗЕМПЛЯР
            await self.reference_data_cache_manager.cache_all_reference_data()
            self.logger.info("✅ Справочные данные успешно кэшированы.")
            return True
        except Exception as e:
            self.logger.critical(f"🚨 Шаг 2: Ошибка при кэшировании справочных данных: {e}", exc_info=True)
            return False